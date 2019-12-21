#!/usr/bin/env python

from flask import render_template, redirect, request, Flask, url_for, abort, send_from_directory
from flask_wtf import FlaskForm, csrf
from wtforms import StringField, FieldList, FormField, SubmitField, IntegerField, FloatField, validators, BooleanField, SelectField
import yaml, sys, binascii, os, hashlib
from server_scripts import Parse, misc, auth, mapmaker, output_scripts
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
    username = auth.current_user.get_id()
    return(render_template('index.html', Identity = username))

#----------- web page to handle project requests ------------------------------------------------------
@APP.route('/projects', methods = ['GET', 'POST'])
@auth.login_required
def projects():
    """ render webpage to display existing project for a user
        User can select a project from this page, we then set user.current_project_name to the selected project
        Also handle requests to create new projects
    """
    next_page = 'input_size'

    # process GET requests
    if request.method == 'GET':
        username = auth.current_user.get_id()
        APP.logger.info('Display projects page for user {}'.format(username))
        existing_projects = db.getProjects(username = username) # pls give me a list of tuple {project_name, p_desc}
        return(render_template('projects.html', create_project = False, existing_projects = existing_projects, Identity = username))

    # process POST requests
    if request.method == 'POST':
        if 'command' in request.form and request.form['command'] == 'Create project':
            project_name = request.form['project_name']
            p_desc = request.form['p_desc']
            # save project to DB
            db.saveProject(auth.current_user.get_id(), project_name, p_desc)
            # switch current project to this project
            auth.current_user.set_project(project_name)
            # redirect to input pages
            return(redirect(url_for('input_size')))
        elif 'select project' in request.form:
            project_name = request.form['select project']
            # switch to selected project
            auth.current_user.set_project(project_name)
            # redirect to input pages
            return(redirect(url_for(next_page)))
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
    next_page = 'population_input'
    prev_page = 'projects'
    username = auth.current_user.get_id()
    current_project = auth.current_user.get_project()
    if current_project is None:
        abort(400, 'No project selected')
    inputSize = InputSize()

    # process GET requests
    if request.method == 'GET':
        APP.logger.info('GET input_size for {}.{}'.format(username, current_project))
        existing_data = db.getInputSize(username, current_project)    # give me all columns from Ns table , if data not exist, return None. E.g. {numpops:1, numplants:None, durations:2}
        # If data exist, fill in the form
        if existing_data['numpops'] is not None:
            inputSize.NPop.data = existing_data['numpops']
        if existing_data['numplants'] is not None:
            inputSize.NPlant.data = existing_data['numplants']
        if existing_data['durations'] is not None:
            inputSize.LifeSpan.data = existing_data['durations']    
        return(render_template('input_size.html', inputSize=inputSize, prev_page = prev_page, Identity = username))

    # process POST requests
    if request.method == 'POST':
        APP.logger.info('POST input_size for {}.{}'.format(username, current_project))
        if inputSize.validate_on_submit():
            # if validate pass, save data to DB and redirect to next page
            db.saveInputSize(inputSize, username, current_project)
            # -- old codes --
            # nPop = inputSize.NPop.data
            # nPlant = inputSize.NPlant.data
            # lifeSpan = inputSize.LifeSpan.data
            APP.logger.info("validation succeed! Transfer to {}".format(url_for(next_page)))
            return(redirect(url_for(next_page)))
        else:
            # if validate fails, print out errors to web page and log
            APP.logger.info("validation failed! Reload page input size")
            return(render_template('input_size.html', inputSize=inputSize, prev_page = prev_page, Identity = username))

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
    next_page = 'tech_input'
    prev_page = 'input_size'
    username = auth.current_user.get_id()
    current_project = auth.current_user.get_project()
    if current_project is None:
        abort(400, 'No project selected')
    populations = PopulationsForm()

    # process GET requests
    if request.method == 'GET':
        # If numpops exist, create the form with numpops rows
        existing_data = db.getInputSize(username, current_project)
        if existing_data['numpops'] is not None and existing_data['numpops'] > 0:
            numpops = existing_data['numpops']
            for i in range(numpops):
                populations.rows.append_entry({'r': i+1})
        else: # throw error
            abort(400, 'Number of populations not given')
        # Find existing data in the populations table
        existing_data = db.getPopulations(username, current_project) # give me all columns from populations table as list of tuples, remember to rename columns to match class OnePopulation. if data not exist, an empty list []}
        # fill in existing data to populations form
        if existing_data is not None:
            for i in range(min(len(existing_data), numpops)):
                populations.rows[i].Name.data = existing_data[i]['name']
                populations.rows[i].Pr.data = existing_data[i]['pr']
                populations.rows[i].GrowthRate.data = existing_data[i]['growthrate']
                populations.rows[i].lat.data = existing_data[i]['lat']
                populations.rows[i].lon.data = existing_data[i]['lon']
        return(render_template('population_input.html', populations = populations, prev_page = prev_page, Identity = username))

    # process POST requests
    if request.method == 'POST':
        if request.form['command'] == 'Next':
            # process saving data command
            if populations.validate():
                # if validation pass, save data to DB and redirect to next page
                db.savePopulations(populations, username, current_project)
                APP.logger.info('populations validation passed! user %s, project %s', username, current_project)
                return(redirect(url_for(next_page)))
            else:
                # if validation fails, print out errors to web page
                APP.logger.info('validation for population_input failed! user %s, project %s. Errors: %s', username, current_project, str(populations.errors))
                return(render_template('population_input.html', populations = populations, prev_page = prev_page, Identity = username))
        elif request.form['command'] == 'Insert Data':
            # process parsing data command (lazy method for inputing data)
            numpops = db.getInputSize(username, current_project)['numpops']
            for i in range(numpops):
                populations.rows.append_entry({'r': i+1})
            populations = Parse.fill_populations(request.form['ExcelData'], populations)
            APP.logger.info('Lazy data parsed in populations form! user %s, project %s', username, current_project)
            return(render_template('population_input.html', populations = populations, prev_page = prev_page, Identity = username))
        else:
            abort(400, 'Unknown request')

    # TODO: calculate projected population

