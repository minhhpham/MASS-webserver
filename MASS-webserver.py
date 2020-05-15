#!/usr/bin/env python

from flask import render_template, redirect, request, Flask, url_for, abort, send_from_directory
from flask_wtf import FlaskForm, csrf
from wtforms import StringField, FieldList, FormField, SubmitField, IntegerField, FloatField, validators, BooleanField, SelectField
import yaml, sys, binascii, os, hashlib, coolname
from server_scripts import Parse, misc, auth, mapmaker, output_scripts
from server_scripts import database as db

# --------------------- CONFIGURATIONS -------------------------------------------------------------------------------------------------------
global APP
APP = Flask(__name__)

# Cross-site scripting protection
CSRF = csrf.CSRFProtect()
CSRF.init_app(APP)
APP.config['SECRET_KEY'] = os.urandom(32)

# load config from server_config.yaml
global config
with open("server_config.yaml", 'r') as stream:
    try:
        config = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        print(exc)
        sys.exit()

# check if db is ready
if not db.db_is_ready():
    try:
        db.init_db()
    except:
        sys.exit("Database is not initialized correclty")

# start routing
@APP.route('/', methods = ['GET'])
def index():
    return(render_template('index.html'))

#----------- web page to handle project requests ------------------------------------------------------
@APP.route('/projects', methods = ['GET', 'POST'])
def projects():
    """ render webpage to display existing project for a user
        User can select a project from this page, we then set user.current_project_name to the selected project
        Also handle requests to create new projects
    """
    next_page = 'input_size'

    # process GET requests
    if request.method == 'GET':
        if 'projectID' in request.args:
            projectID = request.args.get('projectID')
            project_status = db.getProject(projectID)
            return(render_template('projects.html', project_just_created = False, proj_description = "", projectID = projectID, check_proj_status = True, project_status = project_status))
        else:
            return(render_template('projects.html', project_just_created = False, proj_description = "", check_proj_status = False, project_status = None))

    # process POST requests
    if request.method == 'POST':
        if 'command' in request.form and request.form['command'] == 'Create Project':
            # user's input of project desc
            proj_description = request.form['p_desc']
            # keep trying until find a unique projectID
            while True:
                # generate a random projectID
                projectID = coolname.generate_slug()
                # check if projectID already exists in DB
                if not db.projectExists(projectID):
                    break
            # save project to DB
            db.saveProject(projectID, proj_description)
            # re-render the page showing a "Start Input" button
            return(render_template('projects.html', project_just_created = True, proj_description = proj_description, projectID = projectID, check_proj_status = False, project_status = None))

        elif 'command' in request.form and request.form['command'] == 'Start this project':
            projectID = request.form['projectID']
            return(redirect(url_for(next_page, projectID = projectID)))

        elif 'command' in request.form and request.form['command'] == 'Check project status':
            projectID = request.form['projectID']
            return(redirect(url_for('projects', projectID = projectID)))

        else:
            abort(400, 'Unknown request')



#----------- web page to ask for input size ---------------------------------------------------------------------------------------------------
class InputSize(FlaskForm):
    NPop = IntegerField('Number of populations', validators = [validators.InputRequired(), validators.NumberRange(min=0)])
    NPlant = IntegerField('Number of plants', validators = [validators.InputRequired(), validators.NumberRange(min=0)])
    LifeSpan = IntegerField('Life Span of project', validators = [validators.InputRequired(), validators.NumberRange(min=0)])    

