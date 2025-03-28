import requests

BASE_URL = "http://127.0.0.1:8000"

def main_menu():
    print("\n==== User Management System ====")
    print("1. Register")
    print("2. Login")
    print("3. Update Profile")
    print("4. Exit")
    return input("Enter your choice: ")

def register():
    print("\n-- User Registration --")
    username = input("Enter username: ")
    password = input("Enter password: ")
    data = {"username": username, "password": password}
    response = requests.post(f"{BASE_URL}/register", json=data)
    print("Response:", response.json())

def login():
    print("\n-- User Login --")
    username = input("Enter username: ")
    password = input("Enter password: ")
    data = {"username": username, "password": password}
    response = requests.post(f"{BASE_URL}/login", json=data)
    res_json = response.json()
    print("Response:", res_json)
    if response.status_code == 200:
        print(f"Logged in as user with id: {res_json.get('user_id')}")

def update_profile():
    print("\n-- Update Profile --")
    user_id = input("Enter your user ID: ")
    new_username = input("Enter new username (leave blank for no change): ")
    new_password = input("Enter new password (leave blank for no change): ")
    
    data = {"user_id": int(user_id)}
    if new_username:
        data["username"] = new_username
    if new_password:
        data["password"] = new_password
    
    response = requests.put(f"{BASE_URL}/update-profile", json=data)
    print("Response:", response.json())

def main():
    while True:
        choice = main_menu()
        if choice == "1":
            register()
        elif choice == "2":
            login()
        elif choice == "3":
            update_profile()
        elif choice == "4":
            print("Exiting...")
            break
        else:
            print("Invalid choice, please try again.")

if __name__ == "__main__":
    main()
