import psycopg2
import psycopg2.extras
import yaml

global config    # initialized in MASS-webserver.py
with open("server_config.yaml", 'r') as stream:
    try:
        config = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        print(exc)
        sys.exit()

conn = psycopg2.connect(dbname = config["db"]["dbname"], user = config["db"]["user"], 
						password = config["db"]["password"], port = config["db"]["port"])

def init_db():
	""" initialize tables if not found in the database """
	cursor = conn.cursor()
	table_names = ['users', 'projects', 'ns', 'populations', 'plants', 'technologies', 'params']
	for table_name in table_names:
		cursor.execute("""
			SELECT COUNT(*) FROM information_schema.tables WHERE table_name=%s
		""", (table_name,))
		if cursor.fetchone()[0] == 0:
			print("Creating table %s" % table_name)
			init_table(table_name)

	cursor.close()
	# commit the changes
	conn.commit()

def init_table(table_name):
	cursor = conn.cursor()
	try:
		if table_name == 'users':
			cursor.execute("""
				CREATE TABLE Users(
					username		varchar(255),
					password_hashed	varchar(1024),	-- big space in case we need cryptography later
					full_name		varchar(255),
					email			varchar(255),
					PRIMARY KEY(username)
				)
			""")
		elif table_name == 'projects':
			cursor.execute("""
						CREATE TABLE Projects(
							username	varchar(255),
							project_name varchar(255),	
							p_desc		varchar(255),
							PRIMARY KEY(username, project_name)		
						)
			""")
		elif table_name == 'ns':
			cursor.execute("""
						CREATE TABLE Ns(
							username	varchar(255),
							project_name varchar(255),	
							NPop		int,
							NPlant		int,
							LifeSpan	int,
							PRIMARY KEY(username, project_name)
						)
			""")
		elif table_name == 'populations':
			cursor.execute("""
								CREATE TABLE Populations(
									username	varchar(255),
									project_name varchar(255),
									index 		int,	
									Name		varchar(255), -- represent Cluster name
									Pr		    int NOT NULL CHECK (Pr >= 0), -- represent Current Population
									GrowthRate	float, -- represent Population Growth Rate
									lat		    float, -- represent Latitude
									lon		    float, -- represent Longitude
									PRIMARY KEY(username, project_name, index)
								)
			""")
		elif table_name == 'plants':
			cursor.execute("""
								CREATE TABLE Plants(
									username			varchar(255),
									project_name 		varchar(255),
									index 				int,	
									LocationName		varchar(255), -- represent Cluster name
									lat					float, -- represent Latitude
									lon					float, -- represent Longitude
									existing_location	boolean,
									existing_tech		varchar(255),
									PRIMARY KEY(username, project_name, index)
								)
					""")
		elif table_name == 'technologies':
			cursor.execute("""
								CREATE TABLE Technologies(
									username	varchar(255),
									project_name varchar(255),
									index 		int,
									default_tech	BOOLEAN NOT NULL,
									TechnologyName varchar(255),
									Scale		varchar(255),
									Capkt		float,
									CCkt		float, 
									OCt			float, 
									SRWt		float,
									GPt			float,
									PRIMARY KEY(username, project_name, index)
								)
							""")
		elif table_name == 'params':
			cursor.execute("""
								CREATE TABLE Params(
									username	varchar(255),
									project_name varchar(255),
									index 		int,	
									Label		varchar(255), 
									Unit		varchar(255), 
									Value		float, 
									PRIMARY KEY(username, project_name, index)
								)
			""")
		else:
			pass
	except(psycopg2.DatabaseError) as error:
		print(error)
		conn.commit()

def register_user(username, password_hased):
	return

def authenticate_user(username, password_hashed):
	return

# Returns a list of projects
def getProjects(username):
	try:
		cursor = conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

		# Select projects
		cursor.execute("SELECT project_name, p_desc FROM Projects WHERE username = %s", (username,))
		vals = cursor.fetchall() # Get the result

	except(psycopg2.DatabaseError) as error:
		print(error)
	# close communication with the PostgreSQL database server
	cursor.close()
	return vals

