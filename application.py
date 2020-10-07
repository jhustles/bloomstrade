import os
from datetime import datetime
import time
from cs50 import SQL
# import sqlite3 as sl
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import apology, login_required, lookup, usd
# from config import API_KEY

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Global Variables that will be used between different pages
global current_datetime
current_datetime = datetime

global buyEstimatesArray
buyEstimatesArray = []

global sellEstimatesArray
sellEstimatesArray = []

global portfolioBalances
portfolioBalances = []

global portfolioSymbols


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
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route("/", methods=["GET"])
@login_required #We're saying the user must be logged to use this
def index():
    """Show portfolio of stocks"""
    items = db.execute("WITH indexSetup AS ( SELECT u.username, c.symbol,  c.name, t.c_id, t.ordertype, SUM(t.quantity) as quantity, SUM(t.quantity * t.price) AS total FROM transactions t JOIN companies c ON t.c_id = c.id JOIN users u ON t.user_id = u.id WHERE user_id =:user_id GROUP BY  u.username, c.symbol, c.name, t.c_id, t.ordertype), sell as (SELECT username, symbol,  name, c_id, SUM(quantity) as quantity , SUM(total) AS costBasis FROM indexSetup WHERE ordertype = 'SELL' GROUP BY 1, 2, 3, 4), buy AS ( SELECT username, symbol,  name, c_id, SUM(quantity) as quantity , SUM(total) AS costBasis FROM indexSetup WHERE ordertype = 'BUY' GROUP BY 1, 2, 3, 4) ,results AS(SELECT username, symbol,  name, c_id, COALESCE(SUM(b.quantity - s.quantity), b.quantity) as quantity, COALESCE(SUM(b.costBasis - s.CostBasis), b.costBasis)  AS total FROM buy b LEFT JOIN sell s USING(username, symbol, name, c_id) GROUP BY 1, 2, 3, 4 ORDER BY name) SELECT * FROM results WHERE quantity > 0", user_id=session["user_id"])
    
    userCash = db.execute("SELECT username, cash FROM users WHERE id = :user_id", user_id=session["user_id"]) #[0]["username"]
    availableCash = userCash[0]["cash"]

    if request.method =="GET" and not items:
        return render_template("index.html", username=userCash[0]['username'],message="Portfolio is currently empty", availableCash=usd(availableCash), user_id=session["user_id"], current_datetime=current_datetime.now().strftime("%c"), totalInvestments=usd(0))
    
    else: # if GET and items
        # Set the username key to the actual username value
        portfolioSymbols = [i['symbol'] for i in items]
        portfolioQuantities = [i['quantity'] for i in items]
        costBasis = [i['total'] for i in items]
        cnames = [i['name'] for i in items]
        marketPrices = [lookup(i)['price'] for i in portfolioSymbols]
        time.sleep(2) # wait for results.

        portfolioBalances = []
        totalInvestments = 0
        for i in range(len(portfolioSymbols)):
            stock = {}
            stock['symbol'] = portfolioSymbols[i]
            stock['name'] = cnames[i]
            stock['shares'] = "{:,}".format(portfolioQuantities[i])
            stock['costBasis'] = usd(costBasis[i] )
            stock['marketValue'] = usd(portfolioQuantities[i]*marketPrices[i])
            # totalInvestments += float(costBasis[i]) # costBasis
            totalInvestments += float(portfolioQuantities[i]*marketPrices[i])
            # stock['gainLoss'] = usd(float(stock['marketValue']) - float(stock['costBasis']))
            portfolioBalances.append(stock)

        return render_template("index.html",
                            username=session["username"],
                            items=portfolioBalances,
                            current_datetime=current_datetime.now().strftime("%c"),
                            availableCash=usd(availableCash),
                            totalInvestments=usd(totalInvestments)
        )


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    global searchCounter
    global currentSearchHistory
    global searchResultsHistory

    searchCounter = 0
    currentSearchHistory = []
    searchResultsHistory = []

    results = db.execute("SELECT username, cash FROM users WHERE id = :user_id", user_id=session["user_id"]) #[0]["username"]
    availableCash = results[0]["cash"]
    tickerInput = request.form.get("tickerInput")

    if request.method == "GET":
        #current_datetime = datetime.now().strftime("%c")
        return render_template("quote1.html",
                                username=results[0]['username'],
                                availableCash=usd(availableCash),
                                current_datetime=current_datetime.now().strftime("%c")
        )
    else: # else if POST
        if searchCounter == 0:
            # first Search / POST
            quote = lookup(tickerInput)
            currentSearchHistory.append(tickerInput)

        elif searchCounter > 0 and tickerInput == None:
            # Second Search / Post and after
            # quote = lookup(currentSearchHistory[-1])
            pass # keep going!

        else:
            #Scenario where searchCounter is Greater 1, and ticker input is NOT NONE
            quote = lookup(tickerInput)
            currentSearchHistory.append(tickerInput)

        # LookUp symbol to ensure it's valid on POST
        if not lookup(tickerInput):
            message = "Invalid Ticker Symbol. Please try another."
            #current_datetime = datetime.now().strftime("%c")
            return render_template("quote1.html", username=results[0]['username'], availableCash=usd(availableCash), current_datetime=current_datetime.now().strftime("%c"), message=message)

    # Increment the search counter for a successful search
        searchCounter += 1
        #current_datetime = datetime.now().strftime("%c")
        lookUpResults = {
            'search_id' : searchCounter,
            'username' : results[0]['username'],
            'availableCash' : availableCash,
            'current_datetime': current_datetime.now().strftime("%c"),
            'companyName' : quote["name"],
            'latestPrice' : quote["price"], #latestPrice
            'symbol' : quote["symbol"],
            'bidPrice' : quote["price"],
            'askPrice' : quote["price"],
            'week52High' : quote["week52High"],
            'week52Low' : quote["week52Low"],
            'marketCap' : quote["marketCap"],
            'volume' : quote["iexVolume"],
            'avgTotalVolume' : quote["avgTotalVolume"],
            'primaryExchange' : quote["primaryExchange"]
            }
        searchResultsHistory.append(lookUpResults)

        return render_template("buy.html",username=results[0]['username'],
                                            current_datetime=searchResultsHistory[-1]['current_datetime'],
                                            availableCash=usd(results[0]['cash']),
                                            companyName=searchResultsHistory[-1]['companyName'].upper(),
                                            latestPrice=usd(searchResultsHistory[-1]['latestPrice']),
                                            symbol=searchResultsHistory[-1]['symbol'],
                                            bidPrice=usd(searchResultsHistory[-1]['bidPrice']),
                                            askPrice=usd(searchResultsHistory[-1]['askPrice']),
                                            week52High=usd(searchResultsHistory[-1]['week52High']),
                                            week52Low=usd(searchResultsHistory[-1]['week52Low']),
                                            marketCap=usd(searchResultsHistory[-1]['marketCap']),
                                            volume=searchResultsHistory[-1]['volume'],
                                            avgTotalVolume=searchResultsHistory[-1]['avgTotalVolume'],
                                            primaryExchange=searchResultsHistory[-1]['primaryExchange'].upper()
                                            ,currentSearchHistory=currentSearchHistory[-1]
        )
    #return redirect("/quote")


