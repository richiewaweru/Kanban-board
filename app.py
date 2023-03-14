from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
from flask import Flask, render_template, request, redirect, url_for
from flask_migrate import Migrate
from datetime import datetime


app=Flask(__name__)
app.config ['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///Tasks.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'Thisissupposedtobesecret!'
bootstrap = Bootstrap(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# User model
#creates user table
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    tasks = db.relationship('Task', backref='user', lazy=True)

# Task model
#creates task table
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    complete = db.Column(db.Boolean)
    started=db.Column(db.Boolean)
    created_on = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# Home page
@app.route('/')
def home():
    user = None
    if 'username' in session:
        user = User.query.filter_by(username=session['username']).first()
    return render_template('home.html', user=user)



from sqlalchemy.exc import IntegrityError
# Signup page
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    user = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password, method='sha256')
        with app.app_context():
            try:
                new_user = User(username=username, password=hashed_password)
                db.session.add(new_user)
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                flash('Username already exists. Please choose a different username.', 'warning')
                return redirect(url_for('signup'))
            flash('Account created successfully. Please login.', 'success')
            return redirect(url_for('login', _method='GET'))
    return render_template('signup.html',user=user)


# Login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    user=None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        with app.app_context():
            user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['username'] = username
            flash('Logged in successfully.', 'success')
            return redirect(url_for('kanban'))
        else:
            flash('Invalid username or password.', 'error')
            return redirect(url_for('login'))
    return render_template('login.html',user=user)

# Logout
@app.route('/logout')
@login_required
def logout():
    session.pop('username', None)
    flash('Logged out successfully.', 'success')
    return redirect(url_for('home'))

# Kanban page
@app.route('/kanban')
@login_required
def kanban():
    with app.app_context():
        #filters by complete and started status to render the correct view
        user = User.query.filter_by(username=session['username']).first()
        todo_list = Task.query.filter_by(complete=False,started=False,user_id=user.id).order_by(Task.created_on).all()
        done_list = Task.query.filter_by(complete=True,started=True,user_id=user.id).order_by(Task.created_on).all()
        doing_list =Task.query.filter_by(complete=False,started=True,user_id=user.id).order_by(Task.created_on).all()
    return render_template("index.html",user=user,todo_list=todo_list, doing_list=doing_list,done_list=done_list)


#add tasks to todo state
@app.route('/add',methods=["POST"])
def add():
    title = request.form.get("title")
    with app.app_context():
        user = User.query.filter_by(username=session['username']).first()
        new_todo = Task(title=title, complete=False, started=False,user_id=user.id)
        db.session.add(new_todo)
        db.session.commit()
    return redirect(url_for('kanban'))

#update a task to started/doing state
@app.route('/update/<int:todo_id>', methods=['GET', 'POST'])
def update(todo_id):
    with app.app_context():
        todo = Task.query.filter_by(id=todo_id).first()
        todo.started = not todo.started
        db.session.commit()
    return redirect(url_for('kanban'))

#update a task to done/completed state
@app.route("/complete/<int:todo_id>")
def complete(todo_id):
    with app.app_context():
        todo = Task.query.filter_by(id=todo_id).first()
        todo.complete = not todo.complete
        db.session.commit()
    return redirect(url_for('kanban'))

#deletes a task
@app.route("/delete/<int:todo_id>")
def delete(todo_id):
    with app.app_context():
        todo = Task.query.filter_by(id=todo_id).first()
        db.session.delete(todo)
        db.session.commit()
    return redirect(url_for('kanban'))


#edits a task
@app.route("/edit/<int:todo_id>", methods=["GET", "POST"])
def edit(todo_id):
    todo = Task.query.get(todo_id)
    if request.method == "POST":
        title = request.form["title"]
        todo.title = title
        db.session.commit()
        return redirect(url_for('kanban'))
    return render_template("edit.html", todo=todo)



if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    app.run(debug=True)

