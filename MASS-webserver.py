#!/usr/bin/env python

from flask import render_template, redirect, request, Flask, url_for, abort
from flask_wtf import FlaskForm
from wtforms import StringField, FieldList, FormField, SubmitField, IntegerField, FloatField, validators, BooleanField
import yaml, sys, binascii, os

with open("server_config.yaml", 'r') as stream:
    try:
        config = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        print(exc)
        sys.exit()

APP = Flask(__name__)
APP.config['SECRET_KEY'] = binascii.hexlify(os.urandom(128))

@APP.route('/', methods = ['GET'])
def index():
	return(render_template('index.html'))

# variables that will be decalared globally
global nPop, nPlant, lifeSpan
global populations, plants, tech_form, techs, params 	# techs has class TechnologiesForm and has the input data
														# tech_form is the form to be rendered to web interface
#----------- web page to ask for input size -----------------------------------------------------------------
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
			return(redirect(url_for('population_input', _external=True)))

#----------- webpage to ask for populations -----------------------------------------------------------------
class OnePopulation(FlaskForm):
	r = IntegerField('Index')
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
			return(redirect(url_for('plant_input', _external=True)))

	# TODO: calculate projected population

# ------------- webpage to ask for plants ---------------------------------------------------------------------
class OnePlant(FlaskForm):
	k = IntegerField('Index')
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
			return(redirect(url_for('tech_input', _external=True)))


# ------------- webpage to ask for techs ---------------------------------------------------------------------
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
			return(redirect(url_for('parameter_input', _external=True)))

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
			

# ------------- webpage to ask for parameters ----------------------------------------------------------------
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
		return(redirect(url_for('review', _external=True)))


# ------------ review input data ----------------------------------------------------------------------------
@APP.route('/review', methods = ['POST', 'GET'])
def review():
	global nPop, nPlant, lifeSpan, populations, plants, techs, params

	if request.method == 'GET':
		return(render_template('review.html', nPop = nPop, nPlant = nPlant, lifeSpan = lifeSpan,
			populations = populations, plants = plants, techs = techs, params = params))

# ------------ run optimizer ----------------------------------------------------------------------------------
@APP.route('/run_optimizer', methods = ['POST'])
def run_optimizer():
	if request.form['command'] == 'Run optimizer':
		return('TBA')
	else:
		abort(400, 'Unknown command')


# --------------------- RUN SERVER --------------------------------------------------------------------------#
if __name__ == '__main__':
    APP.debug=True
    APP.run(port = 10000, threaded=True)