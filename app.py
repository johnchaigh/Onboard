# @Author: johnhaigh
# @Date:   2020-12-29T17:16:37+00:00
# @Last modified by:   johnhaigh
# @Last modified time: 2021-02-26T18:01:29+00:00

#A web based application to track the onboarding of new recruits.

import os
import sqlite3
import re
import math
from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
import datetime
from datetime import date
from functools import wraps
import os
from os.path import join, dirname, realpath, expanduser
import pandas as pd
import csv

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure session to use filesystem (instead of signed cookies)
#app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config['SESSION_PERMANENT'] = True
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_THRESHOLD'] = 100
app.config['SECRET_KEY'] = '22de23241b664fc2abc8867581a0642d'
sess = Session()
sess.init_app(app)


# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///onboard.db")

def days_between(d1, d2):
    d1 = datetime.strptime(d1, "%Y-%m-%d")
    d2 = datetime.strptime(d2, "%Y-%m-%d")

    return abs((d2 - d1).days)

    # Upload folder
UPLOAD_FOLDER = 'static/files'
app.config['UPLOAD_FOLDER'] =  UPLOAD_FOLDER

def login_required(f):
    """
    Decorate routes to require login.
    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

# Landing Page
@app.route("/")
def index():

    if request.method == "GET":

        if session.get('user_id') is not None:

            info = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
            username = info[0]['email']
            firstname = info[0]['firstname']
            lastname = info[0]['lastname']

            fullname = firstname + ' ' + lastname

            return render_template("dashboard.html", firstname = firstname, FullName = fullname)

        else:

            datetoday = datetime.datetime.today().strftime ('%d%m%Y')

            return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "GET":
        return render_template('register.html')
    else:

        firstname = request.form.get("firstname")
        lastname = request.form.get("lastname")
        email = request.form.get("email")
        password = request.form.get("password")
        company = request.form.get("company")
        jobrole = request.form.get("jobrole")
        hashpassword = generate_password_hash(password)
        companymail = email.split("@")[1]

        # Create table for users
        database = db.execute("CREATE TABLE IF NOT EXISTS users ('id' integer PRIMARY KEY NOT NULL, 'email' text NOT NULL, 'firstname' text NOT NULL,'lastname' text NOT NULL, 'password' text NOT NULL, 'company' text NOT NULL, 'jobrole' text NOT NULL,'companymail' text NOT NULL)")

        # Add user to database, if user already exists say eror username already exists
        row = db.execute("SELECT * FROM users WHERE email = ?", email)
        if row:
            return render_template('apology.html', message="User already registered", bodymessage = "User already registered")
        else:
            db.execute("INSERT INTO users (firstname, lastname, email, password, company, jobrole, companymail) VALUES (?, ?, ?, ?, ?, ?, ?)", firstname, lastname, email, hashpassword, company, jobrole, companymail)

    return redirect("/login")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE email = :username", username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["password"], request.form.get("password")):
            return render_template('apology.html', message="invalid username and/or password", bodymessage = "invalid username and/or password")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/dashboard")

    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/people", methods=["GET", "POST"])
@login_required
def people():

    if request.method == "GET":

        info = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
        username = info[0]['email']
        firstname = info[0]['firstname']
        lastname = info[0]['lastname']
        companymail = info[0]['companymail']

        fullname = firstname + ' ' + lastname

        rows = db.execute("SELECT * FROM people WHERE pdm = ?", username)

        # TODO: Add in calculation for days in pathway

        daytoday = int(datetime.datetime.today().strftime ('%d'))
        monthtoday = int(datetime.datetime.today().strftime ('%m'))
        yeartoday = int(datetime.datetime.today().strftime ('%Y'))
        i = 0
        daysin = {}

        for row in rows:

            dateenrolled = rows[i]['pathwayEnrolledDate']
            if dateenrolled != None:

                x = dateenrolled.split("/", 3)
                yearenrolled = (int(x[2]))
                monthenroleld = (int(x[1]))
                dayenrolled = (int(x[0]))

                d0 = date(yearenrolled, monthenroleld, dayenrolled)
                d1 = date(yeartoday, monthtoday, daytoday)
                delta = d1 - d0
                daysin = delta.days

            else:

                daysin = 0

            db.execute("UPDATE people SET daysinpathway = ?", daysin )

        return render_template("people.html", firstname = firstname, FullName = fullname, companymail=companymail, rows = rows)

    else:

        return render_template("newperson.html", Fullname = fullname)

@app.route("/newperson", methods=["GET", "POST"])
@login_required
def newperson():

    if request.method == "POST":

        info = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
        username = info[0]['email']
        firstname = info[0]['firstname']
        lastname = info[0]['lastname']
        companymail = info[0]['companymail']
        fullname = firstname+''+lastname

        personfirstname = request.form.get("firstname")
        personlastname = request.form.get("lastname")
        personmobile = request.form.get("mobile")
        personemail = request.form.get("email")
        personbam = request.form.get("bam")
        personhistory = request.form.get("history")
        personexemployeddeal = request.form.get("exemployeddeal")
        personexemployeddealexpiry = request.form.get("exemployeddealexpiry")
        personbusinessWrittenPreviousMonth = request.form.get("businessWrittenPreviousMonth")
        personbusinessWrittenYearToDate = request.form.get("businessWrittenYearToDate")

        database = db.execute("""CREATE TABLE IF NOT EXISTS people ('id' integer PRIMARY KEY NOT NULL, 'firstname' text NOT NULL, 'lastname' text NOT NULL, 'mobile' text NOT NULL, 'email' text NOT NULL, 'pdm' text NOT NULL, 'bam' text, 'pathwayEnrolled' text, 'pathwayEnrolledDate' text, 'pathwayEnrolledPosition' text, 'pathwayEnrolledProgress' integer,  'pathwayEnrolledPositionDate' text, 'history' text, 'exEmployedDeal' text, 'exEmployedDealExpiry' text, 'businessWrittenPreviousMonth' integer, 'businessWrittenYearToDate'  integer, 'daysinpathway' integer)""")

        db.execute("INSERT INTO people (firstname, lastname, mobile, email, pdm, bam, history, exEmployedDeal, exEmployedDealExpiry, businessWrittenPreviousMonth, businessWrittenYearToDate) VALUES(?,?,?,?,?,?,?,?,?,?,?)", personfirstname, personlastname, personmobile, personemail, username, personbam, personhistory, personexemployeddeal, personexemployeddealexpiry, personbusinessWrittenPreviousMonth, personbusinessWrittenYearToDate)

        rows = db.execute("SELECT * FROM people WHERE pdm = ? AND email = ?", username, personemail)

        return render_template("viewperson.html", rows = rows, FullName = fullname)

    else:

        info = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
        username = info[0]['email']
        firstname = info[0]['firstname']
        lastname = info[0]['lastname']
        companymail = info[0]['companymail']
        fullname = firstname+''+lastname

        return render_template("newperson.html", FullName = fullname)

@app.route("/viewperson", methods=["GET", "POST"])
@login_required
def viewperson():

    if request.method == "GET":

        info = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
        username = info[0]['email']
        firstname = info[0]['firstname']
        lastname = info[0]['lastname']

        personemail = request.args.get('name')

        fullname = firstname + ' ' + lastname

        rows = db.execute("SELECT DISTINCT * FROM people WHERE email = ?", personemail)

        return render_template("viewperson.html", Fullname = fullname, rows = rows)

@app.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():

    if request.method == "GET":

        info = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
        username = info[0]['email']
        firstname = info[0]['firstname']
        lastname = info[0]['lastname']

        fullname = firstname + ' ' + lastname

        pathways = len(db.execute("SELECT * from pathways WHERE email = ?", username))
        people = len(db.execute("SELECT * from people WHERE pdm = ?", username))

        return render_template("dashboard.html", firstname = firstname, FullName = fullname, pathwayNumber = pathways, people = people)

@app.route("/pathways", methods=["GET", "POST"])
@login_required
def pathways():
    if request.method == "GET":

        info = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
        username = info[0]['email']
        firstname = info[0]['firstname']
        lastname = info[0]['lastname']
        company = info[0]['company']
        email = info[0]['email']

        fullname = firstname + ' ' + lastname

        # Add user to database, if user already exists say eror username already exists
        pathways = db.execute("SELECT * FROM pathways WHERE email = ?", email)

        return render_template("pathways.html", firstname = firstname, company=company, FullName = fullname, pathways = pathways)

@app.route("/newpathway", methods=["GET", "POST"])
@login_required
def newpathway():
    if request.method == "GET":

        info = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
        username = info[0]['email']
        firstname = info[0]['firstname']
        lastname = info[0]['lastname']
        company = info[0]['company']
        fullname = firstname + ' ' + lastname

        return render_template("newpathway.html", firstname = firstname, company=company, FullName = fullname)

    else:

        info = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
        username = info[0]['email']
        firstname = info[0]['firstname']
        lastname = info[0]['lastname']
        company = info[0]['company']
        email = info[0]['email']
        companymail = info[0]['companymail']

        fullname = firstname + ' ' + lastname

        pathwayName = request.form.get("pathwayName")
        pathwayDescription = request.form.get("pathwayDescription")

        if (request.form.get("publicShare") != None):
            share = 'True'
        else:
            share = 'False'

        database = db.execute("CREATE TABLE IF NOT EXISTS pathways ('id' integer PRIMARY KEY NOT NULL, 'pathwayName' text NOT NULL, 'pathwayDescription' text NOT NULL, 'share' text NOT NULL, 'email' text NOT NULL, 'companymail' text NOT NULL, 'enrolled' integer)")

        # Add user to database, if user already exists say eror username already exists
        row = db.execute("SELECT * FROM pathways WHERE pathwayName = ? AND email = ?", pathwayName, username)
        if row:
            return render_template('apology.html', message="Pathway Already Exists", bodymessage = "Pathway Already Exists")
        else:
            db.execute("INSERT INTO pathways (pathwayName, pathwayDescription, email, companymail, share, enrolled) VALUES (?, ?, ?, ?, ?, '0')", pathwayName, pathwayDescription, email, companymail, share)

        return render_template('addsteps.html', pathwayName = pathwayName, pathwayDescription = pathwayDescription)

@app.route("/addsteps", methods=["GET", "POST"])
@login_required
def addsteps():
    if request.method == "GET":

        info = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
        username = info[0]['email']
        firstname = info[0]['firstname']
        lastname = info[0]['lastname']
        company = info[0]['company']
        email = info[0]['email']

        fullname = firstname + ' ' + lastname
        # Write greeting for dashboard header

        pathway = db.execute("SELECT * from pathways WHERE email =?", email)

        pathwayName = pathway[0][pathwayName]
        pathwayDescription = pathway[0][pathwayDescription]

        return render_template("addsteps.html", pathwayName = pathwayName, FullName = fullname, pathwayDescription = pathwayDescription)

@app.route("/finishpathway", methods=["GET", "POST"])
@login_required
def finishpathway():
    if request.method == "POST":

        info = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
        username = info[0]['email']
        firstname = info[0]['firstname']
        lastname = info[0]['lastname']
        company = info[0]['company']
        email = info[0]['email']
        companymail = info[0]['companymail']

        pathwayName = request.form.get("pathwayName")

        database = db.execute("CREATE TABLE IF NOT EXISTS pathwaystages ('id' integer PRIMARY KEY NOT NULL, 'pathwayName' text NOT NULL, 'email' text NOT NULL, 'stagenumber' integer NOT NULL, 'stagecontent' text NOT NULL, 'stageowner' text, 'stagenotes' text)")

        req = request.form
        stagenumber = 1
        numberofentries = (len(req))
        print(numberofentries)
        number = (( numberofentries - 1 ) / 3 )
        print(number)
        number = number+1
        i = 1
        while i < number:

            stagenumberstring = str(stagenumber)
            stagenote = str(stagenumberstring + ' notes')
            stageown = str(stagenumberstring + ' owner')
            stagecontent = req[stagenumberstring]
            stagenotes = req[stagenote]
            stageowner = req[stageown]
            db.execute("INSERT INTO pathwaystages (pathwayName, email, stagenumber, stagecontent, stageowner, stagenotes) VALUES (?, ?, ?, ?, ?, ?)", pathwayName, email, stagenumber, stagecontent, stageowner, stagenotes)
            stagenumber = (stagenumber + 1)
            i = (i+1)

        rows = db.execute("SELECT DISTINCT * from pathwaystages WHERE pathwayName = ? AND email is ?", pathwayName, email)

        return render_template("finishpathway.html", rows = rows, pathwayName = pathwayName)

    else:

        return render_template("pathways.html")

@app.route("/viewpathway", methods=["GET", "POST"])
@login_required
def viewpathway():

    if request.method == "GET":

        info = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])

        firstname = info[0]['firstname']
        lastname = info[0]['lastname']
        email = info[0]['email']
        company = info[0]['company']
        jobrole = info[0]['jobrole']
        fullname = firstname + ' ' + lastname

        pathwayName = request.args.get('name')

        rows = db.execute("SELECT * from pathwaystages WHERE pathwayName = ? AND email = ?", pathwayName, email)

        pathwayDescription = db.execute("SELECT pathwayDescription FROM pathways WHERE pathwayName = ?", pathwayName)

        people = db.execute("SELECT * FROM people WHERE pathwayEnrolled = ? AND pdm = ?", pathwayName, email)

        return render_template("viewpathway.html", rows = rows, pathwayName = pathwayName, pathwayDescription = pathwayDescription[0], FullName = fullname, people = people)

@app.route("/enroll", methods=["GET", "POST"])
@login_required
def enroll():

    if request.method == "GET":

        info = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
        username = info[0]['email']
        firstname = info[0]['firstname']
        lastname = info[0]['lastname']
        companymail = info[0]['companymail']
        fullname = firstname+' '+lastname

        people = db.execute("SELECT * FROM people WHERE pdm = ?", username)
        pathways = db.execute("SELECT * FROM pathways WHERE email = ?", username)

        return render_template("enroll.html", people = people, pathways = pathways, FullName = fullname)

    else:

        info = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
        username = info[0]['email']
        firstname = info[0]['firstname']
        lastname = info[0]['lastname']
        companymail = info[0]['companymail']
        fullnameuser = firstname+' '+lastname

        fullname = request.form.get("name")
        pathway = request.form.get("pathway")

        x = fullname.split()
        firstname = x[0]
        lastname = x[1]

        person = db.execute("SELECT * from people WHERE firstname = ? AND lastname = ? AND pdm = ?", firstname, lastname, username)
        personemail = person[0]['email']

        datetoday = (datetime.datetime.today().strftime ('%d'))+" / "+(datetime.datetime.today().strftime ('%m'))+" / "+(datetime.datetime.today().strftime ('%Y'))

        row = db.execute("SELECT * from people WHERE pathwayEnrolled = ? AND email = ?", pathway, personemail)

        if row:
            return render_template('apology.html', FullName = fullnameuser, message="User already registered", bodymessage = "User already enrolled")

        else:

            db.execute("UPDATE people SET pathwayEnrolledDate = ?, pathwayEnrolled = ?, pathwayEnrolledPosition = ?, pathwayEnrolledProgress = ?, pathwayEnrolledPositionDate = ? WHERE email = ?", datetoday, pathway , 0 , 0 , datetoday, personemail)
            db.execute("UPDATE pathways SET enrolled = enrolled + 1 WHERE pathwayNAME = ? AND email = ?", pathway, username)
            rows = db.execute("SELECT * FROM people where email = ?", personemail)
            pathwaystages = db.execute("SELECT * FROM pathwaystages where pathwayName = ?", pathway)
            position = int(rows[0]['pathwayEnrolledPosition'])

            db.execute("CREATE TABLE IF NOT EXISTS pathwayprogress ('email' text NOT NULL, 'pathwayName' text NOT NULL, 'stagenumber' int, 'stagecontent' text, 'stageowner' text, 'stagenotes' text, 'datecompleted' text, 'completed' int ) ")
            stagenumber = 0
            for i in pathwaystages:
                db.execute("INSERT INTO pathwayprogress (email, pathwayName, stagenumber, stagecontent, stageowner, stagenotes, completed) VALUES (?,?,?,?,?,?,?)", personemail, pathway, pathwaystages[stagenumber]['stagenumber'], pathwaystages[stagenumber]['stagecontent'], pathwaystages[stagenumber]['stageowner'], pathwaystages[stagenumber]['stagenotes'], 0)
                stagenumber = stagenumber + 1

            #daysin = datetoday - datetime.datetime.today().strftime ('%d%m%Y')
            daysin = 0
            pathwayprogress = db.execute("SELECT * FROM pathwayprogress WHERE email = ? AND completed = ? AND pathwayName = ?", personemail, 1, pathway)
            pathwayremaining = db.execute("SELECT * FROM pathwayprogress WHERE email = ? AND completed = ? AND pathwayName = ?", personemail, 0, pathway)

            return render_template("progress.html", FullName = fullnameuser, pathwayprogress = pathwayprogress, pathwayremaining = pathwayremaining, position = position, rows = rows, pathwaystages = pathwaystages, daysin = daysin)

@app.route("/progress", methods=["GET", "POST"])
@login_required
def progress():

    if request.method == "GET":

        info = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
        username = info[0]['email']
        firstname = info[0]['firstname']
        lastname = info[0]['lastname']
        companymail = info[0]['companymail']
        fullname = firstname+' '+lastname

        personemail = request.args.get('name')
        pathway = request.args.get('pathway')

        if pathway == 'None':

            return redirect(url_for('enroll'))

        else:

            rows = db.execute("SELECT * from people WHERE pathwayEnrolled = ? AND email = ?", pathway, personemail)

            pathwayprogress = db.execute("SELECT * FROM pathwayprogress WHERE email = ? AND completed = ? AND pathwayName = ?", personemail, 1, pathway)
            pathwayremaining = db.execute("SELECT * FROM pathwayprogress WHERE email = ? AND completed = ? AND pathwayName = ?", personemail, 0, pathway)

            return render_template("progress.html", FullName = fullname, pathwayprogress = pathwayprogress, pathwayremaining = pathwayremaining, rows = rows)

@app.route("/stagecomplete", methods=["GET", "POST"])
@login_required
def stagecomplete():

    if request.method == "GET":

        info = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
        username = info[0]['email']
        firstname = info[0]['firstname']
        lastname = info[0]['lastname']
        companymail = info[0]['companymail']
        fullname = firstname+' '+lastname

        personemail = request.args.get('name')
        pathway = request.args.get('pathwayname')
        pathwaystage = request.args.get('pathwaystage')

        datetoday = (datetime.datetime.today().strftime ('%d'))+" / "+(datetime.datetime.today().strftime ('%m'))+" / "+(datetime.datetime.today().strftime ('%Y'))

        db.execute("UPDATE pathwayprogress SET datecompleted = ?, completed = 1 WHERE email = ? AND stagenumber = ? AND pathwayName = ?", datetoday, personemail, pathwaystage, pathway)

        #calculation of percentage complete
        stagenumber = db.execute("SELECT stagenumber from pathwaystages WHERE pathwayName = ? ORDER BY stagenumber DESC", pathway)
        numberofstages = int(stagenumber[0]['stagenumber'])
        completed = db.execute("SELECT * FROM pathwayprogress WHERE email = ? AND pathwayName = ? AND completed = 1", personemail, pathway)
        pathwaypercent = int(100 * (len(completed) / numberofstages) )

        db.execute("UPDATE people SET pathwayEnrolledPosition = ?, pathwayEnrolledProgress = ?,  pathwayEnrolledPositionDate = ? WHERE email = ?", pathwaystage, pathwaypercent, datetoday, personemail)

        rows = db.execute("SELECT * from people WHERE pathwayEnrolled = ? AND email = ?", pathway, personemail)

        pathwayprogress = db.execute("SELECT * FROM pathwayprogress WHERE email = ? AND completed = ? AND pathwayName = ?", personemail, 1, pathway)
        pathwayremaining = db.execute("SELECT * FROM pathwayprogress WHERE email = ? AND completed = ? AND pathwayName = ?", personemail, 0, pathway)

        return render_template("progress.html", FullName = fullname, pathwayprogress = pathwayprogress, pathwayremaining = pathwayremaining, rows = rows)

@app.route("/upload", methods=['POST', "GET"])
@login_required
def upload():

    if request.method == 'GET':

        info = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
        username = info[0]['email']
        firstname = info[0]['firstname']
        lastname = info[0]['lastname']
        company = info[0]['company']
        email = info[0]['email']
        companymail = info[0]['companymail']
        fullname = firstname + ' ' + lastname

        return render_template("upload.html", FullName = fullname)

    else:

        info = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
        username = info[0]['email']
        firstname = info[0]['firstname']
        lastname = info[0]['lastname']
        company = info[0]['company']
        email = info[0]['email']
        companymail = info[0]['companymail']
        fullname = firstname + ' ' + lastname

        # get the uploaded file
        uploaded_file = request.files['file']
        if uploaded_file.filename != '':
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], uploaded_file.filename)
            # set the file path
            uploaded_file.save(file_path)
            # save the file
        pathwayName = request.form.get("pathwayName")
        email = username
        pathwayDescription = request.form.get("pathwayDescription")

        if (request.form.get("publicShare") != None):
            share = 'True'
        else:
            share = 'False'

        #Upload pathway to pathways db
        db.execute("INSERT INTO pathways (pathwayName, pathwayDescription, email, companymail, share, enrolled) VALUES (?, ?, ?, ?, ?, '0')", pathwayName, pathwayDescription, email, companymail, share)

        with open(file_path, newline='') as csvfile:
        #csvfile = request.files['file']
            reader = csv.DictReader(csvfile)
            #data = [row for row in reader]
            for row in reader:
                print(row)
                stagenumber = row['stage']
                stagecontent = row['content']
                stagenotes = row['notes']
                stageowner = row['owner']
                #Upload pathwaystage to db
                db.execute("INSERT INTO pathwaystages (pathwayName, email, stagenumber, stagecontent, stageowner, stagenotes) VALUES (?, ?, ?, ?, ?, ?)", pathwayName, email, stagenumber, stagecontent, stageowner, stagenotes)

        rows = db.execute("SELECT DISTINCT * from pathwaystages WHERE pathwayName = ? AND email is ?", pathwayName, email)

        return render_template("finishpathway.html", rows = rows, pathwayName = pathwayName)

@app.route("/report", methods=['POST', "GET"])
@login_required
def report():

    if request.method == 'GET':

        info = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
        username = info[0]['email']
        firstname = info[0]['firstname']
        lastname = info[0]['lastname']
        company = info[0]['company']
        email = info[0]['email']
        companymail = info[0]['companymail']
        fullname = firstname + ' ' + lastname

        people = db.execute("SELECT * FROM people WHERE pdm = ?", username)
        pathway = db.execute("SELECT * FROM pathways WHERE email = ?", username)

        return render_template("report.html", FullName = fullname, people = people, pathway = pathway)

    else:

        info = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
        username = info[0]['email']
        firstname = info[0]['firstname']
        lastname = info[0]['lastname']
        company = info[0]['company']
        email = info[0]['email']
        companymail = info[0]['companymail']
        fullname = firstname + ' ' + lastname

        choicename = request.form.get("nameexport")
        if choicename == "none":
            pass
        elif choicename == "allpeople":
            reportname = 'allpeople'
            rows = db.execute("SELECT * FROM people WHERE pdm = ?", username)
        else:
            reportname = choicename
            rows = db.execute("SELECT * FROM people WHERE email = ? AND pdm = ?", choicename, username)

        choicepathway = request.form.get("pathwayexport")
        if choicepathway == "none":
            pass
        elif choicepathway == "allpathways":
            reportname = choicepathway
            rows = db.execute("SELECT * FROM Pathways WHERE email = ?", username)
        else:
            reportname = choicepathway
            rows = db.execute("SELECT * FROM pathwaystages WHERE email = ? AND pathwayName = ?", username, choicepathway)

        filename = 'files/'+firstname+lastname+'_report_'+str(datetime.datetime.today().strftime ('%d%m%Y'))+'_'+reportname+'.csv'

        df = pd.DataFrame(rows)
        df.to_csv('static/files/export.csv')

        return render_template("report.html", FullName = fullname)

@app.route("/delete", methods=["GET"])
@login_required
def delete():

    if request.method == 'GET':

        info = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
        username = info[0]['email']
        firstname = info[0]['firstname']
        lastname = info[0]['lastname']
        company = info[0]['company']
        email = info[0]['email']
        companymail = info[0]['companymail']
        fullname = firstname + ' ' + lastname
        id = request.args.get('id')

        if id == 'enroll':

            personemail = request.args.get('name')
            pathway = request.args.get('pathwayname')

            daysin = 0

            rows = db.execute("SELECT * from people WHERE pathwayEnrolled = ? AND email = ?", pathway, personemail)

            db.execute("DELETE FROM pathwayprogress WHERE pathwayName = ? AND email =?", pathway, personemail)
            db.execute("UPDATE people SET pathwayEnrolledDate = NULL, pathwayEnrolled = NULL, pathwayEnrolledPosition = NULL, pathwayEnrolledProgress = NULL,  pathwayEnrolledPositionDate = NULL WHERE email = ?", personemail)
            db.execute("UPDATE pathways SET enrolled = enrolled - 1 WHERE pathwayNAME = ? AND email = ?", pathway, username)

            deleted = ('Removed from '+pathway)

            return render_template("/delete.html", FullName = fullname, deleted = deleted)

        elif id == 'person':

            personemail = request.args.get('name')
            db.execute("DELETE FROM people WHERE email = ? AND pdm =?", personemail, username)
            deleted = ( +' removed')

            return render_template("/delete.html", FullName = fullname, deleted = deleted)

        else:

            pathway = request.args.get('pathway')
            db.execute("DELETE FROM pathways WHERE pathwayName = ? AND email = ?", pathway, username)

            return render_template("/delete.html", FullName = fullname, deleted = pathway)


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():

    if request.method == "GET":

        info = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])

        firstname = info[0]['firstname']
        lastname = info[0]['lastname']
        email = info[0]['email']
        company = info[0]['company']
        jobrole = info[0]['jobrole']
        fullname = firstname + ' ' + lastname

        return render_template('profile.html',  firstname = firstname, lastname = lastname, email = email, company = company, jobrole = jobrole, FullName = fullname)

    else:

        return render_template('update.html')

@app.route("/updatefields", methods=["GET", "POST"])
@login_required
def updatefields():

    if request.method == "GET":

        info = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
        username = info[0]['email']
        firstname = info[0]['firstname']
        lastname = info[0]['lastname']

        personemail = request.args.get('name')

        fullname = firstname + ' ' + lastname

        rows = db.execute("SELECT DISTINCT * FROM people WHERE email = ?", personemail)

        return render_template("updatefields.html", Fullname = fullname, rows = rows)

    else:

        info = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
        username = info[0]['email']
        firstname = info[0]['firstname']
        lastname = info[0]['lastname']
        fullname = firstname + ' ' + lastname

        personmobile = request.form.get("mobile")
        personemail = request.form.get("email")
        personbam = request.form.get("bam")
        personhistory = request.form.get("history")
        personexemployeddeal = request.form.get("exemployeddeal")
        personexemployeddealexpiry = request.form.get("exemployeddealexpiry")
        personbusinessWrittenPreviousMonth = request.form.get("businessWrittenPreviousMonth")
        personbusinessWrittenYearToDate = request.form.get("businessWrittenYearToDate")

        db.execute("UPDATE people SET mobile = ?, email = ?, bam = ?, history = ?, exEmployedDeal = ?, exEmployedDealExpiry = ?, businessWrittenPreviousMonth = ?, businessWrittenYearToDate = ? WHERE pdm = ?", personmobile, personemail, personbam, personhistory, personexemployeddeal, personexemployeddealexpiry, personbusinessWrittenPreviousMonth, personbusinessWrittenYearToDate, username)

        rows = db.execute("SELECT DISTINCT * FROM people WHERE email = ?", personemail)

        return render_template("viewperson.html", Fullname = fullname, rows = rows)

if __name__ == '__main__':
    app.run(debug=True)