@app.route("/buyEstimator", methods=["POST"]) # after quote this displays the buy.html using this route
@login_required
def buyEstimator():
    # Scenario 1) first time, buyEStimateArray is Empty, and need to vet the sharesINput
    if request.method == "POST": # Here still on BUY.HTML, and user inputs into sharesInput
        global estimatedTotal # will pass this into the buy function | will need to differentiate for buy / sell 
        global sharesInput
        sharesInput = request.form.get("sharesInput")

        # At this point you're on the buy html with a quote/ route, and you already have a quote for a stock
        # IN THIS STEP, YOU WANT TO ESTIMATE a a quote, which requires a sharesInput
        if not sharesInput: # if there's nothing in the sharesInput or buyEstimatesArray
            # and the user clicks "Estimate", let user know to:
            message = 'To buy, you will first need to perform an estimate. Enter value in the "Buy Quantity".'
            #current_datetime = datetime.now().strftime("%c")
            return render_template("buy.html",username=session["username"],
                                                current_datetime=current_datetime.now().strftime("%c"),
                                                availableCash=usd(searchResultsHistory[-1]['availableCash']),
                                                companyName=searchResultsHistory[-1]['companyName'].upper(),
                                                latestPrice=usd(searchResultsHistory[-1]['latestPrice']),
                                                symbol=searchResultsHistory[-1]['symbol'],
                                                bidPrice=usd(searchResultsHistory[-1]['bidPrice']),
                                                askPrice=usd(searchResultsHistory[-1]['askPrice']),
                                                # sharesInput=sharesInput,
                                                # estimatedTotal=estimatedTotal,
                                                week52High=usd(searchResultsHistory[-1]['week52High']),
                                                week52Low=usd(searchResultsHistory[-1]['week52Low']),
                                                marketCap=searchResultsHistory[-1]['marketCap'],
                                                volume=searchResultsHistory[-1]['volume'],
                                                avgTotalVolume=searchResultsHistory[-1]['avgTotalVolume'],
                                                primaryExchange=searchResultsHistory[-1]['primaryExchange'].upper()
                                                ,currentSearchHistory=currentSearchHistory[-1]
                                                ,searchCounter=searchCounter
                                                ,message=message
            )
        # else if there is a sharesInput or something in the buyEsimtateArray
        # 1) vet the sharesInput 2) populate the buyEstimateArray items and let user know, if execute is pressed, then
        # the most current item in the buyEstimateArray (which needs to be displayed) will be excuted
        # Store shareInput in a global variable for use in Execute Buy
        
        global estimateQuantity
        estimateQuantity = int(sharesInput)
        # these will vet the sharesInput for something valid
        if int(sharesInput) >= 1: # Optimal case: everythign is valid, then return the estimated total
            estimatedTotal = float(searchResultsHistory[-1]['latestPrice']) * int(sharesInput)

        elif sharesInput == None: #if shres's input is none just 
            estimatedTotal = 0.00

        elif sharesInput == 0:
            message = "Cannot estimate zero shares. "
            estimatedTotal = float(searchResultsHistory[-1]['latestPrice']) * 1

        else: # catch all - 
            message = 'Enter in a positive whole number for the quantity to produce an estimate.'
            return render_template("buyExecute.html",username=session["username"],
                                            current_datetime=current_datetime.now().strftime("%c"),
                                            availableCash=usd(searchResultsHistory[-1]['availableCash']),
                                            companyName=searchResultsHistory[-1]['companyName'].upper(),
                                            latestPrice=usd(searchResultsHistory[-1]['latestPrice']),
                                            symbol=searchResultsHistory[-1]['symbol'],
                                            bidPrice=usd(searchResultsHistory[-1]['bidPrice']),
                                            askPrice=usd(searchResultsHistory[-1]['askPrice']),
                                            week52High=usd(searchResultsHistory[-1]['week52High']),
                                            week52Low=usd(searchResultsHistory[-1]['week52Low']),
                                            marketCap=searchResultsHistory[-1]['marketCap'],
                                            volume=searchResultsHistory[-1]['volume'],
                                            avgTotalVolume=searchResultsHistory[-1]['avgTotalVolume'],
                                            primaryExchange=searchResultsHistory[-1]['primaryExchange'].upper()
                                            ,currentSearchHistory=currentSearchHistory[-1]
                                            ,searchCounter=searchCounter
                                            ,message=message
            )

        # After sharesInput has been validated, then calcuate / estimate
        if float(searchResultsHistory[-1]['availableCash']) < estimatedTotal:
            difference = estimatedTotal - float(searchResultsHistory[-1]['availableCash'])
            message = f"Insufficient funds. Balance is short: ${difference:,.2f} Please lower the amount of shares."
            return render_template("buyExecute.html",username=session["username"],
                                            current_datetime=current_datetime.now().strftime("%c"),
                                            availableCash=usd(searchResultsHistory[-1]['availableCash']),
                                            companyName=searchResultsHistory[-1]['companyName'].upper(),
                                            latestPrice=usd(searchResultsHistory[-1]['latestPrice']),
                                            symbol=searchResultsHistory[-1]['symbol'],
                                            bidPrice=usd(searchResultsHistory[-1]['bidPrice']),
                                            askPrice=usd(searchResultsHistory[-1]['askPrice']),
                                            week52High=usd(searchResultsHistory[-1]['week52High']),
                                            week52Low=usd(searchResultsHistory[-1]['week52Low']),
                                            marketCap=searchResultsHistory[-1]['marketCap'],
                                            volume=searchResultsHistory[-1]['volume'],
                                            avgTotalVolume=searchResultsHistory[-1]['avgTotalVolume'],
                                            primaryExchange=searchResultsHistory[-1]['primaryExchange'].upper()
                                            ,currentSearchHistory=currentSearchHistory[-1]
                                            ,searchCounter=searchCounter
                                            ,message=message
            )
        else:
            difference = float(searchResultsHistory[-1]['availableCash']) - estimatedTotal
            message = f"Estimate: {estimateQuantity} shares at current prices, the balance remaining will be: {usd(difference)}. "

        # Store all the details of the buyEstimate in an object
        #current_datetime = datetime.now().strftime("%c")
        buyEstimate = {
            'datetime': current_datetime.now().strftime("%c"),
            'price' : float(searchResultsHistory[-1]['latestPrice']),
            'quantity' : estimateQuantity,
            'total' : estimatedTotal,
            'username': searchResultsHistory[-1]['username'],
            'companyName': searchResultsHistory[-1]['companyName'].upper(),
            'symbol': searchResultsHistory[-1]['symbol'].upper(),
            'primaryExchange' : searchResultsHistory[-1]['primaryExchange'].upper(),
            'search_id': searchResultsHistory[-1]['search_id']
        }
        buyEstimatesArray.append(buyEstimate)

        #current_datetime = datetime.now().strftime("%c")
        message = f'Clicking "Execute Order" will immediate place the order for: {buyEstimatesArray[-1]["quantity"]} Shares of {buyEstimatesArray[-1]["symbol"]} for {usd(buyEstimatesArray[-1]["total"])}. '
        return render_template("buyExecute.html", username=searchResultsHistory[-1]['username'],
                                            current_datetime=current_datetime.now().strftime("%c"),
                                            availableCash=usd(searchResultsHistory[-1]['availableCash']),
                                            companyName=searchResultsHistory[-1]['companyName'].upper(),
                                            latestPrice=usd(searchResultsHistory[-1]['latestPrice']),
                                            symbol=searchResultsHistory[-1]['symbol'],
                                            bidPrice=usd(searchResultsHistory[-1]['bidPrice']),
                                            askPrice=usd(searchResultsHistory[-1]['askPrice']),
                                            estimatedQuantity=int(buyEstimatesArray[-1]['quantity']),
                                            estimatedTotal=usd(buyEstimatesArray[-1]['total']),
                                            buyEstimateSymbol=buyEstimatesArray[-1]['symbol'],
                                            week52High=usd(searchResultsHistory[-1]['week52High']),
                                            week52Low=usd(searchResultsHistory[-1]['week52Low']),
                                            marketCap=searchResultsHistory[-1]['marketCap'],
                                            volume=searchResultsHistory[-1]['volume'],
                                            avgTotalVolume=searchResultsHistory[-1]['avgTotalVolume'],
                                            primaryExchange=searchResultsHistory[-1]['primaryExchange'].upper()
                                            ,currentSearchHistory=currentSearchHistory[-1]
                                            ,searchCounter=searchCounter
                                            ,message=message
                                            # ,display=display
        )

