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
        }
        role=request.json.get('role',None)
        try:
            if role=='users':
              cur.execute(
                "SELECT password FROM users WHERE email = %s",
                (new_data["email"],),
              )
            elif role=='manager':
                cur.execute(
                "SELECT password FROM manager WHERE email = %s",
                (new_data["email"],),
              )
            elif role=='employee':
             cur.execute(
                "SELECT password FROM employee WHERE email = %s",
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
            print(password_str)

            if bcrypt.check_password_hash(password_hash, password_str):
                token1 = jwt.encode(
                    {
                        "user": new_data["email"],
                        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=3),
                    },
                    app.config["SECRET_KEY"],
                )
                if role=='users':
                  cur.execute(
                    "UPDATE users SET token = %s WHERE email = %s",
                    (token1.decode("utf-8"), new_data["email"]),
                  )
                  get_db().commit()
                elif role=='manager':
                    cur.execute(
                    "UPDATE manager SET token = %s WHERE email = %s",
                    (token1.decode("utf-8"), new_data["email"]),
                  )
                    get_db().commit()
                elif role=='employee':
                    cur.execute(
                    "UPDATE employee SET token = %s WHERE email = %s",
                    (token1.decode("utf-8"), new_data["email"]),
                  )
                    get_db().commit()
                  
                return jsonify(message="login successful"), 401
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
    if request.method == "POST":
        req_data = request.get_json()
        if not req_data:
            return jsonify(message="No JSON data provided"), 400

        required_fields = ["username", "email", "password","role"]
        for field in required_fields:
            if field not in req_data:
                return jsonify(message=f"{field} is required"), 400

        new_data = {
            "username": req_data["username"],
            "email": req_data["email"],
            "password": req_data["password"],
            "admin":req_data["admin"]
        
        }
        role=request.json.get('role',None)
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
                jsonify({"message": "Password should contain at least one uppercase letter."}),
                400,
            )

        if not re.search(r"[a-z]", new_data["password"]):
            return (
                jsonify({"message": "Password should contain at least one lowercase letter."}),
                400,
            )

        if not re.search(r"\d", new_data["password"]):
            return (
                jsonify({"message": "Password should contain at least one number."}),
                400,
            )

        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', new_data["password"]):
            return (
                jsonify({"message": "Password should contain at least one special character."}),
                400,
            )

        conn = None
        password_hash = bcrypt.generate_password_hash(new_data["password"]).decode("utf-8")
        
        try:
            role=request.json.get('role',None)
            cur.execute(
            "SELECT id FROM users WHERE username = %s",
            (new_data["admin"],),
            )
              
            result = cur.fetchone()
            if result is None:
                  return (
                    jsonify(message="Access is only for Admin!"),
                    401,
                    )
            elif role=='users':
              
              cur.execute(
                "SELECT id FROM users WHERE email = %s",
                (new_data["email"],),
              )
              result = cur.fetchone()

              if result is not None:
                 return jsonify(message="email already exists"), 409
              else:
                  cur.execute(
                "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
                (
                    new_data["username"],
                    new_data["email"],
                    password_hash,
                ),
                )
              get_db().commit()
            
               
            
            elif role=='employee':
                 cur.execute(
                "SELECT id FROM employee WHERE email = %s",
                (new_data["email"],),
                )
                 result = cur.fetchone()
                 if result is not None:
                  return jsonify(message="email already exists"), 409
                 else:
                  cur.execute(
                 "INSERT INTO employee (username, email, password) VALUES (%s, %s, %s)",
                  (
                    new_data["username"],
                    new_data["email"],
                    password_hash,
                  ),
                  )
                 get_db().commit()
                 
            elif role=='manager':
                cur.execute(
                "SELECT id FROM manager WHERE email = %s",
                (new_data["email"],),
              )
                result = cur.fetchone()
                if result is not None:
                  return jsonify(message="email already exists"), 409
                else:
                  cur.execute(
                "INSERT INTO manager (username, email, password) VALUES (%s, %s, %s)",
                (
                    new_data["username"],
                    new_data["email"],
                    password_hash,
                ),
                )
                get_db().commit()
            return jsonify(message="account created successfully"), 201
    
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
    role=request.json.get('role',None)
    if request.method == "DELETE":
        new_data = {"admin":req_data["admin"],
            "id": req_data["id"]}
    if not token:
        return jsonify({"message": "Token is missing!"}), 401
    try:
        if jwt.decode(
            token.split(" ")[1],
            app.config["SECRET_KEY"],
            algorithms=["HS256"],
        ): 
                cursor.execute(
                "SELECT id FROM users WHERE username = %s",
                (new_data["admin"],),
                )
              
                result = cursor.fetchone()
                if result is None:
                  return (
                    jsonify(message="Access is only for Admin!"),
                    401,
                   )
                if role=='users':
                     cursor.execute("SELECT username,email,password,token from manager WHERE id=%s", (new_data["id"],))
                     result=cursor.fetchone()
                     print(result[0])
                     cursor.execute(
                           "INSERT INTO users (username,email,password,token) VALUES (%s, %s, %s,%s)",
                           (
                           result[0],
                           result[1],
                           result[2],
                           result[3]
                           ),
                           )
                     get_db().commit()
                     
                      
                     cursor.execute("DELETE FROM employee WHERE id=%s", (new_data["id"],))
                     get_db().commit()
                     return jsonify(message="Content deleted successfully"), 200
                           
    except jwt.ExpiredSignatureError:
        return (
            jsonify(message="Your token has expired. Please login again."),
            401,
        )
    except jwt.InvalidTokenError:
        return jsonify({"message": token}), 401

    return jsonify(message="Content was not deleted"), 401



    
