from typing import List
from fastapi import FastAPI, HTTPException, Depends, Query
from pydantic import BaseModel
import pika
import json
import asyncio
import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, String, MetaData, Table, select, update
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from sqlalchemy.sql import text
import asyncpg

# Get database connection info from environment variables
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "pass")
DB_HOST = os.environ.get("DB_HOST", "postgres")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME", "bookings_db")

# Print connection details for debugging
print(f"Database connection details: Host={DB_HOST}, Port={DB_PORT}, User={DB_USER}, DB={DB_NAME}")

# Initial engine to connect to the default 'postgres' database
INIT_DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/postgres"

# Target database URL
DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

async def create_bookings_db():
    try:
        # Add a delay to allow DNS resolution and service discovery
        await asyncio.sleep(10)
        
        print(f"Attempting to connect to PostgreSQL at {DB_HOST}:{DB_PORT}")
        
        # Try connecting with asyncpg directly
        try:
            conn = await asyncpg.connect(
                user=DB_USER, 
                password=DB_PASSWORD, 
                host=DB_HOST, 
                port=int(DB_PORT),  # Ensure port is an integer
                database="postgres"
            )
            print("Successfully connected to PostgreSQL!")
            
            # Check if the database exists
            exists = await conn.fetchval("SELECT 1 FROM pg_database WHERE datname = $1", DB_NAME)
            if not exists:
                # Create the database if it doesn't exist
                await conn.execute(f"CREATE DATABASE {DB_NAME}")
                print(f"Database {DB_NAME} created successfully")
            else:
                print(f"Database {DB_NAME} already exists")
                
            await conn.close()
            return True
        except Exception as conn_err:
            print(f"Direct connection error: {conn_err}")
            return False
            
    except Exception as e:
        print(f"Database creation error: {e}")
        return False

# Now, connect to bookings_db
engine = create_async_engine(
    DATABASE_URL, 
    echo=True,
    pool_pre_ping=True,  # Add connection health check
    pool_recycle=3600,   # Recycle connections after 1 hour
    connect_args={
        "command_timeout": 10  # Set connection timeout
    }
)

async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
metadata = MetaData()

# Define bookings table (PostgreSQL)
bookings_table = Table(
    "bookings", metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("user_id", Integer),
    Column("event_id", String),
    Column("tickets", Integer),
    Column("status", String),
)

# FastAPI instance
app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"]   
)

# Connect to MongoDB for payment records
MONGO_HOST = os.environ.get("MONGO_HOST", "mongodb")
MONGO_PORT = os.environ.get("MONGO_PORT", "27017")
payment_client = MongoClient(f"mongodb://{MONGO_HOST}:{MONGO_PORT}/")
payment_db = payment_client["payment_db"]
payments_collection = payment_db["payment"]

# Booking request model
class BookingRequest(BaseModel):
    user_id: int
    event_id: str
    tickets: int

# Model for returning booking data
class Booking(BaseModel):
    id: int
    user_id: int
    event_id: str
    tickets: int
    status: str

# Payment request model
class PaymentRequest(BaseModel):
    user_id: int
    amount: int

# Dependency to get PostgreSQL database session
async def get_db():
    async with async_session() as session:
        yield session

async def create_tables():
    try:
        # Add a delay to ensure database is ready
        await asyncio.sleep(5)
        print("Attempting to create tables...")
        async with engine.begin() as conn:
            await conn.run_sync(metadata.create_all)  # This will create the "bookings" table
        print("Tables created successfully")
    except Exception as e:
        print(f"Error creating tables: {e}")

