import psycopg2

global config    # initialized in MASS-webserver.py
conn = psycopg2.connect(dbname = config.db.dbname, user = config.db.user, password = config.db.password, port = config.db.port)

def init_db():
	""" initialize tables if not found in the database """
	cursor = conn.cursor()
	table_names = ['Users', 'Projects', 'Ns', 'Populations', 'Plants', 'Technologies', 'Parameters']
	for table_name in table_names:
		cursor.execute("""
			SELECT count(*) FROM information_schema.tables WHERE table_name='{}'
		""".format(table_name = table_name))
		if cursor.rowcount == 0:
			init_table(table_name)

def init_table(table_name):
	cursor = conn.cursor()
	if table_name == 'Users':
		cursor.execute("""
			CREATE TABLE Users(
				username		varchar(255)
				password_hashed	varchar(1024)	-- big space in case we need cryptography later
				full_name		varchar(255)
				email			varchar(255)
			)
		""")

def register_user(username, password_hased):
	return

def authenticate_user(username, password_hashed):
	return


init_db()