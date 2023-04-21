import re
import bcrypt
from flask import Flask, g, jsonify, render_template, request
import psycopg2
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
import jwt
import datetime
from dotenv import load_dotenv
import os
import psycopg2
from flask import Flask, request, jsonify
from flask_bcrypt import Bcrypt

app = Flask(__name__)
bcrypt = Bcrypt(app)

load_dotenv()
url = os.getenv("url")
secret_key = os.getenv("secret_key")


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
app.config["SECRET_KEY"] = secret_key


def get_db():
    if "db" not in g:
        g.db = psycopg2.connect(url)
    return g.db


def get_cursor():
    if "cursor" not in g:
        g.cursor = get_db().cursor()
    return g.cursor


@app.before_request
def before_request():
    get_db()
    get_cursor()


@app.teardown_request
def teardown_request(exception):
    db = g.pop("db", None)
    if db is not None:
        db.close()
    cursor = g.pop("cursor", None)
    if cursor is not None:
        cursor.close()


@app.route("/login", methods=["POST"])
def login():
    cur = get_cursor()
    if request.method == "POST":
        req_data = request.get_json()
        if not req_data:
            return jsonify(message="No JSON data provided"), 400

        required_fields = ["email", "password"]
        for field in required_fields:
            if field not in req_data:
                return jsonify(message=f"{field} is required"), 400

        new_data = {
            "email": req_data["email"],
            "password": req_data["password"],
            "role": req_data["role"],
        }
        role = request.json.get("role", None)
        try:
            cur.execute(
                "SELECT password FROM employee_details WHERE emp_email = %s",
                (new_data["email"],),
            )
            result = cur.fetchone()
            if result is None:
                return (
                    jsonify(message="Login unsuccessful. Email address not found."),
                    401,
                )
            password_hash = result[0]
            password_str = str(new_data["password"])
            if bcrypt.check_password_hash(password_hash, password_str):
                token1 = jwt.encode(
                    {
                        "user": new_data["role"],
                        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=3),
                    },
                    app.config["SECRET_KEY"],
                )
                cur.execute(
                    "UPDATE employee_details SET token = %s WHERE emp_email = %s",
                    (token1, new_data["email"]),
                )
                get_db().commit()
                return jsonify({"token": token1})
            else:
                return (
                    jsonify(message="Login unsuccessful. Incorrect password"),
                    401,
                )
        except (Exception, psycopg2.Error) as error:
            print(f"Error during login: {error}")
            return (
                jsonify(message="Login unsuccessful. Please try again later."),
                500,
            )


@app.route("/registers", methods=["POST"])
def create_user():
    cur = get_cursor()
    token = request.headers.get("Authorization")
    if request.method == "POST":
        req_data = request.get_json()
        if not req_data:
            return jsonify(message="No JSON data provided"), 400

        required_fields = ["username", "email", "password", "role"]
        for field in required_fields:
            if field not in req_data:
                return jsonify(message=f"{field} is required"), 400

        new_data = {
            "id": req_data["id"],
            "username": req_data["username"],
            "email": req_data["email"],
            "password": req_data["password"]
            
        }
        role = request.json.get("role", None)
        if len(new_data["username"]) < 5:
            return (
                jsonify({"message": "username should be at least 5 characters long."}),
                400,
            )
        if len(new_data["password"]) < 8:
            return (
                jsonify({"message": "Password should be at least 8 characters long."}),
                400,
            )
        if not re.search(r"[A-Z]", new_data["password"]):
            return (
                jsonify(
                    {
                        "message": "Password should contain at least one uppercase letter."
                    }
                ),
                400,
            )
        if not re.search(r"[a-z]", new_data["password"]):
            return (
                jsonify(
                    {
                        "message": "Password should contain at least one lowercase letter."
                    }
                ),
                400,
            )
        if not re.search(r"\d", new_data["password"]):
            return (
                jsonify({"message": "Password should contain at least one number."}),
                400,
            )
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', new_data["password"]):
            return (
                jsonify(
                    {
                        "message": "Password should contain at least one special character."
                    }
                ),
                400,
            )
        conn = None
        password_hash = bcrypt.generate_password_hash(new_data["password"]).decode(
            "utf-8"
        )
        try:
            decode_token = jwt.decode(
            token.split(" ")[1],
            app.config["SECRET_KEY"],
            algorithms=["HS256"],
            )

            if decode_token["user"] == "admin":
                    cur.execute(
                    "INSERT INTO employee_details (emp_id,emp_name, emp_email, password,role) VALUES (%s, %s, %s,%s,%s)",
                    (
                        new_data["id"],
                        new_data["username"],
                        new_data["email"],
                        password_hash,
                        role,
                    ),
                    )
                    get_db().commit()
                    return jsonify(message="register successful"), 200
        finally:
            if conn is not None:
                conn.close()
    else:
        return jsonify(message="Invalid method"), 405


