from flask import Flask, render_template, request, Response, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy  import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Email, Length, DataRequired
import datetime
import sqlite3
import time
import os
app = Flask(__name__)
app.config['SECRET_KEY'] = str(os.urandom(255))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hubapp.sqlite'
app.config['SESSION_COOKIE_SECURE'] = True
app.config['REMEMBER_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_NAME'] = "__secure"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(15), unique=True)
    password = db.Column(db.String(80))
 


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class MyForm(FlaskForm):
    telephonenumber = StringField('telephone number', validators=[DataRequired(), Length(max=40)])
    ordr = StringField('order', validators=[DataRequired()])
    submit = SubmitField('Submit')

class LoginForm(FlaskForm):
    username = StringField('username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=8, max=80)])

def get_message():
    '''this could be any function that blocks until data is ready'''
    time.sleep(1.0)
    s = time.ctime(time.time())
    return s


def get_m(queueid):
    '''this could be any function that blocks until data is ready'''
    conn = sqlite3.connect('hubapp.sqlite')
    c = conn.cursor()
    c.execute("SELECT ID, telephone number, category, status, jointime FROM queue WHERE id =?", (queueid,))
    assigned = c.fetchone()
    a = "Your Order is currently: "
    b = assigned[3]
    s = a + b
    conn.close()
    time.sleep(1.0)
    return s

@app.route('/')
def root():
    return 'Virtual Queueing Technology by KittyMagician'

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if check_password_hash(user.password, form.password.data):
                login_user(user)
                return redirect(url_for('admin'))
        print('error.')
        return '<h1>Invalid username or password</h1>'
        #return '<h1>' + form.username.data + ' ' + form.password.data + '</h1>'
    return render_template('login.html', form=form)

@app.route('/queue/<int:queue_id>')
def queueid(queue_id):
    return render_template('queue.html', queueid=queue_id)
  
@app.route('/admin/complete/<int:queue_id>')
@login_required
def completeorder(queue_id):
  conn = sqlite3.connect('hubapp.sqlite')
  c = conn.cursor()
  id = str(queue_id)
  timenow = datetime.datetime.now()
  c.execute("UPDATE queue SET status = ? WHERE ID = ?", ('order has been completed contact the shop', id))
  c.execute("UPDATE queue SET endtime = ? WHERE ID = ?", (timenow, id))
  conn.commit()
  conn.close()
  return redirect(url_for('completedorder'))

@app.route('/admin/ready/<int:queue_id>')
@login_required
def readyorder(queue_id):
  conn = sqlite3.connect('hubapp.sqlite')
  c = conn.cursor()
  id = str(queue_id)
  c.execute("UPDATE queue SET status = ? WHERE ID = ?", ('your order is ready to collect', id))
  conn.commit()
  conn.close()
  return redirect(url_for('readyingorder'))

@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
  conn = sqlite3.connect('hubapp.sqlite')
  c = conn.cursor()
  c.execute("SELECT * FROM queue")
  items = c.fetchall()
  status = "new order"
  category = "food"
  form = MyForm()
  if form.validate_on_submit():  
    conn = sqlite3.connect('hubapp.sqlite')
    c = conn.cursor()
    number = form.telephonenumber.data
    ordr = form.ordr.data
    timenow = datetime.datetime.now()
    c.execute("insert into queue values (?, ?, ?, ?, ?, ?, ?)", (None, number, category, status, ordr, timenow, None))
    conn.commit()
    conn.close()
    return redirect(url_for('neworders'))
  return render_template('admincenter.html', form=form, items=items)

@app.route('/admin/neworders', methods=['GET', 'POST'])
@login_required
def neworders():
  conn = sqlite3.connect('hubapp.sqlite')
  c = conn.cursor()
  c.execute('SELECT * FROM queue WHERE status = \"new order\"')
  items = c.fetchall()
  status = "new order"
  category = "food"
  form = MyForm()
  if form.validate_on_submit():  
    conn = sqlite3.connect('hubapp.sqlite')
    c = conn.cursor()
    number = form.telephonenumber.data
    ordr = form.ordr.data
    timenow = datetime.datetime.now()
    c.execute("insert into queue values (?, ?, ?, ?, ?, ?, ?)", (None, number, category, status, ordr, timenow, None))
    conn.commit()
    conn.close()
    return redirect(url_for('neworders'))
  return render_template('openorder.html', form=form, items=items)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('logoutsuccess'))

@app.route("/logout/success")
def logoutsuccess():
  return render_template('logout.html')

@app.route('/admin/confirm/<int:queue_id>')
@login_required
def confirmorder(queue_id):
  conn = sqlite3.connect('hubapp.sqlite')
  c = conn.cursor()
  id = str(queue_id)
  c.execute("UPDATE queue SET status = ? WHERE ID = ?", ('confirmed order', id))
  conn.commit()
  conn.close()
  return 'order confirmed'

