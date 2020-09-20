import os, sys, getpass, shutil, yaml

global config
with open("server_config.yaml", 'r') as stream:
    try:
        config = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        print(exc)
        sys.exit()

CWD = os.getcwd()
PythonPath = sys.executable
User = os.getlogin()

print('setting up Flask service ...')
# create service files
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

# start service
os.system('sudo systemctl daemon-reload')
os.system('sudo systemctl start MASS-flask')


print('setting up optimizer_scheduler service ...')
n_worker = config['optimizer_n_process']
for i in range(1, n_worker+1):
	# create service file
	if os.path.exists("./MASS-optimizer-scheduler@"+str(i)+".service"):
		os.remove("./MASS-optimizer-scheduler@"+str(i)+".service")

	with open("./MASS-optimizer-scheduler@"+str(i)+".service", 'x') as file:
		file.write("[Unit]\n")
		file.write("Description=MASS optimizer scheduling service\n")
		file.write("After=MASS-flask.service\n\n")
		file.write("[Service]\n")
		file.write("User={}\n".format(User))
		file.write('Environment="SCIPOPTDIR=/home/mass/Documents/scipoptsuite-5.0.1/local/usr/local"\n')
		file.write('Environment="PATH=/home/mass/Documents/julia-1.1.0/:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/snap/bin"\n')
		file.write('Environment="JULIA_NUM_THREADS=8"\n')
		file.write("WorkingDirectory={}\n".format(CWD))
		file.write("ExecStart={0} {1}/optimizer_scheduler.py {2}\n".format(PythonPath, CWD, i))
		file.write("Restart=always\n\n")
		file.write("[Install]\n")
		file.write("WantedBy=multi-user.target\n")

	# copy file to /etc/systemd/system
	shutil.copyfile("./MASS-optimizer-scheduler@"+str(i)+".service", "/etc/systemd/system/MASS-optimizer-scheduler@"+str(i)+".service")

	# start service
	os.system('sudo systemctl daemon-reload')
	os.system("sudo systemctl start MASS-optimizer-scheduler@"+str(i)+".service")

print('setting up apache2 service ...')
# copy apache conf file to /etc/apache2/sites-available
shutil.copyfile("./WasteWATER.apache2.conf", "/etc/apache2/sites-available/000-default.conf")
os.system('sudo systemctl daemon-reload')
os.system('sudo a2enmod proxy_http')
os.system('sudo systemctl restart apache2')
