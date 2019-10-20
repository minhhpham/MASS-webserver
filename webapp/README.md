# Install requirements
 * Install Python (either version 2 or 3.6+) and python-pip.
 * Clone/Download this repository: `git clone https://github.com/minhhpham/MASS-webserver/webapp`
 * `cd MASS-webserver/webapp`
 * Use `pip` or `pip3` depending on your version: `pip install -r requirements.txt`
 * Use `python` or `python3` depending on version: `sudo python setup.py`

# Run
 * Run in Debug or Development mode: `python MASS-webserver.py`
 * Run as service (deployment mode): `sudo systemctl daemon-reload` then `sudo systemctl start MASS-flask`

# Use the web app:
Go to your browser and type `localhost:10000`