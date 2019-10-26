import re, warnings

def parse_input(text):
	""" parse a textarea input from html into a list, delimters are \n and \r """
	data = re.split('[\n\r]', text)
	# remove all empty members from the split
	while True:
		try:
			data.remove('')
		except ValueError:
			break
	return(data)

def fill_populations(text, populations):
	""" parse inputs from text into populations object 
	population is of class PopulationsForm (MASS-webserver.py)
	return an object with class PopulationForm with filled out data
	"""
	inputs = parse_input(text)
	loop_len = min(len(inputs), populations.rows.__len__())	
	for r in range(loop_len):
		rowData = inputs[r].split('\t')
		#  try to fill data in populations object
		try:
			populations.rows[r].Name.data = rowData[0]
			populations.rows[r].Pr.data = rowData[1]
			populations.rows[r].GrowthRate.data = rowData[2]
			populations.rows[r].lat.data = rowData[3]
			populations.rows[r].lon.data = rowData[4]
		except IndexError:
			warnings.warn('Index Error when parsing population input, row {}'.format(r+1), Warning)		
	return(populations)


def fill_plants(text, plants):
	""" parse inputs from text into plants object 
	plants is of class PLantsForm (MASS-webserver.py)
	return an object with class PlantsForm with filled out data
	"""
	inputs = parse_input(text)
	loop_len = min(len(inputs), plants.rows.__len__())	
	for r in range(loop_len):
		rowData = inputs[r].split('\t')
		#  try to fill data in populations object
		try:
			plants.rows[r].LocationName.data = rowData[0]
			plants.rows[r].lat.data = rowData[1]
			plants.rows[r].lon.data = rowData[2]			
		except IndexError:
			warnings.warn('Index Error when parsing plant input, row {}'.format(r+1), Warning)		
	return(plants)
