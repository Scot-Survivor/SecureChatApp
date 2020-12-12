import hashlib
import sqlite3
import secrets
from datetime import datetime
from random import randint


def connect():
    connection = sqlite3.connect("ChatApp.db")
    c = connection.cursor()
    return c, connection


def create_tables(c):
    c.execute(
        "CREATE TABLE IF NOT EXISTS users(user_id INT PRIMARY KEY UNIQUE, username TEXT UNIQUE, password TEXT, salt TEXT, work_factor TEXT, date TEXT);")


def login(user_password: bytes, username: str, c) -> bool:
    sql_state = """SELECT password, salt, work_factor FROM users WHERE username = '{}';""".format(username)
    c.execute(sql_state)  # Execute
    results = c.fetchall()  # Fetch all the results
    for user in results:  # Loop through all the results
        salt = user[1].encode('utf-8')  # Grab the salt
        work_factor = int(user[2])  # This will be doing things
        hashed_user_password = hex_pbkdf2(user_password, salt, work_factor)  # hash the inputted password
        if hashed_user_password.hex() == user[0]:  # Check if the passwords match
            return True
    return False


def remove_user(username: str, c, connection) -> bool or str:
    sql_state = """DELETE FROM users WHERE username = "{}";""".format(username)
    try:
        c.execute(sql_state)
    except Exception as e:
        return f"{str(e)} Delete Error."
    connection.commit()
    return True


def hex_pbkdf2(password: bytes, salt: bytes, work_factor: int) -> bytes:  # Hash the password and return the bytes
    password = hashlib.pbkdf2_hmac("sha256", password, salt, work_factor)  # Hash the password
    return password  # return the password


# noinspection PyShadowingNames
def add_user(password: bytes, username: str, work_factor: int, c, connection) -> bool or str:  # Adds a user to the database and returns bool or string depending on success or error
    sql_state = """SELECT username FROM users;"""
    c.execute(sql_state)
    results = c.fetchall()
    if username in results:
        return f"{username} Already in use."
    salt = secrets.token_urlsafe(64).encode('utf-8')  # Creates a unique salt
    hashed_password = hex_pbkdf2(password, salt, work_factor)
    hashed_password = hashed_password.hex()
    sql_state = f"""INSERT INTO users (user_id, username, password, salt, work_factor, date) VALUES ({randint(0, 10000)}, "{username}", "{str(hashed_password)}", "{salt.decode('utf-8')}", "{str(work_factor)}", "{datetime.now().strftime('%d/%m/%Y')}");"""
    try:
        c.execute(sql_state)
    except Exception as e:
        return f"{str(e)} Insertion Error"
    connection.commit()
    return True


def return_users(new_c):
    sql_state = """SELECT username FROM users;"""
    new_c.execute(sql_state)
    results = new_c.fetchall()
    return results