@app.route("/buy", methods=["POST"]) #this will render on buyExcute.html with this buyRoute
@login_required
def buy(): 
    if request.method == "POST":
        #scenario: Post, Empty currentSharesInput, and NO ESTIMATES in the buyEstimatesArray
        # Result: return the buy.html
        #current_datetime = datetime.now().strftime("%c")
        currentPrice = lookup(searchResultsHistory[-1]['symbol'])['price']
        updatedTotal = float(currentPrice) * int(buyEstimatesArray[-1]['quantity'])

        if updatedTotal > float(searchResultsHistory[-1]['availableCash']):
            difference = updatedTotal - float(searchResultsHistory[-1]['availableCash'])
            message = f"Insufficient funds. Balance is short: ${difference:,.2f} Please lower the amount of shares."
            return render_template("buy.html",username=session["username"],
                                                current_datetime=current_datetime.now().strftime("%c"),
                                                availableCash=usd(searchResultsHistory[-1]['availableCash']),
                                                companyName=searchResultsHistory[-1]['companyName'].upper(),
                                                latestPrice=usd(searchResultsHistory[-1]['latestPrice']),
                                                symbol=searchResultsHistory[-1]['symbol'],
                                                bidPrice=usd(searchResultsHistory[-1]['bidPrice']),
                                                askPrice=usd(searchResultsHistory[-1]['askPrice']),
                                                # sharesInput=sharesInput,
                                                # estimatedTotal=estimatedTotal,
                                                week52High=usd(searchResultsHistory[-1]['week52High']),
                                                week52Low=usd(searchResultsHistory[-1]['week52Low']),
                                                marketCap=searchResultsHistory[-1]['marketCap'],
                                                volume=searchResultsHistory[-1]['volume'],
                                                avgTotalVolume=searchResultsHistory[-1]['avgTotalVolume'],
                                                primaryExchange=searchResultsHistory[-1]['primaryExchange'].upper()
                                                ,currentSearchHistory=currentSearchHistory[-1]
                                                ,searchCounter=searchCounter
                                                ,message=message
            )
        
        db.execute("INSERT INTO companies (symbol, name, exchange) VALUES(:symbol, :name, :exchange) EXCEPT SELECT symbol, name, exchange FROM companies WHERE symbol = :symbol",
            symbol=buyEstimatesArray[-1]['symbol'],
            name=buyEstimatesArray[-1]['companyName'],
            exchange=buyEstimatesArray[-1]['primaryExchange']
        )
        
        c_id = db.execute("SELECT id FROM companies WHERE symbol = :symbol", symbol=buyEstimatesArray[-1]['symbol'])[0]['id']
        #user_id = db.execute("SELECT id FROM users WHERE username = :username", username=buyEstimatesArray[-1]['username'])[0]['id']
        
        buyExecute_datetime = current_datetime.now().strftime("%c")
        db.execute("INSERT INTO transactions (datetime, ordertype, price, quantity, total, c_id, user_id) VALUES (:datetime, :orderType, :price, :quantity, :total, :c_id, :user_id)",
            datetime=buyExecute_datetime,
            orderType='BUY',
            # price=buyEstimatesArray[-1]['price'],
            price=currentPrice,
            quantity=buyEstimatesArray[-1]['quantity'],
            total=updatedTotal,
            c_id=c_id,
            user_id=session["user_id"]
        )

        trans_id = db.execute("SELECT trans_id FROM transactions WHERE user_id = :user_id ORDER BY datetime DESC LIMIT 1", user_id=session["user_id"])[0]['trans_id']

        debit = 0 # Debit will be for Sells to increase cash balance
        db.execute("INSERT INTO cash (datetime, debit, credit, user_id, trans_id) VALUES(:datetime, :debit, :credit, :user_id, :trans_id)",
            datetime=buyExecute_datetime,
            debit=debit,
            credit=updatedTotal, # Buying decreases cash
            user_id=session["user_id"],
            trans_id=trans_id
        )

        db.execute("UPDATE users SET cash = (SELECT TOTAL(debit - credit) AS balance FROM cash WHERE user_id = :user_id) ", user_id=session["user_id"])

        # #Give the most recent transaction details - limit 1
        confirmation = db.execute("SELECT t.ordertype, t.datetime, t.quantity, t.total, c.symbol, c.name FROM transactions t JOIN companies c ON t.c_id = c.id WHERE t.user_id = :user_id ORDER BY t.datetime DESC LIMIT 1", user_id=session["user_id"])
        ordertype = confirmation[0]['ordertype']
        datetime = confirmation[0]['datetime']
        quantity = confirmation[0]['quantity']
        total = confirmation[0]['total']
        symbol = confirmation[0]['symbol']
        companyName = confirmation[0]['name'] #companyName

        return render_template("confirmation.html", #display=buyEstimatesArray[-1]
                                                    c_id=c_id,
                                                    user_id=session["user_id"],
                                                    trans_id=trans_id,
                                                    ordertype=ordertype,
                                                    datetime=datetime,
                                                    quantity=quantity,
                                                    total=usd(total),
                                                    symbol=symbol,
                                                    companyName=companyName
        )


