import requests
import os

# Base URL for the booking service POST endpoint
BASE_URL = "http://127.0.0.1:8002/bookings"

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")

def create_booking():
    print("\n=== Create Booking ===")
    try:
        user_id = int(input("Enter user ID: "))
    except ValueError:
        print("User ID must be a number.")
        return

    event_id = input("Enter event ID: ").strip()
    try:
        tickets = int(input("Enter number of tickets: "))
    except ValueError:
        print("Tickets must be a number.")
        return

    data = {
        "user_id": user_id,
        "event_id": event_id,
        "tickets": tickets
    }
    try:
        response = requests.post(BASE_URL, json=data)
        if response.status_code == 200:
            print("✅ Booking confirmed!")
            print("Response:", response.json())
        else:
            print("❌ Failed to create booking. Status Code:", response.status_code)
            print("Response:", response.text)
    except Exception as e:
        print("Error connecting to the booking service:", e)

def menu():
    while True:
        clear_screen()
        print("=== Booking Service CLI ===")
        print("1. Create Booking")
        print("2. Exit")
        choice = input("Enter your choice: ").strip()
        
        if choice == "1":
            create_booking()
        elif choice == "2":
            print("Exiting... Goodbye!")
            break
        else:
            print("Invalid choice! Please try again.")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    menu()
