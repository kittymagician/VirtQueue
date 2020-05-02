import sqlite3
conn = sqlite3.connect('hubapp.sqlite')
c = conn.cursor()
c.execute('''DROP TABLE User''')
c.execute('''DROP TABLE queue''')
c.execute('''DROP TABLE queueadmin''')
conn.commit()
conn.close()
