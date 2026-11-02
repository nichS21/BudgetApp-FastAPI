# BudgetApp-FastAPI
FastAPI program for a web based budgeting app. 


## General Overview
This project is a backend web, RESTful API using the FastAPI framework alongside SQLAlchemy for the ORM, PostgreSQL for the database, Alembic for database migrations, and Pipenv for project dependencies management. The API handles the registration, authentication and CRUD operations that are needed by the frontend component of the web-based budgeting app, and responds in JSON to easily be received by the frontend. The application relies on JSON Web Tokens (JWT) for authentication purposes; the server is responsible for giving JWTs when relevant and denying access to protected resources when an invalid JWT or no JWT is present in the request. 


## Data Objects Overview
The API operates on these key data objects (SQLAlchemy ORM Models):
1) **User** - The end user that logs in to the application and can modify resources related to their budget
2) **Income** - The annual salary and income tax associated with a user
3) **Contribution** - These represent income allocated to things like savings accounts, retirement accounts, or other savings goals; this is money that the user is paying themselves with on a monthly basis
4) **Expense** - These represent all possible living expenses, needs, or debt payments taken on a monthly basis

All of the ORM specifications for these objects are found in the `application/models` directory


## Routers Overview
Routers are how FastAPI knows to handle a request made to itself. They direct a request accordingly based on the URL received in the HTTP request itself, and then execute a function that corresponds to the URL, in the correct router. All routers are in the `application/routers` directory

The routers in the application:
1) **Authentication** - handles logging in to the system and giving a JWT token in its response body if successful
2) **Registration** - Responsible for signing up users to the system, allowing signed in users to change their password, and handling a forgotten password request to change a user's password using a recovery code
3) **Income** - Handles CRU operations for Income objects in the database
4) **Expenses** - Handles CRUD operations for Expense objects in the database
5) **Contributions** - Handles CRUD operations for Contribution objects in the database
6) **Overview** - Retrieves income, the list of contributions, and the list of expenses associated with a user 

**Further API documentation available in the browser can be found at the `/openapi.json`, `/docs`, and `/redoc` endpoints when the API is ran in develoment mode (local `.env` file contains `debug=True`)**


## Testing Overview
This application includes unit tests for each router, hitting expected successes and expected possible failures for each endpoint. The tests are all written using the PyTest library. The tests themselves are located in the `application/testing/tests` directory, while `application/testing/fixtures` contains PyTest 'fixtures' that are special reusable parameters utilized by the test when ran.


## General Application Layout / Configuration
1) The app is created in `application/app.py` and all routers are added to it in this file. This is where the application 'runs' from in FastAPI
2) `application/config.py` defines the application's environment variables that are to be read in from a `.env` file in the root of the project directory (one up from `application/`) as well as setting them up so they can be used throughout the app via dependency injection
3) `application/database.py` creates the database connection and a 'Session' object that allows the app to run commands on the database. The session object is also created such that it can be used through dependency injection in each endpoint.
4) `application/auth_utilites.py` contains various helper functions used in the authentication and registration endpoints to hash and verify passwords or recovery codes


## Setup
See `dev/project-setup.md` for more details on how to setup the project locally. The code base for development is configured such that a PostgreSQL database and Adminer instance are setup via Docker to easily and quickly get started.

