import sqlite3

db = sqlite3.connect('pm_weather.db')
cursor = db.cursor()

cursor.execute('''
CREATE TABLE WHistory
       (Store_ID    CHAR(50),
       Salesperson  CHAR(50),
       Sales         INT
       );
       
''')
db.commit()