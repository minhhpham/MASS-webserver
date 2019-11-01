from flask_login import LoginManager, login_user, login_required

# User model
class User():
	def __init__(self, username):
		self.username = username
		self.authenticated = False

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

login_manager = LoginManager()
login_manager.login_view = 'login' # points to login webpage

@login_manager.user_loader
def user_loader(username):
	return(User(username))