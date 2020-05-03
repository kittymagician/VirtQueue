import sqlite3
conn = sqlite3.connect('hubapp.sqlite')
c = conn.cursor()
c.execute('''CREATE TABLE queue
             (ID INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, telephonenumber text, category text, status text, queueorder text, jointime timestamp, endtime timestamp)''')
conn.commit()
conn.close()
