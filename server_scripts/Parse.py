import re, warnings, csv

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

def parse_optimizer_output(path_to_file1, path_to_file2):
	""" parse data from optimizer_output_file1 and 2 into database format """
	print(path_to_file1)
	# parse file 1
	output1 = []
	with open(path_to_file1, 'r') as file1:
		# headers
		headers = file1.readline()
		# print(headers)
		headers = re.split(' | \t', headers)
		for line in file1:
			line = line.strip()
			# print(line)
			data = re.split(' | \t', line)
			output1.append(data)
	# print(headers)
	# cross-tab transform output1
	output1_crosstab = []
	for col_index in range(5, len(headers)):
		solution_label = headers[col_index].strip('Sol_')
		for row in output1:
			# print(row)
			# only read w and q variables
			if row[1]!='w' and row[1]!='q':
				continue
			value = round(float(row[col_index])); print(value)
			# check if value is binary
			if value not in [0,1]:
				print('VALUE NOT ROUNDED TO 0 OR 1: ' + str(row[col_index]))
				return -1, -1
			# convert index to integers
			row[2] = 0 if row[2]=='-' else int(row[2])
			row[3] = 0 if row[3]=='-' else int(row[3])
			row[4] = 0 if row[4]=='-' else int(row[4])
			# add new row to crosstab
			output1_crosstab.append([
				row[0], row[1], row[2], row[3], row[4],
				solution_label, value
			])

	# parse file 2
	output2 = []
	with open(path_to_file2, 'r') as file2:
		next(file2) 		# skip first line
		for line in file2:
			data = re.split(' | \t', line.strip('\n'))
			data[0] = data[0].strip('Sol_')
			# remove solutions with 0 ZC and ZE
			if float(data[1])!=0 or float(data[2])!=0:
				output2.append(data)
	return output1_crosstab, output2

def read_optimizer_log(path_to_log):
	with open(path_to_log) as file:
		log = file.read()
	return log
