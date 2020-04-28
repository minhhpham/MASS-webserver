import psycopg2
import psycopg2.extras
import yaml, time, sys

global config    # initialized in MASS-webserver.py
with open("server_config.yaml", 'r') as stream:
    try:
        config = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        print(exc)
        sys.exit()

conn = psycopg2.connect(dbname = config["db"]["dbname"], user = config["db"]["user"], 
						password = config["db"]["password"], port = config["db"]["port"])

table_names = ['projects', 'ns', 'populations', 'plants', 'technologies', 'params', 'request_queue', 'optimizer_output1', 'optimizer_output2', 'optimizer_outputlog']

def init_db():
	""" initialize tables if not found in the database """
	cursor = conn.cursor()
	for table_name in table_names:
		cursor.execute("""
			SELECT COUNT(*) FROM information_schema.tables WHERE table_name=%s
		""", [table_name])
		if cursor.fetchone()[0] == 0:
			print("Creating table %s" % table_name)
			init_table(table_name)

	cursor.close()
	# commit the changes
	conn.commit()

def init_table(table_name):
	cursor = conn.cursor()
	try:
		if table_name == 'projects':
			cursor.execute("""
						CREATE TABLE Projects(
							projectID 	varchar(255),	
							p_desc		varchar(4096),
							status 		varchar(255),
							last_optimized varchar(255),
							PRIMARY KEY(projectID)		
						)
			""")
		elif table_name == 'ns':
			cursor.execute("""
						CREATE TABLE Ns(
							projectID	varchar(255),	
							NPop		int,
							NPlant		int,
							LifeSpan	int,
							PRIMARY KEY(projectID)
						)
			""")
		elif table_name == 'populations':
			cursor.execute("""
								CREATE TABLE Populations(
									projectID 	varchar(255),
									index 		int,	
									Name		varchar(255), -- represent Cluster name
									Pr		    int NOT NULL CHECK (Pr >= 0), -- represent Current Population
									GrowthRate	float, -- represent Population Growth Rate
									lat		    float, -- represent Latitude
									lon		    float, -- represent Longitude
									PRIMARY KEY(projectID, index)
								)
			""")
		elif table_name == 'plants':
			cursor.execute("""
								CREATE TABLE Plants(
									projectID 		varchar(255),
									index 				int,	
									LocationName		varchar(255), -- represent Cluster name
									lat					float, -- represent Latitude
									lon					float, -- represent Longitude
									existing_location	boolean,
									existing_tech		varchar(255),
									PRIMARY KEY(projectID, index)
								)
					""")
		elif table_name == 'technologies':
			cursor.execute("""
								CREATE TABLE Technologies(
									projectID 	varchar(255),
									index 		int,
									default_tech	BOOLEAN NOT NULL,
									TechnologyName varchar(255),
									Scale		varchar(255),
									Capkt		float,
									CCkt		float, 
									OCt			float, 
									SRWt		float,
									GPt			float,
									PRIMARY KEY(projectID, index)
								)
							""")
		elif table_name == 'params':
			cursor.execute("""
								CREATE TABLE Params(
									projectID varchar(255),
									index 		int,	
									Label		varchar(255), 
									Unit		varchar(255), 
									Value		float, 
									PRIMARY KEY(projectID, index)
								)
			""")
		elif table_name == 'request_queue':
			cursor.execute("""
								CREATE TABLE request_queue(
									projectID 	varchar(255),
									queue_order	int
								)
			""")
		elif table_name == 'optimizer_output1':
			cursor.execute("""
								CREATE TABLE optimizer_output1(
									projectID 	varchar(255),
									var_name	varchar(255),
									var			varchar(255),
									r			SMALLINT,
									k			SMALLINT,
									t			SMALLINT,
									solution_label varchar(255),
									value 		SMALLINT
								)
			""")
		elif table_name == 'optimizer_output2':
			cursor.execute("""
								CREATE TABLE optimizer_output2(
									projectID 	varchar(255),
									solution_label varchar(255),
									zc 			float,
									ze 			float 
								)
			""")
		elif table_name == 'optimizer_outputlog':
			cursor.execute("""
								CREATE TABLE optimizer_outputlog(
									projectID 	varchar(255),
									log 		varchar 
								)
			""")

		else:
			pass
	except(psycopg2.DatabaseError) as error:
		print(error)
		conn.commit()

