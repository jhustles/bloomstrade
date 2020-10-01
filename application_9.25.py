import os
import datetime
from cs50 import SQL
# import sqlite3 as sl
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd
from config import API_KEY

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

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)**
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")
# con = sl.connect("finance.db", check_same_thread=False)

# Make sure API key is set - assuming you uploaded it into the os environment
# if not os.environ.get("API_KEY"):
#     raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required #We're saying the user must be logged to use this
def index():
    """Show portfolio of stocks"""


    return apology("TODO")


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    # Read in from the Results Object (search results from Quote) - make it global variable
    # This buy route should only be for estimating, not producting a quote as well.
    # Will need to store the results of this in a global variable as well or append to a list the total estimated amount
    # Use the estimated amount and post to Porfolio and Trasaction History table (queries and create the tables)
    # Use SQL to sum up total transactions: total buys & Sells grouped by date, stock ticker, number of shares, price, and total amount booked
    # For the portfolio table, only display place if more than zero


    searchCounter = 0
    current_datetime = datetime.datetime.now().strftime("%c")
    results = db.execute("SELECT username, cash FROM users WHERE id = :username", username=session["user_id"]) #[0]["username"]
    username = results[0]["username"]
    availableCash = f'${results[0]["cash"]:,.2f}'
    tickerInput = request.form.get("tickerInput")
    currentSearchHistory = []
    searchResultsHistory = []
    

    sharesInput = request.form.get("sharesInput")
    if sharesInput == None:
        sharesInput = 0
    # global currentTicker = tickerInput


    if request.method == "GET":
        return render_template("buy.html", username=username, availableCash=availableCash, current_datetime=current_datetime)
    else: # else if POST
        if searchCounter == 0:
            # first Search / POST
            quote = lookup(tickerInput)
            searchCounter += 1

        elif searchCounter > 0 and tickerInput == None:
            # Second Search / Post and after
            # quote = lookup(currentSearchHistory[-1])
            pass

        else:
            #Scenario where searchCounter is Greater 1, and ticker input is NOT NONE
            quote = lookup(tickerInput)
            searchCounter += 1
        
        # LookUp symbol to ensure it's valid on POST
        
        # if not lookup(tickerInput):
        #     message = "Invalid Ticker Symbol. Please try another."
        #     return message

        # Increment the search counter for a successful search
        # searchCounter += 1
        # print(result)

        # Perhaps make this one a global variable. Access it on the buy page
        results = {
            'companyName' : quote["name"],
            'price' : quote["price"],
            'latestPrice' : f'${quote["price"]:,.2f}', #latestPrice
            'symbol' : f'Ticker: {quote["symbol"]}',
            'bidPrice' : f'${quote["bidPrice"]:,.2f}',
            'askPrice' : f'${quote["askPrice"]:,.2f}',
            'week52High' : f'${quote["week52High"]:,.2f}',
            'week52Low' : f'${quote["week52Low"]:,.2f}',
            'marketCap' : f'{quote["marketCap"]:,}',
            'volume' : f'{quote["iexVolume"]:,}',
            'avgTotalVolume' : f'{quote["avgTotalVolume"]:,}',
            'primaryExchange' : quote["primaryExchange"]
            }
        searchResultsHistory.append(results) # access: searchResultsHistory[-1].results.symbol
        

        if tickerInput != None and searchCounter > 0:
            currentSearchHistory.append(tickerInput)

        
        if int(sharesInput) >= 1:
            estimatedTotal = int(searchResultsHistory[-1]['price']) * int(sharesInput)
        elif sharesInput == None:
            estimatedTotal = "$0.00"
        elif sharesInput == 0:
            estimatedTotal = int(searchResultsHistory[-1]['price']) * 0
            estimatedTotal = f'${estimatedTotal:,.2f}'
        else:
            return render_template("buy.html", message="Please enter in a valid quantity for estimates. ")

        return render_template("buy.html",username=username,
                                            current_datetime=current_datetime,
                                            availableCash=availableCash,
                                            companyName=searchResultsHistory[-1]['companyName'],
                                            price=searchResultsHistory[-1]['latestPrice'],
                                            symbol=searchResultsHistory[-1]['symbol'],
                                            bidPrice=searchResultsHistory[-1]['bidPrice'],
                                            askPrice=searchResultsHistory[-1]['askPrice'],
                                            sharesInput=sharesInput,
                                            estimatedTotal=estimatedTotal,
                                            week52High=searchResultsHistory[-1]['week52High'],
                                            week52Low=searchResultsHistory[-1]['week52Low'],
                                            marketCap=searchResultsHistory[-1]['marketCap'],
                                            volume=searchResultsHistory[-1]['volume'],
                                            avgTotalVolume=searchResultsHistory[-1]['avgTotalVolume'],
                                            primaryExchange=searchResultsHistory[-1]['primaryExchange']
                                            ,currentSearchHistory=currentSearchHistory[-1]
                                            , searchCounter=searchCounter
                                            )
    
    return apology("TODO")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    return apology("TODO")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    username = request.form.get("username")
    password = request.form.get("password")

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        # if not request.form.get("username"):
        if not username:
            return apology("must provide username", 403)

        # Ensure password was submitted
        # elif not request.form.get("password"):
        elif not password:
            return apology("must provide password", 403)

        # Query database for username
        # Original with cs50
        rows = db.execute("SELECT * FROM users WHERE username = :username", username=username)
        
        # JG's
        # c = con.cursor()
        # rows = c.execute("SELECT * FROM users WHERE username = ?", username=request.form.get("username"))
        ############

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], password):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    current_datetime = datetime.datetime.now().strftime("%c")
    results = db.execute("SELECT username, cash FROM users WHERE id = :username", username=session["user_id"]) #[0]["username"]
    username = results[0]["username"]
    availableCash = f'${results[0]["cash"]:,.2f}'

    if request.method == "GET":
        return render_template("quote.html", username=username, availableCash=availableCash, current_datetime=current_datetime)
    else: # else if post
        ticker = request.form.get("ticker")
        quote = lookup(ticker)
        # print(result)

        companyName = quote["name"]
        price = f'${quote["price"]:,.2f}' #latestPrice
        symbol = f'Ticker: {quote["symbol"]}'
        bidPrice = f'${quote["bidPrice"]:,.2f}'
        askPrice = f'${quote["askPrice"]:,.2f}'
        week52High = f'${quote["week52High"]:,.2f}'
        week52Low = f'${quote["week52Low"]:,.2f}'
        marketCap = f'{quote["marketCap"]:,}'
        volume = f'{quote["iexVolume"]:,}'
        avgTotalVolume = f'{quote["avgTotalVolume"]:,}'
        primaryExchange = quote["primaryExchange"]

