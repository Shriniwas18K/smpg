from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import random
app = FastAPI()
# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
from datetime import datetime
from cryptography.fernet import Fernet
# Generate a key
# key = Fernet.generate_key()
key=b'B8rPRkgG8ZuBIEIX5z-Auu9qB59jvFdVkJOIXbdlZ6I='
cipher = Fernet(key)


'''********************************************************************
                    database connection and set up
'''
import psycopg2
try:
    connection = psycopg2.connect(
        user="postgres",
        password="WtDEHOANEnCJAiHBkBanzcIUzGCkplNb",
        host="monorail.proxy.rlwy.net",
        port=31171,
        database="railway"
    )
    print("database connected successfully")
    cur=connection.cursor()

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
cur.execute('''
    create table if not exists transactions(
        atTime timestamp,
        phone varchar(10),
        description varchar(30)
    )
''')
connection.commit()
'''*********************************************************************'''



'''request models are given below'''
from pydantic import BaseModel
class signinsignup(BaseModel):
    phone:str
    username:str
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
        validation , signin signup routes
*********************************************************'''

def generate_token():
    '''This function generates a token from currenttimestamp
        which is sent to client frontend, and everytime client
        has to give this token to access any of the owner routes'''
    generationtimestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S").encode()
    return cipher.encrypt(generationtimestamp)

def validate_token(tokenvalue):
    ''' This function checks the validity of the token ,
        one client can use one token on
        one device only for 1 hour, else token will be expired 
        and session will be inactive'''
    try:
        generationtimestamp=cipher.decrypt(tokenvalue)
        generationtimestamp=datetime.strptime(
                                                generationtimestamp.decode(),
                                                "%Y-%m-%d %H:%M:%S"
                                             )
        currenttimestamp=datetime.now()
        diff=currenttimestamp-generationtimestamp
        if(diff.seconds>3600):
            return False
    except:
            return False
    return True

@app.post("/signup/")
async def signup(requ:signinsignup):
    cur.execute(f"select * from credentials where phone='{requ.phone}'")
    rows=cur.fetchall()
    if(len(rows)==1):
        return {
            "message":"user already exists try to signin"
        }
    else:
        cur.execute("insert into credentials values (%s,%s,%s,%s)",(requ.phone,requ.username,requ.password,datetime.now()))
        cur.execute("insert into transactions values(%s,%s,%s)",(datetime.now(),requ.phone,'signup'))
        connection.commit()
        return {
            "message":"user created"
        }
    
@app.post("/signin/")
async def signin(requ:signinsignup):
    '''function will check wheter username exists in database'''
    cur.execute("select * from credentials where phone=%s",(requ.phone,))
    rows=cur.fetchall()
    if(rows==[]):
        return { "message" : "user does not exists pls sign up"}
    else:
        cur.execute("insert into transactions values(%s,%s,%s)",(datetime.now(),requ.phone,'signin'))
        connection.commit()
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
    "phone": "6674566753",
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
    if((validate_token(token))==False):
        return {"error" : "forbidden action pls signin "}
    cur.execute(f"select count(*),username from properties where username='{req.username}' group by username")
    rows=cur.fetchall();
    try:
        if(rows[0][0]==5):
            return {"message" : "limit reached"}
    except: pass
    propertypid=int(random.random()*100000)
    cur.execute("insert into properties values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (propertypid,req.phone,req.username,req.address,req.pincode,
                 req.noOfPeopleToAccomodate,req.rentPerPerson,req.areaInSqft,
                 req.wifiFacility,req.furnished,req.description,datetime.now())
    )
    cur.execute("insert into transactions values(%s,%s,%s)",(datetime.now(),req.phone,'new property posted'))
    connection.commit()
    return{"message":"post successful"}
'''to prevent overflow of posts by single user i.e. in a situation
 where same user puts many advertisements for same property in 
 order to get it rented more faster, to prevent this we will limit
 the number of advertisements sinlge user can put to be as 5,it is
 implemented above'''

class allpropertiesreq(BaseModel):
    username:str
    phone:str
@app.get('/getUserProperties/')
async def getpropertiesofuser(token:str,req:allpropertiesreq):
    if(validate_token(token)==False):
        return {"message":"token expired , pls login again"}
    cur.execute('select address,url1 from properties where username=%s and phone=%s',(req.username,req.phone))
    rows=cur.fetchall()
    return rows



from fastapi.responses import JSONResponse
from typing import Annotated
import uuid,os
from fastapi import File
UPLOAD_DIR = "uploaded_images"
@app.post("/uploadImage/{phn}/{unm}")
async def create_file(token:str,file: Annotated[bytes, File()],phn,unm):
    print(file)
    os.makedirs(UPLOAD_DIR+f'/{phn+unm}/', exist_ok=True)
    with open(UPLOAD_DIR+f'/{phn+unm}/'+str(uuid.uuid4())+'.png',"wb") as f:
        f.write(file)
    return JSONResponse(
        content={"image_path": UPLOAD_DIR+f'/{phn+unm}/'+str(uuid.uuid4())+'.png'}
    )





'''****************************************************************
                        VISITOR ROUTES
****************************************************************'''
@app.get("/retrieveProperties/{pincode}")
async def sendProperties(pincode:int):
    cur.execute(f'select * from properties where pincode between {pincode-2} and {pincode+2}')
    rows=cur.fetchall()
    return rows


