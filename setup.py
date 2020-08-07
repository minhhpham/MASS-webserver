import os, sys, getpass, shutil
from server_scripts import database as db

# initiate database tables
db.init_db()

CWD = os.getcwd()
PythonPath = sys.executable
User = os.getlogin()

# create service files
if os.path.exists("./MASS-flask.service"):
	os.remove("./MASS-flask.service")
if os.path.exists("./MASS-optimizer-scheduler.service"):
	os.remove("./MASS-optimizer-scheduler.service")

with open("./MASS-flask.service", 'x') as file:
	file.write("[Unit]\n")
	file.write("Description=Wastewater management web app\n")
	file.write("After=network.target\n\n")
	file.write("[Service]\n")
	file.write("User={}\n".format(User))
	file.write("WorkingDirectory={}\n".format(CWD))
	file.write("ExecStart={0} {1}/MASS-webserver.py\n".format(PythonPath, CWD))
	file.write("Restart=Always\n\n")
	file.write("[Install]\n")
	file.write("WantedBy=multi-user.target\n")

with open("./MASS-optimizer-scheduler.service", 'x') as file:
	file.write("[Unit]\n")
	file.write("Description=MASS optimizer scheduling service\n")
	file.write("After=MASS-flask.service\n\n")
	file.write("[Service]\n")
	file.write("User={}\n".format(User))
	file.write("WorkingDirectory={}\n".format(CWD))
	file.write("ExecStart={0} {1}/optimizer_scheduler.py\n".format(PythonPath, CWD))
	file.write("Restart=Always\n\n")
	file.write("[Install]\n")
	file.write("WantedBy=multi-user.target\n")


# copy file to /etc/systemd/system
shutil.copyfile("./MASS-flask.service", "/etc/systemd/system/MASS-flask.service")
shutil.copyfile("./MASS-optimizer-scheduler.service", "/etc/systemd/system/MASS-optimizer-scheduler.service")

# copy apache conf file to /etc/apache2/sites-available
shutil.copyfile("./WasteWATER.apache2.conf", "/etc/apache2/sites-available/000-default.conf")