# Run database creation on startup
@app.on_event("startup")
async def startup_event():
    print("Starting booking service...")
    print(f"Database connection: {DATABASE_URL}")
    
    # Try to create the database and tables with retries
    max_retries = 5
    for i in range(max_retries):
        print(f"Attempt {i+1}/{max_retries} to connect to database")
        db_created = await create_bookings_db()
        if db_created:
            await create_tables()  # Ensure tables exist
            print("Startup completed successfully")
            break
        else:
            if i < max_retries - 1:
                retry_delay = 5 * (i + 1)  # Incremental backoff
                print(f"Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
            else:
                print("Failed to connect to the database after multiple attempts")

# Remaining API endpoints remain the same...

# POST endpoint to create a booking
@app.post("/bookings")
async def create_booking(request: BookingRequest, db: AsyncSession = Depends(get_db)):
    print("Received booking request:", request.dict())
    
    # Save booking in PostgreSQL
    insert_query = bookings_table.insert().values(
        user_id=request.user_id,
        event_id=request.event_id,
        tickets=request.tickets,
        status="CONFIRMED"
    ).returning(bookings_table.c.id)
    
    try:
        result = await db.execute(insert_query)
        booking_id = result.scalar()
        await db.commit()
        print("Booking Saved with ID:", booking_id)
    except Exception as e:
        print("Error saving booking:", str(e))
        raise HTTPException(status_code=500, detail="Error saving booking")
    
    # Publish confirmation message to RabbitMQ
    booking_data = {
        "id": booking_id,
        "user_id": request.user_id,
        "event_id": request.event_id,
        "tickets": request.tickets,
        "status": "CONFIRMED"
    }
    
    RABBITMQ_HOST = os.environ.get("RABBITMQ_HOST", "rabbitmq")
    
    try:
        # Use the Docker service name 'rabbitmq', not 'localhost'
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))  
        channel = connection.channel()
        
        # Declare queue to ensure it exists
        channel.queue_declare(queue='notification_queue', durable=True)
        
        channel.basic_publish(
            exchange='',
            routing_key='notification_queue',
            body=json.dumps(booking_data)
        )
        
        connection.close()
        print("Confirmation message published to RabbitMQ:", booking_data)
    except Exception as e:
        print("Error publishing to RabbitMQ:", str(e))
        raise HTTPException(status_code=500, detail="Error publishing notification")
    
    return {"message": "Booking confirmed", "booking_id": booking_id}

# GET endpoint to list all bookings
@app.get("/bookings")
async def get_bookings(db: AsyncSession = Depends(get_db)):
    query = select(bookings_table)
    results = await db.execute(query)
    rows = results.fetchall()
    bookings = [dict(row._mapping) for row in rows]
    return bookings

# GET endpoint to list bookings for a specific user
@app.get("/bookings/me", response_model=List[Booking])
async def get_my_bookings(
    user_id: int = Query(..., description="ID of the logged-in user"),
    db: AsyncSession = Depends(get_db)
):
    query = select(bookings_table).where(
        bookings_table.c.user_id == user_id,
        bookings_table.c.status.in_(["CONFIRMED", "PENDING"])
    )
    results = await db.execute(query)
    rows = results.fetchall()
    bookings = [dict(row._mapping) for row in rows]
    return bookings

# POST endpoint to process payment
@app.post("/payments")
async def process_payment(request: PaymentRequest, db: AsyncSession = Depends(get_db)):
    query = select(bookings_table).where(
        bookings_table.c.user_id == request.user_id,
        bookings_table.c.status.in_(["CONFIRMED", "PENDING"])
    )
    results = await db.execute(query)
    rows = results.fetchall()
    bookings = [dict(row._mapping) for row in rows]
    
    if not bookings:
        raise HTTPException(status_code=404, detail="No pending bookings found for this user")
    
    # Calculate total due (each ticket costs ₹500)
    total_due = sum(booking["tickets"] * 500 for booking in bookings if booking["status"] in ["CONFIRMED", "PENDING"])
    if request.amount != total_due:
        raise HTTPException(status_code=400, detail=f"Amount does not match total due: ₹{total_due}")
    
    # Update each booking to 'PAID' and insert a payment record into MongoDB
    for booking in bookings:
        update_stmt = bookings_table.update().where(bookings_table.c.id == booking["id"]).values(status="PAID")
        await db.execute(update_stmt)
        payment_cost = booking["tickets"] * 500
        payment_document = {
            "user_id": request.user_id,
            "event_id": booking["event_id"],
            "cost": payment_cost
        }
        payments_collection.insert_one(payment_document)
    
    await db.commit()
    
    return {"message": "Payment successful and bookings updated", "total_paid": total_due}