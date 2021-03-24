# @Author: johnhaigh
# @Date:   2020-12-29T17:16:37+00:00
# @Last modified by:   johnhaigh
# @Last modified time: 2021-03-17T20:03:13+00:00

#A web based application to track the onboarding of new recruits


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
import csv
import random
import pandas as pd
import shutil

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
        db = SQL("sqlite:///onboard.db")
        firstname = request.form.get("firstname")
        lastname = request.form.get("lastname")
        email = request.form.get("email")
        password = request.form.get("password")
        company = request.form.get("company")
        jobrole = request.form.get("jobrole")
        hashpassword = generate_password_hash(password)
        companymail = email.split("@")[1]

        # Create table for users
        db.execute("CREATE TABLE IF NOT EXISTS users ('id' integer PRIMARY KEY NOT NULL, 'email' text NOT NULL, 'firstname' text NOT NULL,'lastname' text NOT NULL, 'password' text NOT NULL, 'company' text NOT NULL, 'jobrole' text NOT NULL,'companymail' text NOT NULL)")

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

        db = SQL("sqlite:///onboard.db")
        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE email = :username", username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["password"], request.form.get("password")):
            return render_template('apology.html', message="invalid username and/or password", bodymessage = "invalid username and/or password")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]
        date = datetime.datetime.now()

        #Store when user last logged in
        db.execute("UPDATE users SET lastlogin = ?", date)

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

        db = SQL("sqlite:///onboard.db")

        info = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
        username = info[0]['email']
        firstname = info[0]['firstname']
        lastname = info[0]['lastname']
        companymail = info[0]['companymail']
        fullname = firstname + ' ' + lastname

        daytoday = int(datetime.datetime.today().strftime ('%d'))
        monthtoday = int(datetime.datetime.today().strftime ('%m'))
        yeartoday = int(datetime.datetime.today().strftime ('%Y'))

        # Iterate over people in database
        i = 0
        rows = db.execute("SELECT * FROM people WHERE pdm = ?", username)
        for row in rows:

            dateenrolled = rows[i]['pathwayEnrolledDate']
            # Are they enrolled in anything?
            if dateenrolled != None:

                x = dateenrolled.split("/", 3)
                yearenrolled = (int(x[2]))
                monthenroleld = (int(x[1]))
                dayenrolled = (int(x[0]))

                d0 = date(yearenrolled, monthenroleld, dayenrolled)
                d1 = date(yeartoday, monthtoday, daytoday)
                delta = d1 - d0
                daysin = delta.days

            #Check if the person has been appointed
            if rows[i]['appointed'] == 1:

                #Calculate days since appointment
                dateappointed = rows[i]['dateappointed']
                x = dateappointed.split("/", 3)
                year = (int(x[2]))
                month = (int(x[1]))
                day = (int(x[0]))

                d0 = date(year, month, day)
                d1 = date(yeartoday, monthtoday, daytoday)
                delta = d1 - d0
                dayssinceappointment = delta.days

                #If progress is 0% then skip over the calculation for estimated completion
                progressnumber = int(rows[i]['pathwayEnrolledProgress'])
                if progressnumber == 0:
                    estcompletion = 'Not yet known'
                    score = 0

                else:

                    #Based on rate of progress estimate a completion date
                    daysleft = int((daysin / progressnumber) * 100)
                    estcompletion = d0 + datetime.timedelta(days=daysleft)

                    #And prepare it to be inserted into the database
                    j = (str(estcompletion).split("-",3))
                    year = (j[0])
                    month = (j[1])
                    day = (j[2])
                    estcompletion = day + " / " + month + " / " + year

                    #Set score
                    score = round((progressnumber / daysin), 2)

            else:

                #Calculate for people that have not yet been appointed
                dayssinceappointment = 0
                score = 0
                estcompletion = 'Not yet known'

            db.execute("UPDATE people SET daysinpathway = ?, estcompletion = ?, score = ?, dayssinceappointment = ? WHERE email = ?", daysin, estcompletion, score, dayssinceappointment, rows[i]['email'])
            i = i+1

        #Prepare data for charting on page V1
        #Harvest info from DB
        rows = db.execute("SELECT * from people WHERE pdm = ? AND appointed = 1", username)

        #Declare lists to format data
        newlist = []
        percent = []
        datalabels = []
        bubblecolour = []
        days = []

        #Fill lists with information
        i = 0
        while i < len(rows):
            percent.append(rows[i]['pathwayEnrolledProgress'])
            days.append(rows[i]['dayssinceappointment'])
            datalabels.append(rows[i]['firstname']+' '+rows[i]['lastname'])
            if (int(rows[i]['businessWrittenYearToDate']) < (int(rows[i]['dayssinceappointment']) * 165)):
                bubblecolour.append('tomato')
            else:
                bubblecolour.append('DodgerBlue')
            i = i+1

        #Combine lists into scatterdata variable
        for h, w in zip(percent, days):
            newlist.append({'x': h, 'y': w})
        scatterdata = str(newlist).replace('\'', '')

        # Create variables to hold info on appointed and pre-appointment people

        appointed = db.execute("SELECT * FROM people WHERE pdm = ? AND appointed = 1", username)
        preappointment = db.execute("SELECT * FROM people WHERE pdm = ? AND appointed = 0", username)

        return render_template("people.html", firstname = firstname, FullName = fullname, companymail=companymail, appointed = appointed, preappointment = preappointment, data=scatterdata, bubblecolour = bubblecolour, labels = datalabels)

    elif request.method == "POST":

        db = SQL("sqlite:///onboard.db")

        info = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
        username = info[0]['email']
        firstname = info[0]['firstname']
        lastname = info[0]['lastname']
        companymail = info[0]['companymail']

        fullname = firstname + ' ' + lastname

        if request.form.get('sort') == 'score':

            appointed = db.execute("SELECT * FROM people WHERE pdm = ? AND appointed = 1 ORDER BY score DESC", username)
            preappointment = db.execute("SELECT * FROM people WHERE pdm = ? AND appointed = 0", username)

        if request.form.get('sort') == 'days':

            appointed = db.execute("SELECT * FROM people WHERE pdm = ? AND appointed = 1 ORDER BY dayssinceappointment DESC", username)
            preappointment = db.execute("SELECT * FROM people WHERE pdm = ? AND appointed = 0 ORDER BY daysinpathway DESC", username)

        if request.form.get('sort') == 'progress':

            appointed = db.execute("SELECT * FROM people WHERE pdm = ? AND appointed = 1 ORDER BY pathwayEnrolledProgress DESC", username)
            preappointment = db.execute("SELECT * FROM people WHERE pdm = ? AND appointed = 0 ORDER BY pathwayEnrolledProgress DESC", username)

        if request.form.get('sort') == 'name':

            appointed = db.execute("SELECT * FROM people WHERE pdm = ? AND appointed = 1 ORDER BY lastname", username)
            preappointment = db.execute("SELECT * FROM people WHERE pdm = ? AND appointed = 0 ORDER BY lastname", username)

        if request.form.get('sort') == 'pathway':

            appointed = db.execute("SELECT * FROM people WHERE pdm = ? AND appointed = 1 ORDER BY pathwayEnrolled", username)
            preappointment = db.execute("SELECT * FROM people WHERE pdm = ? AND appointed = 0  ORDER BY pathwayEnrolled", username)

        #Prepare data for charting on page V1
        #Harvest info from DB
        rows = db.execute("SELECT * from people WHERE pdm = ? AND appointed = 1", username)

        #Declare lists to format data
        newlist = []
        percent = []
        datalabels = []
        bubblecolour = []
        days = []

        #Fill lists with information
        i = 0
        while i < len(rows):
            percent.append(rows[i]['pathwayEnrolledProgress'])
            days.append(rows[i]['daysinpathway'])
            datalabels.append(rows[i]['firstname']+' '+rows[i]['lastname'])
            if (int(rows[i]['businessWrittenYearToDate']) < (int(rows[i]['dayssinceappointment']) * 165)):
                bubblecolour.append('tomato')
            else:
                bubblecolour.append('DodgerBlue')
            i = i+1

        print (bubblecolour)
        #Combine lists into scatterdata variable
        for h, w in zip(percent, days):
            newlist.append({'x': h, 'y': w})
        scatterdata = str(newlist).replace('\'', '')

        return render_template("people.html", firstname = firstname, FullName = fullname, companymail=companymail, appointed = appointed, preappointment = preappointment, data=scatterdata, bubblecolour = bubblecolour, labels = datalabels)