@app.route('/admin/prepair/<int:queue_id>')
@login_required
def prepairorder(queue_id):
  conn = sqlite3.connect('hubapp.sqlite')
  c = conn.cursor()
  id = str(queue_id)
  c.execute("UPDATE queue SET status = ? WHERE ID = ?", ('prepairing order', id))
  conn.commit()
  conn.close()
  return redirect(url_for('prepairingorder'))

@app.route('/admin/prepairingorder', methods=['GET', 'POST'])
@login_required
def prepairingorder():
  conn = sqlite3.connect('hubapp.sqlite')
  c = conn.cursor()
  c.execute('SELECT * FROM queue WHERE status = \"prepairing order\"')
  items = c.fetchall()
  status = "new order"
  category = "food"
  form = MyForm()
  if form.validate_on_submit():  
    conn = sqlite3.connect('hubapp.sqlite')
    c = conn.cursor()
    number = form.telephonenumber.data
    ordr = form.ordr.data
    timenow = datetime.datetime.now()
    c.execute("insert into queue values (?, ?, ?, ?, ?, ?, ?)", (None, number, category, status, ordr, timenow, None))
    conn.commit()
    conn.close()
    return redirect(url_for('neworders'))
  return render_template('prepairorder.html', form=form, items=items)

@app.route('/admin/readyorder', methods=['GET', 'POST'])
@login_required
def readyingorder():
  conn = sqlite3.connect('hubapp.sqlite')
  c = conn.cursor()
  c.execute('SELECT * FROM queue WHERE status = \"your order is ready to collect\"')
  items = c.fetchall()
  status = "new order"
  category = "food"
  form = MyForm()
  if form.validate_on_submit():  
    conn = sqlite3.connect('hubapp.sqlite')
    c = conn.cursor()
    number = form.telephonenumber.data
    ordr = form.ordr.data
    timenow = datetime.datetime.now()
    c.execute("insert into queue values (?, ?, ?, ?, ?, ?, ?)", (None, number, category, status, ordr, timenow, None))
    conn.commit()
    conn.close()
    return redirect(url_for('neworders'))
  return render_template('readyorder.html', form=form, items=items)

@app.route('/admin/completedorder', methods=['GET', 'POST'])
@login_required
def completedorder():
  conn = sqlite3.connect('hubapp.sqlite')
  c = conn.cursor()
  c.execute('SELECT * FROM queue WHERE status = \"order has been completed contact the shop\"')
  items = c.fetchall()
  status = "new order"
  category = "food"
  form = MyForm()
  if form.validate_on_submit():  
    conn = sqlite3.connect('hubapp.sqlite')
    c = conn.cursor()
    number = form.telephonenumber.data
    ordr = form.ordr.data
    timenow = datetime.datetime.now()
    c.execute("insert into queue values (?, ?, ?, ?, ?, ?, ?)", (None, number, category, status, ordr, timenow, None))
    conn.commit()
    conn.close()
    return redirect(url_for('neworders'))
  return render_template('completedorder.html', form=form, items=items)
  
  

# @app.route('/admin/new', methods=['GET', 'POST'])
# @login_required
# def neworder():
#   status = "new order"
#   category = "food"
#   form = MyForm()
#   if form.validate_on_submit():  
#     conn = sqlite3.connect('hubapp.sqlite')
#     c = conn.cursor()
#     number = form.telephonenumber.data
#     ordr = form.ordr.data
#     timenow = datetime.datetime.now()
#     c.execute("insert into queue values (?, ?, ?, ?, ?, ?, ?)", (None, number, category, status, ordr, timenow, None))
#     conn.commit()
#     conn.close()
#     return "<p>Added Order!</p>"
#   return render_template('neworder.html', form=form)

  #c.execute("insert into queue values (?, ?, ?, ?, ?)", (None, telephone, category, status, timenow))
  #conn.commit()
  #c.execute("SELECT MAX(ID) AS LastID FROM queue")
  #lastid = c.fetchone()
  #conn.close()
  #return 'opened order: ' + str(lastid[0])
  
@app.route('/stream')
def stream():
    def eventStream():
        while True:
            # wait for source data to be available, then push it
            yield 'data: {}\n\n'.format(get_message())
    return Response(eventStream(), mimetype="text/event-stream")

@app.route('/stream/<int:queue_id>')
def streamid(queue_id):
    def eventStream():
        while True:
            # wait for source data to be available, then push it
            yield 'data: {}\n\n'.format(get_m(queue_id))
    return Response(eventStream(), mimetype="text/event-stream")
                  
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=3000, debug=True)