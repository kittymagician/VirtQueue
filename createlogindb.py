from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String
engine = create_engine('sqlite:///hubapp.sqlite', echo = False)
meta = MetaData()
login = Table(
   'User', meta, 
   Column('id', Integer, primary_key = True), 
   Column('username', String), 
   Column('password', String),
)
meta.create_all(engine)