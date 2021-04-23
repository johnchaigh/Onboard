from werkzeug.security import check_password_hash, generate_password_hash
import sqlite3
from cs50 import SQL

db = SQL("sqlite:///onboard.db")

password = 'q'
hashpassword = generate_password_hash(password)

db.execute("UPDATE users SET password = ?", hashpassword)