@app.route("/newperson", methods=["GET", "POST"])
@login_required
def newperson():

    if request.method == "POST":

        db = SQL("sqlite:///onboard.db")

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
        minincome = request.form.get("minincome")
        personexemployeddealexpiry = request.form.get("exemployeddealexpiry")
        personbusinessWrittenPreviousMonth = request.form.get("businessWrittenPreviousMonth")
        personbusinessWrittenYearToDate = request.form.get("businessWrittenYearToDate")
        practice = request.form.get('practice')
        appointed = 0
        #db.execute("""CREATE TABLE IF NOT EXISTS people ('id' integer PRIMARY KEY NOT NULL, 'firstname' text NOT NULL, 'lastname' text NOT NULL, 'mobile' text NOT NULL, 'email' text NOT NULL, 'pdm' text NOT NULL, 'bam' text, 'pathwayEnrolled' text, 'pathwayEnrolledDate' text, 'pathwayEnrolledPosition' text, 'pathwayEnrolledProgress' integer,  'pathwayEnrolledPositionDate' text, 'history' text, 'exEmployedDeal' text, 'exEmployedDealExpiry' text, 'businessWrittenPreviousMonth' integer, 'businessWrittenYearToDate'  integer, 'daysinpathway' integer, 'estcompletion' text, 'score' int, 'minincome' int, 'dateappointed' text, 'practice' text)""")

        db.execute("INSERT INTO people (firstname, lastname, mobile, email, pdm, bam, history, exEmployedDeal, exEmployedDealExpiry, businessWrittenPreviousMonth, businessWrittenYearToDate, minincome, practice, appointed, pathwayEnrolled) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", personfirstname, personlastname, personmobile, personemail, username, personbam, personhistory, personexemployeddeal, personexemployeddealexpiry, personbusinessWrittenPreviousMonth, personbusinessWrittenYearToDate, minincome, practice, appointed, 'None')

        rows = db.execute("SELECT * FROM people WHERE pdm = ? AND email = ?", username, personemail)

        return render_template("viewperson.html", rows = rows, FullName = fullname)

    else:

        db = SQL("sqlite:///onboard.db")

        info = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
        username = info[0]['email']
        firstname = info[0]['firstname']
        lastname = info[0]['lastname']
        companymail = info[0]['companymail']
        fullname = firstname+''+lastname

        rows = db.execute("SELECT pathwayName from pathways WHERE email = ?  ORDER by pathwayName", username)

        return render_template("newperson.html", FullName = fullname, rows = rows)

