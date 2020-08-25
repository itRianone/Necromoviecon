import sqlite3

db = sqlite3.connect("mydatabase.db")
cursor = db.cursor()

cursor.execute("""CREATE TABLE IF NOT EXISTS movies(
    name TEXT
  )
""")

db.commit()

#for e in cursor.execute("SELECT name FROM movies"):
  #print(e)