def db_is_ready():
	""" check if database has the correct tables """
	cursor = conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
	for table_name in table_names:
		cursor.execute("""
			SELECT COUNT(*) FROM information_schema.tables WHERE table_name=%s
		""", [table_name])
		if cursor.fetchone()['count'] == 0:
			return False
	return True

# Returns a list of projects
def getProject(projectID):
	try:
		cursor = conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

		# Select projects
		cursor.execute("SELECT projectID, p_desc, status, last_optimized FROM Projects WHERE projectID = %s", (projectID,))
		vals = cursor.fetchone() # Get the result

	except(psycopg2.DatabaseError) as error:
		raise Exception(str(error))
	# close communication with the PostgreSQL database server
	cursor.close()
	return vals

def projectExists(projectID):
	search_result = getProject(projectID)
	if search_result is None:
		return False
	else:
		return True

# Creates a new project
def saveProject(projectID, p_desc):
	try:
		cursor = conn.cursor()

		vals = (projectID, p_desc, 'input uncompleted, not yet optimized')
		cursor.execute('''INSERT INTO Projects VALUES (%s, %s, %s)''', vals)

	except(psycopg2.DatabaseError) as error:
		print(error)
	# close communication with the PostgreSQL database server
	cursor.close()
	# commit the changes
	conn.commit()

def updateProjectStatus(projectID, new_status):
	try:
		cursor = conn.cursor()
		cursor.execute("UPDATE Projects SET status=%s WHERE projectID=%s", [new_status, projectID])
	except(psycopg2.DatabaseError) as error:
		print(error)
	# close communication with the PostgreSQL database server
	cursor.close()
	# commit the changes
	conn.commit()


# Inserts an Inputsize for a given user and projectID, update records if data exists
def saveInputSize(inputSize, projectID):
	# insert records
	try:
		cursor = conn.cursor()

		vals = (projectID, inputSize.NPlant.data, inputSize.NPop.data, inputSize.LifeSpan.data)
		cursor.execute('''INSERT INTO Ns VALUES (%s, %s, %s, %s)
			ON CONFLICT (projectID) DO
			UPDATE SET nplant=EXCLUDED.nplant, npop=EXCLUDED.npop, lifespan=EXCLUDED.lifespan''', vals)
		
	except(psycopg2.DatabaseError) as error:
		print(error)
	# close communication with the PostgreSQL database server
	cursor.close()
	# commit the changes
	conn.commit()

# Retrieve an Inputsize for a given user and projectID
# 	Returns an InputSize object
def getInputSize(projectID):
	try:
		cursor = conn.cursor()

		cursor.execute("SELECT NPop, NPlant, LifeSpan FROM Ns WHERE projectID = %s", (projectID,))
		vals = cursor.fetchone() # Get the result

		newInputSize = {}
		if vals is None:
			newInputSize["numplants"] = None
			newInputSize["numpops"] = None
			newInputSize["durations"] = None
		else:
			newInputSize["numplants"] = vals[0]
			newInputSize["numpops"] = vals[1]
			newInputSize["durations"] = vals[2]
	except(psycopg2.DatabaseError) as error:
		print(error)
	# close communication with the PostgreSQL database server
	cursor.close()
	return newInputSize

# Retrieve a population for a given user and projectID
# 	Returns an list of dictionaries with the column names
def getPopulations(projectID):
	try:
		cursor = conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

		cursor.execute("SELECT * FROM populations WHERE projectID = %s", (projectID,))
		vals = cursor.fetchall() # Get the result

	except(psycopg2.DatabaseError) as error:
		print(error)
	# close communication with the PostgreSQL database server
	cursor.close()
	return vals

