import os, sys, getpass, shutil

CWD = os.getcwd()
PythonPath = sys.executable
User = getpass.getuser()

# create service file
if os.path.exists("./MASS-flask.service"):
	os.remove("./MASS-flask.service")

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

# copy file to /etc/systemd/system
shutil.copyfile("./MASS-flask.service", "/etc/systemd/system/MASS-flask.service")