@app.route("/user", methods=["DELETE"])
def delete():
    cursor = get_cursor()
    req_data = request.get_json()
    token = request.headers.get("Authorization")
    role = request.json.get("role", None)
    if request.method == "DELETE":
        new_data = {
          
            "id": req_data["id"],
            "role": req_data["role"]
        }
    if not token:
        return jsonify({"message": "Token is missing!"}), 401
    try:
        decode_token = jwt.decode(
            token.split(" ")[1],
            app.config["SECRET_KEY"],
            algorithms=["HS256"],
        )

        if decode_token["user"] == "admin":
            cursor.execute(
                "UPDATE employee_details SET role=%s WHERE emp_id=%s",
                (new_data["role"], new_data["id"]),
            )
            cursor.execute(
                "UPDATE employee_details SET reporting_id='0' where emp_id=%s",
                (new_data["id"]),
            )
            cursor.execute(
                "UPDATE employee_details SET reporting_id='0'where reporting_id=%s",
                (new_data["id"]),
            )
            # cursor.execute("DELETE FROM employee_details WHERE emp_id=%s", (new_data["id"],))
            get_db().commit()
            return (
                jsonify(message="role updated successful and reporting id is null"),
                200,
            )
        else:
            return jsonify(message="admin can only access"), 200

    except jwt.ExpiredSignatureError:
        return (
            jsonify(message="Your token has expired. Please login again."),
            401,
        )
    except jwt.InvalidTokenError:
        return jsonify({"message": token}), 400


@app.route("/admin", methods=["PATCH"])
def admin():
    cursor = get_cursor()
    req_data = request.get_json()
    token = request.headers.get("Authorization")
    role = request.json.get("role", None)
    if request.method == "PATCH":
        new_data = {
            # "admin": req_data["admin"],
            "userid": req_data["userid"],
            "manager_name": req_data["manager_name"]
        }
        if not token:
            return jsonify({"message": "Token is missing!"}), 401
        try:
            decode_token = jwt.decode(
                token.split(" ")[1],
                app.config["SECRET_KEY"],
                algorithms=["HS256"],
            )

            cursor.execute(
                "SELECT emp_id FROM employee_details WHERE emp_id = %s AND role = 'manager' or role ='ceo'",
                (new_data["manager_name"],),
            )
            result1 = cursor.fetchone()

            if decode_token["user"] == "admin":
                if result1:
                    cursor.execute(
                        "UPDATE employee_details SET reporting_id=%s WHERE emp_id=%s",
                        (new_data["manager_name"], new_data["userid"]),
                    )
                    get_db().commit()
                    return jsonify(message="updated successfully")
                else:
                    return jsonify(message="manager is not there")
            else:
                return jsonify(message="admin can only access")

        except jwt.ExpiredSignatureError:
            return (
                jsonify(message="Your token has expired. Please login again."),
                401,
            )
        except jwt.InvalidTokenError:
            return jsonify({"message": token}), 401

    else:
        return render_template(message="method is not patch")