# ------------- webpage to ask for plants --------------------------------------------------------------------------------------------------------------------
class OnePlant(FlaskForm):
    LocationName = StringField('Location Name')
    lat = FloatField('Latitude')
    lon = FloatField('Longitude')
    existing_location = BooleanField('Existing Location')
    existing_tech = SelectField('Technology at existing location')
class PlantsForm(FlaskForm):
    rows = FieldList(FormField(OnePlant), min_entries = 0)

@APP.route('/plant_input', methods = ['GET', 'POST'])
@auth.login_required
def plant_input():
    """ render webpage to ask for plants input, save data to global plants (class PlantsForm) 
        then redirect to tech_input """
    prev_page = 'tech_input'
    next_page = 'parameter_input'
    username = auth.current_user.get_id()
    current_project = auth.current_user.get_project()
    if current_project is None:
        abort(400, 'No project selected')
    plants = PlantsForm()

    # find the technology choices for the form
    tech_choices = db.getSelectedTechnologies(username, current_project)
    if len(tech_choices)==0:
        abort(400, 'No technology data was found to create plant form. Perhaps you did not submit the tech_input form.')


    # process GET request
    if request.method == 'GET':
        # If numplants exist, create the form with numplants rows
        existing_data = db.getInputSize(username, current_project)
        if existing_data['numplants'] is not None and existing_data['numplants'] > 0:
            numplants = existing_data['numplants']
            for i in range(numplants):
                plants.rows.append_entry({'r': i+1})
                plants.rows[i].existing_tech.choices = tech_choices
        else: # throw error
            abort(400, 'Number of plants not given')
        # Find existing data in the plants table
        existing_data = db.getPlants(username, current_project) # give me all columns from populations table as list of tuples, remember to rename columns to match class OnePopulation. if data not exist, an empty list []}
        # fill in existing data to populations form
        if existing_data is not None:
            for i in range(min(len(existing_data), numplants)):
                plants.rows[i].LocationName.data = existing_data[i]['locationname']
                plants.rows[i].lat.data = existing_data[i]['lat']
                plants.rows[i].lon.data = existing_data[i]['lon']
                plants.rows[i].existing_location.data = existing_data[i]['existing_location']
                plants.rows[i].existing_tech.data = existing_data[i]['existing_tech']
        return(render_template('plant_input.html', plants = plants, prev_page = prev_page, Identity = username))

    # process POST request
    if request.method == 'POST':
        if request.form['command'] == 'Next':
            # set tech choices for data validation
            numplants = db.getInputSize(username, current_project)['numplants']
            for i in range(numplants):
                plants.rows[i].existing_tech.choices = tech_choices
            # process saving data command
            if plants.validate():
                # if validation pass, save data to DB and redirect to next page
                db.savePlants(plants, username, current_project)
                APP.logger.info('plants validation passed! user %s, project %s', username, current_project)
                return(redirect(url_for(next_page)))
            else:
                # if validation fails, print out errors to web page
                APP.logger.info('validation for plants_input failed! user %s, project %s. Errors: %s', username, current_project, str(plants.errors))
                return(render_template('plant_input.html', plants = plants, prev_page = prev_page, Identity = username))
        elif request.form['command'] == 'Insert Data':
            # process parsing data command (lazy method for inputing data)
            numplants = db.getInputSize(username, current_project)['numplants']
            for i in range(numplants):
                plants.rows.append_entry({'r': i+1})
                plants.rows[i].existing_tech.choices = tech_choices
            numplants = Parse.fill_plants(request.form['ExcelData'], plants)
            APP.logger.info('Lazy data parsed in plants form! user %s, project %s', username, current_project)
            return(render_template('plant_input.html', plants = plants, prev_page = prev_page, Identity = username))
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
    default_tech = BooleanField('Does this belong to default tech?')
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
    global config
    prev_page = 'population_input'
    next_page = 'plant_input'
    username = auth.current_user.get_id()
    current_project = auth.current_user.get_project()
    if current_project is None:
        abort(400, 'No project selected')

    # load default tech data from server_config.yaml file
    default_techs = config['techs']
    tech_form = CombinedForm(n_additional = 0)

    # process GET request
    if request.method == 'GET':
        # initialize form with default tech data from config file
        for t in default_techs:
            tech_form.default_techs.rows.append_entry({
                'Technology': t,
                'Small': default_techs[t]['Small'],
                'Medium': default_techs[t]['Medium'],
                'Large': default_techs[t]['Large']
            })
        # fill in data from database to the form object
        existing_data = db.getTechnologies(username, current_project) # give me everything in the DB
        tech_form = misc.fill_dbdata_tech(tech_form, existing_data)
        return(render_template('tech_input.html', techs = tech_form, prev_page = prev_page, Identity = username))

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
            return(render_template('tech_input.html', techs = tech_form, prev_page = prev_page, Identity = username))
        # process saving data command
        elif tech_form.submit.data:
            # TODO: data validation
            techs = misc.tech_combine(tech_form)
            db.saveTechnologies(techs, username, current_project) # techs is of class TechnologiesForm. In db, set type='default' if the row is in techs.default_techs, 'additional' if it is in additional_techs
            APP.logger.info("transfer to {}".format(url_for('parameter_input')))
            return(redirect(url_for(next_page)))
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
    prev_page = 'plant_input'
    next_page = 'review'
    username = auth.current_user.get_id()
    current_project = auth.current_user.get_project()
    if current_project is None:
        abort(400, 'No project selected')

    default_params = config['params']
    params = ParamsForm()

    existing_data = db.getParams(username, current_project) # give me everything in the DB
    # TODO (M): pre-fill form data with data from database

    # process GET requests
    if request.method == 'GET':
        for p in default_params:
            params.rows.append_entry(p)            
        return(render_template('param_input.html', params = params, prev_page = prev_page, Identity = username))

    # process POST requests
    if request.method == 'POST':
        # TODO (M): data validation
        db.saveParams(params, username, current_project)
        APP.logger.info("transfer to {}".format(url_for(next_page)))
        return(redirect(url_for(next_page)))


