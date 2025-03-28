# Event Booking System
## Project Overview
The Event Booking System is a microservices-based application designed to streamline event ticket booking, payment processing, and real-time notifications. Built using FastAPI, PostgreSQL, MongoDB, and RabbitMQ, it ensures secure transactions, high availability, and a seamless user experience.
## How It Works (Project Flow)
1. **User Authentication (`user_service.py`)**  
   - Users log in using the `/login` endpoint.  
   - Credentials are validated against PostgreSQL `users_db`.  
   - If successful, the system returns a unique `user_id`.
2. **Event Booking (`booking_service.py`)**  
   - Users request a booking via `/bookings`.  
   - The system checks ticket availability.  
   - Calls the payment service to process the transaction.  
   - On successful payment, the booking is stored in PostgreSQL (`booking_db`).  
   - A confirmation is published to RabbitMQ for notifications.  
3. **Payment Processing (`payment_service.py`)**  
   - Listens for incoming payment requests via `/payments`.  
   - Stores transaction details in MongoDB (`payment_db`).  
   - Returns a `SUCCESS` status upon successful payment.  
4. **Notifications (`notification_service.py`)**  
   - Listens for messages from RabbitMQ.  
   - Stores booking notifications in MongoDB (`notification_db`).  
   - Can be extended to send email/SMS alerts.  
## Installation Guide
1. **Clone the Repository**:
   ```bash
   git clone <repository-url>
   cd CS4067-Assgt-EventBooking-i220784-Abdullah-Aslam
   ```
2. **Set Up a Virtual Environment (Recommended)**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On macOS/Linux
   venv\Scripts\activate     # On Windows
   ```
3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Start Services**:
   - Start RabbitMQ, MongoDB, and PostgreSQL.  
   - Run each microservice:  
   ```bash
   uvicorn user_service:app --reload --port 8000
   uvicorn booking_service:app --reload --port 8002
   uvicorn payment_service:app --reload --port 8004
   uvicorn notification_service:app --reload --port 8006
   ```
## API Endpoints
### User Service (`user_service.py`)
- **Login:** `POST /login`
  ```json
  {
    "username": "testuser",
    "password": "password123"
  }
  ```
  - Returns `user_id` if authentication is successful.
### Booking Service (`booking_service.py`)
- **Create Booking:** `POST /bookings`
  ```json
  {
    "user_id": 1,
    "event_id": "E123",
    "tickets": 2
  }
  ```
  - Checks availability, charges the user, and confirms the booking.
### Payment Service (`payment_service.py`)
- **Process Payment:** `POST /payments`
  ```json
  {
    "user_id": 1,
    "amount": 100.0
  }
  ```
  - Stores payment details in MongoDB (`payment_db`).
### Notification Service (`notification_service.py`)
- **Processes messages from RabbitMQ**  
  - Stores booking confirmations in MongoDB (`notification_db`).
## Technology Stack
| Component           | Technology  |
|--------------------|------------|
| Backend           | FastAPI    |
| Database         | PostgreSQL & MongoDB |
| Message Queue    | RabbitMQ   |
| Web Server       | Uvicorn    |
## Database Structure
### PostgreSQL (`booking_db`, `users_db`)
- **Bookings Table**: Stores event bookings.
- **Users Table**: Manages user authentication.
### MongoDB (`payment_db`, `notification_db`)
- **Payments Collection**: Stores transaction history.
- **Notifications Collection**: Stores booking confirmations.

