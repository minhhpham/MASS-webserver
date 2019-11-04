import psycopg2
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
			SELECT * FROM information_schema.tables WHERE table_name=%s
		""", (table_name,))
		if cursor.rowcount is None:
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
							PRIMARY KEY(username, project_name),
							FOREIGN KEY(username) REFERENCES Users			
						)
			""")
		elif table_name == 'Ns':
			cursor.execute("""
						CREATE TABLE Ns(
							username	varchar(255),
							pid			int,	
							n1		int,
							n2		int,
							n3		int,
							PRIMARY KEY(username, pid),
							FOREIGN KEY(username) REFERENCES Users
						)
			""")
		elif table_name == 'Populations':
			cursor.execute("""
								CREATE TABLE Populations(
									username	varchar(255),
									pid			int,
									index 		int,	
									pname		varchar(255), -- represent Cluster name
									psize		    int NOT NULL CHECK (psize >= 0), -- represent Current Population
									pgrowthrate	float, -- represent Population Growth Rate
									lat		    float, -- represent Latitude
									long	    float, -- represent Longitude
									PRIMARY KEY(username, pid, index)
								)
			""")
		elif table_name == 'Plants':
			cursor.execute("""
								CREATE TABLE Plants(
									username	varchar(255),
									pid			int,
									index 		int,	
									locname		varchar(255), -- represent Cluster name
									lat		float, -- represent Latitude
									long		float, -- represent Longitude
									PRIMARY KEY(username, pid, index)
								)
					""")
		elif table_name == 'Technologies':
			cursor.execute("""
								CREATE TABLE Technologies(
									username	varchar(255),
									pid			int,
									index 		int,	
									Capkt		float,
									CCkt		float, 
									OCt			float, 
									SRWt		float,
									GPt			float,
									PRIMARY KEY(username, pid, index)
								)
							""")
		elif table_name == 'Params':
			cursor.execute("""
								CREATE TABLE Params(
									username	varchar(255),
									pid			int,
									index 		int,	
									label		varchar(255), 
									unit		varchar(255), 
									value		float, 
									PRIMARY KEY(username, pid, index),
									FOREIGN KEY(username) REFERENCES Users,
									FOREIGN KEY(pid) REFERENCES Projects,
									FOREIGN KEY(index) REFERENCES Pops
								)
			""")
		else:
			pass
	except(Exception, psycopg2.DatabaseError) as error:
		print(error)

def register_user(username, password_hased):
	return

def authenticate_user(username, password_hashed):
	return

# Returns a list of projects
def getProjects(username):
	try:
		cursor = conn.cursor()

		# Select projects
		cursor.execute("SELECT project_name, p_desc FROM Projects WHERE username = %s", (username,))
		vals = cur.fetchall() # Get the result

		# close communication with the PostgreSQL database server
		cursor.close()
		# commit the changes
		conn.commit()
	except(Exception, psycopg2.DatabaseError) as error:
		vals = []
		print(error)
	finally:
		if conn is not None:
			conn.close()
	return vals

# Creates a new project
def saveProject(username, project_name, p_desc):
	try:
		cursor = conn.cursor()

		vals = (username, project_name, p_desc)
		cursor.execute("INSERT INTO Projects VALUES (%s, %s, %s)", vals)
		# close communication with the PostgreSQL database server
		cursor.close()
		# commit the changes
		conn.commit()
	except(Exception, psycopg2.DatabaseError) as error:
		print(error)
	finally:
		if conn is not None:
			conn.close()

# Inserts an Inputsize for a given user and projectID
def saveInputSize(inputSize, username, projectID):
	try:
		cursor = conn.cursor()

		vals = (username, projectID, inputSize.NPlant.data, inputSize.NPop.data, inputSize.LifeSpan.data)
		cursor.execute("INSERT INTO Ns VALUES (%s, %d, %d, %d, %d)", vals)
		# close communication with the PostgreSQL database server
		cursor.close()
		# commit the changes
		conn.commit()
	except(Exception, psycopg2.DatabaseError) as error:
		print(error)
	finally:
		if conn is not None:
			conn.close()

# Updates an Inputsize for a given user and projectID
def saveInputSize(inputSize, username, projectID):
	try:
		cursor = conn.cursor()

		vals = (inputSize.NPlant.data, inputSize.NPop.data, inputSize.LifeSpan.data, username, projectID)
		cursor.execute("UPDATE Ns SET n1=%d, n2=%d, n3=%d WHERE username=%s AND pid=%d", vals)
		# close communication with the PostgreSQL database server
		cursor.close()
		# commit the changes
		conn.commit()
	except(Exception, psycopg2.DatabaseError) as error:
		print(error)
	finally:
		if conn is not None:
			conn.close()

# Retrieve an Inputsize for a given user and projectID
# 	Returns an InputSize object
def getInputSize(username, projectID):
	try:
		cursor = conn.cursor()

		vals = (username, projectID)

		# Selec
		cursor.execute("SELECT n1, n2, n3 FROM Ns WHERE username = %s AND pid = %d", vals)
		vals = cur.fetchone() # Get the result

		# Create the new object
		newInputSize = {}
		newInputSize["numplants"] = vals[0]
		newInputSize["numpops"] = vals[1]
		newInputSize["durations"] = vals[2]

		# close communication with the PostgreSQL database server
		cursor.close()
		# commit the changes
		conn.commit()
	except(Exception, psycopg2.DatabaseError) as error:
		newInputSize = {}
		print(error)
	finally:
		if conn is not None:
			conn.close()
	return newInputSizes

init_db()

