import keyring
from getpass import getpass

DEFAULT_URI = ""
BIND_USERNAME = ""
BIND_PASSWORD = keyring.get_password("ldap", BIND_USERNAME)
SEARCH_BASE = ""

def set_password(password):
    keyring.set_password("LDAP", BIND_USERNAME, password)

def main():
    password_one = getpass(f"Password for {BIND_USERNAME}@{DEFAULT_URI}: ")
    password_two = getpass("Confirm Password: ")
    if not(password_one == password_two):
        print("Not equal. Try again.")
        main()
    print("Success")
    set_password(password_one)

if __name__ == "__main__":
    main()