# Inserts populations table for a given user and projectID
# update records if exists
# otherwise insert
# populations has class PopulationsForm
def savePopulations(populations, projectID):
	# wipe existing data
	try:
		cursor = conn.cursor()
		cursor.execute('''DELETE FROM populations WHERE projectID = %s''', [projectID])
	except(psycopg2.DatabaseError) as error:
		print(error)

	# insert data
	try:
		cursor = conn.cursor()

		index = 0
		for r in populations.rows:
			index = index + 1
			vals = (projectID, index, r.Name.data, r.Pr.data, r.GrowthRate.data, r.lat.data, r.lon.data)
			cursor.execute('''INSERT INTO populations VALUES (%s, %s, %s, %s, %s, %s, %s)''', vals)
		
	except(psycopg2.DatabaseError) as error:
		print(error)
	# close communication with the PostgreSQL database server
	cursor.close()
	# commit the changes
	conn.commit()

# Insert plants table, update if present
# plants is a plantsform object
def savePlants(plants, projectID):
	# wipe existing data
	try:
		cursor = conn.cursor()
		cursor.execute('''DELETE FROM plants WHERE projectID = %s''', [projectID])
	except(psycopg2.DatabaseError) as error:
		print(error)

	# insert data
	try:
		cursor = conn.cursor()

		index = 0
		for r in plants.rows:
			index = index + 1
			vals = (projectID, index, r.LocationName.data, r.lat.data, r.lon.data, r.existing_location.data, r.existing_tech.data)
			cursor.execute('''INSERT INTO plants VALUES (%s, %s, %s, %s, %s, %s, %s)''', vals)
	except(psycopg2.DatabaseError) as error:
		print(error)
	# close communication with the PostgreSQL database server
	cursor.close()
	# commit the changes
	conn.commit()

# Retrieve the plants for a given user and projectID
# 	Returns an list of dictionaries with the column names
def getPlants(projectID):
	try:
		cursor = conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

		cursor.execute("SELECT * FROM plants WHERE projectID = %s", [projectID])
		vals = cursor.fetchall() # Get the result

	except(psycopg2.DatabaseError) as error:
		print(error)
	# close communication with the PostgreSQL database server
	cursor.close()
	return vals


# Retrieve the tech for a given user and projectID
# 	Returns an list of dictionaries with the column names
def getTechnologies(projectID):
	try:
		cursor = conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

		cursor.execute("SELECT * FROM technologies WHERE projectID = %s", [projectID])
		vals = cursor.fetchall() # Get the result

	except(psycopg2.DatabaseError) as error:
		print(error)
	# close communication with the PostgreSQL database server
	cursor.close()
	return vals

def getSelectedTechnologies(projectID):
	""" Get technologies that were selected by user after submitting tech form """
	techs_db = getTechnologies(projectID)
	output = [('1', 'N/A')] # initialize output set
	for r in techs_db:
		techs_found = [o[1] for o in output]
		if r['technologyname'] not in techs_found:
			# append this new tech to output
			output.append((str(len(output)+1), r['technologyname']))
	return(output)

# Insert technologies table, update if present
# Technologies is a technologiesform object
def saveTechnologies(tech, projectID):
	# wipe existing data
	try:
		cursor = conn.cursor()
		cursor.execute('''DELETE FROM technologies WHERE projectID = %s''', [projectID])
	except(psycopg2.DatabaseError) as error:
		print(error)

	# insert data
	try:
		cursor = conn.cursor()

		index = 0
		for r in tech.rows:
			# insert small scale
			index = index + 1
			vals = (projectID, index, r.default_tech.data, r.Technology.data, 'Small',
					r.Small.Capkt.data, r.Small.CCkt.data, r.Small.OCt.data, r.Small.SRWt.data, r.Small.GPt.data)
			cursor.execute('''INSERT INTO technologies VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''', vals)
			# insert medium scale
			index = index + 1
			vals = (projectID, index, r.default_tech.data, r.Technology.data, 'Medium',
					r.Medium.Capkt.data, r.Medium.CCkt.data, r.Medium.OCt.data, r.Medium.SRWt.data, r.Medium.GPt.data)
			cursor.execute('''INSERT INTO technologies VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''', vals)
			# insert large scale
			index = index + 1
			vals = (projectID, index, r.default_tech.data, r.Technology.data, 'Large',
					r.Large.Capkt.data, r.Large.CCkt.data, r.Large.OCt.data, r.Large.SRWt.data, r.Large.GPt.data)
			cursor.execute('''INSERT INTO technologies VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''', vals)
	except(psycopg2.DatabaseError) as error:
		print(error)
	# close communication with the PostgreSQL database server
	cursor.close()
	# commit the changes
	conn.commit()

