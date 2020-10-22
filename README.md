# BloomsTrade - Free Stock Trading Web Application Using Real-Time Quotes From API


![about](./readme_pics/0_about.png)


## Scope & Purpose

* I built a stock trading web application where users can invest stocks with a real-time stock quotes starting with $10,0000 of virtual money. This project is inspired by my passion for stock trading, computer science, and coding. This is a Python web application using Flask, Werkzeug exceptions and security, SQLite3, Requests, Jinja, Bootstrap4, Javascript, HTML5, and CSS3.


## System Prerequisites To Get Started

You will need the following installed on your computer system and import the following libraries:
* Python >= 3.7
* os
* datetime
* time
* SQLite3
* Flask and flash, jsonify, redirect, render_template, and request
* Flask_session
* tempfile
* Werkzeug.exceptions and default_exceptions, HTTPException, InternalServerError
* Werkzeug.security and check_password_hash, generate_password_hash


## Getting Started

* API Key from https://iexcloud.io/ as they are the real-time stock data provider

* Clone / Download Entire Repository

* Open up the terminal and navigate to the repository

* Export your API_KEY into the terminal

* Run "python application.py"

## Code Review - Recruiters / Hiring Managers

* Please view the application.py - here is where most of my Python logic and coding remains, including most of my SQL queries (e.g. common expression tables, Insert, and Update queries)

* Jinja Templates are in the "templates" folder where I created a layout, and created several custom dynamic pages

## Main Built-in Functionalities

* Password Hashing - this web application hashes the user's password upon account registration, so no real passwords are stored in the database

* Portfolio Balance - presents users current investment portfolio and cash position. Default new users start with $10,000.

* Quote & Buy - in a three step process, the user will first query for a stock ticker, perform a buy estimate, and either executes a buy order, or not, using real time API quotes provided by IEX Cloud (https://iexcloud.io/) This process is concluded with a buy order confirmation

* Sell - in a two step process, users may estimate, and subsequently, execute a sell order

* Transaction History - view when all orders were place in the History page where the database displays all executed orders

* Responsive Algorithm Preventing Errors - the algorithm will not allow users to purchase more shares of stock they can afford, or sell more shares than they have or do not own. The program will also instruct users what they need to fix in order to proceed


## Web Application Walkthrough

* Account Registration Page - all fields must be complete or application will return an error message
![registration](./readme_pics/1_registration.png)

* Registration Error - Example of an error message if a field is missing
![registrationError](./readme_pics/1a_registration_error.png)

* Registration Complete
![registrationComplete](./readme_pics/2a_complete.png)

* Initial Login Page Of New Users
![signedInEmpty](./readme_pics/3_signedin_empty.png)

* Quote & Buy - Phase 1 - Enter in a Valid Stock Ticker
![quotebuy1](./readme_pics/4_quotebuy.png)

* Quote & Buy - Phase 2 - Enter in a Valid Stock Ticker
![quotebuy2](./readme_pics/4a_searchResult.png)

* Quote & Buy - Phase 3 - Enter in a Valid Stock Ticker
![quotebuy3](./readme_pics/4b_buyEstimateResult.png)

* Quote & Buy - Phase 3b - If user click's "Estimate" with a blank quantity
![quotebuy3b](./readme_pics/4c_error_prevention_buyEstimate.png)

* Buy Confirmation
![quotebuyConfirm](./readme_pics/4d_confirmation.png)

* Portfolio View 
![portfolio](./readme_pics/5_portfolio.png)

* Sell - Phase 1 Estimate Order
![sell1](./readme_pics/6a_sellError_no_input.png)

* Sell - Phase 1a Estimate Order - Error Example Invalid "Sell Quantity"
![sell2](./readme_pics/6_sellError_quantity.png)

* Sell - Phase 1b Estimate Order - Error Example Invalid Stock Symbol
![sell3](./readme_pics/6b_sellError_symbol.png)

* Sell - Phase 2 Successful Estimate Order
![sell4](./readme_pics/6c_sellEstimate.png)

* Sell Confirmation
![sell4](./readme_pics/6d_sellConfirmation.png)

* Transaction History
![history](./readme_pics/7_history.png)

* Portfolio View After Sale
![portfolioAfterSale](./readme_pics/8_portfolioAfterSale.png)

* Database Structure Design - Entity Relationship Diagram
![erd](./readme_pics/9_finance_db_ERD.png)

* Flask App Snippets - Python, Flask and SQLite3
![1](./readme_pics/code_snippets/1.png)
![2](./readme_pics/code_snippets/2.png)
![3](./readme_pics/code_snippets/3.png)
![4](./readme_pics/code_snippets/4.png)
![5](./readme_pics/code_snippets/5.png)
![6](./readme_pics/code_snippets/6.png)
![7](./readme_pics/code_snippets/7.png)
![8](./readme_pics/code_snippets/8.png)
![9](./readme_pics/code_snippets/9.png)
![10](./readme_pics/code_snippets/10.png)
![11](./readme_pics/code_snippets/11.png)
![12](./readme_pics/code_snippets/12.png)
![13](./readme_pics/code_snippets/13.png)
![14](./readme_pics/code_snippets/14.png)



## Next Steps Considerations

* Use Regular Expressions to vet unwanted inputs
  
* Update to production grade database infrastructure using PostGres SQL and deploy using Heroku because of it's free cost structure for dynamic data

* Create function to allow users to change passwords or add more money


### Personal Note

* Hope you enjoyed it. Thank you for your time!

## Author

* **Johneson Giang** - *Invidual Project* - [Github](https://github.com/jhustles)

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments & Credits

* Shout out to David J. Mahlan and Brian Yu
* BootStrap4 Free Templates - Kelly

* I definitely want to give a shout out to my dear teacher, mentor, and friend @CodingWithCorgis!