# Creates a new project
def saveProject(username, project_name, p_desc):
	try:
		cursor = conn.cursor()

		vals = (username, project_name, p_desc)
		cursor.execute('''INSERT INTO Projects VALUES (%s, %s, %s)
			ON CONFLICT (username, project_name) DO
			UPDATE SET p_desc=EXCLUDED.p_desc''', vals)

	except(psycopg2.DatabaseError) as error:
		print(error)
	# close communication with the PostgreSQL database server
	cursor.close()
	# commit the changes
	conn.commit()

# Inserts an Inputsize for a given user and projectID, update records if data exists
def saveInputSize(inputSize, username, project_name):
	# insert records
	try:
		cursor = conn.cursor()

		vals = (username, project_name, inputSize.NPlant.data, inputSize.NPop.data, inputSize.LifeSpan.data)
		cursor.execute('''INSERT INTO Ns VALUES (%s, %s, %s, %s, %s)
			ON CONFLICT (username, project_name) DO
			UPDATE SET nplant=EXCLUDED.nplant, npop=EXCLUDED.npop, lifespan=EXCLUDED.lifespan''', vals)
		
	except(psycopg2.DatabaseError) as error:
		print(error)
	# close communication with the PostgreSQL database server
	cursor.close()
	# commit the changes
	conn.commit()

# Retrieve an Inputsize for a given user and projectID
# 	Returns an InputSize object
def getInputSize(username, project_name):
	try:
		cursor = conn.cursor()

		vals = (username, project_name)

		cursor.execute("SELECT NPop, NPlant, LifeSpan FROM Ns WHERE username = %s AND project_name = %s", vals)
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
def getPopulations(username, project_name):
	try:
		cursor = conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

		vals = (username, project_name)

		cursor.execute("SELECT * FROM populations WHERE username = %s AND project_name = %s", vals)
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
def savePopulations(populations, username, project_name):
	# wipe existing data
	try:
		cursor = conn.cursor()
		cursor.execute('''DELETE FROM populations WHERE username = %s AND project_name = %s''', [username, project_name])
	except(psycopg2.DatabaseError) as error:
		print(error)

	# insert data
	try:
		cursor = conn.cursor()

		index = 0
		for r in populations.rows:
			index = index + 1
			vals = (username, project_name, index, r.Name.data, r.Pr.data, r.GrowthRate.data, r.lat.data, r.lon.data)
			cursor.execute('''INSERT INTO populations VALUES (%s, %s, %s, %s, %s, %s, %s, %s)''', vals)
		
	except(psycopg2.DatabaseError) as error:
		print(error)
	# close communication with the PostgreSQL database server
	cursor.close()
	# commit the changes
	conn.commit()

# Insert plants table, update if present
# plants is a plantsform object
def savePlants(plants, username, project_name):
	# wipe existing data
	try:
		cursor = conn.cursor()
		cursor.execute('''DELETE FROM plants WHERE username = %s AND project_name = %s''', [username, project_name])
	except(psycopg2.DatabaseError) as error:
		print(error)

	# insert data
	try:
		cursor = conn.cursor()

		index = 0
		for r in plants.rows:
			index = index + 1
			vals = (username, project_name, index, r.LocationName.data, r.lat.data, r.lon.data, r.existing_location.data, r.existing_tech.data)
			cursor.execute('''INSERT INTO plants VALUES (%s, %s, %s, %s, %s, %s, %s, %s)''', vals)
	except(psycopg2.DatabaseError) as error:
		print(error)
	# close communication with the PostgreSQL database server
	cursor.close()
	# commit the changes
	conn.commit()

# Retrieve the plants for a given user and projectID
# 	Returns an list of dictionaries with the column names
def getPlants(username, project_name):
	try:
		cursor = conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

		vals = (username, project_name)

		cursor.execute("SELECT * FROM plants WHERE username = %s AND project_name = %s", vals)
		vals = cursor.fetchall() # Get the result

	except(psycopg2.DatabaseError) as error:
		print(error)
	# close communication with the PostgreSQL database server
	cursor.close()
	return vals


