#!/usr/bin/env python

from flask import render_template, redirect, request, Flask, url_for, abort, send_from_directory
from flask_wtf import FlaskForm
from wtforms import StringField, FieldList, FormField, SubmitField, IntegerField, FloatField, validators, BooleanField
import yaml, sys, binascii, os
from xlwt import Workbook
from math import sin, cos, acos, radians


with open("server_config.yaml", 'r') as stream:
    try:
        config = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        print(exc)
        sys.exit()

APP = Flask(__name__)
APP.config['SECRET_KEY'] = binascii.hexlify(os.urandom(128))
APP.config['UPLOAD_FOLDER'] = 'data'

@APP.route('/', methods = ['GET'])
def index():
	return(render_template('index.html'))

# variables that will be decalared globally
global nPop, nPlant, lifeSpan
global populations, plants, tech_form, techs, params 	# techs has class TechnologiesForm and has the input data
														# tech_form is the form to be rendered to web interface
#----------- web page to ask for input size ---------------------------------------------------------------------------------------------------
class NRow(FlaskForm):
	NPop = IntegerField('Number of populations', validators = [validators.InputRequired()])
	NPlant = IntegerField('Number of plants', validators = [validators.InputRequired()])
	LifeSpan = IntegerField('Life Span of project', validators = [validators.InputRequired()])	
@APP.route('/input_size', methods=['GET', 'POST'])
def input_size():
	global nPop, nPlant, lifeSpan
	nRow = NRow()
	if request.method == 'GET':		
		return(render_template('input_size.html', nRow=nRow))
	if request.method == 'POST':
		if nRow.validate_on_submit():
			nPop = nRow.NPop.data
			nPlant = nRow.NPlant.data
			lifeSpan = nRow.LifeSpan.data
			APP.logger.info("transfer to {}".format(url_for('population_input')))
			return(redirect(url_for('population_input')))

#----------- webpage to ask for populations ------------------------------------------------------------------------------------------------------------
class OnePopulation(FlaskForm):
	Name = StringField('Cluster Name')
	Pr = IntegerField('Current Population')
	GrowthRate = FloatField('Population Growth Rate')
	lat = FloatField('Latitude')
	lon = FloatField('Longitude')
	ProjPr = IntegerField('Projected Population')
class PopulationsForm(FlaskForm):
	submit = SubmitField('Next')
	rows = FieldList(FormField(OnePopulation), min_entries = 0)

@APP.route('/population_input', methods=['GET', 'POST'])
def population_input():
	global nPop
	global populations	
	populations = PopulationsForm()
	if request.method == 'GET':
		try: nPop
		except NameError:
			abort(400, 'Number of populations not found')
		else:			
			for i in range(nPop):
				populations.rows.append_entry({'r': i+1})
			return(render_template('population_input.html', populations = populations))

	if request.method == 'POST':
		if populations.submit.data:
			APP.logger.info("transfer to {}".format(url_for('plant_input')))
			return(redirect(url_for('plant_input')))

	# TODO: calculate projected population

# ------------- webpage to ask for plants --------------------------------------------------------------------------------------------------------------------
class OnePlant(FlaskForm):
	LocationName = StringField('Location Name')
	lat = FloatField('Latitude')
	lon = FloatField('Longitude')
class PlantsForm(FlaskForm):
	submit = SubmitField('Next')
	rows = FieldList(FormField(OnePlant), min_entries = 0)

@APP.route('/plant_input', methods = ['GET', 'POST'])
def plant_input():
	global nPlant
	global plants	
	plants = PlantsForm()
	if request.method == 'GET':
		try: nPlant
		except NameError:
			abort(400, 'Number of plants not found')
		else:
			for i in range(nPlant):
				plants.rows.append_entry({'k': i+1})
			return(render_template('plant_input.html', plants = plants))

	if request.method == 'POST':
		if plants.submit.data:
			APP.logger.info("transfer to {}".format(url_for('tech_input')))
			return(redirect(url_for('tech_input')))


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
	default_techs = FormField(TechnologiesForm)
	additional_techs = FormField(TechnologiesForm)
	n_additional = IntegerField('Add more techs')
	addMoreTechs = SubmitField('Input more Technologies')
	submit = SubmitField('Next')