@app.route("/admin", methods=["PATCH"])
def admin():
    cursor = get_cursor()
    req_data = request.get_json()
    token = request.headers.get("Authorization")
    role=request.json.get('role',None)
    if request.method == "PATCH":
        new_data = {
            "admin":req_data["admin"],
            "username":req_data["username"],
            "manager_name": req_data["manager_name"]
        }
        if not token:
            return jsonify({"message": "Token is missing!"}), 401
        try:
            if jwt.decode(
                token.split(" ")[1],
                app.config["SECRET_KEY"],
                algorithms=["HS256"],
            ):
                cursor.execute(
                "SELECT id FROM users WHERE username = %s",
                (new_data["admin"],),
                )
              
                result = cursor.fetchone()
                cursor.execute(
                "SELECT id FROM manager WHERE username = %s",
                (new_data["manager_name"],),
                )
                result1=cursor.fetchone()

                if result is None:
                  return (
                    jsonify(message="Access is only for Admin!"),
                    401,
                   )
                if result1:
                    cursor.execute(
                    "UPDATE employee SET manager_name=%s WHERE username=%s",
                    (new_data["manager_name"], new_data["username"]),
                     )
                    get_db().commit()
                    return jsonify(message="updated successfully")
                else:return jsonify(message="manager is not there")

        except jwt.ExpiredSignatureError:
            return (
                jsonify(message="Your token has expired. Please login again."),
                401,
            )
        except jwt.InvalidTokenError:
            return jsonify({"message": token}), 401
        else:
            return jsonify(message="update have error")
    else:
        cursor.execute("SELECT * FROM curd")
        # fmt:off
        tasks = [{"id": task[0], "content": task[1]} for task in cursor.fetchall()]
        # fmt:on
        return render_template("update.html", tasks=tasks)
    
@app.route("/user", methods=["PATCH"])
def update():
    cursor = get_cursor()
    req_data = request.get_json()
    token = request.headers.get('Authorization')
    role=request.json.get('role',None)
    if request.method == "PATCH":
        new_data = {
            'admin':req_data['admin'],
            'username': req_data['username'],
            'id':req_data['id']}
        if not token:
           return jsonify({'message': 'Token is missing!'}), 401
        try:
            if jwt.decode(token.split(" ")[1], app.config['SECRET_KEY'], algorithms=['HS256']):
                cursor.execute(
                "SELECT id FROM users WHERE username = %s",
                (new_data["admin"],),
                )
              
                result = cursor.fetchone()

                if result is None:
                  return (
                    jsonify(message="Access is only for Admin!"),
                    401,
                   )
               
                if role=='employee':
                    cursor.execute("UPDATE employee SET username=%s WHERE id=%s", (new_data['username'], new_data['id']))
                    get_db().commit()
                    return jsonify(message="updated successfully")
                elif role=='manager':
                    cursor.execute("UPDATE manager SET username=%s WHERE id=%s", (new_data['username'], new_data['id']))
                    get_db().commit()
                    return jsonify(message="updated successfully")

                

           
        except jwt.ExpiredSignatureError:
           return jsonify(message="Your token has expired. Please login again."), 401
        except jwt.InvalidTokenError:
            return jsonify({'message':token}), 401
        else:
            return jsonify(message= "update have error")
    else:
        cursor.execute("SELECT * FROM curd")
        tasks = [{"id": task[0], "content": task[1]} for task in cursor.fetchall()]
        return render_template("update.html", tasks=tasks)
    

@app.route("/joins", methods=["PATCH"])
def joins():
    cursor = get_cursor()
    req_data = request.get_json()
    token = request.headers.get('Authorization')
    role=request.json.get('role',None)
    if request.method == "PATCH":
        new_data = {
            'admin':req_data['admin'],
            'username': req_data['username'],
            }
        if not token:
           return jsonify({'message': 'Token is missing!'}), 401
        try:
            if jwt.decode(token.split(" ")[1], app.config['SECRET_KEY'], algorithms=['HS256']):
                cursor.execute(
                "SELECT id FROM users WHERE username = %s",
                (new_data["admin"],),
                )
              
                result = cursor.fetchone()

                if result is None:
                  return (
                    jsonify(message="Access is only for Admin!"),
                    401,
                   )
               
                
                cursor.execute("SELECT username,email FROM employee WHERE manager_name=%s", (new_data['username'],))
                users=cursor.fetchall()
                cursor.execute("SELECT e.username,e.email,m.username,m.email from employee as e join manager as m on e.manager_name=%s",(new_data['username'],))
                user_details1 = []
                users=cursor.fetchall()
                for user in users:
                  user_details1.append(
                 { 
                 "employee_username": user[0], 
                 "employee_email": user[1],
                 "manager_username": user[2],
                 "manager_email": user[3]
                 })

                return jsonify(user_details1)
                
                # user_details = []
                # for user in users:
                #    user_details.append(
                #    { "username": user[0], "email": user[1]})

                # return jsonify(user_details)
                
                
                    

        except jwt.ExpiredSignatureError:
           return jsonify(message="Your token has expired. Please login again."), 401
        except jwt.InvalidTokenError:
            return jsonify({'message':token}), 401
        else:
            return jsonify(user_details1)
    else:
        
        return render_template(message= "update have error")


if __name__ == "__main__":
    app.run(debug=True)