@app.route("/viewperson", methods=["GET", "POST"])
@login_required
def viewperson():

    if request.method == "GET":

        db = SQL("sqlite:///onboard.db")

        info = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
        username = info[0]['email']
        firstname = info[0]['firstname']
        lastname = info[0]['lastname']

        personemail = request.args.get('name')

        fullname = firstname + ' ' + lastname

        rows = db.execute("SELECT DISTINCT * FROM people WHERE email = ?", personemail)

        if rows[0]['appointed'] == 1:

            targetnumber = int(rows[0]['dayssinceappointment']) * 165
            resultnumber = int(rows[0]['businessWrittenYearToDate']) - targetnumber

            if resultnumber < 0:
                resultstring = '£'+str(resultnumber) + ' below target'
                style = 'red'
            else:
                resultstring = '+£'+str(resultnumber) + ' above target'
                style = 'green'

            return render_template("viewperson.html", FullName = fullname, rows = rows, targetnumber = targetnumber, result = resultstring, style = style)

        else:

            return render_template("viewperson.html", FullName = fullname, rows = rows)

@app.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():

    if request.method == "GET":

        db = SQL("sqlite:///onboard.db")

        info = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
        username = info[0]['email']
        firstname = info[0]['firstname']
        lastname = info[0]['lastname']

        fullname = firstname + ' ' + lastname

        rows = db.execute("SELECT * FROM people WHERE pdm = ?", username)
        print(rows)

        if rows != None:

            daytoday = int(datetime.datetime.today().strftime ('%d'))
            monthtoday = int(datetime.datetime.today().strftime ('%m'))
            yeartoday = int(datetime.datetime.today().strftime ('%Y'))
            i = 0
            daysin = {}

            #Update length of time they've been enrolled in the pathway

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

                    if daysin != 0:

                        #Based on rate of progress estimate a completion date

                        progressnumber = int(rows[i]['pathwayEnrolledProgress'])
                        score = round((progressnumber / daysin), 2)

                    # They've not in a pathway more than a day so score is 0
                    else:
                        score = 0

                # They're not in a pathway so score is 0
                else:
                    score = 0
                    daysin = 'None'

                db.execute("UPDATE people SET daysinpathway = ?, score = ? WHERE email = ?", daysin, score, rows[i]['email'])
                i = i+1

            #Prepare data for Progress / Time chart
            #Harvest info from DB
            rows = db.execute("SELECT * from people WHERE pdm = ? AND appointed = 1", username)

            #Declare lists to format data
            newlist = []
            percent = []
            datalabels = []
            days = []

            #Fill lists with information
            i = 0
            while i < len(rows):
                percent.append(rows[i]['pathwayEnrolledProgress'])
                days.append(rows[i]['daysinpathway'])
                datalabels.append(rows[i]['firstname']+' '+rows[i]['lastname'])
                i = i+1

            #Combine lists into scatterdata variable
            for h, w in zip(percent, days):
                newlist.append({'x': h, 'y': w})
            scatterdata = str(newlist).replace('\'', '')

            #Data preperation for charts of people appointed = 1

            rows = db.execute("SELECT * FROM people where pdm = ? AND appointed = 1", username)

            longestinpathwaydaysin = []
            targetperformance = []
            score = []
            incomedata = []
            totalbusiness = 0
            names = []

            i = 0
            while i < len(rows):

                #Data preperation for Table 3 Dashboard - Longest in pathway
                longestinpathwaydaysin.append(rows[i]['daysinpathway'])
                #Data preperation for Table 4 Dashboard - Earnings performance against target
                #If it's their first day of appointment, skip the calculation
                print(rows[i])
                if rows[i]['dayssinceappointment'] == None:
                    result = 0
                else:
                    target = (rows[i]['dayssinceappointment'] * 165 )
                    result = (rows[i]['businessWrittenYearToDate'] - target)
                targetperformance.append(result)
                #Data preperation for Table 5 Dashboard - Top People by score
                score.append(rows[i]['score'])
                #Data preperation for Chart1 Dashboard - Total Business Written
                incomedata.append(rows[i]['businessWrittenYearToDate'])
                totalbusiness = totalbusiness + rows[i]['businessWrittenYearToDate']
                names.append(rows[i]['firstname'] + ' ' + rows[i]['lastname'])

                i = i+1

            #Data preperation for chart - Distribution of people

            pathwaynames = []
            pathwaynumbers = []
            rows = db.execute("SELECT * from pathways where email = ?", username)

            i = 0
            while i < len(rows):

                pathwaynames.append(rows[i]['pathwayName'])
                pathwaynumbers.append(rows[i]['enrolled'])
                i = i+1

            #Data preperation for pre-appoint charts

            stepsremain = []
            stepsremainnames = []
            rows = db.execute("SELECT * FROM people where pdm = ? AND appointed = 0", username)

            i = 0
            while i < len(rows):
                if rows[i]['pathwayEnrolledProgress'] != None:
                    #Steps remaining until appointemnt
                    stepsremainnames.append(rows[i]['firstname'] + ' ' + rows[i]['lastname'])
                    stepsremain.append(rows[i]['pathwayEnrolledProgress'])

                i = i+1

            # Set colours for charts
            colours = ["#1D8269", "#F2FF26","#4376A8","#85FFF3","#2594F5", "#7BB7F5", "#3B5875","#75301A", "#145A75", "#FFFA61", "#AC32B3", "#36A89D","#85FFF3","#1A7559", "#4376A8", "#7BB7F5", "#3B5875", "#1D8269", "#75301A", "#145A75", "#FFFA61", "#AC32B3"]

            return render_template("dashboard.html", FullName = fullname, pathwayNumber = pathways, incomedata = incomedata, totalbusiness = totalbusiness, pathwaynames = pathwaynames, pathwaynumbers = pathwaynumbers, longestinpathwaydaysin = longestinpathwaydaysin, targetperformance = targetperformance, score = score, scatterdata=scatterdata, labels = datalabels, stepsremainnames = stepsremainnames, stepsremain = stepsremain, colours=colours, names = names)

        else:

            return render_template("dashboard.html", FullName = fullname)

