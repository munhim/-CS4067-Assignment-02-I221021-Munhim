from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select
from sqlalchemy import Column, Integer, String, MetaData, Table, insert, update
from fastapi.middleware.cors import CORSMiddleware

# PostgreSQL connection URL
DATABASE_URL = "postgresql+asyncpg://myuser:mypassword@postgres:5433/users_db"

engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
metadata = MetaData()

# Define the users table
users_table = Table(
    "users", metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("username", String, unique=True, index=True),
    Column("password", String),
)

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow requests from any origin
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"]   # Allow all headers
)

# Ensure the database and table are created at startup
@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(metadata.create_all)

# Request models
class LoginRequest(BaseModel):
    username: str
    password: str

class RegistrationRequest(BaseModel):
    username: str
    password: str

class UpdateProfileRequest(BaseModel):
    user_id: int
    username: str = None
    password: str = None

# Dependency to get a DB session
async def get_db():
    async with async_session() as session:
        yield session

# Login endpoint
@app.post("/login")
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    query = select(users_table).where(
        users_table.c.username == request.username,
        users_table.c.password == request.password
    )
    result = await db.execute(query)
    user = result.fetchone()
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    return {"message": "Login successful", "user_id": user.id}

# Registration endpoint
@app.post("/register")
async def register(request: RegistrationRequest, db: AsyncSession = Depends(get_db)):
    # Check if the username already exists
    query = select(users_table).where(users_table.c.username == request.username)
    result = await db.execute(query)
    existing_user = result.fetchone()
    
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")
    
    stmt = insert(users_table).values(username=request.username, password=request.password)
    await db.execute(stmt)
    await db.commit()
    
    return {"message": "Registration successful"}

# Update profile endpoint
@app.put("/update-profile")
async def update_profile(request: UpdateProfileRequest, db: AsyncSession = Depends(get_db)):
    # Verify the user exists
    query = select(users_table).where(users_table.c.id == request.user_id)
    result = await db.execute(query)
    user = result.fetchone()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    update_data = {}
    if request.username is not None:
        update_data["username"] = request.username
    if request.password is not None:
        update_data["password"] = request.password
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No update data provided")
    
    stmt = update(users_table).where(users_table.c.id == request.user_id).values(**update_data)
    await db.execute(stmt)
    await db.commit()
    
    return {"message": "Profile updated successfully"}

@app.get("/")
async def home():
    return {"Hello": "kaisay ho"}