# ------------ review input data ----------------------------------------------------------------------------------------------------------------------------------
@APP.route('/review', methods = ['GET'])
@auth.login_required
def review():
    """ review input data before running optimizer
        TODO: create links for editing data """
    prev_page = 'parameter_input'
    username = auth.current_user.get_id()
    current_project = auth.current_user.get_project()
    if current_project is None:
        abort(400, 'No project selected')
    ### first pull data from db ###
    input_size = db.getInputSize(username, current_project)
    populations = db.getPopulations(username, current_project)
    plants = db.getPlants(username, current_project)
    tech_choices = db.getSelectedTechnologies(username, current_project)
    techs = db.getTechnologies(username, current_project)
    params = db.getParams(username, current_project)

    # create markers for the map
    population_markers = mapmaker.createPopulationsGeoJson(populations)
    plant_markers = mapmaker.createLocationsGeoJson(plants)

    if request.method == 'GET':
        return(render_template('review.html', nPop = input_size['numpops'], nPlant = input_size['numplants'], lifeSpan = input_size['durations'],
            populations = populations, plants = plants, techs = techs, params = params, tech_choices = tech_choices,
            population_markers = population_markers, plant_markers = plant_markers, MAPBOX_KEY = config['MAPBOX_KEY'],
            prev_page = prev_page, Identity = username, project_name = current_project))