@app.route("/pathways", methods=["GET", "POST"])
@login_required
def pathways():
    if request.method == "GET":

        db = SQL("sqlite:///onboard.db")

        info = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
        username = info[0]['email']
        firstname = info[0]['firstname']
        lastname = info[0]['lastname']
        company = info[0]['company']
        email = info[0]['email']

        fullname = firstname + ' ' + lastname

        # Add user to database, if user already exists say eror username already exists
        pathways = db.execute("SELECT * FROM pathways WHERE email = ? ORDER BY pathwayName", email)

        return render_template("pathways.html", firstname = firstname, company=company, FullName = fullname, pathways = pathways)

@app.route("/newpathway", methods=["GET", "POST"])
@login_required
def newpathway():
    if request.method == "GET":

        db = SQL("sqlite:///onboard.db")

        info = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
        username = info[0]['email']
        firstname = info[0]['firstname']
        lastname = info[0]['lastname']
        company = info[0]['company']
        fullname = firstname + ' ' + lastname

        return render_template("newpathway.html", firstname = firstname, company=company, FullName = fullname)

    else:

        db = SQL("sqlite:///onboard.db")

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

        #db.execute("CREATE TABLE IF NOT EXISTS pathways ('id' integer PRIMARY KEY NOT NULL, 'pathwayName' text NOT NULL, 'pathwayDescription' text NOT NULL, 'share' text NOT NULL, 'email' text NOT NULL, 'companymail' text NOT NULL, 'enrolled' integer, 'appointmentstage' text)")

        # Add pathway to database, if user already exists say eror pathway already exists
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

        db = SQL("sqlite:///onboard.db")

        info = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
        username = info[0]['email']
        firstname = info[0]['firstname']
        lastname = info[0]['lastname']
        company = info[0]['company']
        email = info[0]['email']
        fullname = firstname + ' ' + lastname

        pathway = db.execute("SELECT * from pathways WHERE email =?", email)

        pathwayName = pathway[0][pathwayName]
        pathwayDescription = pathway[0][pathwayDescription]

        return render_template("addsteps.html", pathwayName = pathwayName, FullName = fullname, pathwayDescription = pathwayDescription)

