#!/usr/bin/env python

from flask import render_template, redirect, request, Flask, url_for, abort, send_from_directory
from flask_wtf import FlaskForm, csrf
from wtforms import StringField, FieldList, FormField, SubmitField, IntegerField, FloatField, validators, BooleanField
import yaml, sys, binascii, os, hashlib
from server_scripts import Parse, misc
from server_scripts import auth
from server_scripts import database as db

# --------------------- CONFIGURATIONS -------------------------------------------------------------------------------------------------------
global APP
APP = Flask(__name__)

# Cross-site scripting protection
CSRF = csrf.CSRFProtect()
CSRF.init_app(APP)
APP.config['SECRET_KEY'] = os.urandom(32)

# data folder
APP.config['UPLOAD_FOLDER'] = 'data'

# load config from server_config.yaml
global config
with open("server_config.yaml", 'r') as stream:
    try:
        config = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        print(exc)
        sys.exit()

# login manager
auth.login_manager.init_app(APP)

# ----- old codes ----------------
# declare global variables for holding data (temporarily)
# global nPop, nPlant, lifeSpan
# global populations, plants, tech_form, techs, params     
    # techs has class TechnologiesForm and has the input data
    # tech_form is the form to be rendered to web interface

@APP.route('/', methods = ['GET'])
def index():
    return(render_template('index.html'))

#----------- web page to handle project requests ------------------------------------------------------
@APP.route('/projects', methods = ['GET', 'POST'])
@auth.login_required
def projects():
    """ render webpage to display existing project for a user
        User can select a project from this page, we then set user.current_project_name to the selected project
        Also handle requests to create new projects
    """
    # process GET requests
    if request.method == 'GET':
        username = auth.current_user.get_id()
        APP.logger.info('Display projects page for user {}'.format(username))
        existing_projects = db.getProjects(username = username) # pls give me a list of tuple {project_name, p_desc}
        return(render_template('projects.html', create_project = False, existing_projects = existing_projects, populations=populations))

    # process POST requests
    if request.method == 'POST':
        if request.form['command'] == 'Create project':
            project_name = request.form['project_name']
            p_desc = request.form['p_desc']
            # save project to DB
            db.saveProject(auth.current_user.get_id(), project_name, p_desc)
            # switch current project to this project
            auth.current_user.set_project(project_name)
            # redirect to input pages
            return(redirect(url_for('input_size')))
        elif request.form['select project'] is not None:
            # switch to selected project
            auth.current_user.set_project(project_name)
            # redirect to input pages
            return(redirect(url_for('input_size')))
        else:
            abort(400, 'Unknown request')



#----------- web page to ask for input size ---------------------------------------------------------------------------------------------------
class InputSize(FlaskForm):
    NPop = IntegerField('Number of populations', validators = [validators.InputRequired(), validators.NumberRange(min=0)])
    NPlant = IntegerField('Number of plants', validators = [validators.InputRequired(), validators.NumberRange(min=0)])
    LifeSpan = IntegerField('Life Span of project', validators = [validators.InputRequired(), validators.NumberRange(min=0)])    

@APP.route('/input_size', methods=['GET', 'POST'])
@auth.login_required
def input_size():
    """ render webpage to ask for input sizes, save data to global nPop, nPlant, lifeSpan 
        then redirect to population_input """
    # global nPop, nPlant, lifeSpan
    username = auth.current_user.get_id()
    current_project = auth.current_user.get_project()
    inputSize = InputSize()

    # process GET requests
    if request.method == 'GET':
        existing_data = db.getInputSize(username, current_project)    # give me all columns from Ns table , if data not exist, return None. E.g. {numpops:1, numplants:None, durations:2}
        # If data exist, fill in the form
        if existing_data['numpops'] is not None:
            input_size.NPop.data = existing_data['numpops']
        if existing_data['numplants'] is not None:
            input_size.NPop.data = existing_data['numplants']
        if existing_data['durations'] is not None:
            input_size.NPop.data = existing_data['durations']    
        return(render_template('input_size.html', inputSize=inputSize))

    # process POST requests
    if request.method == 'POST':
        if inputSize.validate_on_submit():
            # if validate pass, save data to DB and redirect to next page
            db.saveInputSize(inputSize, username, projectID)
            # -- old codes --
            # nPop = inputSize.NPop.data
            # nPlant = inputSize.NPlant.data
            # lifeSpan = inputSize.LifeSpan.data
            APP.logger.info("validation succeed! Transfer to {}".format(url_for('population_input')))
            return(redirect(url_for('population_input')))
        else:
            # if validate fails, print out errors to web page and log
            APP.logger.info("validation failed! Reload page input size")
            return(render_template('input_size.html', inputSize=inputSize))