@app.route("/history", methods=["GET"])
@login_required
def history():
    """Show history of transactions"""
    if request.method == "GET":
        #refer to ERD for columns or print schema in the db
        items = db.execute("SELECT * from transactions t JOIN companies c ON t.c_id = c.id WHERE user_id=:user_id GROUP BY t.c_id, t.ordertype ORDER BY datetime DESC, t.c_id;", user_id=session["user_id"])

        return render_template("history.html",username=session["username"],
                                items=items,
                                current_datetime=current_datetime.now().strftime("%c")
        )


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""
    # Forget any user_id
    session.clear()

    username = request.form.get("username")
    password = request.form.get("password")

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted - if not request.form.get("username"):
        if not username:
            return apology("must provide username", 403)

        # Ensure password was submitted - elif not request.form.get("password"):
        elif not password:
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username", username=username)
        
        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], password):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]
        session["username"] = rows[0]["username"]

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


@app.route("/register", methods=["GET", "POST"])
def register():
    first_name = request.form.get("firstName")
    last_name = request.form.get("lastName")
    username = request.form.get("username")
    emailAddress = request.form.get("emailAddress")
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
            
        # Check for Duplicate username and email address
        username_result = db.execute("SELECT username FROM users WHERE username = :username", username=username)
        email_result = db.execute("SELECT email_address FROM names WHERE email_address = :emailAddress", emailAddress=emailAddress)
        if len(username_result) >= 1:
            return render_template("register.html", message="Sorry this username is already taken.")
        
        elif len(email_result) >= 1:
            return render_template("register.html", message="Sorry this email address is already taken. Perhaps you forogt your password?")
        
        else:
            hash_pass = generate_password_hash(password)
            db.execute("INSERT INTO users (username, hash) VALUES(:username, :hash)", username=username, hash=hash_pass)
            user_id = db.execute("SELECT id FROM users WHERE username = :username", username=username)[0]['id']
            db.execute("INSERT INTO names (first_name, last_name, email_address) VALUES (:first_name, :last_name, :emailAddress)", first_name=first_name, last_name=last_name, emailAddress=emailAddress)
            db.execute("INSERT INTO cash (datetime, debit, credit, trans_id, user_id) VALUES(:datetime, :debit, :credit, :trans_id, :user_id)",
                            datetime=current_datetime.now().strftime("%c"),
                            debit=10000,
                            credit=0,
                            trans_id='DEP',
                            user_id=user_id)
            return render_template("login.html", message="Account was successfully created. Please login now.")
    return redirect("/")