@app.route("/finishpathway", methods=["GET", "POST"])
@login_required
def finishpathway():

    if request.method == "POST":

        db = SQL("sqlite:///onboard.db")

        info = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
        username = info[0]['email']
        firstname = info[0]['firstname']
        lastname = info[0]['lastname']
        company = info[0]['company']
        email = info[0]['email']
        companymail = info[0]['companymail']

        pathwayName = request.form.get("pathwayName")

        #database = db.execute("CREATE TABLE IF NOT EXISTS pathwaystages ('id' integer PRIMARY KEY NOT NULL, 'pathwayName' text NOT NULL, 'email' text NOT NULL, 'stagenumber' integer NOT NULL, 'stagecontent' text NOT NULL, 'stageowner' text, 'stagenotes' text)")

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
            #Find the point that a person becomes 'appointed'
            if req[stagenumberstring] == 'Appointed':
                #Record at white point a person becomes 'appointed'
                db.execute('UPDATE pathways SET appointmentstage = ? WHERE pathwayName = ?', stagenumber, pathwayName)

            i = (i+1)

        rows = db.execute("SELECT DISTINCT * from pathwaystages WHERE pathwayName = ? AND email is ?", pathwayName, email)

        return render_template("finishpathway.html", rows = rows, pathwayName = pathwayName)

    else:

        return render_template("pathways.html")

@app.route("/viewpathway", methods=["GET", "POST"])
@login_required
def viewpathway():

    if request.method == "GET":

        db = SQL("sqlite:///onboard.db")

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

        db = SQL("sqlite:///onboard.db")

        info = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
        username = info[0]['email']
        firstname = info[0]['firstname']
        lastname = info[0]['lastname']
        companymail = info[0]['companymail']
        fullname = firstname+' '+lastname

        people = db.execute("SELECT * FROM people WHERE pdm = ? AND pathwayEnrolled = ?", username, 'None')
        pathways = db.execute("SELECT * FROM pathways WHERE email = ? ORDER BY pathwayName", username)

        print(people)
        return render_template("enroll.html", people = people, pathways = pathways, FullName = fullname)

    else:

        db = SQL("sqlite:///onboard.db")

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

        print(person)
        personemail = person[0]['email']

        datetoday = (datetime.datetime.today().strftime ('%d'))+" / "+(datetime.datetime.today().strftime ('%m'))+" / "+(datetime.datetime.today().strftime ('%Y'))

        #Check to see if user already enrolled in a pathway

        row = db.execute("SELECT * from people WHERE email = ? and pdm = ?", personemail, username)
        pathwaystring = str(row[0]['pathwayEnrolled'])

        if pathwaystring == 'None':

            daysin = 1
            db.execute("UPDATE people SET pathwayEnrolledDate = ?, pathwayEnrolled = ?, pathwayEnrolledPosition = ?, pathwayEnrolledProgress = ?, pathwayEnrolledPositionDate = ?, daysinpathway = 1, estcompletion = ?, score = 0 WHERE email = ?", datetoday, pathway , 0 , 0 , datetoday, 'Not yet known', personemail)
            db.execute("UPDATE pathways SET enrolled = enrolled + 1 WHERE pathwayNAME = ? AND email = ?", pathway, username)
            rows = db.execute("SELECT * FROM people where email = ?", personemail)
            pathwaystages = db.execute("SELECT * FROM pathwaystages where pathwayName = ?", pathway)
            position = int(rows[0]['pathwayEnrolledPosition'])

            #db.execute("CREATE TABLE IF NOT EXISTS pathwayprogress ('email' text NOT NULL, 'pathwayName' text NOT NULL, 'stagenumber' int, 'stagecontent' text, 'stageowner' text, 'stagenotes' text, 'datecompleted' text, 'completed' int ) ")
            stagenumber = 0
            for i in pathwaystages:
                db.execute("INSERT INTO pathwayprogress (email, pathwayName, stagenumber, stagecontent, stageowner, stagenotes, completed) VALUES (?,?,?,?,?,?,?)", personemail, pathway, pathwaystages[stagenumber]['stagenumber'], pathwaystages[stagenumber]['stagecontent'], pathwaystages[stagenumber]['stageowner'], pathwaystages[stagenumber]['stagenotes'], 0)
                stagenumber = stagenumber + 1

            pathwayprogress = db.execute("SELECT * FROM pathwayprogress WHERE email = ? AND completed = ? AND pathwayName = ?", personemail, 1, pathway)
            pathwayremaining = db.execute("SELECT * FROM pathwayprogress WHERE email = ? AND completed = ? AND pathwayName = ?", personemail, 0, pathway)

            return render_template("progress.html", FullName = fullnameuser, pathwayprogress = pathwayprogress, pathwayremaining = pathwayremaining, position = position, rows = rows, pathwaystages = pathwaystages, daysin = daysin)

        else:

            print(pathway)
            bodymessage = "User already enrolled in: " + row[0]['pathwayEnrolled']
            return render_template('apology.html', FullName = fullnameuser, bodymessage = bodymessage)