# ------------ run optimizer -------------------------------------------------------------------------------------------------------------------------------------------
@APP.route('/run_optimizer', methods = ['POST'])
@auth.login_required
def run_optimizer():
    username = auth.current_user.get_id()
    current_project = auth.current_user.get_project()
    
    global nPop, nPlant, lifeSpan, populations, plants, techs, params
    if request.form['command'] == 'Run optimizer':
        # write data to disk and call optimizer
        # misc.write_excel(populations, plants, techs, params, APP.config['UPLOAD_FOLDER'], filename = 'Data.xls')
        
        # update last_executed time for this project in the db
        db.updateProjectExecution(username, current_project)
        # return to projects page
        return(redirect(url_for('projects')))
    else:
        abort(400, 'Unknown command')

# ----------- output page -------------------------------------------------------------------------------------------------------------------------------------------------------
@APP.route('/output', methods = ['GET'])
@auth.login_required
def output():
    username = auth.current_user.get_id()
    current_project = request.args.get('project_name')

    # first pull output data
    values = output_scripts.output_values(username, project_name = None)
    solution_details = output_scripts.output_solutions(username, project_name = None)

    # map data of population clusters for all solutions
    populations = db.getPopulations(username, current_project)
    population_markers = mapmaker.createPopulationsGeoJson(populations)  # population markers for MapBox

    # map data of locations for all solutions (markers)
    plants = db.getPlants(username, current_project)
    location_markers_allSols = mapmaker.createLocationsSolutionsGeoJson(plants, solution_details)

    # map data of LineString connecting locations and population clusters for all solutions
    plants_pop_linestring = mapmaker.createLocationClusterLinestringGeoJson(plants, populations, solution_details)

    return(render_template('output.html', valuesData = values, solutionDetails = solution_details, 
        population_markers = population_markers, location_markers_allSols = location_markers_allSols,
        plants_pop_linestring = plants_pop_linestring, MAPBOX_KEY = config['MAPBOX_KEY'],
        Identity = username, project_name = current_project))



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
            APP.logger.info('AUTH: user %s logged in', user.get_id())
            auth.login_user(user)
            if request.args.get("next") is not None:
                # redirect to requested page
                return(redirect(url_for(str(request.args.get('next'))[1:])))
            else: # return to Projects page
                return(redirect(url_for('projects')))
        else:
            # print errors to webpage
            return(render_template('login.html', login_failed = True))

@APP.route("/logout", methods = ['GET'])
def logout():
    try:
        APP.logger.info('AUTH: user %s logged out', auth.current_user.get_id())
        auth.logout_user()
        auth.current_user.authenticated = False
    except Exception as e:
        APP.logger.error('Error when trying to log out: {}'.format(e))
    return('<h2>logged out</h2>')

# ------------ user register webpage -------------------------------------------------------------------------------------------------------------------------------------------
@APP.route('/register', methods = ['GET', 'POST'])
def register():
    if request.method == 'GET':
        return(render_template('register.html', login_failed = False))

    if request.method == 'POST':
        if request.form['register'] == 'submit':
            fullname = request.form['fullname']
            username = request.form['username']
            password = request.form['password']
            email = request.form['email']
            success = db.registerUser(fullname, username, password, email)
            if not success:
                pass # Handle error 
        else:
            abort(400, 'Unknown request')

# ------------- Contact page (static) --------------------------------------------------------------------------------------------------------------------------------------------
@APP.route('/contact', methods = ['GET'])
def Contact():
    return(render_template('Contact.html'))

# --------------------- RUN SERVER ---------------------------------------------------------------------------------------------------------------------------------------#
if __name__ == '__main__':
    APP.debug=True
    APP.run(host = "0.0.0.0", port = 10000, threaded=True)