from flask import Flask, render_template, request, Response, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy  import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField
from wtforms.validators import InputRequired, Email, Length, DataRequired
from twilio.rest import Client
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
sms_support = False # Change this to activate SMS support. 
account_sid = 'twilio account sid here' #Twilio Account SID
auth_token = 'twilio auth token here' #Twilio Auth Token
twilio_number = 'twilio number here' #Twilio Number
domain = 'domain.com' # Change this for SMS/Email messages to include your domain.

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(15), unique=True)
    password = db.Column(db.String(80))
 
def sendsms(number, msg):
  client = Client(account_sid, auth_token)
  wmsg = " This text was sent automatically by the VirtQueue Service. To opt out of future texts text STOP to this number."
  cmsg = msg + wmsg
  client.messages.create(from_=twilio_number,
                       to=number,
                       body=cmsg)
  
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class MyForm(FlaskForm):
    telephonenumber = StringField('telephone number', validators=[DataRequired(), Length(max=11)])
    ordr = StringField('order', validators=[DataRequired()])
    submit = SubmitField('Submit')

class LoginForm(FlaskForm):
    username = StringField('username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=8, max=80)])

def get_m(queueid):
    '''this could be any function that blocks until data is ready'''
    conn = sqlite3.connect('hubapp.sqlite')
    c = conn.cursor()
    c.execute("SELECT ID, telephonenumber, category, status, jointime FROM queue WHERE id =?", (queueid,))
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
  if sms_support == True:
    msg = 'Your order is ready for collection at the shop. Track progress online: https://' + domain + '/queue/' + id
    c.execute("SELECT telephonenumber FROM queue where ID = ?", (id,))
    numtogether = c.fetchall()
    if len(numtogether) > 0:
      numselect = len(numtogether) - 1 #list starts at 0.
      number = numtogether[numselect]
    else:
      number = numtogether[0]
    sendsms(number, msg)
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
    c.execute("SELECT ID from queue WHERE telephonenumber=?", (number,))
    queueidget = c.fetchall()
    queueselect = len(queueidget) - 1 #list starts at 0.
    if queueselect > 0:
    	 queueid = queueidget[queueselect]
    else:
     queueid = str(queueidget[0])
    conn.close()
    if sms_support == True:
      print(queueid)
      msg = 'Your order:' + ordr + ' has been confirmed by the shop. Track progress online: https://' + domain + '/queue/' + str(queueid[0])
      sendsms(number, msg)
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
    c.execute("SELECT ID from queue WHERE telephonenumber=?", (number,))
    queueidget = c.fetchall()
    queueselect = len(queueidget) - 1 #list starts at 0.
    if queueselect > 0:
    	 queueid = queueidget[queueselect]
    else:
     queueid = str(queueidget[0])
    conn.close()
    if sms_support == True:
      print(queueid)
      msg = 'Your order:' + ordr + ' has been confirmed by the shop. Track progress online: https://' + domain + '/queue/' + str(queueid[0])
      sendsms(number, msg)
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
    c.execute("SELECT ID from queue WHERE telephonenumber=?", (number,))
    queueidget = c.fetchall()
    queueselect = len(queueidget) - 1 #list starts at 0.
    if queueselect > 0:
    	 queueid = queueidget[queueselect]
    else:
     queueid = str(queueidget[0])
    conn.close()
    if sms_support == True:
      print(queueid)
      msg = 'Your order:' + ordr + ' has been confirmed by the shop. Track progress online: https://' + domain + '/queue/' + str(queueid[0])
      sendsms(number, msg)
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
    c.execute("SELECT ID from queue WHERE telephonenumber=?", (number,))
    queueidget = c.fetchall()
    queueselect = len(queueidget) - 1 #list starts at 0.
    if queueselect > 0:
    	 queueid = queueidget[queueselect]
    else:
     queueid = str(queueidget[0])
    conn.close()
    if sms_support == True:
      print(queueid)
      msg = 'Your order:' + ordr + ' has been confirmed by the shop. Track progress online: https://' + domain + '/queue/' + str(queueid[0])
      sendsms(number, msg)
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
    c.execute("SELECT ID from queue WHERE telephonenumber=?", (number,))
    queueidget = c.fetchall()
    queueselect = len(queueidget) - 1 #list starts at 0.
    if queueselect > 0:
    	 queueid = queueidget[queueselect]
    else:
     queueid = str(queueidget[0])
    conn.close()
    if sms_support == True:
      print(queueid)
      msg = 'Your order:' + ordr + ' has been confirmed by the shop. Track progress online: https://' + domain + '/queue/' + str(queueid[0])
      sendsms(number, msg)
    return redirect(url_for('neworders'))
  return render_template('completedorder.html', form=form, items=items)

@app.route('/stream/<int:queue_id>')
def streamid(queue_id):
    def eventStream():
        while True:
            # wait for source data to be available, then push it
            yield 'data: {}\n\n'.format(get_m(queue_id))
    return Response(eventStream(), mimetype="text/event-stream")
                  
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=3000, debug=False)