@app.route("/progress", methods=["GET", "POST"])
@login_required
def progress():

    if request.method == "GET":

        db = SQL("sqlite:///onboard.db")

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

        db = SQL("sqlite:///onboard.db")

        info = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
        username = info[0]['email']
        firstname = info[0]['firstname']
        lastname = info[0]['lastname']
        companymail = info[0]['companymail']
        fullname = firstname+' '+lastname

        personemail = request.args.get('name')
        pathway = request.args.get('pathwayname')
        pathwaystage = request.args.get('pathwaystage')

        #Which stage triggers appointment status in the pathway
        appointmentstage = db.execute("SELECT appointmentstage from pathways WHERE pathwayName = ? AND email = ?", pathway, username)

        # Create the variable for todays date
        datetoday = (datetime.datetime.today().strftime ('%d'))+" / "+(datetime.datetime.today().strftime ('%m'))+" / "+(datetime.datetime.today().strftime ('%Y'))

        #Check if stage is being marked complete or rolled back. ID in href on button is tested here.
        if request.args.get('id') == 'complete':

            #Check to see if that task was the stage that meant they were 'appointed'
            if appointmentstage[0]['appointmentstage'] == pathwaystage:
                db.execute("UPDATE people SET dateappointed = ?, appointed = 1 WHERE email = ? AND pdm = ?", datetoday, personemail, username)

            #Update completed stages in database
            db.execute("UPDATE pathwayprogress SET datecompleted = ?, completed = 1 WHERE email = ? AND stagenumber = ? AND pathwayName = ?", datetoday, personemail, pathwaystage, pathway)

        elif request.args.get('id') == 'delete':

            #Update completed stages in database
            db.execute("UPDATE pathwayprogress SET datecompleted = ?, completed = 0 WHERE email = ? AND stagenumber = ? AND pathwayName = ?", 'Not complete', personemail, pathwaystage, pathway)

        rows = db.execute("SELECT * FROM people WHERE pdm = ? AND email = ?", username, personemail)

        if rows[0]['appointed'] == 1:

            #Calculation of percentage complete
            #Percentage metrics are not counted until someone has been appointed, however they still are in the same pathway.
            #Therefore any calculation of percentage complete must include a deduction of the stages required to get to 'appointment'
            stagenumber = db.execute("SELECT stagenumber from pathwaystages WHERE pathwayName = ? ORDER BY stagenumber DESC", pathway)
            appointment = db.execute("SELECT * from pathways WHERE pathwayName = ?", pathway)
            appointmentstage = int(appointment[0]['appointmentstage'])
            numberofstages = int(stagenumber[0]['stagenumber'])
            completed = db.execute("SELECT * FROM pathwayprogress WHERE email = ? AND pathwayName = ? AND completed = 1", personemail, pathway)
            pathwaypercent = int(100 * (((len(completed))-appointmentstage) / (numberofstages-appointmentstage)))

            db.execute("UPDATE people SET pathwayEnrolledPosition = ?, pathwayEnrolledProgress = ?,  pathwayEnrolledPositionDate = ?, pathwayEnrolledPosition = ? WHERE email = ?", pathwaystage, pathwaypercent, datetoday, pathwaystage, personemail)

        else:

            #Calculation of stages remaining before appointment
            appointment = db.execute("SELECT * from pathways WHERE pathwayName = ?", pathway)
            appointmentstage = int(appointment[0]['appointmentstage'])
            progress = int(appointment[0]['appointmentstage']) - int(pathwaystage)
            db.execute("UPDATE people SET pathwayEnrolledPosition = ?, pathwayEnrolledProgress = ?,  pathwayEnrolledPositionDate = ?, pathwayEnrolledPosition = ? WHERE email = ?", pathwaystage, progress, datetoday, pathwaystage, personemail)


        rows = db.execute("SELECT * from people WHERE pathwayEnrolled = ? AND email = ?", pathway, personemail)

        pathwayprogress = db.execute("SELECT * FROM pathwayprogress WHERE email = ? AND completed = ? AND pathwayName = ?", personemail, 1, pathway)
        pathwayremaining = db.execute("SELECT * FROM pathwayprogress WHERE email = ? AND completed = ? AND pathwayName = ?", personemail, 0, pathway)

        return render_template("progress.html", FullName = fullname, pathwayprogress = pathwayprogress, pathwayremaining = pathwayremaining, rows = rows)


