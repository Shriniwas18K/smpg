from fastapi import FastAPI
app=FastAPI()
import cryptocode
import uuid
import random
from datetime import datetime
secret_key="r9m330924mc2059m205052cm5205"


'''********************************************************************
                    database connection and set up
'''
import psycopg2
try:
    connection = psycopg2.connect(
        user="postgres",
        password="HHDbAgqDkNkwiTgrmsBWEgxKBliGffbF",
        host="roundhouse.proxy.rlwy.net",
        port="37139",
        database="railway"
    )
    print("database connected successfully")
    cur = connection.cursor()
except (Exception, psycopg2.Error) as error:
    print("Error while connecting to PostgreSQL:", error)
cur.execute(
    '''
    create table if not exists credentials(
        phone varchar(10),
        username varchar(20),
        password varchar(10),
        createdOn timestamp
    )
    '''
)
cur.execute(
    '''create table if not exists properties
        (
         pid varchar(6),
         username varchar(20),
         phone varchar(10),
         address varchar(200),
         pincode integer,
         noOfPeopleToAccomodate integer,
         rentPerPerson integer,
         areaInSqft float,
         wifiFacility varchar(3),
         furnished varchar(3),
         description varchar(200),
         postedOn timestamp
        )'''
)
connection.commit()
'''*********************************************************************'''



'''request models are given below'''
from pydantic import BaseModel
class loginsignup(BaseModel):
    phone:str
    password:str

class Property(BaseModel):
    username:str
    phone:str
    address:str
    pincode:int
    noOfPeopleToAccomodate:int
    rentPerPerson:int
    areaInSqft:float
    wifiFacility:str
    furnished:str
    description:str







'''*********************************************************
    below given are authentication and token generation 
        validation , login signup routes
*********************************************************'''

def generate_token():
    '''This function generates a token from currenttimestamp
        which is sent to client frontend, and everytime client
        has to give this token to access any of the owner routes'''
    generationtimestamp=datetime.strftime(datetime.now(),"%Y-%m-%d %H:%M:%S")
    return cryptocode.encrypt(generationtimestamp,secret_key)

def validate_token(token):
    ''' This function checks the validity of the token ,
        one client can use one token on
        one device only for 1 hour, else token will be expired 
        and session will be inactive'''
    try:
        generationtimestamp=cryptocode.decrypt(token,secret_key)
        generationtimestamp=datetime.strptime(
                                                generationtimestamp,
                                                "%Y-%m-%d %H:%M:%S"
                                             )
        print(generationtimestamp)
        currenttimestamp=datetime.now()
        diff=currenttimestamp-generationtimestamp
        print(diff)
        print(diff.seconds)
        if(diff.seconds>3600):
            return False
    except:
            return False
    return True

@app.post("/signup/")
async def signup(requ:loginsignup):
    cur.execute(f"select * from credentials where username={requ.username}")
    rows=cur.fetchall()
    if(len(rows)==1):
        return {
            "message":"user already exists try to login"
        }
    else:
        cur.execute(f'''insert into credentials values (
                    {requ.phone},
                    '{requ.username}',
                    '{requ.password}',
                    '{datetime.strftime(datetime.now(),"%Y-%m-%d %H:%M:%S")}'
                    )''')
        return {
            "message":"user created"
        }
    
@app.get("/login/")
async def login(requ:loginsignup):
    '''function will check wheter username exists in database'''
    cur.execute(
        f"select * from credentials where phone={requ.phone}"
    )
    rows=cur.fetchall()
    if(rows==[]):
        return { "message" : "user does not exists pls sign up"}
    else:
        '''if exists then we return him token'''
        return{"token":generate_token()}









'''
***************************************************
    OWNER routes when he has logged in and 
        has valid token are given below
***************************************************
'''

'''Posting a new property'''

'''
// this is below example of what content and request
// is put in the frontend

const propertyDetails = {
    "phone": 6674566753,
    "username":"sdfhyyuyfth",
    "address": "123 Main St",
    "pincode": 412434,
    "noOfPeopleToAccomodate": 4,
    "rentPerPerson": 500,
    "areaInSqft": 1000.0,
    "wifiFacility": "Yes",
    "furnished": "Yes",
    "description": "Spacious apartment with modern amenities"
};

// Define the token
const token = "Uuxt6MjEFEL2VYqK0T8YybZiIWU=*hl+75Qq/xtAaUktrCXtA3Q==*6DJ4ExTU/c0J6EeH/xyEMA==*LvXtk0D8jealdGc3NU2oGg==";

// Construct the request URL with the token as a URL parameter
const url = `/postProperty/?token=${encodeURIComponent(token)}`;

// Make a POST request with Fetch API
fetch(url, {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    },
    body: JSON.stringify(propertyDetails)
})
.then(response => {
    if (!response.ok) {
        throw new Error('Network response was not ok');
    }
    return response.json();
})
'''
@app.post("/postProperty/")
async def postProperty(token,req:Property):
    # if((validate_token(token))==False):
        # return {"error" : "forbidden action pls login "}
    cur.execute(f"select count(*),username from properties where username={req.username}")
    rows=cur.fetchall();
    if(rows[0][0]==5):
        return {"message" : "limit reached"}
    cur.execute(f"insert into properties values({int(random.random()*100000)},{req.phone},'{req.username}','{req.address}',{req.pincode},{req.noOfPeopleToAccomodate},{req.rentPerPerson},{req.areaInSqft},'{req.wifiFacility}','{req.furnished}','{req.description}','{datetime.strftime(datetime.now(),'%Y-%m-%d %H:%M:%S')}')")
    connection.commit()
    return{"message":"post successful"}
'''to prevent overflow of posts by single user i.e. in a situation
 where same user puts many advertisements for same property in 
 order to get it rented more faster, to prevent this we will limit
 the number of advertisements sinlge user can put to be as 5,it is
 implemented above'''




'''****************************************************************
                        VISITOR ROUTES
****************************************************************'''
@app.get("/retrieveProperties/{pincode}")
async def sendProperties(pincode:int):
    cur.execute(f'select * from properties where pincode between {pincode-2} and {pincode+2}')
    rows=cur.fetchall()
    print(rows)