@APP.route('/tech_input', methods = ['GET', 'POST'])
def tech_input():
	global config, techs
	default_techs = config['techs']
	tech_form = CombinedForm(n_additional = 0)
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

	if request.method == 'POST':
		if tech_form.addMoreTechs.data:
			# reset additional tech data
			for r in range(tech_form.additional_techs.rows.__len__()):
				tech_form.additional_techs.rows.pop_entry()
			# add additional tech data
			for i in range(tech_form.n_additional.data):
				tech_form.additional_techs.rows.append_entry()
			return(render_template('tech_input.html', techs = tech_form))
		if tech_form.submit.data:
			techs = tech_combine(tech_form)
			APP.logger.info("transfer to {}".format(url_for('parameter_input')))
			return(redirect(url_for('parameter_input')))		

# ------------- webpage to ask for parameters ---------------------------------------------------------------------------------------------------------
class OneParam(FlaskForm):
	Label = StringField('Parameter')
	Unit = StringField('Unit')
	Value = FloatField('Value')
class Params(FlaskForm):
	rows = FieldList(FormField(OneParam), min_entries = 0)
	submit = SubmitField('Next')

@APP.route('/parameter_input', methods = ['POST', 'GET'])
def parameter_input():
	global params
	default_params = config['params']
	params = Params()
	if request.method == 'GET':
		for p in default_params:
			params.rows.append_entry(p)			
		return(render_template('param_input.html', params = params))

	if request.method == 'POST':
		APP.logger.info("transfer to {}".format(url_for('review')))
		return(redirect(url_for('review')))


# ------------ review input data ----------------------------------------------------------------------------------------------------------------------------------
@APP.route('/review', methods = ['POST', 'GET'])
def review():
	global nPop, nPlant, lifeSpan, populations, plants, techs, params

	if request.method == 'GET':
		return(render_template('review.html', nPop = nPop, nPlant = nPlant, lifeSpan = lifeSpan,
			populations = populations, plants = plants, techs = techs, params = params))

# ------------ run optimizer -------------------------------------------------------------------------------------------------------------------------------------------
@APP.route('/run_optimizer', methods = ['POST'])
def run_optimizer():
	global nPop, nPlant, lifeSpan, populations, plants, techs, params
	if request.form['command'] == 'Run optimizer':
		write_excel(populations, plants, techs, params, filename = 'Data.xls')
		return(send_from_directory(APP.config['UPLOAD_FOLDER'], 'Data.xls', as_attachment=True))
	else:
		abort(400, 'Unknown command')



# --------------------- HELPER FUNCTIONS ---------------------------------------------------------------------------------------------------------------------
def tech_combine(_techs):
	""" Combine selected techs.default_techs and techs.additional_techs
		return a TechnologiesForm object with selected techs
	"""
	selected_techs = TechnologiesForm()
	for t in  _techs.default_techs.rows:
		if t.Select.data: # if default tech is selected by user, add to selected_techs
			selected_techs.rows.append_entry(t)
	if _techs.additional_techs.rows.__len__() > 0:
		for t in _techs.additional_techs.rows:
			selected_techs.rows.append_entry(t)
	return(selected_techs)

def distance(lat1, lon1, lat2, lon2):
	""" distance (in miles) between 2 points on earth """
	return(0.000189394*
		(3963*acos(cos(radians(90-lat1))*cos(radians(90-lat2))+
			sin(radians(90-lat1))*sin(radians(90-lat2))*cos(radians(lon1-lon2))))*5280
	)
def distance_pop_plant(pops, plants):
	""" distance between populations and plants 
		pops has class PopulationsForm, plants has class PlantsForm
		returns a 2D array of size nPops*nPlants
	"""
	nPop = pops.rows.__len__()
	nPlant = plants.rows.__len__()
	# initialize output 
	out = [[0 for j in range(nPlant)] for i in range(nPop)]
	# loop through pops and plants
	for i in range(nPop):
		for j in range(nPlant):
			out[i][j] = distance(pops.rows[i].lat.data, pops.rows[i].lon.data,
								plants.rows[j].lat.data, plants.rows[j].lon.data)
	return(out)

