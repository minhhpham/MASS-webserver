from flask_login import LoginManager, login_user, login_required, current_user, logout_user
from flask import session

# User model
class User():
	def __init__(self, username):
		self.username = username
		self.authenticated = False
		self.current_project_name = None

	def is_active(self):
		# all users are active
		return(True)

	def get_id(self):
		return(self.username)

	def is_authenticated(self):
		# default is False
		return(self.authenticated)

	def is_anonymous(self):
		# not using this
		return(False)

	def authenticate(self, password):
		# TODO: create authentication process when database is ready
		self.authenticated = True

	def set_project(self, project_name):
		# set current project user is working on
		session["project_name"] = project_name
		self.current_project_name = project_name

	def get_project(self):
		# get current project user is working on
		return(self.current_project_name)

login_manager = LoginManager()
login_manager.login_view = 'login' # points to login webpage

@login_manager.user_loader
def user_loader(username):
	user = User(username)
	try:
		user.set_project(session["project_name"])
	except:
		# Not set yet
		pass
	return(user)