@APP.route('/input_size', methods=['GET', 'POST'])
def input_size():
    """ render webpage to ask for input sizes, save data to global nPop, nPlant, lifeSpan 
        then redirect to population_input """
    if 'projectID' not in request.args:
        abort(400, 'projectID not provided')
    projectID = request.args.get('projectID')
    next_page = 'population_input'
    prev_page = 'projects'
    inputSize = InputSize()

    # process GET requests
    if request.method == 'GET':
        APP.logger.info('GET input_size for {}'.format(projectID))
        existing_data = db.getInputSize(projectID)
        # If data exist, fill in the form
        if existing_data['numpops'] is not None:
            inputSize.NPop.data = existing_data['numpops']
        if existing_data['numplants'] is not None:
            inputSize.NPlant.data = existing_data['numplants']
        if existing_data['durations'] is not None:
            inputSize.LifeSpan.data = existing_data['durations']    
        return(render_template('input_size.html', inputSize=inputSize, prev_page = prev_page, projectID = projectID))

    # process POST requests
    if request.method == 'POST':
        APP.logger.info('POST input_size for {}'.format(projectID))
        if inputSize.validate_on_submit():
            # if validate pass, save data to DB and redirect to next page
            db.saveInputSize(inputSize, projectID)
            APP.logger.info("validation succeed! Transfer to {}".format(url_for(next_page)))
            return(redirect(url_for(next_page, projectID = projectID)))
        else:
            # if validate fails, print out errors to web page and log
            APP.logger.info("validation failed! Reload page input size")
            return(render_template('input_size.html', inputSize=inputSize, prev_page = prev_page, projectID = projectID))

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
def population_input():
    """ render webpage to ask for population input, save data to global populations (class PopulationsForm) 
        then redirect to plant_input """
    if 'projectID' not in request.args:
        abort(400, 'projectID not provided')
    projectID = request.args.get('projectID')
    next_page = 'tech_input'
    prev_page = 'input_size'
    populations = PopulationsForm()

    # process GET requests
    if request.method == 'GET':
        # If numpops exist, create the form with numpops rows
        existing_data = db.getInputSize(projectID)
        if existing_data['numpops'] is not None and existing_data['numpops'] > 0:
            numpops = existing_data['numpops']
            for i in range(numpops):
                populations.rows.append_entry({'r': i+1})
        else: # throw error
            abort(400, 'Number of populations not given')
        # Find existing data in the populations table
        existing_data = db.getPopulations(projectID)
        # fill in existing data to populations form
        if existing_data is not None:
            for i in range(min(len(existing_data), numpops)):
                populations.rows[i].Name.data = existing_data[i]['name']
                populations.rows[i].Pr.data = existing_data[i]['pr']
                populations.rows[i].GrowthRate.data = existing_data[i]['growthrate']*100
                populations.rows[i].lat.data = existing_data[i]['lat']
                populations.rows[i].lon.data = existing_data[i]['lon']
        return(render_template('population_input.html', populations = populations, prev_page = prev_page, projectID = projectID))

    # process POST requests
    if request.method == 'POST':
        if request.form['command'] == 'Next':
            # process saving data command
            if populations.validate():
                # if validation pass, save data to DB and redirect to next page
                # first scale down growthrate by 100
                for i in range(populations.rows.__len__()):
                    populations.rows[i].GrowthRate.data = populations.rows[i].GrowthRate.data/100
                db.savePopulations(populations, projectID)
                APP.logger.info('populations validation passed! project %s', projectID)
                return(redirect(url_for(next_page, projectID = projectID)))
            else:
                # if validation fails, print out errors to web page
                APP.logger.info('validation for population_input failed! project %s. Errors: %s', projectID, str(populations.errors))
                return(render_template('population_input.html', populations = populations, prev_page = prev_page, projectID = projectID))
        elif request.form['command'] == 'Insert Data':
            # process parsing data command (lazy method for inputing data)
            numpops = db.getInputSize(projectID)['numpops']
            for i in range(numpops):
                populations.rows.append_entry({'r': i+1})
            populations = Parse.fill_populations(request.form['ExcelData'], populations)
            APP.logger.info('Lazy data parsed in populations form! project %s', projectID)
            return(render_template('population_input.html', populations = populations, prev_page = prev_page, projectID = projectID))
        else:
            abort(400, 'Unknown request')



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
def plant_input():
    """ render webpage to ask for plants input, save data to global plants (class PlantsForm) 
        then redirect to tech_input """
    if 'projectID' not in request.args:
        abort(400, 'projectID not provided')
    projectID = request.args.get('projectID')
    prev_page = 'tech_input'
    next_page = 'parameter_input'
    plants = PlantsForm()

    # find the technology choices for the form
    tech_choices = db.getSelectedTechnologies(projectID)
    if len(tech_choices)==0:
        abort(400, 'No technology data was found to create plant form. Perhaps you did not submit the tech_input form.')

    # process GET request
    if request.method == 'GET':
        # If numplants exist, create the form with numplants rows
        existing_data = db.getInputSize(projectID)
        if existing_data['numplants'] is not None and existing_data['numplants'] > 0:
            numplants = existing_data['numplants']
            for i in range(numplants):
                plants.rows.append_entry({'r': i+1})
                plants.rows[i].existing_tech.choices = tech_choices
        else: # throw error
            abort(400, 'Number of plants not given')
        # Find existing data in the plants table
        existing_data = db.getPlants(projectID) # give me all columns from populations table as list of tuples, remember to rename columns to match class OnePopulation. if data not exist, an empty list []}
        # fill in existing data to populations form
        if existing_data is not None:
            for i in range(min(len(existing_data), numplants)):
                plants.rows[i].LocationName.data = existing_data[i]['locationname']
                plants.rows[i].lat.data = existing_data[i]['lat']
                plants.rows[i].lon.data = existing_data[i]['lon']
                plants.rows[i].existing_location.data = existing_data[i]['existing_location']
                plants.rows[i].existing_tech.data = existing_data[i]['existing_tech']
        return(render_template('plant_input.html', plants = plants, prev_page = prev_page, projectID = projectID))

    # process POST request
    if request.method == 'POST':
        if request.form['command'] == 'Next':
            # set tech choices for data validation
            numplants = db.getInputSize(projectID = projectID)['numplants']
            for i in range(numplants):
                plants.rows[i].existing_tech.choices = tech_choices
            # process saving data command
            if plants.validate():
                # if validation pass, save data to DB and redirect to next page
                db.savePlants(plants, projectID)
                APP.logger.info('plants validation passed! project %s', projectID)
                return(redirect(url_for(next_page, projectID = projectID)))
            else:
                # if validation fails, print out errors to web page
                APP.logger.info('validation for plants_input failed! project %s. Errors: %s', projectID, str(plants.errors))
                return(render_template('plant_input.html', plants = plants, prev_page = prev_page, projectID = projectID))
        elif request.form['command'] == 'Insert Data':
            # process parsing data command (lazy method for inputing data)
            numplants = db.getInputSize(projectID)['numplants']
            for i in range(numplants):
                plants.rows.append_entry({'r': i+1})
                plants.rows[i].existing_tech.choices = tech_choices
            numplants = Parse.fill_plants(request.form['ExcelData'], plants)
            APP.logger.info('Lazy data parsed in plants form! project %s', projectID)
            return(render_template('plant_input.html', plants = plants, prev_page = prev_page, projectID = projectID))
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
def tech_input():
    """ render webpage to ask for plants input, save data to global techs (class TechnologiesForm) 
        then redirect to parameter_input"""
    global config
    prev_page = 'population_input'
    next_page = 'plant_input'
    if 'projectID' not in request.args:
        abort(400, 'projectID not provided')
    projectID = request.args.get('projectID')

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
        existing_data = db.getTechnologies(projectID) # give me everything in the DB
        tech_form = misc.fill_dbdata_tech(tech_form, existing_data)
        return(render_template('tech_input.html', techs = tech_form, prev_page = prev_page, projectID = projectID))

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
            return(render_template('tech_input.html', techs = tech_form, prev_page = prev_page, projectID = projectID))
        # process saving data command
        elif tech_form.submit.data:
            # TODO: data validation
            techs = misc.tech_combine(tech_form)
            db.saveTechnologies(techs, projectID) # techs is of class TechnologiesForm. In db, set type='default' if the row is in techs.default_techs, 'additional' if it is in additional_techs
            APP.logger.info("transfer to {}".format(url_for('parameter_input')))
            return(redirect(url_for(next_page, projectID = projectID)))
        else:
            abort(400, 'Unknown request')