@app.route("/upload", methods=['POST', "GET"])
@login_required
def upload():

    if request.method == 'GET':

        db = SQL("sqlite:///onboard.db")

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

        db = SQL("sqlite:///onboard.db")

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
                if row['content'] == 'Appointed':
                    #Record at white point a person becomes 'appointed'
                    db.execute('UPDATE pathways SET appointmentstage = ? WHERE pathwayName = ?', stagenumber, pathwayName)
                #Upload pathwaystage to db
                db.execute("INSERT INTO pathwaystages (pathwayName, email, stagenumber, stagecontent, stageowner, stagenotes) VALUES (?, ?, ?, ?, ?, ?)", pathwayName, email, stagenumber, stagecontent, stageowner, stagenotes)

        rows = db.execute("SELECT DISTINCT * from pathwaystages WHERE pathwayName = ? AND email is ?", pathwayName, email)

        return render_template("finishpathway.html", rows = rows, pathwayName = pathwayName)

@app.route("/report", methods=['POST', "GET"])
@login_required
def report():

    if request.method == 'GET':

        db = SQL("sqlite:///onboard.db")

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

        db = SQL("sqlite:///onboard.db")

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

        #filename = 'files/'+firstname+lastname+'_report_'+str(datetime.datetime.today().strftime ('%d%m%Y'))+'_'+reportname+'.csv'

        people = db.execute("SELECT * FROM people WHERE pdm = ?", username)
        pathway = db.execute("SELECT * FROM pathways WHERE email = ?", username)

        df = pd.DataFrame(rows)
        link = 'static/files/'+ 'report_' + email +'.csv'
        df.to_csv(link)

        return render_template("report.html", FullName = fullname, link = link, people = people, pathway = pathway)

@app.route("/delete", methods=["GET"])
@login_required
def delete():

    if request.method == 'GET':

        db = SQL("sqlite:///onboard.db")

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

            db.execute("DELETE FROM pathwayprogress WHERE email = ?", personemail)
            db.execute("UPDATE people SET pathwayEnrolledDate = NULL, pathwayEnrolled = ?, pathwayEnrolledPosition = NULL, pathwayEnrolledProgress = NULL,  pathwayEnrolledPositionDate = NULL, score = 0, daysinpathway = Null, estcompletion = Null, dateappointed = NULL, dayssinceappointment = Null, appointed = 0 WHERE email = ?", 'None',personemail)
            db.execute("UPDATE pathways SET enrolled = enrolled - 1 WHERE pathwayNAME = ? AND email = ?", pathway, username)

            deleted = ('Removed from '+pathway)

            return render_template("/delete.html", FullName = fullname, deleted = deleted)

        elif id == 'person':

            personemail = request.args.get('name')
            db.execute("DELETE FROM people WHERE email = ? AND pdm =?", personemail, username)
            deleted = (personemail +' removed')

            return render_template("/delete.html", FullName = fullname, deleted = deleted)

        else:

            pathway = request.args.get('pathway')
            db.execute("DELETE FROM pathways WHERE pathwayName = ? AND email = ?", pathway, username)

            return render_template("/delete.html", FullName = fullname, deleted = pathway)


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():

    if request.method == "GET":

        db = SQL("sqlite:///onboard.db")

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

        db = SQL("sqlite:///onboard.db")

        info = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
        username = info[0]['email']
        firstname = info[0]['firstname']
        lastname = info[0]['lastname']

        personemail = request.args.get('name')

        fullname = firstname + ' ' + lastname

        rows = db.execute("SELECT DISTINCT * FROM people WHERE email = ?", personemail)

        lanes = db.execute("SELECT pathwayName FROM pathways WHERE email = ? ORDER by pathwayName", username)

        return render_template("updatefields.html", FullName = fullname, rows = rows, lanes = lanes)

    else:

        db = SQL("sqlite:///onboard.db")

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
        minincome = request.form.get("minincome")

        db.execute("UPDATE people SET mobile = ?, email = ?, bam = ?, history = ?, exEmployedDeal = ?, exEmployedDealExpiry = ?, businessWrittenPreviousMonth = ?, businessWrittenYearToDate = ?, minincome = ? WHERE pdm = ? AND email = ?", personmobile, personemail, personbam, personhistory, personexemployeddeal, personexemployeddealexpiry, personbusinessWrittenPreviousMonth, personbusinessWrittenYearToDate, minincome, username, personemail)

        rows = db.execute("SELECT DISTINCT * FROM people WHERE email = ?", personemail)

        targetnumber = int(rows[0]['dayssinceappointment']) * 165
        resultnumber = int(rows[0]['businessWrittenYearToDate']) - targetnumber

        if resultnumber < 0:
            resultstring = '£'+str(resultnumber) + ' below target'
            style = 'red'
        else:
            resultstring = '+£'+str(resultnumber) + ' above target'
            style = 'green'

        return render_template("viewperson.html", FullName = fullname, rows = rows, targetnumber = targetnumber, result = resultstring, style = style)

