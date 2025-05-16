Sure! Here's your **Event Booking System README** updated and tailored based on your project details with microservices, Docker images, Kubernetes, ports, and services you mentioned earlier:

---

# Event Booking System - Microservices Project

## Project Overview

This Event Booking System is a microservices-based application designed to handle event ticket booking, user management, payments, and real-time notifications. It is built using FastAPI, PostgreSQL, MongoDB, RabbitMQ, and deployed with Docker and Kubernetes. The system ensures secure, scalable, and maintainable service separation for each core functionality.

---

## Project Flow and Microservices

1. **User Service (`user-service`)**

   * Handles user registration, login, and authentication.
   * Connects to PostgreSQL `users_db` for managing user data.
   * Exposes REST API on port `8000`.
   * Docker image: `abdulmunhim/cs4067-assignment-02-i221021-munhim-user-service:latest`

2. **Event Service (`event-service`)**

   * Manages events catalog and details.
   * Exposes REST API on port `8001`.
   * Docker image: `abdulmunhim/cs4067-assignment-02-i221021-munhim-event-service:latest`

3. **Booking Service (`booking-service`)**

   * Allows users to book tickets for events.
   * Checks availability in PostgreSQL `booking_db`.
   * Calls payment service for processing transactions.
   * Publishes booking confirmations to RabbitMQ.
   * Exposes REST API on port `8002`.
   * Docker image: `abdulmunhim/cs4067-assignment-02-i221021-munhim-booking-service:latest`

4. **Payment Service (`payment-service`)**

   * Processes payments and stores payment records in MongoDB `payment_db`.
   * Exposes REST API on port `8004`.
   * Docker image: `abdulmunhim/cs4067-assignment-02-i221021-munhim-payment-service:latest`

5. **Notification Service (`notification-service`)**

   * Listens to RabbitMQ for booking events.
   * Sends notifications and logs them to MongoDB `notification_db`.
   * Exposes REST API on port `8003`.
   * Docker image: `abdulmunhim/cs4067-assignment-02-i221021-munhim-notification-service:latest`

6. **Frontend Service (`frontend-service`)**

   * Serves the UI of the application.
   * Runs on port `80`.
   * Docker image: `abdulmunhim/cs4067-assignment-02-i221021-munhim-frontend-service:latest`

---

## Installation Guide

### Prerequisites

* Docker Desktop installed and running
* Kubernetes cluster enabled (Docker Desktop or Minikube)
* `kubectl` CLI installed and configured
* RabbitMQ, MongoDB, PostgreSQL services running inside Kubernetes

---

### Steps to Run Locally

1. Clone repository

   ```bash
   git clone <your-repository-url>
   cd <your-project-folder>
   ```

2. Build Docker images for each microservice if not already built

   ```bash
   docker build -t abdulmunhim/cs4067-assignment-02-i221021-munhim-user-service ./user-service
   docker build -t abdulmunhim/cs4067-assignment-02-i221021-munhim-event-service ./event-service
   docker build -t abdulmunhim/cs4067-assignment-02-i221021-munhim-booking-service ./booking-service
   docker build -t abdulmunhim/cs4067-assignment-02-i221021-munhim-payment-service ./payment-service
   docker build -t abdulmunhim/cs4067-assignment-02-i221021-munhim-notification-service ./notification-service
   docker build -t abdulmunhim/cs4067-assignment-02-i221021-munhim-frontend-service ./frontend-service
   ```

3. Push images to Docker Hub

   ```bash
   docker push abdulmunhim/cs4067-assignment-02-i221021-munhim-user-service:latest
   docker push abdulmunhim/cs4067-assignment-02-i221021-munhim-event-service:latest
   docker push abdulmunhim/cs4067-assignment-02-i221021-munhim-booking-service:latest
   docker push abdulmunhim/cs4067-assignment-02-i221021-munhim-payment-service:latest
   docker push abdulmunhim/cs4067-assignment-02-i221021-munhim-notification-service:latest
   docker push abdulmunhim/cs4067-assignment-02-i221021-munhim-frontend-service:latest
   ```

4. Deploy Kubernetes manifests (namespaces, deployments, services, ingress)

   ```bash
   kubectl apply -f k8s/namespace.yaml
   kubectl apply -f k8s/configmap.yaml
   kubectl apply -f k8s/postgres.yaml
   kubectl apply -f k8s/user.yaml
   kubectl apply -f k8s/event.yaml
   kubectl apply -f k8s/booking.yaml
   kubectl apply -f k8s/notification.yaml
   kubectl apply -f k8s/frontend.yaml
   kubectl apply -f k8s/ingress.yaml
   ```

5. Add `onlineeventbooking.local` to your hosts file (for Ingress)

   ```
   127.0.0.1 onlineeventbooking.local
   ```

6. Access frontend in browser at:

   ```
   http://onlineeventbooking.local
   ```

---

## API Endpoints Summary

| Microservice         | Port | Base Path            | Example Endpoint | Description        |
| -------------------- | ---- | -------------------- | ---------------- | ------------------ |
| User Service         | 8000 | `/api/users`         | POST `/register` | Register new users |
|                      |      |                      | POST `/login`    | Authenticate user  |
| Event Service        | 8001 | `/api/events`        | GET `/`          | List all events    |
| Booking Service      | 8002 | `/api/bookings`      | POST `/`         | Create new booking |
| Payment Service      | 8004 | `/api/payments`      | POST `/`         | Process payment    |
| Notification Service | 8003 | `/api/notifications` | GET `/`          | Get notifications  |
| Frontend Service     | 80   | `/`                  | `/`              | UI Frontend        |

---

## Tech Stack

| Component        | Technology                |
| ---------------- | ------------------------- |
| Backend          | FastAPI (Python)          |
| Databases        | PostgreSQL, MongoDB       |
| Message Queue    | RabbitMQ                  |
| Containerization | Docker                    |
| Orchestration    | Kubernetes (with Ingress) |
| Web Server       | Uvicorn                   |

---

## Databases

### PostgreSQL

* `users_db`: stores user credentials and profiles
* `booking_db`: stores bookings and availability

### MongoDB

* `payment_db`: stores payment transaction records
* `notification_db`: stores booking notification logs

---

