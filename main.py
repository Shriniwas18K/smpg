from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from cryptography.fernet import Fernet
from pydantic import BaseModel
import random
import sqlite3

app = FastAPI()

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Generate a key
key = b'B8rPRkgG8ZuBIEIX5z-Auu9qB59jvFdVkJOIXbdlZ6I='
cipher = Fernet(key)

# Establish database connection and set up tables
connection = sqlite3.connect('example.db')
cur = connection.cursor()

cur.execute('''
    CREATE TABLE IF NOT EXISTS credentials (
        phone VARCHAR(10),
        username VARCHAR(20),
        password VARCHAR(10),
        createdOn VARCHAR(200)
    )
''')

cur.execute('''
    CREATE TABLE IF NOT EXISTS properties (
        pid VARCHAR(6),
        username VARCHAR(20),
        phone VARCHAR(10),
        address VARCHAR(200),
        pincode INTEGER,
        noOfPeopleToAccomodate INTEGER,
        rentPerPerson INTEGER,
        areaInSqft FLOAT,
        wifiFacility VARCHAR(200),
        furnished VARCHAR(200),
        url1 VARCHAR(500),
        url2 VARCHAR(500),
        url3 VARCHAR(500),
        description VARCHAR(200),
        postedOn VARCHAR(200)
    )
''')

cur.execute('''
    CREATE TABLE IF NOT EXISTS transactions (
        atTime VARCHAR(200),
        phone VARCHAR(10),
        description VARCHAR(30)
    )
''')

connection.commit()


# Request models
class SigninSignup(BaseModel):
    phone: str
    username: str
    password: str


class Property(BaseModel):
    username: str
    phone: str
    address: str
    pincode: int
    noOfPeopleToAccommodate: int
    rentPerPerson: int
    areaInSqft: float
    wifiFacility: str
    furnished: str
    url1: str
    url2: str
    url3: str
    description: str


# Authentication and token generation/validation
def generate_token():
    generation_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S").encode()
    return cipher.encrypt(generation_timestamp)


def validate_token(token_value):
    try:
        generation_timestamp = cipher.decrypt(token_value)
        generation_timestamp = datetime.strptime(generation_timestamp.decode(), "%Y-%m-%d %H:%M:%S")
        current_timestamp = datetime.now()
        diff = current_timestamp - generation_timestamp
        if diff.seconds > 3600:
            return False
    except:
        return False
    return True


@app.post("/signup/")
async def signup(req: SigninSignup):
    cur.execute(f"SELECT * FROM credentials WHERE phone = '{req.phone}'")
    rows = cur.fetchall()
    if len(rows) == 1:
        return {"message": "User already exists. Please sign in."}
    else:
        cur.execute(f"INSERT INTO credentials (phone, username, password, createdOn) "
                    f"VALUES ('{req.phone}', '{req.username}', '{req.password}', '{str(datetime.now())}')")
        cur.execute(f"INSERT INTO transactions (atTime, phone, description) "
                    f"VALUES ('{str(datetime.now())}', '{req.phone}', 'signup')")
        connection.commit()
        return {"message": "User created successfully"}


@app.post("/signin/")
async def signin(req: SigninSignup):
    cur.execute(f"SELECT * FROM credentials WHERE phone='{req.phone}'")
    rows = cur.fetchall()
    if not rows:
        return {"message": "User does not exist. Please sign up."}
    else:
        cur.execute(f"INSERT INTO transactions VALUES ('{str(datetime.now())}', '{req.phone}', 'signin')")
        connection.commit()
        return {"token": generate_token()}


# Owner routes
@app.post("/postProperty/")
async def postProperty(token, req: Property):
    if not validate_token(token):
        return {"error": "Forbidden action. Please sign in."}

    cur.execute(f"SELECT COUNT(*), username FROM properties WHERE username='{req.username}' GROUP BY username")
    rows = cur.fetchall()

    try:
        if rows[0][0] == 5:
            return {"message": "Limit reached"}
    except IndexError:
        pass

    propertypid = int(random.random() * 100000)
    cur.execute(f"INSERT INTO properties VALUES "
                f"('{propertypid}', '{req.phone}', '{req.username}', '{req.address}', '{req.pincode}', "
                f"'{req.noOfPeopleToAccommodate}', '{req.rentPerPerson}', '{req.areaInSqft}', "
                f"'{req.wifiFacility}', '{req.furnished}', '{req.url1}', '{req.url2}', '{req.url3}', "
                f"'{req.description}', '{str(datetime.now())}')")
    cur.execute(f"INSERT INTO transactions VALUES ('{str(datetime.now())}', '{req.phone}', 'new property posted')")
    connection.commit()

    return {"message": "Post successful"}


# Visitor routes
@app.get("/retrieveProperties/{pincode}")
def retrieve_properties(pincode: int):
    try:
        min_pincode = pincode - 2
        max_pincode = pincode + 2

        cur.execute(f"SELECT * FROM properties WHERE pincode BETWEEN {min_pincode} AND {max_pincode}")
        rows = cur.fetchall()

        return rows
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/retrieve/{phone}")
def retrieveProperties(phone: str):
    cur.execute(f"SELECT * FROM properties WHERE phone='{phone}'")
    properties = cur.fetchall()
    if not properties:
        raise HTTPException(status_code=404, detail="Properties not found")
    return properties


@app.delete("/removeProperty/{property_id}")
def removeProperty(property_id: str):
    cur.execute(f"SELECT * FROM properties WHERE pid = '{property_id}'")
    row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Property not found")
    cur.execute(f"DELETE FROM properties WHERE pid = '{property_id}'")
    connection.commit()
    return {"message": "Property deleted successfully"}
