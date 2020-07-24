from math import sin, cos, acos, radians
from xlwt import Workbook
from flask_wtf import FlaskForm, csrf
from wtforms import StringField, FieldList, FormField, SubmitField, IntegerField, FloatField, validators, BooleanField
import os, yaml
from server_scripts import database as db

global config    # initialized in MASS-webserver.py
with open("server_config.yaml", 'r') as stream:
    try:
        config = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        print(exc)
        sys.exit()

""" HELPER FUNCTIONS """
def fill_dbdata_tech(tech_form, existing_data):
	""" Fill a CombinedForm object with existing data from database 
		existing_data is a list of tuple from the db
	"""
	if len(existing_data) == 0: # no existing data in db
		return(tech_form)

	assert len(existing_data)%3 == 0

	count_additional_techs = 0 # count number of additional techs
	# loop through each tech in existing_data
	for techid in range(int(len(existing_data)/3)):
		row = techid*3 # rowid in existing_data
		selected_tech = existing_data[row]['technologyname']
		if selected_tech in config['techs'].keys():
			# fill this in default_techs
			for r in range(tech_form.default_techs.rows.__len__()):
				if tech_form.default_techs.rows[r].Technology.data == selected_tech:
					# fill this default tech's data
					tech_form.default_techs.rows[r].Select.data = True
					tech_form.default_techs.rows[r].Small.Capkt.data = existing_data[row]['capkt']
					tech_form.default_techs.rows[r].Small.CCkt.data = existing_data[row]['cckt']
					tech_form.default_techs.rows[r].Small.OCt.data = existing_data[row]['oct']
					tech_form.default_techs.rows[r].Small.SRWt.data = existing_data[row]['srwt']
					tech_form.default_techs.rows[r].Small.GPt.data = existing_data[row]['gpt']

					tech_form.default_techs.rows[r].Medium.Capkt.data = existing_data[row+1]['capkt']
					tech_form.default_techs.rows[r].Medium.CCkt.data = existing_data[row+1]['cckt']
					tech_form.default_techs.rows[r].Medium.OCt.data = existing_data[row+1]['oct']
					tech_form.default_techs.rows[r].Medium.SRWt.data = existing_data[row+1]['srwt']
					tech_form.default_techs.rows[r].Medium.GPt.data = existing_data[row+1]['gpt']

					tech_form.default_techs.rows[r].Large.Capkt.data = existing_data[row+2]['capkt']
					tech_form.default_techs.rows[r].Large.CCkt.data = existing_data[row+2]['cckt']
					tech_form.default_techs.rows[r].Large.OCt.data = existing_data[row+2]['oct']
					tech_form.default_techs.rows[r].Large.SRWt.data = existing_data[row+2]['srwt']
					tech_form.default_techs.rows[r].Large.GPt.data = existing_data[row+2]['gpt']

		else:
			count_additional_techs = count_additional_techs + 1
			# fill this in additional_techs
			# first create a new row
			tech_form.additional_techs.rows.append_entry()
			r = tech_form.additional_techs.rows.__len__() - 1 # current row id in additional_techs
			tech_form.additional_techs.rows[r].Technology.data = existing_data[row]['technologyname']

			tech_form.additional_techs.rows[r].Small.Capkt.data = existing_data[row]['capkt']
			tech_form.additional_techs.rows[r].Small.CCkt.data = existing_data[row]['cckt']
			tech_form.additional_techs.rows[r].Small.OCt.data = existing_data[row]['oct']
			tech_form.additional_techs.rows[r].Small.SRWt.data = existing_data[row]['srwt']
			tech_form.additional_techs.rows[r].Small.GPt.data = existing_data[row]['gpt']

			tech_form.additional_techs.rows[r].Medium.Capkt.data = existing_data[row+1]['capkt']
			tech_form.additional_techs.rows[r].Medium.CCkt.data = existing_data[row+1]['cckt']
			tech_form.additional_techs.rows[r].Medium.OCt.data = existing_data[row+1]['oct']
			tech_form.additional_techs.rows[r].Medium.SRWt.data = existing_data[row+1]['srwt']
			tech_form.additional_techs.rows[r].Medium.GPt.data = existing_data[row+1]['gpt']

			tech_form.additional_techs.rows[r].Large.Capkt.data = existing_data[row+2]['capkt']
			tech_form.additional_techs.rows[r].Large.CCkt.data = existing_data[row+2]['cckt']
			tech_form.additional_techs.rows[r].Large.OCt.data = existing_data[row+2]['oct']
			tech_form.additional_techs.rows[r].Large.SRWt.data = existing_data[row+2]['srwt']
			tech_form.additional_techs.rows[r].Large.GPt.data = existing_data[row+2]['gpt']
	# done looping through existing_data
	tech_form.n_additional.data = count_additional_techs
	return(tech_form)

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

