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
<<<<<<< HEAD
	table_names = ['users', 'projects', 'users_has_projects', 'ns', 'populations', 'plants', 'technologies', 'parameters']
=======
	table_names = ['users', 'projects', 'ns', 'populations', 'plants', 'technologies', 'params']
>>>>>>> 27d8ebb2a16cb262470647fc8c5ef5fea02b3ee4
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
				CREATE TABLE users(
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
							project_id VARCHAR(25) NOT NULL,
  							project_name VARCHAR(255) NULL,
  							project_desc VARCHAR(255) NULL,		
						)
			""")
		elif table_name == 'users_has_projects':
			cursor.execute("""
						CREATE TABLE Projects(
						username VARCHAR(255) NOT NULL,
  						project_id VARCHAR(25) NOT NULL,
  						PRIMARY KEY (username, project_id),
  						-- constraint statement allows developer to rename the auto generated foreign key for communication purpose
  						-- However, more importantly, using constraint statement also allows to refer to the PK including two columns 
						  CONSTRAINT fk_tab_users
						    FOREIGN KEY (username)
						    REFERENCES users (username)
						    ON DELETE NO ACTION
						    ON UPDATE NO ACTION,
						  CONSTRAINT fk_tab_projects
						    FOREIGN KEY (project_id)
						    REFERENCES projects(project_id)
						    ON DELETE NO ACTION
						    ON UPDATE NO ACTION);	
						)
			""")
		elif table_name == 'ns':
			cursor.execute("""
						CREATE TABLE Ns(
							nsid SERIAL NOT NULL,
							NPop INT NULL,
							NPlant INT NULL,
							LifeSpan INT NULL,
							username VARCHAR(255) NOT NULL,
							project_id VARCHAR(25) NOT NULL,
							PRIMARY KEY (nsid, username, project_id),
							 -- INDEX fk_ns_users_has_projects1_idx (username, project_id) ,
							CONSTRAINT fk_ns_users_has_projects1
							    FOREIGN KEY (username , project_id)
							    REFERENCES users_has_projects (username , project_id)
							    ON DELETE NO ACTION
							    ON UPDATE NO ACTION)
			""")
		elif table_name == 'populations':
			cursor.execute("""
								CREATE TABLE Populations(
									popid SERIAL NOT NULL,
									mindex INT NULL,
									mname VARCHAR(255) NULL,
									Pr INT NULL,
									GrowthRate FLOAT NULL,
									lat FLOAT NULL,
									lon FLOAT NULL,
									username VARCHAR(255) NOT NULL,
									project_id VARCHAR(25) NOT NULL,
									PRIMARY KEY (popid, username, project_id),
									--  INDEX fk_populations_users_has_projects1_idx (username, project_id) ,
									CONSTRAINT fk_populations_users_has_projects1
									    FOREIGN KEY (username , project_id)
									    REFERENCES users_has_projects (username , project_id)
									    ON DELETE NO ACTION
									    ON UPDATE NO ACTION)
			""")
		elif table_name == 'plants':
			cursor.execute("""
								CREATE TABLE Plants(
									planid SERIAL NOT NULL,
  									mindex INT NULL,
  									LocationName VARCHAR(255) NULL,
  									lat FLOAT NULL,
  									lon FLOAT NULL,
  									username VARCHAR(255) NOT NULL,
  									project_id VARCHAR(25) NOT NULL,
  									PRIMARY KEY (planid, username, project_id),
									--  INDEX fk_plants_users_has_projects1_idx (username, project_id) ,
									CONSTRAINT fk_plants_users_has_projects1
									    FOREIGN KEY (username , project_id)
									    REFERENCES users_has_projects (username , project_id)
									    ON DELETE NO ACTION
									    ON UPDATE NO ACTION)
					""")
		elif table_name == 'technologies':
			cursor.execute("""
								CREATE TABLE Technologies(
									techid SERIAL NOT NULL,
								  mindex INT NULL,
								  mtype VARCHAR(255) NULL,
								  TechnologyName VARCHAR(255) NULL,
								  Scale VARCHAR(255) NULL,
								  Capkt FLOAT NULL,
								  Cckt FLOAT NULL,
								  mOct FLOAT NULL,
								  SRWt FLOAT NULL,
								  Gpt FLOAT NULL,
								  username VARCHAR(255) NOT NULL,
								  project_id VARCHAR(25) NOT NULL,
								  PRIMARY KEY (techid, username, project_id),
								--  INDEX fk_technologies_users_has_projects1_idx (username, project_id) ,
								  CONSTRAINT fk_technologies_users_has_projects1
								    FOREIGN KEY (username , project_id)
								    REFERENCES users_has_projects (username , project_id)
								    ON DELETE NO ACTION
								    ON UPDATE NO ACTION)
							""")
		elif table_name == 'params':
			cursor.execute("""
								CREATE TABLE Params(
									paramid SERIAL NOT NULL,
									mIndex INT NULL,
									Label VARCHAR(255) NULL,
									Unit VARCHAR(255) NULL,
									mValue FLOAT NULL,
									username VARCHAR(255) NOT NULL,
									project_id VARCHAR(25) NOT NULL,
									PRIMARY KEY (paramid, username, project_id),
									 -- INDEX fk_Params_users_has_projects1_idx (username, project_id) ,
									CONSTRAINT fk_Params_users_has_projects1
									FOREIGN KEY (username , project_id)
									REFERENCES users_has_projects (username , project_id)
									    ON DELETE NO ACTION
									    ON UPDATE NO ACTION)
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
	# insert data
	try:
		cursor = conn.cursor()

		index = 0
		for r in populations.rows:
			index = index + 1
			vals = (username, project_name, index, r.Name.data, r.Pr.data, r.GrowthRate.data, r.lat.data, r.lon.data)
			cursor.execute('''INSERT INTO populations VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
				ON CONFLICT (username, project_name, index) DO
				UPDATE SET name=EXCLUDED.name, pr=EXCLUDED.pr, growthrate=EXCLUDED.growthrate, 
				lat=EXCLUDED.lat, lon=EXCLUDED.lon''', vals)
		
	except(psycopg2.DatabaseError) as error:
		print(error)
	# close communication with the PostgreSQL database server
	cursor.close()
	# commit the changes
	conn.commit()

# Insert plants table, update if present
# plants is a plantsform object
def savePlants(plants, username, project_name):
	# insert data
	try:
		cursor = conn.cursor()

		index = 0
		for r in plants.rows:
			index = index + 1
			vals = (username, project_name, index, r.LocationName.data, r.lat.data, r.lon.data)
			cursor.execute('''INSERT INTO plants VALUES (%s, %s, %s, %s, %s, %s)
				ON CONFLICT (username, project_name, index) DO
				UPDATE SET locationname=EXCLUDED.locationname, lat=EXCLUDED.lat, lon=EXCLUDED.lon''', vals)
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

# Insert technologies table, update if present
# Technologies is a technologiesform object
def saveTechnologies(tech, username, project_name):
	# insert data
	try:
		cursor = conn.cursor()

		index = 0
		# for r in tech.rows:
			# index = index + 1
			# vals = (username, project_name, index, r.type.data, r.TechnologyName.data, r.lon.data)
			# cursor.execute('''INSERT INTO technologies VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
				# ON CONFLICT (username, project_name, index) DO
				# UPDATE SET locationname=EXCLUDED.locationname, lat=EXCLUDED.lat, lon=EXCLUDED.lon''', vals)
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

