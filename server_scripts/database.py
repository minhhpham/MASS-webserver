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
	table_names = ['Users', 'Projects', 'Ns', 'Populations', 'Plants', 'Technologies', 'Parameters']
	for table_name in table_names:
		cursor.execute("""
			SELECT COUNT(*) FROM information_schema.tables WHERE table_name=%s
		""", (table_name,))
		if cursor.fetchone()[0] == 0:
			init_table(table_name)

	cursor.close()
	# commit the changes
	conn.commit()

def init_table(table_name):
	cursor = conn.cursor()
	try:
		if table_name == 'Users':
			cursor.execute("""
				CREATE TABLE Users(
					username		varchar(255),
					password_hashed	varchar(1024),	-- big space in case we need cryptography later
					full_name		varchar(255),
					email			varchar(255),
					PRIMARY KEY(username)
				)
			""")
		elif table_name == 'Projects':
			cursor.execute("""
						CREATE TABLE Projects(
							username	varchar(255),
							project_name varchar(255),	
							p_desc		varchar(255),
							PRIMARY KEY(username, project_name)		
						)
			""")
		elif table_name == 'Ns':
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
		elif table_name == 'Populations':
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
		elif table_name == 'Plants':
			cursor.execute("""
								CREATE TABLE Plants(
									username			varchar(255),
									project_name 		varchar(255),
									index 				int,	
									LocationName		varchar(255), -- represent Cluster name
									lat					float, -- represent Latitude
									lon					float, -- represent Longitude
									PRIMARY KEY(username, project_name, index)
								)
					""")
		elif table_name == 'Technologies':
			cursor.execute("""
								CREATE TABLE Technologies(
									username	varchar(255),
									project_name varchar(255),
									index 		int,	
									Capkt		float,
									CCkt		float, 
									OCt			float, 
									SRWt		float,
									GPt			float,
									PRIMARY KEY(username, project_name, index)
								)
							""")
		elif table_name == 'Params':
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
	except(Exception, psycopg2.DatabaseError) as error:
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
		cursor.execute("INSERT INTO Projects VALUES (%s, %s, %s)", vals)

	except(psycopg2.DatabaseError) as error:
		print(error)
	# close communication with the PostgreSQL database server
	cursor.close()
	# commit the changes
	conn.commit()

# Inserts an Inputsize for a given user and projectID, update records if data exists
def saveInputSize(inputSize, username, project_name):
	# first check if records exist in database
	existing_data = getInputSize(username, project_name)
	if existing_data is not None:
		# delete records if exists and then insert again
		try:
			cursor = conn.cursor()
			cursor.execute("DELETE FROM Ns WHERE username = %s AND project_name = %s", (username, project_name))
		except(psycopg2.DatabaseError) as error:
			print(error)

	# insert records
	try:
		cursor = conn.cursor()

		vals = (username, project_name, inputSize.NPlant.data, inputSize.NPop.data, inputSize.LifeSpan.data)
		cursor.execute("INSERT INTO Ns VALUES (%s, %s, %s, %s, %s)", vals)
		
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
	existing_data = getPopulations(username, project_name)
	if existing_data is not None:
	# delete existing record first, then insert
		try:
			cursor = conn.cursor()
			cursor.execute("DELETE FROM populations WHERE username = %s AND project_name = %s", (username, project_name))
		except(psycopg2.DatabaseError) as error:
			print(error)
	# insert data
	try:
		cursor = conn.cursor()

		index = 0
		for r in populations.rows:
			index = index + 1
			vals = (username, project_name, index, r.Name.data, r.Pr.data, r.GrowthRate.data, r.lat.data, r.lon.data)
			cursor.execute("INSERT INTO populations VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", vals)
		
	except(psycopg2.DatabaseError) as error:
		print(error)
	# close communication with the PostgreSQL database server
	cursor.close()
	# commit the changes
	conn.commit()



init_db()