def tech_combine(_techs):
	""" _techs has class CombinedForm
		Combine selected _techs.default_techs and _techs.additional_techs
		return a TechnologiesForm object with selected techs
	"""
	selected_techs = TechnologiesForm()
	for t in  _techs.default_techs.rows:
		if t.Select.data: # if default tech is selected by user, add to selected_techs
			t.default_tech.data = True	# identifier for database's boolean field
			selected_techs.rows.append_entry(t.data)

	if _techs.additional_techs.rows.__len__() > 0:
		for t in _techs.additional_techs.rows:
			t.default_tech.data = False # identifier for database's boolean field
			selected_techs.rows.append_entry(t.data)
	return(selected_techs)

def distance(lat1, lon1, lat2, lon2):
	""" distance (in miles) between 2 points on earth """
	return(0.000189394*
		(3963*acos(cos(radians(90-lat1))*cos(radians(90-lat2))+
			sin(radians(90-lat1))*sin(radians(90-lat2))*cos(radians(lon1-lon2))))*5280
	)
def distance_pop_plant(pops, plants):
	""" distance between populations and plants 
		pops is an array of tuples as read from database
		plants is an array of tuples as read from database
		returns a 2D array of size nPops*nPlants
	"""
	nPop = len(pops)
	nPlant = len(plants)
	# initialize output 
	out = [[0 for j in range(nPlant)] for i in range(nPop)]
	# loop through pops and plants
	for i in range(nPop):
		for j in range(nPlant):
			try:
				lat1 = float(pops[i]['lat'])
				lon1 = float(pops[i]['lon'])
				lat2 = float(plants[j]['lat'])
				lon2 = float(plants[j]['lon'])
			except ValueError:
				raise TypeError('cannot convert coordinates to float')
			out[i][j] = distance(lat1, lon1, lat2, lon2)
	return(out)

def write_input_to_tsv(projectID, directory, filename):
	""" write input data to tab-separated file. this file will be read by the optimizer.
		data are previously saved under a username and project_name
	"""
	# delete file if exists
	filename = directory+'/'+filename
	if os.path.exists(filename):
		os.remove(filename)
	# pull data from db
	populations = db.getPopulations(projectID)
	plants = db.getPlants(projectID)
	techs = db.getTechnologies(projectID)
	params = db.getParams(projectID)
	duration = db.getInputSize(projectID)['durations']

	# determine the max number of column (later we will pad all rows with \t to reach this number of columns)
	n_col_tsv = max(3, 					# number of cols in first row
					7,					# second row
					len(populations),
					len(techs), 		# row 4-8
					len(plants)			# row 9 and after
	)

	# create file and start writing
	with open(filename, 'w') as file:
		# first line:
		file.write(
			str(len(populations)) + '\t' + 	# no. of pop clusters
			str(len(plants)) + '\t' + 		# no. of locations
			str(len(techs))	+				# no. of techs
			(n_col_tsv-3)*'\t' 				# padding with tabs
		)
		file.write('\n')
		# second line: parameters and duration
		value_array = [str(r['value']) for r in params]
		value_array.append(str(duration))
		file.write('\t'.join(value_array))
		file.write((n_col_tsv-len(value_array))*'\t')
		file.write('\n')
		# third line: population number for all clusters, projected at the end of duration
		value_array = [str(r['pr']*(1+r['growthrate'])**duration) for r in populations]
		file.write('\t'.join(value_array))
		file.write((n_col_tsv-len(value_array))*'\t')
		file.write('\n')
		# -- line 4-8: tech table--
		# line 4: Capkt of all techs
		value_array = [str(r['capkt']) for r in techs]
		file.write('\t'.join(value_array))
		file.write((n_col_tsv-len(value_array))*'\t')
		file.write('\n')
		# line 5: CCkt of all techs
		value_array = [str(r['cckt']) for r in techs]
		file.write('\t'.join(value_array))
		file.write((n_col_tsv-len(value_array))*'\t')
		file.write('\n')
		# line 6: OCt of all techs
		value_array = [str(r['oct']) for r in techs]
		file.write('\t'.join(value_array))
		file.write((n_col_tsv-len(value_array))*'\t')
		file.write('\n')
		# line 7: SRwt of all techs
		value_array = [str(r['srwt']) for r in techs]
		file.write('\t'.join(value_array))
		file.write((n_col_tsv-len(value_array))*'\t')
		file.write('\n')
		# line 8: GPt of all techs
		value_array = [str(r['gpt']) for r in techs]
		file.write('\t'.join(value_array))
		file.write((n_col_tsv-len(value_array))*'\t')
		file.write('\n')

		# line 9 and on: distance table
		distance_matrix = distance_pop_plant(populations, plants)
		value_array_each_row = []
		for row in distance_matrix:
			value_array = [str(value) for value in row]
			value_array_each_row.append('\t'.join(value_array) + (n_col_tsv-len(value_array))*'\t')
		value_array_all = '\n'.join(value_array_each_row)
		file.write(value_array_all)

	# done