# Insert params table, update if present
# params is a paramsform object
def saveParams(params, projectID):
	# insert data
	try:
		cursor = conn.cursor()

		index = 0
		for r in params.rows:
			index = index + 1
			vals = (projectID, index, r.Label.data, r.Unit.data, r.Value.data)
			cursor.execute('''INSERT INTO params VALUES (%s, %s, %s, %s, %s)
				ON CONFLICT (projectID, index) DO
				UPDATE SET label=EXCLUDED.label, unit=EXCLUDED.unit, value=EXCLUDED.value''', vals)
	except(psycopg2.DatabaseError) as error:
		print(error)
	# close communication with the PostgreSQL database server
	cursor.close()
	# commit the changes
	conn.commit()

# Retrieve the params for a given user and projectID
# 	Returns an list of dictionaries with the column names
def getParams(projectID):
	try:
		cursor = conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

		cursor.execute("SELECT label, unit, value FROM params WHERE projectID = %s", [projectID])
		vals = cursor.fetchall() # Get the result

	except(psycopg2.DatabaseError) as error:
		print(error)
	# close communication with the PostgreSQL database server
	cursor.close()

	# convert labels of vals to uppercase
	vals1 = []
	for r in vals:
		vals1.append({'Label': r['label'], 'Unit': r['unit'], 'Value': r['value']})
	return vals

# --------------- FUNCTIONS FOR optimizer_scheduler -----------------------------
def isQueueNotEmpty():
	""" return True if queue is not empty in db """
	try:
		cursor = conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
		cursor.execute("SELECT * FROM request_queue")
		vals = cursor.fetchall() # Get the result

	except(psycopg2.DatabaseError) as error:
		print(error)
	# close communication with the PostgreSQL database server
	cursor.close()

	if len(vals) == 0:
		return False
	else:
		return True

def updateQueueOrder(projectID):
	""" update the projectID's queue order in the projects table """
	try:
		cursor = conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

		# get current queue order
		cursor.execute('''SELECT max(queue_order) as order FROM request_queue WHERE projectid = %s''', [projectID])
		queue_order =  cursor.fetchone()['order']

		# update projects table
		status = "input completed, on queue for optimizing at queue position " + str(queue_order)
		cursor.execute('''UPDATE projects SET status = %s WHERE projectid = %s ''', [status, projectID])

	except(psycopg2.DatabaseError) as error:
		print(error)

	cursor.close()
	conn.commit()

def popQueue():
	""" pop the first request in the queue """
	try:
		cursor = conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

		# first get the record with the lowest queue_order
		cursor.execute(''' SELECT * FROM request_queue WHERE queue_order IN
				(SELECT min(queue_order) FROM request_queue)
			'''
		)
		projectID = cursor.fetchone()['projectid']

		# then pop the record and decrease all queue_order by 1
		cursor.execute(''' 
			DELETE FROM request_queue WHERE projectID = %s;
			UPDATE request_queue SET queue_order = queue_order - 1;
			''', [projectID]
		)

	except(psycopg2.DatabaseError) as error:
		print(error)

	# then update the status of this projectID
	updateProjectStatus(projectID, "input completed, optimizing")

	# then update the status of other projectID
	cursor.execute('''SELECT DISTINCT projectid FROM request_queue''')
	projects_on_queue = cursor.fetchall()
	for project in projects_on_queue:
		projectID = project['projectid']
		updateQueueOrder(projectID)

	# close communication with the PostgreSQL database server
	cursor.close()
	conn.commit()
	return projectID