@app.route("/about", methods=["GET"])
def about():

    if request.method == "GET":
        return render_template("about.html")


@app.route("/sellEstimator", methods=["GET", "POST"])
@login_required
def sellEstimator():

    userCash = db.execute("SELECT username, cash FROM users WHERE id = :user_id", user_id=session["user_id"]) #[0]["username"]
    availableCash = userCash[0]["cash"]
    if request.method == "GET":
        counter = 0
        if counter == 0:
            try:
                items = db.execute("WITH indexSetup AS ( SELECT u.username, c.symbol,  c.name, t.c_id, t.ordertype, SUM(t.quantity) as quantity, SUM(t.quantity * t.price) AS total FROM transactions t JOIN companies c ON t.c_id = c.id JOIN users u ON t.user_id = u.id WHERE user_id =:user_id GROUP BY  u.username, c.symbol, c.name, t.c_id, t.ordertype), sell as (SELECT username, symbol,  name, c_id, SUM(quantity) as quantity , SUM(total) AS costBasis FROM indexSetup WHERE ordertype = 'SELL' GROUP BY 1, 2, 3, 4), buy AS ( SELECT username, symbol,  name, c_id, SUM(quantity) as quantity , SUM(total) AS costBasis FROM indexSetup WHERE ordertype = 'BUY' GROUP BY 1, 2, 3, 4) SELECT username, symbol,  name, c_id, COALESCE(SUM(b.quantity - s.quantity), b.quantity) as quantity, COALESCE(SUM(b.costBasis - s.CostBasis), b.costBasis)  AS total FROM buy b LEFT JOIN sell s USING(username, symbol, name, c_id) GROUP BY 1, 2, 3, 4 ORDER BY name", user_id=session["user_id"])
                # users = [i['username'] for i in items][0]
                global portfolioSymbols
                portfolioSymbols = [i['symbol'] for i in items]
                portfolioQuantities = [i['quantity'] for i in items]
                costBasis = [i['total'] for i in items]
                cnames = [i['name'] for i in items]
                marketPrices = [lookup(i)['price'] for i in portfolioSymbols]
                time.sleep(2)
            except Exception as e:
                print(e)

        if not items:
            return render_template("empty.html", availableCash=usd(availableCash), message="Portfolio is currently empty. No items to sell.")
        
        else: # data is available in the database, then gather it first and setup data structure
            for i in range(len(portfolioSymbols)):
                stock = {}
                stock['symbol'] = portfolioSymbols[i]
                stock['name'] = cnames[i]
                stock['shares'] = "{:,}".format(portfolioQuantities[i])
                stock['costBasis'] = usd(costBasis[i])
                stock['marketValue'] = usd(portfolioQuantities[i]*marketPrices[i])
                stock['username'] = session["username"]
                stock['user_id'] = session["user_id"]
                # stock['gainLoss'] = usd(float(stock['marketValue']) - float(stock['costBasis']))
                if stock in portfolioBalances:
                    pass # do not append if its already in the object
                else: # only want unique items
                    portfolioBalances.append(stock)
                    counter += 1

            return render_template("sell.html", username=portfolioBalances[-1]['username'], availableCash=usd(availableCash), items=portfolioBalances, current_datetime=current_datetime.now().strftime("%c"))

    else: # if request.method == "POST":
        # Need to be able to access these variables in the next page route /sell
        global sellEstimatedTotal # will pass this into the buy function | will need to differentiate for buy / sell 
        global sellSharesInput

        sellSymbol = request.form.get("sellSymbol").upper()
        sellSharesInput = request.form.get("sellSharesInput")

        # Scenarios for missing inputs for  POST-ing to sellEstimator
        if not sellSharesInput and not sellSymbol:
            message = "Estimating a sell order requires Ticker Symbol you own and number of shares. "
            return render_template("sell.html", username=portfolioBalances[-1]['username'], availableCash=usd(availableCash), items=portfolioBalances, current_datetime=current_datetime.now().strftime("%c"), message=message)

        if not sellSharesInput:
            message = "Estimating requires a whole quantity number. Enter a value in the Sell Quantity."
            return render_template("sell.html", username=portfolioBalances[-1]['username'], availableCash=usd(availableCash), items=portfolioBalances, current_datetime=current_datetime.now().strftime("%c"), message=message)

        if sellSymbol not in portfolioSymbols:
            message = "Enter in a valid stock symbol in your portfolio."
            return render_template("sell.html", username=portfolioBalances[-1]['username'], availableCash=usd(availableCash), items=portfolioBalances, current_datetime=current_datetime.now().strftime("%c"), message=message)
        
        # Store shareInput in a global variable for use in Execute Sell
        global sellEstimateQuantity
        sellEstimateQuantity = int(sellSharesInput)

        # Validate Shares to be greater than 1 and only a number
        if sellEstimateQuantity >= 1:
            sellEstimatedTotal = float(lookup(sellSymbol)['price'] * sellEstimateQuantity)
        # elif sellEstimateQuantity == 0:
        #     # sellEstimatedTotal = float(lookup(sellSymbol)['price']) * 0
        #     sellEstimatedTotal = 0.00
            # estimatedTotal = f'${estimatedTotal:,.2f}'
        else:
            message="Please enter in a valid quantity for estimates. "
            return render_template("sell.html", username=portfolioBalances[-1]['username'], availableCash=usd(availableCash), items=portfolioBalances, current_datetime=current_datetime.now().strftime("%c"), message=message)

        # Assuming quanitity is valid, loop thru the portfolioBalances, if symbol matches, return the quantity
        sharesOwned = 0
        for i in portfolioBalances:
            if i['symbol'] == sellSymbol:
                sharesOwned = int(i['shares'])

        if sellEstimateQuantity > sharesOwned:
            difference = sellEstimateQuantity - sharesOwned
            message = f"Cannot sell {difference} additional shares you do not own. Lower the amount of shares for an estimate."
            total = 0.00
            return render_template("sell.html", username=portfolioBalances[-1]['username'], availableCash=usd(availableCash), items=portfolioBalances, current_datetime=current_datetime.now().strftime("%c"), message=message, sellEstimateQuantity=sellEstimateQuantity, sellEstimatedTotal=usd(total))
        # Grab the stored variable if sellEstimateQuanitty passes, and store in a sell estimate object

        updatedSellQuote = lookup(sellSymbol)
        sellEstimate = {
            'datetime': current_datetime.now().strftime("%c"),
            'price' : updatedSellQuote['price'], #lookup here
            'quantity': sellEstimateQuantity,
            'total' : float(updatedSellQuote['price'] * sellEstimateQuantity),
            'companyName': updatedSellQuote['name'],
            'symbol': sellSymbol.upper(),
            'primaryExchange' : updatedSellQuote['primaryExchange'],
            'username' : session["username"],
            'availableCash': availableCash
        }
        sellEstimatesArray.append(sellEstimate)

        quantity = sellEstimatesArray[-1]['quantity']
        total = sellEstimatesArray[-1]['total']
        message = f'Clicking "Execute Order" will immediately place the following trade: {sellEstimatesArray[-1]["quantity"]} of {sellEstimatesArray[-1]["symbol"]} for {usd(sellEstimatesArray[-1]["total"])}. '
        
        return render_template("sellExecute.html", username=portfolioBalances[-1]['username'], availableCash=usd(availableCash), items=portfolioBalances, current_datetime=current_datetime.now().strftime("%c"), message=message, sellEstimateQuantity=quantity, sellEstimatedTotal=usd(total), sellEstimateSymbol=sellEstimatesArray[-1]['symbol'], latestPrice=sellEstimatesArray[-1]['price'])