##########
        if request.form.get("buyQuantity") == None:
            buyQuantity = 0.00
        else:
            buyQuantity = request.form.get("buyQuantity")
            buyQuantity = int(buyQuantity)

        # if request.form.get("sellQuantity") == None:
        #     sellQuantity = 0.00
        # else:
        #     sellQuantity = int(request.form.get("sellQuantity"))

        # sellQuantity = int(request.form.get("sellQuantity"))
        # buyQuantity = int(request.form.get("buyQuantity"))
        # buyEstimate = f'${buyQuantity * price}'
        # # sellEstimate = f'${(int(sellQuantity) * price)}'

        # if buyQuantity  0:
        #     return render_template("apology.html", message="You may only have either a Buy Quantity or Sell Quantity, not both!")

#######
        return render_template("quote.html",username=username,
                                            current_datetime=current_datetime,
                                            availableCash=availableCash,
                                            companyName=companyName,
                                            price=price,
                                            symbol=symbol,
                                            bidPrice=bidPrice,
                                            askPrice=askPrice,
                                            week52High=week52High,
                                            week52Low=week52Low,
                                            marketCap=marketCap,
                                            volume=volume,
                                            avgTotalVolume=avgTotalVolume,
                                            primaryExchange=primaryExchange
                                            #,buyEstimate=buyEstimate, #######
                                            # sellEstimate=sellEstimate ########
                                            )

    return redirect("/quote")

    # return apology("TODO")
    


@app.route("/register", methods=["GET", "POST"])
def register():
    first_name = request.form.get("firstName")
    last_name = request.form.get("lastName")
    username = request.form.get("username")
    password = request.form.get("password")
    password_confirmation = request.form.get("passwordConfirm")

    """Register user"""
    if request.method == "GET": #Render the register.html page
        return render_template("register.html", message="")

    else: # else if, you're already on the page, and want to submit results back to the API, use method = "POST"
        if not first_name:
            return render_template("register.html", message="First name is required.")
        
        if not last_name:
            return render_template("register.html", message="Last name is required.")
        
        if not username:
            return render_template("register.html", message="Username is required.")
        
        if not password:
            return render_template("register.html", message="Password is required.")

        if not password_confirmation:
            return render_template("register.html", message="We must reconfirm your password, or we cannot proceed.")

        if password != password_confirmation:
            return render_template("register.html", message="Your passwords must match before we proceed.")
            
        # Check for Duplicate username
        username_result = db.execute("SELECT username FROM users WHERE username = :username", username=request.form.get("username"))
        if len(username_result) >= 1:
            return render_template("register.html", message="Sorry this username is already taken.")

        else:
            hash_pass = generate_password_hash(password)
            db.execute("INSERT INTO users (username, hash) VALUES(:username, :hash)", username=username, hash=hash_pass)
            db.execute("INSERT INTO names (first_name, last_name) VALUES (:first_name, :last_name)", first_name=first_name, last_name=last_name)
            return render_template("login.html", message="Account was successfully created. Please login now.")


    # **Remember: finish inserting all fields into SQLite3 db

    # replace this with the old version. Go to: CS50 IDE
    # c = con.cursor()
    # c.execute("INSERT INTO users (username, hash) VALUES (?, ?)", insert_login_info)
    # c.execute("INSERT INTO names (first_name, last_name) VALUES (?, ?)", insert_full_name)



    # return apology("TODO")
    return redirect("/")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    return apology("TODO")


# From SQLite3 website
# def dict_factory(cursor, row):
#     d = {}
#     for idx, col in enumerate(cursor.description):
#         d[col[0]] = row[idx]
#     return d


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)



app.run()