def enQueue(projectID):
	""" add a processing request to queue """
	try:
		cursor = conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

		# insert with the highest queue order
		cursor.execute('''INSERT INTO request_queue
			SELECT %s, count(queue_order)+1 FROM request_queue
			''', [projectID])
		# get the queue order
		cursor.execute('''SELECT max(queue_order) as order FROM request_queue WHERE projectid = %s;''', [projectID])
		queue_order = cursor.fetchone()['order']

	except(psycopg2.DatabaseError) as error:
		print(error)

	# close communication with the PostgreSQL database server
	cursor.close()
	# commit the changes
	conn.commit()

	# update the queue order in project status
	status = "input completed, on queue for optimizing at queue position " + str(queue_order)
	updateProjectStatus(projectID, status)


# ------------------- functions to save and retrieve optimizer output ---------------
def save_optimizer_output(projectID, output1, output2):
	"""
	output1: an array of arrays. Each sub-array has 7 elements:  var_name, var, r, k, t, solution_label, value
	output2: an array of arrays. Each sub array has 3 elements: Solution label, ZC, ZE
	"""
	# delete records if exist
	try:
		cursor = conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
		cursor.execute('''DELETE FROM optimizer_output1 WHERE projectid = %s''', [projectID])
		cursor.execute('''DELETE FROM optimizer_output2 WHERE projectid = %s''', [projectID])
	except(psycopg2.DatabaseError) as error:
		print(error)

	# insert output1
	try:
		cursor = conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
		for r in output1:
			vals = [projectID, r[0], r[1], r[2], r[3], r[4], r[5], r[6]]
			cursor.execute('''INSERT INTO optimizer_output1 VALUES (%s, %s, %s, %s, %s, %s, %s, %s)''', vals)
	except(psycopg2.DatabaseError) as error:
		print(error)

	# insert output2
	try:
		cursor = conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
		for r in output2:
			vals = [projectID, r[0], r[1], r[2]]
			cursor.execute('''INSERT INTO optimizer_output2 VALUES (%s, %s, %s, %s)''', vals)
	except(psycopg2.DatabaseError) as error:
		print(error)

	# close communication with the PostgreSQL database server
	cursor.close()
	# commit the changes
	conn.commit()

def get_optimizer_output(projectID):
	"""
	return: output1, output2
	output1: array of dict with keys project_id, var_name, var, r, k, t
	output2: array of dict with keys project_id, ze, zc
	"""
	# get output1
	try:
		cursor = conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
		cursor.execute('''DELETE * optimizer_output1 WHERE projectid = %s''', [projectID])
		output1 = cursor.fetchall()
	except(psycopg2.DatabaseError) as error:
		print(error)

	# get output2
	try:
		cursor = conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
		cursor.execute('''DELETE * optimizer_output2 WHERE projectid = %s''', [projectID])
		output2 = cursor.fetchall()
	except(psycopg2.DatabaseError) as error:
		print(error)

	# close communication with the PostgreSQL database server
	cursor.close()

	return output1, output2

def save_optimizer_log(projectID, log):
	"""
	log: a very long string
	"""
	# delete record if exists
	try:
		cursor = conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
		cursor.execute('''DELETE FROM optimizer_outputlog WHERE projectid = %s''', [projectID])
	except(psycopg2.DatabaseError) as error:
		print(error)
	# insert
	try:
		cursor = conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
		cursor.execute('''INSERT INTO optimizer_outputlog VALUES (%s, %s)''', [projectID, log])
	except(psycopg2.DatabaseError) as error:
		print(error)

	# close communication with the PostgreSQL database server
	cursor.close()
	# commit the changes
	conn.commit()

def get_optimizer_log(projectID):
	try:
		cursor = conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
		cursor.execute('''SELECT FROM optimizer_outputlog WHERE projectid = %s''', [projectID])
		vals = cursor.fetchone()
	except(psycopg2.DatabaseError) as error:
		print(error)

	# close communication with the PostgreSQL database server
	cursor.close()
	# commit the changes
	conn.commit()
	return vals
