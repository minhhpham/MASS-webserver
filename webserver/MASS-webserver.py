#!/usr/bin/env python

from flask import render_template, redirect, request, Flask, url_for, abort
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, FieldList, FormField, SubmitField, IntegerField, FloatField
import yaml, sys, binascii, os

with open("server_config.yaml", 'r') as stream:
    try:
        config = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        print(exc)
        sys.exit()

APP = Flask(__name__)
APP.config['SECRET_KEY'] = binascii.hexlify(os.urandom(128))

#----------- web page to ask for input size ----------------------------
class NRow(FlaskForm):
	NPop = IntegerField('Number of populations')
	NPlant = IntegerField('Number of plants')
	LifeSpan = IntegerField('Life Span of project')
@APP.route('/input_size', methods=['GET', 'POST'])
def input_size():
	nRow = NRow()
	if request.method == 'GET':		
		return(render_template('input_size.html', nRow=nRow))
	if request.method == 'POST':
		if nRow.validate_on_submit():
			nPop = nRow.NPop.data
			nPlant = nRow.NPlant.data
			lifeSpan = nRow.LifeSpan.data
			return(redirect(url_for('population_input', nPop = nPop)))

#----------- webpage to ask for populations -----------------------------
# Taking nPop as input
class OnePopulation(FlaskForm):
	r = IntegerField('Index')
	Pr = IntegerField('Current Population')
	lat = FloatField('Latitude')
	lon = FloatField('Longitude')
class PopulationsForm(FlaskForm):
	submit = SubmitField('Submit')
	rows = FieldList(FormField(OnePopulation), min_entries = 0)
@APP.route('/population_input', methods=['GET', 'POST'])
def population_input():
	populations = PopulationsForm()
	if request.method == 'GET':
		if 'nPop' not in request.args:
			abort(400, 'Number of populations not provided in request')
		else:
			nPop = int(request.args['nPop'])				
			for i in range(nPop):
				populations.rows.append_entry(
					{'r': i+1,
					 'Pr': None,
					 'lon': None,
					 'lat': None}
				)
			return(render_template('population_input.html', populations = populations))

	if request.method == 'POST':
		if populations.submit.data:
			return('The form has been submitted')






# --------------------- END SERVER ---------------------------------------#
if __name__ == '__main__':
    APP.debug=True
    APP.run(port = 5001)