#----------- webpage to ask for populations ------------------------------------------------------------------------------------------------------------
class OnePopulation(FlaskForm):
    Name = StringField('Cluster Name', validators = [validators.DataRequired()])
    Pr = IntegerField('Current Population', validators = [validators.DataRequired()])
    GrowthRate = FloatField('Population Growth Rate', validators = [validators.DataRequired()])
    lat = FloatField('Latitude', validators = [validators.DataRequired()])
    lon = FloatField('Longitude', validators = [validators.DataRequired()])
class PopulationsForm(FlaskForm):
    rows = FieldList(FormField(OnePopulation), min_entries = 0)

@APP.route('/population_input', methods=['GET', 'POST'])
@auth.login_required
def population_input():
    """ render webpage to ask for population input, save data to global populations (class PopulationsForm) 
        then redirect to plant_input """
    # global nPop
    # global populations

    populations = PopulationsForm()
    # process GET requests
    if request.method == 'GET':
        APP.logger.info('creating a fresh populations form')
        try: nPop
        except NameError:
            abort(400, 'Number of populations not found')
        else:
            for i in range(nPop):
                populations.rows.append_entry({'r': i+1})
        return(render_template('population_input.html', populations = populations))

    # process POST requests
    if request.method == 'POST':
        if request.form['command'] == 'Next':
            # process saving data command
            if populations.validate():
                # if validation pass, save data to DB and redirect to next page
                # TBD: someFunctionSavetoDB(populations, username, projectID). populations is of class PopulationsForm
                APP.logger.info('transfer to {}'.format(url_for('plant_input')))
                return(redirect(url_for('plant_input')))
            else:
                # if validation fails, print out errors to web page
                return(render_template('population_input.html', populations = populations))
        elif request.form['command'] == 'Parse':
            # process parsing data command (lazy method for inputing data)
            populations = Parse.fill_populations(request.form['ExcelData'], populations)
            return(render_template('population_input.html', populations = populations))
        else:
            abort(400, 'Unknown request')

    # TODO: calculate projected population

# ------------- webpage to ask for plants --------------------------------------------------------------------------------------------------------------------
class OnePlant(FlaskForm):
    LocationName = StringField('Location Name')
    lat = FloatField('Latitude')
    lon = FloatField('Longitude')
class PlantsForm(FlaskForm):
    rows = FieldList(FormField(OnePlant), min_entries = 0)

@APP.route('/plant_input', methods = ['GET', 'POST'])
@auth.login_required
def plant_input():
    """ render webpage to ask for plants input, save data to global plants (class PlantsForm) 
        then redirect to tech_input """
    global nPlant
    global plants    
    
    # process GET request
    if request.method == 'GET':
        APP.logger.info('creating a fresh plants form')
        plants = PlantsForm()
        try: nPlant
        except NameError:
            abort(400, 'Number of plants not found')
        else:
            for i in range(nPlant):
                plants.rows.append_entry({'k': i+1})
            return(render_template('plant_input.html', plants = plants))

    # process POST request
    if request.method == 'POST':
        if request.form['command'] == 'Next':
            # process saving data command
            if plants.validate():
                # if validation pass, save data to DB and redirect to next page
                # TBD: someFunctionSavetoDB(plants, username, projectID). plants if of class PlantsForm
                APP.logger.info("transfer to {}".format(url_for('tech_input')))
                return(redirect(url_for('tech_input')))
            else:
                # if validation fails, print errors to webpage
                return(render_template('plant_input.html', plants = plants))
        elif request.form['command'] == 'Parse':
            # process parsing data command (lazy method for inputing data)
            plants = Parse.fill_plants(request.form['ExcelData'], plants)
            return(render_template('plant_input.html', plants = plants))
        else:
            abort(400, 'Unknown request')


# ------------- webpage to ask for techs ---------------------------------------------------------------------------------------------------------------------
class OneScale(FlaskForm): # defining technology numbers in each scale
    Capkt = FloatField('Capkt (m3/year)')
    CCkt = FloatField('CCkt ($/(m3/year))')
    OCt = FloatField('OCt ($/m3)')
    SRWt = FloatField('SRWt ($/m3)')
    GPt = FloatField('GPt (gr CO2-eq/m3)')
class OneTech(FlaskForm):
    Select = BooleanField('Check to select')
    Technology = StringField('Technology')
    Small = FormField(OneScale)
    Medium = FormField(OneScale)
    Large = FormField(OneScale)
class TechnologiesForm(FlaskForm):    
    rows = FieldList(FormField(OneTech), min_entries = 0)    
    
class CombinedForm(FlaskForm):
    """ This form is for convenient display on the web  """
    default_techs = FormField(TechnologiesForm)
    additional_techs = FormField(TechnologiesForm)
    n_additional = IntegerField('Add more techs')
    addMoreTechs = SubmitField('Input more Technologies')
    submit = SubmitField('Next')

