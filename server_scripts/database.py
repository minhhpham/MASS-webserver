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
	table_names = ['users', 'projects', 'users_has_projects', 'ns', 'populations', 'plants', 'technologies', 'params']
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
				CREATE TABLE IF NOT EXISTS users (
				username VARCHAR(255) NOT NULL,
				password_hashed VARCHAR(255) NULL,
				full_name VARCHAR(255) NULL,
				email VARCHAR(255) NULL,
				PRIMARY KEY (username))
			""")
		elif table_name == 'projects':
			cursor.execute("""
				CREATE TABLE IF NOT EXISTS projects (
				project_id SERIAL,
				project_name VARCHAR(255) NULL,
				project_desc TEXT NULL,
				PRIMARY KEY (project_id))
			""")
		elif table_name == 'ns':
			cursor.execute("""
				CREATE TABLE IF NOT EXISTS ns (
				nsid SERIAL,
				NPop INT NULL,
				NPlant INT NULL,
				LifeSpan INT NULL,
				project_id INT NOT NULL,
				PRIMARY KEY (nsid, project_id),
				CONSTRAINT fk_ns_projects1
					FOREIGN KEY (project_id)
					REFERENCES projects (project_id)
					ON DELETE NO ACTION
					ON UPDATE NO ACTION)
			""")
		elif table_name == 'users_has_projects':
			cursor.execute("""
				CREATE TABLE IF NOT EXISTS users_has_projects (
				username VARCHAR(255) NOT NULL,
				project_id INT  NOT NULL,
				PRIMARY KEY (username, project_id),
				CONSTRAINT fk_users_has_projects_users1
					FOREIGN KEY (username)
					REFERENCES users (username)
					ON DELETE NO ACTION
					ON UPDATE NO ACTION,
				CONSTRAINT fk_users_has_projects_projects1
					FOREIGN KEY (project_id)
					REFERENCES projects (project_id)
					ON DELETE NO ACTION
					ON UPDATE NO ACTION)
			""")
		elif table_name == 'populations':
			cursor.execute("""
				CREATE TABLE IF NOT EXISTS populations (
				popid SERIAL,
				index INT NULL,
				Name VARCHAR(255) NULL,
				Pr INT NULL,
				GrowthRate FLOAT NULL,
				lat FLOAT NULL,
				long FLOAT NULL,
				project_id INT  NOT NULL,
				PRIMARY KEY (popid, project_id),
				CONSTRAINT fk_populations_projects1
					FOREIGN KEY (project_id)
					REFERENCES projects (project_id)
					ON DELETE NO ACTION
					ON UPDATE NO ACTION)
			""")
		elif table_name == 'plants':
			cursor.execute("""
				CREATE TABLE IF NOT EXISTS plants (
				plantid SERIAL,
				index INT NULL,
				LocationName VARCHAR(255) NULL,
				lat FLOAT NULL,
				lon FLOAT NULL,
				existing_location BOOLEAN NULL,
  				existing_tech TEXT NULL,
				project_id INT  NOT NULL,
				PRIMARY KEY (plantid, project_id),
				CONSTRAINT fk_plants_projects1
					FOREIGN KEY (project_id)
					REFERENCES projects (project_id)
					ON DELETE NO ACTION
					ON UPDATE NO ACTION)
			""")
		elif table_name == 'technologies':
			cursor.execute("""
				CREATE TABLE IF NOT EXISTS technologies (
				techid SERIAL,
				index INT NULL,
				type VARCHAR(255) NULL,
				TechnologyName VARCHAR(255) NULL,
				Scale VARCHAR(255) NULL,
				Capkt FLOAT NULL,
				Cckt FLOAT NULL,
				Oct FLOAT NULL,
				SRWt FLOAT NULL,
				Gpt FLOAT NULL,
				project_id INT  NOT NULL,
				PRIMARY KEY (techid, project_id),
				CONSTRAINT fk_technologies_projects1
					FOREIGN KEY (project_id)
					REFERENCES projects (project_id)
					ON DELETE NO ACTION
					ON UPDATE NO ACTION)
			""")
		elif table_name == 'params':
			cursor.execute("""
				CREATE TABLE IF NOT EXISTS params (
				paramid SERIAL,
				index INT NULL,
				Label VARCHAR(255) NULL,
				Unit VARCHAR(255) NULL,
				Value FLOAT NULL,
				project_id INT  NOT NULL,
				PRIMARY KEY (paramid, project_id),
				CONSTRAINT fk_Params_projects1
					FOREIGN KEY (project_id)
					REFERENCES projects (project_id)
					ON DELETE NO ACTION
					ON UPDATE NO ACTION)
			""")
		else:
			pass
	except(psycopg2.DatabaseError) as error:
		print(error)
		conn.commit()

# Returns a list of projects
def getProjects(username):
	vals = {}
	try:
		cursor = conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

		# Select projects
		cursor.execute("""SELECT p.* 
						FROM Projects p 
						JOIN users_has_projects up ON up.project_id=p.project_id 
						WHERE username = %s""", (username,))
		vals = cursor.fetchall() # Get the result

	except(psycopg2.DatabaseError) as error:
		print(error)
	# close communication with the PostgreSQL database server
	cursor.close()
	# commit the changes
	conn.commit()
	return vals

# Creates a new project
def saveProject(project_name, p_desc):
	id = -1
	try:
		cursor = conn.cursor()

		vals = (project_name, p_desc)
		cursor.execute('''INSERT INTO Projects (project_name, project_desc) VALUES (%s, %s)''', vals)
		
		cursor.execute('''select currval(pg_get_serial_sequence('projects', 'project_id'));''')
		id = cursor.fetchone()[0]
	except(psycopg2.DatabaseError) as error:
		print(error)
	# close communication with the PostgreSQL database server
	cursor.close()
	# commit the changes
	conn.commit()
	return id

#Adds a user to a project
def addUserToProject(username, p_id):
	try:
		cursor = conn.cursor()

		vals = (username, p_id)
		cursor.execute('''INSERT INTO users_has_projects (username, project_id) VALUES (%s, %s)
			ON CONFLICT DO NOTHING''', vals)
	except(psycopg2.DatabaseError) as error:
		print(error)
	# close communication with the PostgreSQL database server
	cursor.close()
	# commit the changes
	conn.commit()

# Inserts an Inputsize for a given user and projectID, update records if data exists
def saveInputSize(inputSize, project_id):
	# insert records
	try:
		cursor = conn.cursor()
		# Remove existing values and insert new ones
		cursor.execute('''DELETE FROM Ns WHERE project_id=%s''', (project_id))
		vals = (project_id, inputSize.NPlant.data, inputSize.NPop.data, inputSize.LifeSpan.data)
		cursor.execute('''INSERT INTO Ns (project_id, NPlant, NPop, LifeSpan) VALUES (%s, %s, %s, %s)''', vals)
	except(psycopg2.DatabaseError) as error:
		print(error)
	# close communication with the PostgreSQL database server
	cursor.close()
	# commit the changes
	conn.commit()

# Retrieve an Inputsize for a given user and projectID
# 	Returns an InputSize object
def getInputSize(project_id):
	newInputSize = {}
	try:
		cursor = conn.cursor()

		vals = (project_id)

		cursor.execute("""SELECT NPop, NPlant, LifeSpan FROM Ns n JOIN users_has_projects p ON n.project_id=p.project_id WHERE p.project_id = %s""", vals)
		vals = cursor.fetchone() # Get the result

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
	# commit the changes
	conn.commit()
	return newInputSize

# Retrieve a population for a given user and projectID
# 	Returns an list of dictionaries with the column names
def getPopulations(project_id):
	try:
		cursor = conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

		vals = (project_id,)

		cursor.execute("SELECT * FROM populations WHERE project_id = %s", vals)
		vals = cursor.fetchall() # Get the result

	except(psycopg2.DatabaseError) as error:
		print(error)
	# close communication with the PostgreSQL database server
	cursor.close()
	# commit the changes
	conn.commit()
	return vals

# Inserts populations table for a given user and projectID
# update records if exists
# otherwise insert
# populations has class PopulationsForm
def savePopulations(populations, project_id):
	# insert data
	try:
		cursor = conn.cursor()

		cursor.execute("DELETE FROM populations WHERE project_id=%s", (project_id,))
		index = 0
		for r in populations.rows:
			index = index + 1
			vals = (project_id, index, r.Name.data, r.Pr.data, r.GrowthRate.data, r.lat.data, r.lon.data)
			cursor.execute('''INSERT INTO populations (project_id, index, Name, Pr, GrowthRate, lat, long) 
				VALUES (%s, %s, %s, %s, %s, %s, %s)''', vals)
		
	except(psycopg2.DatabaseError) as error:
		print(error)
	# close communication with the PostgreSQL database server
	cursor.close()
	# commit the changes
	conn.commit()

# Insert plants table, update if present
# plants is a plantsform object
def savePlants(plants, project_id):
	# insert data
	try:
		cursor = conn.cursor()
		cursor.execute("DELETE FROM plants WHERE project_id=%s", (project_id),)

		index = 0
		for r in plants.rows:
			index = index + 1
			vals = (project_id, index, r.LocationName.data, r.lat.data, r.lon.data, r.existing_location.data, r.existing_tech.data)
			cursor.execute('''INSERT INTO plants (project_id, index, LocationName, lat, lon, existing_location, existing_tech) 
				VALUES ( %s, %s, %s, %s, %s, %s, %s)''', vals)
	except(psycopg2.DatabaseError) as error:
		print(error)
	# close communication with the PostgreSQL database server
	cursor.close()
	# commit the changes
	conn.commit()

# Retrieve the plants for a given user and projectID
# 	Returns an list of dictionaries with the column names
def getPlants(project_id):
	try:
		cursor = conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

		vals = (project_id,)

		cursor.execute("SELECT * FROM plants WHERE project_id = %s", vals)
		vals = cursor.fetchall() # Get the result

	except(psycopg2.DatabaseError) as error:
		print(error)
	# close communication with the PostgreSQL database server
	cursor.close()
	return vals


# Retrieve the tech for a given user and projectID
# 	Returns an list of dictionaries with the column names
def getTechnologies(project_id):
	try:
		cursor = conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

		vals = (project_id,)

		cursor.execute("SELECT * FROM technologies WHERE project_id = %s", vals)
		vals = cursor.fetchall() # Get the result

	except(psycopg2.DatabaseError) as error:
		print(error)
	# close communication with the PostgreSQL database server
	cursor.close()
	return vals

def getSelectedTechnologies(project_id):
	""" Get technologies that were selected by user after submitting tech form """
	techs_db = getTechnologies(project_id)
	output = [('1', 'N/A')] # initialize output set
	for r in techs_db:
		print(r)
		techs_found = [o[1] for o in output]
		if r['technologyname'] not in techs_found:
			# append this new tech to output
			output.append((str(len(output)+1), r['technologyname']))
	return(output)

# Insert technologies table, update if present
# Technologies is a technologiesform object
def saveTechnologies(tech, project_id):
	# insert data
	try:
		cursor = conn.cursor()
		# Clear any existing data
		cursor.execute('''DELETE FROM technologies WHERE project_id = %s''', (project_id,))

		index = 0
		for r in tech.rows:
			# insert small scale
			index = index + 1
			vals = (project_id, index, r.default_tech.data, r.Technology.data.data, 'Small',
					r.Small.Capkt.data.data, r.Small.CCkt.data.data, r.Small.OCt.data.data, r.Small.SRWt.data.data, r.Small.GPt.data.data)
			cursor.execute('''INSERT INTO technologies 
				(project_id, index, type, TechnologyName, Scale, Capkt, Cckt, Oct, SRWt, Gpt)
				VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''', vals)
			# insert medium scale
			index = index + 1
			vals = (project_id, index, r.default_tech.data, r.Technology.data.data, 'Medium',
					r.Medium.Capkt.data.data, r.Medium.CCkt.data.data, r.Medium.OCt.data.data, r.Medium.SRWt.data.data, r.Medium.GPt.data.data)
			cursor.execute('''INSERT INTO technologies 
				(project_id, index, type, TechnologyName, Scale, Capkt, Cckt, Oct, SRWt, Gpt)
				VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''', vals)
			# insert large scale
			index = index + 1
			vals = (project_id, index, r.default_tech.data, r.Technology.data.data, 'Large',
					r.Large.Capkt.data.data, r.Large.CCkt.data.data, r.Large.OCt.data.data, r.Large.SRWt.data.data, r.Large.GPt.data.data)
			cursor.execute('''INSERT INTO technologies 
				(project_id, index, type, TechnologyName, Scale, Capkt, Cckt, Oct, SRWt, Gpt)
				VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''', vals)
	except(psycopg2.DatabaseError) as error:
		print(error)
	# close communication with the PostgreSQL database server
	cursor.close()
	# commit the changes
	conn.commit()

# Insert params table, update if present
# params is a paramsform object
def saveParams(params, project_id):
	# insert data
	try:
		cursor = conn.cursor()

		index = 0
		for r in params.rows:
			index = index + 1
			vals = (project_id, index, r.Label.data, r.Unit.data, r.Value.data)
			cursor.execute('''INSERT INTO params (project_id, index, Label, Unit, Value) 
				VALUES (%s, %s, %s, %s, %s)''', vals)
	except(psycopg2.DatabaseError) as error:
		print(error)
	# close communication with the PostgreSQL database server
	cursor.close()
	# commit the changes
	conn.commit()

# Retrieve the params for a given user and projectID
# 	Returns an list of dictionaries with the column names
def getParams(project_id):
	try:
		cursor = conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

		vals = (project_id,)

		cursor.execute("SELECT * FROM params WHERE project_id = %s", vals)
		vals = cursor.fetchall() # Get the result

	except(psycopg2.DatabaseError) as error:
		print(error)
	# close communication with the PostgreSQL database server
	cursor.close()
	# commit the changes
	conn.commit()
	return vals

# Registers a new user
def registerUser(fullname, username, password, email):
	# insert records
	try:
		cursor = conn.cursor()

		vals = (username, password, fullname, email)
		cursor.execute('''INSERT INTO users VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING''', vals)
		
	except(psycopg2.DatabaseError) as error:
		print(error)
		# close communication with the PostgreSQL database server
		cursor.close()
		# commit the changes
		conn.commit()
		return False
	# close communication with the PostgreSQL database server
	cursor.close()
	# commit the changes
	conn.commit()
	return True

#TODO:
def authenticateUser(username, password):
	# insert records
	try:
		cursor = conn.cursor()
		cursor.execute("""
			SELECT COUNT(*) FROM users WHERE username=%s AND password_hashed=%s
		""", (username,password))
		if cursor.fetchone()[0] == 1:
			return True
		else:
			return False
	except(psycopg2.DatabaseError) as error:
		print(error)
	# close communication with the PostgreSQL database server
	cursor.close()
	# commit the changes
	conn.commit()
	return False


init_db()