# ------------- webpage to ask for parameters ---------------------------------------------------------------------------------------------------------
class OneParam(FlaskForm):
    Label = StringField('Parameter')
    Unit = StringField('Unit')
    Value = FloatField('Value')
    Description = StringField('Description')
class ParamsForm(FlaskForm):
    rows = FieldList(FormField(OneParam), min_entries = 0)
    submit = SubmitField('Next')

@APP.route('/parameter_input', methods = ['POST', 'GET'])
def parameter_input():
    """ render webpage to ask for parameter input, save data to global params (class ParamsForm) """
    prev_page = 'plant_input'
    next_page = 'review'
    if 'projectID' not in request.args:
        abort(400, 'projectID not provided')
    projectID = request.args.get('projectID')

    default_params = config['params']
    params = ParamsForm()
    existing_data = db.getParams(projectID)

    # process GET requests
    if request.method == 'GET':
        # if there is existing data, use it, otherwise use default parameters
        if len(existing_data) > 0:
            for r in existing_data:
                params.rows.append_entry({'Label': r['label'], 'Unit': r['unit'], 'Value': r['value'], 'Description': r['description']})
        else:
            for p in default_params:
                params.rows.append_entry(p)
        return(render_template('param_input.html', params = params, prev_page = prev_page, projectID = projectID))

    # process POST requests
    if request.method == 'POST':
        # TODO (M): data validation
        db.saveParams(params, projectID)
        # update status of this project in the DB
        db.updateProjectStatus(projectID, 'input completed, not yet optimized')
        APP.logger.info("transfer to {}".format(url_for(next_page)))
        return(redirect(url_for(next_page, projectID = projectID)))