@app.route("/sell", methods=["POST"])
@login_required
def sell():
    """Sell shares of stock"""
    if request.method == "POST":

        # If there's is a valid sellEstimate in the array, then execute:
        c_id = db.execute("SELECT id FROM companies WHERE symbol = :symbol", symbol=sellEstimatesArray[-1]['symbol'])[0]['id']
        sell_datetime = current_datetime.now().strftime("%c")
        db.execute("INSERT INTO transactions (datetime, ordertype, price, quantity, total, c_id, user_id) VALUES (:datetime, :orderType, :price, :quantity, :total, :c_id, :user_id)",
            datetime=sell_datetime,
            orderType='SELL',
            price=sellEstimatesArray[-1]['price'],
            quantity=(int(sellEstimatesArray[-1]['quantity'])),
            total=sellEstimatesArray[-1]['total'],
            c_id=c_id,
            user_id=session["user_id"] #global varible
        )

        trans_id = db.execute("SELECT trans_id FROM transactions WHERE user_id = :user_id ORDER BY datetime DESC LIMIT 1", user_id=session["user_id"])[0]['trans_id']

        credit = 0 # Debit will be for Sells to increase cash balance
        db.execute("INSERT INTO cash (datetime, debit, credit, user_id, trans_id) VALUES(:datetime, :debit, :credit, :user_id, :trans_id)",
            datetime=sell_datetime,
            debit=sellEstimatesArray[-1]['total'],
            credit=credit, # Buying decreases cash
            user_id=session["user_id"],
            trans_id=trans_id
        )

        db.execute("UPDATE users SET cash = (SELECT TOTAL(debit - credit) AS balance FROM cash WHERE user_id = :user_id) ", user_id=session["user_id"])

        # #Give the most recent transaction details - limit 1
        confirmation = db.execute("SELECT t.ordertype, t.datetime, t.quantity, t.total, c.symbol, c.name FROM transactions t JOIN companies c ON t.c_id = c.id WHERE t.user_id = :user_id ORDER BY t.datetime DESC LIMIT 1", user_id=session["user_id"])
        ordertype = confirmation[0]['ordertype']
        datetime = confirmation[0]['datetime']
        quantity = confirmation[0]['quantity']
        total = confirmation[0]['total']
        symbol = confirmation[0]['symbol']
        companyName = confirmation[0]['name'] #companyName

        return render_template("confirmation.html", #display=buyEstimatesArray[-1]
                                                    c_id=c_id,
                                                    user_id=session["user_id"],
                                                    trans_id=trans_id,
                                                    ordertype=ordertype,
                                                    datetime=current_datetime.now().strftime("%c"),
                                                    quantity=quantity,
                                                    total=usd(total),
                                                    symbol=symbol,
                                                    companyName=companyName
        )

def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)


app.run()