from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String
from werkzeug.security import generate_password_hash
engine = create_engine('sqlite:///hubapp.sqlite', echo = True)
meta = MetaData()
User = Table(
   'User', meta, 
   Column('id', Integer, primary_key = True), 
   Column('username', String), 
   Column('password', String),
)
uname = 'tester'
ipass = 'yM37A^cF%ndu8cy!u#ikt8mn'
print(len(uname))
if len(uname) >= 4:
  if len(uname) <= 15:
    hashed_password = generate_password_hash(ipass, method='sha256')
    pword = hashed_password
    ins = User.insert().values(username = uname, password = pword)
    conn = engine.connect()
    result = conn.execute(ins)
  else:
    print('Your username is too long.')
else:
  print('Your password is too short.')