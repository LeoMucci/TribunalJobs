from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError

app = Flask(__name__)
app.secret_key = 'tribunaljobs'


app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:081314@localhost/tribunaljobs'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Login(db.Model):
    __tablename__ = 'Login'
    IdUser = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(255), nullable=False)
    senha = db.Column(db.String(255), nullable=False)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'email' in request.form and 'senha' in request.form:
        email = request.form['email']
        senha = request.form['senha']
        try:
            account = Login.query.filter_by(email=email, senha=senha).first()
            if account:
                session['loggedin'] = True
                session['id'] = account.IdUser
                session['email'] = account.email
                msg = 'Logged in successfully!'
                return redirect(url_for('home'))
            else:
                msg = 'Incorrect username/password!'
        except SQLAlchemyError as e:
            msg = str(e)
    return render_template('login.html', msg=msg)

@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('email', None)
    return redirect(url_for('login'))

@app.route('/home')
def home():
    if 'loggedin' in session:
        return f'Logged in as {session["email"]}'
    return redirect(url_for('login'))

@app.route('/cadastro')
def cadastro():
    return render_template('cadastro.html')

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