@APP.route('/tech_input', methods = ['GET', 'POST'])
@auth.login_required
def tech_input():
    """ render webpage to ask for plants input, save data to global techs (class TechnologiesForm) 
        then redirect to parameter_input"""
    global config, techs
    default_techs = config['techs']
    tech_form = CombinedForm(n_additional = 0)

    # process GET request
    if request.method == 'GET':
        # load default tech data from server_config.yaml file
        for t in default_techs:
            tech_form.default_techs.rows.append_entry({
                'Technology': t,
                'Small': default_techs[t]['Small'],
                'Medium': default_techs[t]['Medium'],
                'Large': default_techs[t]['Large']
            })
        return(render_template('tech_input.html', techs = tech_form))

    # process POST request
    if request.method == 'POST':
        # process adding more techs command
        if tech_form.addMoreTechs.data:
            # reset additional tech data
            for r in range(tech_form.additional_techs.rows.__len__()):
                tech_form.additional_techs.rows.pop_entry()
            # add additional tech data
            for i in range(tech_form.n_additional.data):
                tech_form.additional_techs.rows.append_entry()
            return(render_template('tech_input.html', techs = tech_form))
        # process saving data command
        elif tech_form.submit.data:
            techs = misc.tech_combine(tech_form)
            # TBD: someFunctionSavetoDB(techs, username, projectID). techs is of class TechnologiesForm
            APP.logger.info("transfer to {}".format(url_for('parameter_input')))
            return(redirect(url_for('parameter_input')))        
        else:
            abort(400, 'Unknown request')

# ------------- webpage to ask for parameters ---------------------------------------------------------------------------------------------------------
class OneParam(FlaskForm):
    Label = StringField('Parameter')
    Unit = StringField('Unit')
    Value = FloatField('Value')
class ParamsForm(FlaskForm):
    rows = FieldList(FormField(OneParam), min_entries = 0)
    submit = SubmitField('Next')

@APP.route('/parameter_input', methods = ['POST', 'GET'])
@auth.login_required
def parameter_input():
    """ render webpage to ask for parameter input, save data to global params (class ParamsForm) """
    global params
    default_params = config['params']
    params = ParamsForm()

    # process GET requests
    if request.method == 'GET':
        for p in default_params:
            params.rows.append_entry(p)            
        return(render_template('param_input.html', params = params))

    # process POST requests
    if request.method == 'POST':
        # TBD: someFunctionSavetoDB(techs, username, projectID)
        APP.logger.info("transfer to {}".format(url_for('review')))
        return(redirect(url_for('review')))


# ------------ review input data ----------------------------------------------------------------------------------------------------------------------------------
@APP.route('/review', methods = ['POST', 'GET'])
@auth.login_required
def review():
    """ review input data before running optimizer
        TODO: create links for editing data """
    global nPop, nPlant, lifeSpan, populations, plants, techs, params

    if request.method == 'GET':
        return(render_template('review.html', nPop = nPop, nPlant = nPlant, lifeSpan = lifeSpan,
            populations = populations, plants = plants, techs = techs, params = params))

# ------------ run optimizer -------------------------------------------------------------------------------------------------------------------------------------------
@APP.route('/run_optimizer', methods = ['POST'])
@auth.login_required
def run_optimizer():
    global nPop, nPlant, lifeSpan, populations, plants, techs, params
    if request.form['command'] == 'Run optimizer':
        misc.write_excel(populations, plants, techs, params, APP.config['UPLOAD_FOLDER'], filename = 'Data.xls')
        return(send_from_directory(APP.config['UPLOAD_FOLDER'], 'Data.xls', as_attachment=True))
    else:
        abort(400, 'Unknown command')

# ------------ login and out webpage -------------------------------------------------------------------------------------------------------------------------------------------
@APP.route('/login', methods = ['GET', 'POST'])
def login():
    if request.method == 'GET':
        return(render_template('login.html', login_failed = False))

    if request.method == 'POST':
        username = request.form['username']
        password_hashed = hashlib.md5(request.form['password'].encode('utf8')).digest()
        user = auth.User(username)
        user.authenticate(password_hashed)

        if user.is_authenticated():
            auth.login_user(user)
            if request.args.get("next") is not None:
                # redirect to requested page
                return(redirect(url_for(str(request.args.get('next'))[1:])))
            else: # return to Projects page
                return(redirect(url_for('index')))            
        else:
            # print errors to webpage
            return(render_template('login.html', login_failed = True))

@APP.route("/logout")
def logout():
    try: 
        logout_user()
    except Exception as e:
        APP.logger.error('Error when trying to log out: {}'.format(e))
    return('<h2>logged out</h2>')

# --------------------- RUN SERVER ---------------------------------------------------------------------------------------------------------------------------------------#
if __name__ == '__main__':
    APP.debug=True
    APP.run(host = "0.0.0.0", port = 10000, threaded=True)