@app.route("/updatedates", methods=["GET", "POST"])
@login_required
def updatedates():

    #Updates the completion dates of pathway stages

    if request.method == "GET":

        db = SQL("sqlite:///onboard.db")

        info = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
        username = info[0]['email']
        firstname = info[0]['firstname']
        lastname = info[0]['lastname']
        fullname = firstname + ' ' + lastname

        id = request.args.get('dates')
        personemail = request.args.get('name')
        pathway = request.args.get('pathwayname')

        rows = db.execute("SELECT * from people WHERE pathwayEnrolled = ? AND email = ?", pathway, personemail)

        pathwayprogress = db.execute("SELECT * FROM pathwayprogress WHERE email = ? AND completed = ? AND pathwayName = ?", personemail, 1, pathway)

        return render_template("updatedates.html", FullName = fullname, pathwayprogress = pathwayprogress,rows = rows)

    if request.method == "POST":

        db = SQL("sqlite:///onboard.db")

        info = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
        username = info[0]['email']
        firstname = info[0]['firstname']
        lastname = info[0]['lastname']
        fullname = firstname + ' ' + lastname

        id = request.args.get('dates')
        personemail = request.args.get('name')
        pathway = request.args.get('pathwayname')
        rows = db.execute("SELECT * from people WHERE email = ?", personemail)

        req = request.form
        numberofentries = (len(req) - 1 )
        newenrolleddate = req['enrolleddate']
        if rows[0]['appointed'] == 1:
            newappointmentdate = req['appointed']
            db.execute("UPDATE people SET pathwayEnrolledDate = ?, dateappointed = ? WHERE email = ? AND pdm = ?", newenrolleddate, newappointmentdate, personemail, username)
        else:
            db.execute("UPDATE people SET pathwayEnrolledDate = ? WHERE email = ? AND pdm = ?", newenrolleddate, personemail, username)
        i = 1

        while i < numberofentries:

            number = str(i)
            datechange = req[number]
            stagenumber = i
            db.execute("UPDATE pathwayprogress SET datecompleted = ? WHERE stagenumber = ? AND email = ? AND pathwayName = ?", datechange, stagenumber, personemail, pathway)
            print(number)
            i = (i+1)

        rows = db.execute("SELECT * from people WHERE pathwayEnrolled = ? AND email = ?", pathway, personemail)

        pathwayprogress = db.execute("SELECT * FROM pathwayprogress WHERE email = ? AND completed = ? AND pathwayName = ?", personemail, 1, pathway)
        pathwayremaining = db.execute("SELECT * FROM pathwayprogress WHERE email = ? AND completed = ? AND pathwayName = ?", personemail, 0, pathway)

        return render_template("progress.html", FullName = fullname, pathwayprogress = pathwayprogress, pathwayremaining = pathwayremaining, rows = rows)

@app.route("/backup", methods=["GET"])
def backup():

    # Create a backup of the onboard.db file

    if request.method == "GET":

        db = SQL("sqlite:///onboard.db")

        import shutil

        original = r'onboard.db'
        target = r'static/files/onboard.db'

        shutil.copyfile(original, target)

        link = "static/files/onboard.db"

    return render_template("backup.html", link = link)


@app.route("/view", methods=["GET"])
@login_required
def view():

    db = SQL("sqlite:///onboard.db")

    #Start of the management level views for the app

    info = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
    username = info[0]['email']
    firstname = info[0]['firstname']
    lastname = info[0]['lastname']
    companymail = info[0]['companymail']
    fullname = firstname+' '+lastname

    rows = db.execute("SELECT * from people WHERE pdm = (SELECT email FROM users WHERE companymail = ?) GROUP BY pdm", companymail)


    return render_template('view.html', rows = rows)


if __name__ == '__main__':
    app.run(debug=True)