# Retrieve the tech for a given user and projectID
# 	Returns an list of dictionaries with the column names
def getTechnologies(username, project_name):
	try:
		cursor = conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

		vals = (username, project_name)

		cursor.execute("SELECT * FROM technologies WHERE username = %s AND project_name = %s", vals)
		vals = cursor.fetchall() # Get the result

	except(psycopg2.DatabaseError) as error:
		print(error)
	# close communication with the PostgreSQL database server
	cursor.close()
	return vals

def getSelectedTechnologies(username, project_name):
	""" Get technologies that were selected by user after submitting tech form """
	techs_db = getTechnologies(username, project_name)
	output = [('1', 'N/A')] # initialize output set
	for r in techs_db:
		techs_found = [o[1] for o in output]
		if r['technologyname'] not in techs_found:
			# append this new tech to output
			output.append((str(len(output)+1), r['technologyname']))
	return(output)

# Insert technologies table, update if present
# Technologies is a technologiesform object
def saveTechnologies(tech, username, project_name):
	# wipe existing data
	try:
		cursor = conn.cursor()
		cursor.execute('''DELETE FROM technologies WHERE username = %s AND project_name = %s''', [username, project_name])
	except(psycopg2.DatabaseError) as error:
		print(error)

	# insert data
	try:
		cursor = conn.cursor()

		index = 0
		for r in tech.rows:
			# insert small scale
			index = index + 1
			vals = (username, project_name, index, r.default_tech.data, r.Technology.data, 'Small',
					r.Small.Capkt.data, r.Small.CCkt.data, r.Small.OCt.data, r.Small.SRWt.data, r.Small.GPt.data)
			cursor.execute('''INSERT INTO technologies VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''', vals)
			# insert medium scale
			index = index + 1
			vals = (username, project_name, index, r.default_tech.data, r.Technology.data, 'Medium',
					r.Medium.Capkt.data, r.Medium.CCkt.data, r.Medium.OCt.data, r.Medium.SRWt.data, r.Medium.GPt.data)
			cursor.execute('''INSERT INTO technologies VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''', vals)
			# insert large scale
			index = index + 1
			vals = (username, project_name, index, r.default_tech.data, r.Technology.data, 'Large',
					r.Large.Capkt.data, r.Large.CCkt.data, r.Large.OCt.data, r.Large.SRWt.data, r.Large.GPt.data)
			cursor.execute('''INSERT INTO technologies VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''', vals)
	except(psycopg2.DatabaseError) as error:
		print(error)
	# close communication with the PostgreSQL database server
	cursor.close()
	# commit the changes
	conn.commit()

# Insert params table, update if present
# params is a paramsform object
def saveParams(params, username, project_name):
	# insert data
	try:
		cursor = conn.cursor()

		index = 0
		for r in params.rows:
			index = index + 1
			vals = (username, project_name, index, r.Label.data, r.Unit.data, r.Value.data)
			cursor.execute('''INSERT INTO params VALUES (%s, %s, %s, %s, %s, %s)
				ON CONFLICT (username, project_name, index) DO
				UPDATE SET label=EXCLUDED.label, unit=EXCLUDED.unit, value=EXCLUDED.value''', vals)
	except(psycopg2.DatabaseError) as error:
		print(error)
	# close communication with the PostgreSQL database server
	cursor.close()
	# commit the changes
	conn.commit()

# Retrieve the params for a given user and projectID
# 	Returns an list of dictionaries with the column names
def getParams(username, project_name):
	try:
		cursor = conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

		vals = (username, project_name)

		cursor.execute("SELECT * FROM params WHERE username = %s AND project_name = %s", vals)
		vals = cursor.fetchall() # Get the result

	except(psycopg2.DatabaseError) as error:
		print(error)
	# close communication with the PostgreSQL database server
	cursor.close()
	return vals

# Inserts an Inputsize for a given user and projectID, update records if data exists
def registerUser(fullname, username, password, email):
	# insert records
	try:
		cursor = conn.cursor()

		vals = (username, password, fullname, email) #TODO: Add hashing
		cursor.execute('''INSERT INTO users VALUES (%s, %s, %s, %s)''', vals)
		
	except(psycopg2.DatabaseError) as error:
		print(error)
		return False
	# close communication with the PostgreSQL database server
	cursor.close()
	# commit the changes
	conn.commit()
	return True


init_db()