@app.route("/user", methods=["PATCH"])
def update():
    cursor = get_cursor()
    req_data = request.get_json()
    token = request.headers.get("Authorization")
    role = request.json.get("role", None)
    if request.method == "PATCH":
        new_data = {
           
            "username": req_data["username"],
            "id": req_data["id"]
        }
        if not token:
            return jsonify({"message": "Token is missing!"}), 401
        try:
            decode_token = jwt.decode(
                token.split(" ")[1], app.config["SECRET_KEY"], algorithms=["HS256"]
            )
            if decode_token == "admin":
                cursor.execute(
                    "UPDATE employee_details SET emp_id=%s WHERE emp_name=%s",
                    (new_data["id"], new_data["username"]),
                )
                get_db().commit()
                return jsonify(message="updated successfully")
            else:
                return jsonify(message="admin can only access")
        except jwt.ExpiredSignatureError:
            return jsonify(message="Your token has expired. Please login again."), 401
        except jwt.InvalidTokenError:
            return jsonify({"message": token}), 401

    else:
        return render_template(message="this is not patch method")


@app.route("/search", methods=["PATCH"])
def search():
    cursor = get_cursor()
    req_data = request.get_json()
    token = request.headers.get("Authorization")
    decoded_token = jwt.decode(
        token.split(" ")[1], app.config["SECRET_KEY"], algorithms=["HS256"]
    )
    if request.method == "PATCH":
        new_data = { "userid": req_data["userid"]}
        user_details = []
        user_details2 = []

        if decoded_token["user"] == "name":
            cursor.execute(
                "SELECT emp_id,emp_name,emp_email,role FROM employee_details WHERE emp_id=%s",
                (new_data["userid"],),
            )
            users = cursor.fetchall()
            for user in users:
                user_details.append(
                    {
                        "userid": user[0],
                        "employee_name": user[1],
                        "employee_email": user[2],
                        "role": user[3],
                    }
                )
            return jsonify(user_details), 401
        elif decoded_token["user"] == "employee":
            cursor.execute(
                "SELECT emp_id,emp_name,emp_email,role FROM employee_details"
            )
            users = cursor.fetchall()
            for user in users:
                user_details2.append(
                    {
                        "userid": user[0],
                        "employee_name": user[1],
                        "employee_emal": user[2],
                        "role": user[3],
                    }
                )
            return jsonify(user_details2), 401
        if not token:
            return jsonify({"message": "Token is missing!"}), 401
        try:
            user_details1 = []
    
            if decoded_token["user"] == "manager":
                cursor.execute(
                    "SELECT emp_id, emp_name, emp_email FROM employee_details WHERE reporting_id = %s",
                    (new_data["userid"]),
                )
                users = cursor.fetchall()
                for user in users:
                    user_details1.append(
                        {
                            "employee_id": user[0],
                            "employee_name": user[1],
                            "employee_email": user[2],
                        }
                    )
                return jsonify(user_details1)
                # return jsonify({message="only manager can view this data"}), 401

            elif decoded_token["user"] == 'admin':
                # print(current_user)

                cursor.execute(
                "SELECT e.emp_id, e.emp_name, e.emp_email, m.emp_name AS reporting_manager, e.role FROM employee_details e INNER JOIN employee_details m ON e.reporting_id = m.emp_id WHERE e.emp_id = %s",
                (new_data["userid"],)
                )

                users = cursor.fetchall()
                for user in users:
                    user_details1.append(
                        {
                            "username": user[0],
                            "email": user[1],
                            "employee_email": user[2],
                            "manager_id": user[3],
                        }
                    )
                   
                return jsonify(user_details1)

        except jwt.ExpiredSignatureError:
            return jsonify(message="Your token has expired. Please login again."), 401
        except jwt.InvalidTokenError:
            return jsonify({"message": token}), 401
        else:
            return jsonify(user_details1)
    else:
        return render_template(message="this is not patch method")


if __name__ == "__main__":
    app.run(debug=True)
