from flask import Flask, request, redirect, render_template, session, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://blogz:password@localhost:8889/blogz'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)
app.secret_key = "d=-Tr@a:LBE.P9!v"

class Blog(db.Model):

	id = db.Column(db.Integer, primary_key=True)
	title = db.Column(db.String(127))
	body = db.Column(db.String(255))
	owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))

	def __init__(self, title, body, owner):
		self.title = title
		self.body = body
		self.owner = owner

class User(db.Model):

	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(120))
	password = db.Column(db.String(120))
	blogs = db.relationship('Blog', backref='owner')

	def __init__(self, username, password):
		self.username = username
		self.password = password

@app.before_request
def require_login():
	allowed_routes = ['index','login', 'signup', 'list_blogs']
	if request.endpoint not in allowed_routes and 'username' not in session:
		return redirect('/login')

@app.route('/', methods=['POST', 'GET'])
def index():
	users = User.query.all()
	return render_template("index.html", users=users)

@app.route('/login', methods=['POST', 'GET'])
def login():
	if request.method == 'POST':
		username = request.form['username']
		password = request.form['password']
		user = User.query.filter_by(username=username).first()

		username_error = ""
		password_error = ""

		if user and user.password == password:
			session['username'] = username
			return redirect('/newpost')
		else:
			if not user:
				username_error = "There is no account with that username"
			if user and user.password != password:
				password_error = "The password you entered is incorrect"
			return render_template("login.html", 
				username=username,
				username_error=username_error,
				password_error=password_error)
			
	return render_template("login.html")

@app.route('/signup', methods=['POST', 'GET'])
def signup():
	if request.method == 'POST':
		username = request.form['username']
		password = request.form['password']
		verify = request.form['verify']

		username_error = ""
		password_error = ""
		verify_error = ""

		existing_user = User.query.filter_by(username=username).first()
		if len(username) > 2 and not existing_user and len(password) > 2 and password == verify:
			new_user = User(username, password)
			db.session.add(new_user)
			db.session.commit()
			session['username'] = username
			return redirect('/newpost')
		else:
			if existing_user:
				username_error = "That username is already taken"
			elif len(username) < 3:
				if username == "":
					username_error = "You must enter a username"
				else:
					username_error = "Username must be at least 3 characters"
			if len(password) < 3:
				if password == "":
					password_error = "You must enter a password"
				else:
					password_error = "Password must be at least 3 characters"
			if verify == "":
				verify_error = "You must verify your password"
			elif password != verify:
				verify_error = "Passwords do not match"

			return render_template("signup.html",
				username=username,
				username_error=username_error,
				password_error=password_error,
				verify_error=verify_error)
	else:
		return render_template("signup.html")

@app.route('/logout')
def logout():
	del session['username']
	return redirect('/blog')


@app.route('/blog', methods=['POST', 'GET'])
def list_blogs():
	blogs = Blog.query.all()
	
	if request.args.get('id'):
		id = request.args.get('id')
		title = Blog.query.filter_by(id=id).first().title
		body= Blog.query.filter_by(id=id).first().body
		owner = Blog.query.filter_by(id=id).first().owner
		return render_template("individual_entry.html", title=title, body=body, owner=owner)
	elif request.args.get('user'):
		id = request.args.get('user')
		owner_id = Blog.query.filter_by(id=id).first().owner.id
		blogs_by_user = Blog.query.filter_by(owner_id=id).all()
		return render_template("individual_user.html", blogs_by_user=blogs_by_user)
	else:
		return render_template("list_blogs.html", blogs=blogs)

@app.route('/newpost')
def display_entry_form():
	return render_template("newpost.html")

@app.route('/newpost', methods=['POST'])
def newpost():
	title = request.form['title']
	body = request.form['body']

	user_id = User.query.filter_by(username=session['username']).first()

	title_error = ""
	body_error = ""

	if title == "":
		title_error = "Please fill in the title"
	if body == "":
		body_error = "Please fill in the body"

	if title_error or body_error:
		return render_template("newpost.html", 
			title=title, title_error=title_error, 
			body=body, body_error=body_error)
	else:
		new_blog = Blog(title, body, user_id)
		db.session.add(new_blog)
		db.session.commit()
		new_id = new_blog.id
		path = "/blog?id=" + str(new_id)
		return redirect(path)

if __name__ == "__main__":
	app.run()