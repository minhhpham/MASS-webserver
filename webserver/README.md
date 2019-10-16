
First, install Python (either version 2 or 3.6+). If you are on Ubuntu, you can just run `sudo apt-get install python`. If you are on Windows, after installing python, make sure to add python.exe and pip.exe to your PATH to make the commands `python` and `pip` available in command line.

Clone/Download this repository and go to terminal/command line and cd into `MASS-webserver\webserver`

Next, rename file `sample_server_config.yaml` into `server_config.yaml` and configure if needed.

Next, run the following commands:

`pip install -r requirements.txt`

`python MASS-webserver.py`

Go to your browser and type `localhost:10000`