def write_excel(populations, plants, techs, params, filename):
	""" write an excel file from given inputs """
	wb = Workbook()
	sheet1 = wb.add_sheet('Sheet 1')

	# write Populations to columns 0 to 4
	sheet1.write(0, 0, 'r'); sheet1.write(0, 1, 'Pr'); sheet1.write(0, 2, 'Population Growth Rate')
	sheet1.write(0, 3, 'Latitude'); sheet1.write(0, 4, 'Longitude')
	for r in range(populations.rows.__len__()):
		sheet1.write(r+1, 0, r + 1)
		sheet1.write(r+1, 1, populations.rows[r].Pr.data)
		sheet1.write(r+1, 2, populations.rows[r].GrowthRate.data)
		sheet1.write(r+1, 3, populations.rows[r].lat.data)
		sheet1.write(r+1, 4, populations.rows[r].lon.data)

	# write plants to columns 5 to 8
	sheet1.write(0, 5, 'k'); sheet1.write(0, 6, 'Location'); sheet1.write(0, 7, 'Latitude'); sheet1.write(0, 8, 'Longitude')
	for r in range(plants.rows.__len__()):
		sheet1.write(r+1, 5, r + 1)
		sheet1.write(r+1, 6, plants.rows[r].LocationName.data)
		sheet1.write(r+1, 7, plants.rows[r].lat.data)
		sheet1.write(r+1, 8, plants.rows[r].lon.data)

	# write technology to columns 9 to 16
	sheet1.write(0, 9, 'Technology'); sheet1.write(0, 10, 'Scale'); sheet1.write(0, 11, 't'); sheet1.write(0, 12, 'Capkt');
	sheet1.write(0, 13, 'CCkt'); sheet1.write(0, 14, 'OCt'); sheet1.write(0, 15, 'SRWt'); sheet1.write(0, 16, 'GPt')
	t = 0
	for techid in range(techs.rows.__len__()):
		r = 3*techid		
		sheet1.write_merge(r+1, r+3, 9, 9, techs.rows[techid].Technology.data.data)
		t+=1
		sheet1.write(r+1, 10, 'Small')
		sheet1.write(r+1, 11, t)
		sheet1.write(r+1, 12, techs.rows[techid].Small.Capkt.data.data)
		sheet1.write(r+1, 13, techs.rows[techid].Small.CCkt.data.data)
		sheet1.write(r+1, 14, techs.rows[techid].Small.OCt.data.data)
		sheet1.write(r+1, 15, techs.rows[techid].Small.SRWt.data.data)
		sheet1.write(r+1, 16, techs.rows[techid].Small.GPt.data.data)
		t+=1
		sheet1.write(r+2, 10, 'Medium')
		sheet1.write(r+2, 11, t)
		sheet1.write(r+2, 12, techs.rows[techid].Medium.Capkt.data.data)
		sheet1.write(r+2, 13, techs.rows[techid].Medium.CCkt.data.data)
		sheet1.write(r+2, 14, techs.rows[techid].Medium.OCt.data.data)
		sheet1.write(r+2, 15, techs.rows[techid].Medium.SRWt.data.data)
		sheet1.write(r+2, 16, techs.rows[techid].Medium.GPt.data.data)
		t+=1
		sheet1.write(r+3, 10, 'Large')
		sheet1.write(r+3, 11, t)
		sheet1.write(r+3, 12, techs.rows[techid].Large.Capkt.data.data)
		sheet1.write(r+3, 13, techs.rows[techid].Large.CCkt.data.data)
		sheet1.write(r+3, 14, techs.rows[techid].Large.OCt.data.data)
		sheet1.write(r+3, 15, techs.rows[techid].Large.SRWt.data.data)
		sheet1.write(r+3, 16, techs.rows[techid].Large.GPt.data.data)

	# write parameters to columns 17 to 19
	sheet1.write(0, 17, 'Parameter'); sheet1.write(0, 18, 'Unit'); sheet1.write(0, 19, 'Value')
	for r in range(params.rows.__len__()):
		sheet1.write(r+1, 17, params.rows[r].Label.data)
		sheet1.write(r+1, 18, params.rows[r].Unit.data)
		sheet1.write(r+1, 19, params.rows[r].Value.data)

	# write distance to columns 20 and above
	distance_matrix = distance_pop_plant(populations, plants)
	offset = 20
		# write headers
	for i in range(populations.rows.__len__()):
		sheet1.write(i+1, offset, 'r = ' + str(i+1))
	for j in range(plants.rows.__len__()):
		sheet1.write(0, offset+1+j, 'k = ' + str(j+1))
		# write data
	for i in range(populations.rows.__len__()):
		for j in range(plants.rows.__len__()):
			sheet1.write(i+1, offset+1+j, distance_matrix[i][j])

	# save to disk
	if not os.path.exists(APP.config['UPLOAD_FOLDER']):
		os.makedirs(APP.config['UPLOAD_FOLDER'])
	wb.save(APP.config['UPLOAD_FOLDER']+'/'+filename)

# --------------------- RUN SERVER ---------------------------------------------------------------------------------------------------------------------------------------#
if __name__ == '__main__':
    APP.debug=True
    APP.run(host = "0.0.0.0", port = 10000, threaded=True)