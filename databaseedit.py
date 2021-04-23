import sqlite3
from cs50 import SQL

db = SQL("sqlite:///onboard.db")

#db.execute("ALTER TABLE pathways ADD COLUMN 'nummbercompleted' int")
#db.execute("ALTER TABLE users ADD COLUMN 'region' int")
#db.execute("ALTER TABLE people ADD COLUMN 'region' int")
#db.execute("ALTER TABLE users ADD COLUMN 'averagebusinesstarget' int")
#db.execute("ALTER TABLE users ADD COLUMN 'averageprogressnumber' int")




#print(db.execute("SELECT * FROM people"))

#db.execute("UPDATE pathways SET region = ?", 'Southwest and Northern Island')
#db.execute("DELETE FROM pathwaystages")
#db.execute("DELETE FROM people")
#db.execute("DELETE FROM pathways")
#db.execute("DELETE FROM pathwayprogress")
#db.execute("UPDATE people SET pdm = 'gary@icloud.com' WHERE pdm = ?", 'Gary@icloud.com')
#db.execute("UPDATE users SET email = 'gary@icloud.com' WHERE email = ?", 'Gary@icloud.com')
db.execute("UPDATE people SET completed = 0")

rows = db.execute("SELECT * FROM people")

print(rows[0])
