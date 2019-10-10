#!/usr/bin/env python

from flask import render_template, redirect, request, Flask, url_for, abort
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, FieldList, FormField, SubmitField, IntegerField, FloatField, validators
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
global populations, plants, techs, params
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
			return(redirect(url_for('population_input')))

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
		if 'nPop' not in globals():
			abort(400, 'Number of populations not found')
		else:			
			for i in range(nPop):
				populations.rows.append_entry({'r': i+1})
			return(render_template('population_input.html', populations = populations))

	if request.method == 'POST':
		if populations.submit.data:
			return(redirect(url_for('plant_input')))

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
		if 'nPlant' not in globals():
			abort(400, 'Number of plants not found')
		else:
			for i in range(nPlant):
				plants.rows.append_entry({'k': i+1})
			return(render_template('plant_input.html', plants = plants))

	if request.method == 'POST':
		if plants.submit.data:
			return('submitted')


# ------------- webpage to ask for techs ---------------------------------------------------------------------

# ------------- webpage to ask for parameters ----------------------------------------------------------------

# --------------------- END SERVER --------------------------------------------------------------------------#
if __name__ == '__main__':
    APP.debug=True
    APP.run(port = 100)