# ------------ review input data ----------------------------------------------------------------------------------------------------------------------------------
@APP.route('/review', methods = ['GET'])
def review():
    """ review input data before running optimizer
        TODO: create links for editing data """
    prev_page = 'parameter_input'
    if 'projectID' not in request.args:
        abort(400, 'projectID not provided')
    projectID = request.args.get('projectID')

    ### step0: check if input is completed for this project, if not then abort ###
    project_status = db.getProject(projectID)
    if project_status['status'] == 'input uncompleted, not yet optimized':
        abort(400, 'input data not completed')

    
    ### first pull data from db ###
    input_size = db.getInputSize(projectID)
    populations = db.getPopulations(projectID)
    plants = db.getPlants(projectID)
    tech_choices = db.getSelectedTechnologies(projectID)
    techs = db.getTechnologies(projectID)
    params = db.getParams(projectID)

    # create markers for the map
    population_markers = mapmaker.createPopulationsGeoJson(populations)
    plant_markers = mapmaker.createLocationsGeoJson(plants)

    if request.method == 'GET':
        return(render_template('review.html', nPop = input_size['numpops'], nPlant = input_size['numplants'], lifeSpan = input_size['durations'],
            populations = populations, plants = plants, techs = techs, params = params, tech_choices = tech_choices,
            population_markers = population_markers, plant_markers = plant_markers, MAPBOX_KEY = config['MAPBOX_KEY'],
            prev_page = prev_page, projectID = projectID))

# ------------ run optimizer -------------------------------------------------------------------------------------------------------------------------------------------
@APP.route('/run_optimizer', methods = ['POST'])
def run_optimizer():
    if 'projectID' not in request.form:
        abort(400, 'projectID not provided')
    projectID = request.form['projectID']

    # enque the given projectID
    db.enQueue(projectID)
    # the optimizer_scheduler service will take care of the rest

    # return to projects page showing the status of this projectID
    project_status = db.getProject(projectID)
    return(redirect(url_for('projects', projectID = projectID)))

# ----------- output page -------------------------------------------------------------------------------------------------------------------------------------------------------
@APP.route('/output', methods = ['GET'])
def output():
    if 'projectID' not in request.args:
        abort(400, 'projectID not provided')
    projectID = request.args.get('projectID')

    # first pull output data
    solution_values, solution_details  = output_scripts.get_output(projectID)

    # map data of population clusters for all solutions
    populations = db.getPopulations(projectID)
    population_markers = mapmaker.createPopulationsGeoJson(populations)  # population markers for MapBox

    # map data of locations for all solutions (markers)
    plants = db.getPlants(projectID)
    location_markers_allSols = mapmaker.createLocationsSolutionsGeoJson(plants, solution_details)

    # map data of LineString connecting locations and population clusters for all solutions
    plants_pop_linestring = mapmaker.createLocationClusterLinestringGeoJson(plants, populations, solution_details)

    return(render_template('output.html', valuesData = solution_values, solutionDetails = solution_details, 
        population_markers = population_markers, location_markers_allSols = location_markers_allSols,
        plants_pop_linestring = plants_pop_linestring, MAPBOX_KEY = config['MAPBOX_KEY'],
        projectID = projectID))


# ------------- Static pages -------------------------------------------------------------------

@APP.route('/demo', methods = ['GET'])
def demo():
    return(render_template('demo.html'))

@APP.route('/documentation', methods = ['GET'])
def documentation():
    return(render_template('documentation.html'))

@APP.route('/contact', methods = ['GET'])
def Contact():
    return(render_template('Contact.html'))

# --------------------- RUN SERVER ---------------------------------------------------------------------------------------------------------------------------------------#
if __name__ == '__main__':
    APP.debug=True
    APP.run(host = "0.0.0.0", port = 10000, threaded=True)