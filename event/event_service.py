from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pymongo import MongoClient
from bson import ObjectId
from typing import List, Optional
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow requests from any origin
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"]   # Allow all headers
)

# Set up MongoDB connection using PyMongo
client = MongoClient("mongodb://mongodb:27017/events_db")
db = client["events_db"]  # Replace with your actual database name
events_collection = db["events"]

print("Connected to MongoDB: events_db")

# Event model
class Event(BaseModel):
    id: Optional[str] = None
    name: str
    venue: str
    date: str  # Accepting date as a string (ISO format) for compatibility with MongoDB

    class Config:
        allow_population_by_field_name = True
        extra = "forbid"  # Forbid extra fields except those defined
        json_encoders = {
            ObjectId: str
        }

# Endpoint to list all events
@app.get("/events", response_model=List[Event])
def list_events():
    events = []
    for doc in events_collection.find():
        doc["id"] = str(doc["_id"])
        doc.pop("_id", None)
        if isinstance(doc["date"], datetime):
            doc["date"] = doc["date"].strftime("%Y-%m-%d")  # Convert to string format
        events.append(doc)
    return events

# Endpoint to create a new event
@app.post("/events", response_model=Event)
def create_event(event: Event):
    try:
        event_dict = event.dict(by_alias=True)
        event_dict.pop("_id", None)

        # Convert date string to datetime object before inserting into MongoDB
        event_dict["date"] = datetime.strptime(event_dict["date"], "%Y-%m-%d")

        result = events_collection.insert_one(event_dict)
        created_event = events_collection.find_one({"_id": result.inserted_id})
        
        if created_event and "_id" in created_event:
            created_event["id"] = str(created_event["_id"])
            created_event.pop("_id", None)
            created_event["date"] = created_event["date"].strftime("%Y-%m-%d")  # Convert back to string

        return Event(**created_event)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating event: {str(e)}")

# Endpoint to delete an event
@app.delete("/events/{id}")
def delete_event(id: str):
    try:
        result = events_collection.delete_one({"_id": ObjectId(id)})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Event not found")
        return {"message": "Event deleted successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting event: {str(e)}")
