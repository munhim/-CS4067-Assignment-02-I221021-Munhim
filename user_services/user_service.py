from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select
from sqlalchemy import Column, Integer, String, MetaData, Table, insert, update
from fastapi.middleware.cors import CORSMiddleware
import os
import asyncio
import re

# Print all environment variables to debug connection issues
print("Environment variables:")
for key, value in os.environ.items():
    print(f"{key}: {value}")

# Get database connection info
# First check if we have a complete DATABASE_URL
database_url = os.getenv("DATABASE_URL")

if database_url:
    print(f"Found DATABASE_URL: {database_url}")
    # Use the provided DATABASE_URL directly
    DATABASE_URL = database_url
else:
    # If not, build it from individual components
    db_user = os.getenv("DB_USER", "myuser")  # Changed default from "postgres" to "myuser"
    db_password = os.getenv("DB_PASSWORD", "mypassword")  # Changed default from "pass" to "mypassword"
    db_host = os.getenv("DB_HOST", "postgres")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "users_db")
    
    # Build the database URL
    DATABASE_URL = f"postgresql+asyncpg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

print(f"Connecting to database with URL: {DATABASE_URL.replace(db_password if 'db_password' in locals() else re.search(r'://([^:]+):([^@]+)@', DATABASE_URL).group(2), '******')}")

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
    print(f"Starting up application, connecting to {DATABASE_URL.replace(db_password if 'db_password' in locals() else re.search(r'://([^:]+):([^@]+)@', DATABASE_URL).group(2), '******')}")
    try:
        # Add a retry mechanism for database connection
        max_retries = 5
        retry_count = 0
        last_exception = None
        
        while retry_count < max_retries:
            try:
                print(f"Attempt {retry_count + 1} to connect to database")
                async with engine.begin() as conn:
                    await conn.run_sync(metadata.create_all)
                print("Database connection successful and tables created!")
                return
            except Exception as e:
                print(f"Connection attempt {retry_count + 1} failed: {str(e)}")
                last_exception = e
                retry_count += 1
                await asyncio.sleep(5)  # Wait 5 seconds before retrying
        
        # If we reach here, all retries failed
        print(f"All {max_retries} connection attempts failed. Last error: {str(last_exception)}")
        raise last_exception
    except Exception as e:
        print(f"Fatal error during startup: {str(e)}")
        raise

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
        try:
            yield session
        except Exception as e:
            await session.rollback()
            raise
        finally:
            await session.close()

# Login endpoint
@app.post("/login")
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    try:
        query = select(users_table).where(
            users_table.c.username == request.username,
            users_table.c.password == request.password
        )
        result = await db.execute(query)
        user = result.fetchone()
        
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        return {"message": "Login successful", "user_id": user.id}
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# Registration endpoint
@app.post("/register")
async def register(request: RegistrationRequest, db: AsyncSession = Depends(get_db)):
    try:
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
    except Exception as e:
        await db.rollback()
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# Update profile endpoint
@app.put("/update-profile")
async def update_profile(request: UpdateProfileRequest, db: AsyncSession = Depends(get_db)):
    try:
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
    except Exception as e:
        await db.rollback()
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/health")
async def health():
    try:
        # Verify database connectivity
        async with async_session() as session:
            await session.execute(select(1))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {
            "status": "unhealthy", 
            "database": "disconnected", 
            "error": str(e),
            "database_url": DATABASE_URL.replace(db_password if 'db_password' in locals() else re.search(r'://([^:]+):([^@]+)@', DATABASE_URL).group(2), "******")  # Hide password in logs
        }

@app.get("/")
async def home():
    return {"Hello": "kaisay ho"}