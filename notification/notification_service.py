# notification_service.py
import asyncio
import json
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
import pika

app = FastAPI()

# Enable CORS for local frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow requests from any origin
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"]   # Allow all headers
)

# Connect to MongoDB
client = MongoClient("mongodb://mongodb:27017/notifications_db")
db = client["notification_db"]
notifications_collection = db["notifications"]

async def process_messages():
    """Continuously listen to RabbitMQ 'notification_queue' and store messages in MongoDB."""
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='notification_queue')

    def callback(ch, method, properties, body):
        try:
            notification = json.loads(body.decode("utf-8"))
            # Mark as unread by default
            notification["read"] = False
            notifications_collection.insert_one(notification)
            print("Stored notification:", notification)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")

    channel.basic_consume(queue='notification_queue', on_message_callback=callback, auto_ack=True)
    print("Notification Service: Listening on 'notification_queue'...")

    # Start consuming in a separate thread via the event loop
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, channel.start_consuming)

@app.on_event("startup")
async def startup_event():
    # Launch the RabbitMQ consumer in the background
    asyncio.create_task(process_messages())

@app.get("/notifications")
def get_notifications(user_id: int = Query(...), unread_only: bool = Query(False)):
    """
    Return notifications for a given user_id.
    If unread_only=true, return notifications where read=false.
    """
    query = {"user_id": user_id}
    if unread_only:
        query["read"] = False
    
    # Sort by newest first
    results = notifications_collection.find(query).sort("_id", -1)
    notifications = []
    for doc in results:
        doc["_id"] = str(doc["_id"])  # Convert ObjectId to string
        notifications.append(doc)
    return notifications

@app.post("/notifications/{notif_id}/read")
def mark_as_read(notif_id: str):
    """
    Mark a specific notification as read by its id.
    """
    from bson import ObjectId
    result = notifications_collection.update_one(
        {"_id": ObjectId(notif_id)},
        {"$set": {"read": True}}
    )
    if result.modified_count == 1:
        return {"message": "Notification marked as read"}
    else:
        return {"message": "Notification not found or already read"}
