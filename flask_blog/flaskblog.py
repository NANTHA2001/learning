

from forms import LoginForm
import bcrypt
from flask import Flask, g, jsonify,render_template, request,url_for,flash,redirect
import psycopg2
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from forms import RegistrationForm


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:GNanthu$2001@localhost/password'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
bcrypt= Bcrypt(app)
app.config['SECRET_KEY']='33c7a01f8988502409176555d933e603'

posts=[
    {
    'title':'1984',
    'author':'George Orwell',
    'content':"1984 is a dystopian novel set in a totalitarian society where individualism is banned and the government has complete control over every aspect of citizens' lives. The story follows the protagonist, Winston Smith, as he rebels against the oppressive regime and tries to find freedom and love. It is a haunting and thought-provoking work that has become a classic of modern literature.",
    'gender':'M'
    },
    {
    'author':'The Great Gatsby',
    'title':'F. Scott Fitzgerald',
    'gender':'M',
     'content':"The Great Gatsby is a classic novel set in the Roaring Twenties of America, a time of excess and decadence. The story is narrated by Nick Carraway, a young man who moves to New York and becomes involved in the lives of his wealthy and mysterious neighbor, Jay Gatsby, and his cousin, Daisy Buchanan. Through their intertwined relationships, the novel explores themes of love, wealth, class, and the American Dream. The Great Gatsby is a masterpiece of modern literature, known for its poetic prose and vivid depictions of the Jazz Age."
    }
]




@app.route("/")
@app.route("/home")
def home():
    return render_template("home.html", posts=posts)
@app.route("/about")
def about():
    return render_template('resume.html',title='about')

@app.route("/register", methods=['GET','POST'])
def register():
    form =RegistrationForm()
    if form.validate_on_submit():
       
      if form.create_user() == True:
       flash(f"Account created for {form.username.data}!", 'success')

       return redirect('home')
    return render_template('register.html',title='login',form=form)




  
  
# @app.route('/store/<string:name>/item')
# def get_store_item(name):
#     for store in stores:
#       if (store['name'] == name):
#         return jsonify(store['items'])
    
#     return jsonify({"message : not found"})


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        conn = psycopg2.connect(
        host="Localhost",
        database="password",
        user="postgres",
        password="GNanthu$2001"
    )
        cur = conn.cursor()
        cur.execute("SELECT email FROM users")
        tasks =  cur.fetchall()
        for task in tasks:
            if (task[0] == form.email.data):
                cur.execute(
                "SELECT password FROM users WHERE email = %s",
                (form.email.data,)
                )
                result = cur.fetchone()
                conn.close()
            
                password_str = str(form.password.data) 
            
                if bcrypt.check_password_hash(result[0], password_str):
                # flash('Login successful!', 'success')
                   return render_template('index.html')
                     
                # ,render_template('index.html') jsonify(message="Login successful"),
                else:
                    return jsonify(message="Login unsuccessful. Please check your email and password"),render_template('login.html',form=form)
                # 
                # flash('Login unsuccessful. Please check your email and password', 'danger')
    return render_template('login.html',form=form)

   


   

def get_db():
    if "db" not in g:
        g.db = psycopg2.connect(
            host="Localhost",
            database="password",
            user="postgres",
            password="GNanthu$2001",
        )
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


@app.route("/index/", methods=["POST", "GET"])
def index():
    cursor = get_cursor()
    if request.method == "POST":
        task_content = request.form["content"]
        try:
            cursor.execute("INSERT INTO curd (content) VALUES (%s)", (task_content,))
            get_db().commit()
            return redirect("/index/")
        except:
            return "there was a problem adding that row"
    else:
        cursor.execute("SELECT * FROM curd")
        tasks = [{"id": task[0], "content": task[1]} for task in cursor.fetchall()]
        return render_template("index.html", tasks=tasks)


@app.route("/delete/<int:id>", methods=["POST", "GET"])
def delete(id):
    cursor = get_cursor()
    try:
        cursor.execute("DELETE FROM curd WHERE id=%s", (id,))
        get_db().commit()
        return redirect("/index/")
    except:
        return "there was a problem deleting that row"


@app.route("/update/<int:id>", methods=["GET", "POST"])
def update(id):
    cursor = get_cursor()
    if request.method == "POST":
        content = request.form["content"]
        try:
            cursor.execute("UPDATE curd SET content=%s WHERE id=%s", (content, id))
            get_db().commit()
            return redirect("/index/")
        except:
            return "update have error"
    else:
        cursor.execute("SELECT * FROM curd")
        tasks = [{"id": task[0], "content": task[1]} for task in cursor.fetchall()]
        return render_template("update.html", tasks=tasks)
    



if __name__ =='__main__':
    app.run(debug=True)


 