def tech_data_validation(tech_form):
	""" 
	validate tech data
	tech_form is a CombinedForm
	"""
	### validate default tech
	for i in range(tech_form.default_techs.rows.__len__()):
		row = tech_form.default_techs.rows[i]
		# check if name is blank
		if row.Technology.data is None or row.Technology.data == '':
			return False
		# check Small
		if row.Small.Capkt.data is None or row.Small.Capkt.data == '':
			return False
		if row.Small.CCkt.data is None or row.Small.CCkt.data == '':
			return False
		if row.Small.OCt.data is None or row.Small.OCt.data == '':
			return False
		if row.Small.SRWt.data is None or row.Small.SRWt.data == '':
			return False
		if row.Small.GPt.data is None or row.Small.GPt.data == '':
			return False
		# check medium
		if row.Medium.Capkt.data is None or row.Medium.Capkt.data == '':
			return False
		if row.Medium.CCkt.data is None or row.Medium.CCkt.data == '':
			return False
		if row.Medium.OCt.data is None or row.Medium.OCt.data == '':
			return False
		if row.Medium.SRWt.data is None or row.Medium.SRWt.data == '':
			return False
		if row.Medium.GPt.data is None or row.Medium.GPt.data == '':
			return False
		# check large
		if row.Large.Capkt.data is None or row.Large.Capkt.data == '':
			return False
		if row.Large.CCkt.data is None or row.Large.CCkt.data == '':
			return False
		if row.Large.OCt.data is None or row.Large.OCt.data == '':
			return False
		if row.Large.SRWt.data is None or row.Large.SRWt.data == '':
			return False
		if row.Large.GPt.data is None or row.Large.GPt.data == '':
			return False

	### validate additional tech
	for i in range(tech_form.additional_techs.rows.__len__()):
		row = tech_form.additional_techs.rows[i]
		# check if name is blank
		if row.Technology.data is None or row.Technology.data == '':
			return False
		# check Small
		if row.Small.Capkt.data is None or row.Small.Capkt.data == '':
			return False
		if row.Small.CCkt.data is None or row.Small.CCkt.data == '':
			return False
		if row.Small.OCt.data is None or row.Small.OCt.data == '':
			return False
		if row.Small.SRWt.data is None or row.Small.SRWt.data == '':
			return False
		if row.Small.GPt.data is None or row.Small.GPt.data == '':
			return False
		# check medium
		if row.Medium.Capkt.data is None or row.Medium.Capkt.data == '':
			return False
		if row.Medium.CCkt.data is None or row.Medium.CCkt.data == '':
			return False
		if row.Medium.OCt.data is None or row.Medium.OCt.data == '':
			return False
		if row.Medium.SRWt.data is None or row.Medium.SRWt.data == '':
			return False
		if row.Medium.GPt.data is None or row.Medium.GPt.data == '':
			return False
		# check large
		if row.Large.Capkt.data is None or row.Large.Capkt.data == '':
			return False
		if row.Large.CCkt.data is None or row.Large.CCkt.data == '':
			return False
		if row.Large.OCt.data is None or row.Large.OCt.data == '':
			return False
		if row.Large.SRWt.data is None or row.Large.SRWt.data == '':
			return False
		if row.Large.GPt.data is None or row.Large.GPt.data == '':
			return False
	
	return True