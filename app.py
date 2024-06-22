from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError, DataError, IntegrityError
import re, os 
from werkzeug.utils import secure_filename
import uuid

app = Flask(__name__)
app.secret_key = 'tribunaljobs'

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:081314@localhost/tribunaljobs'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'  # Diretório para armazenar as imagens
app.config['MAX_CONTENT_PATH'] = 1024 * 1024  # Limite de tamanho do arquivo (1MB)

db = SQLAlchemy(app)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

class Login(db.Model):
    __tablename__ = 'Login'
    IdUser = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(255), nullable=False)
    senha = db.Column(db.String(255), nullable=False)

class Empresa(db.Model):
    __tablename__ = 'Empresa'
    cnpj = db.Column(db.String(14), primary_key=True)
    nomeEmpresa = db.Column(db.String(255), nullable=False)
    contato = db.Column(db.String(255), nullable=True)
    cpfADM = db.Column(db.String(11), nullable=False, unique=True)

class ADM(db.Model):
    __tablename__ = 'ADM'
    IdADM = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome = db.Column(db.String(255), nullable=False)
    fone = db.Column(db.String(20))
    oab = db.Column(db.String(20))
    email = db.Column(db.String(255), nullable=False)
    senha = db.Column(db.String(255), nullable=False)
    cnpj = db.Column(db.String(14), db.ForeignKey('Empresa.cnpj'))
    cpfADM = db.Column(db.String(11), db.ForeignKey('Empresa.cpfADM'))
    imagem = db.Column(db.String(255))  # Campo para o caminho da imagem

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
                msg = 'Email ou Senha não autenticados!'
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

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    msg = ''
    if request.method == 'POST' and all(key in request.form for key in ['nomeEmpresa', 'cnpj', 'contato', 'cpfADM']):
        nomeEmpresa = request.form['nomeEmpresa']
        cnpj = request.form['cnpj']
        contato = request.form['contato']
        cpfADM = request.form['cpfADM']

        # Validação dos campos CNPJ e CPF
        if not re.match(r'^\d{14}$', cnpj):
            msg = 'CNPJ inválido. Deve conter 14 dígitos numéricos.'
        elif not re.match(r'^\d{11}$', cpfADM):
            msg = 'CPF do Administrador inválido. Deve conter 11 dígitos numéricos.'
        else:
            try:
                nova_empresa = Empresa(nomeEmpresa=nomeEmpresa, cnpj=cnpj, contato=contato, cpfADM=cpfADM)
                db.session.add(nova_empresa)
                db.session.commit()
                return redirect(url_for('cadastroADM', cnpj=cnpj, cpfADM=cpfADM))
            except IntegrityError:
                db.session.rollback()
                msg = 'CNPJ ou CPF do Administrador já está registrado!'
            except DataError:
                db.session.rollback()
                msg = 'Erro nos dados fornecidos. Verifique os campos e tente novamente.'
            except SQLAlchemyError as e:
                db.session.rollback()
                msg = str(e)
    return render_template('cadastro.html', msg=msg)

@app.route('/cadastroADM', methods=['GET', 'POST'])
def cadastroADM():
    msg = ''
    cnpj = request.args.get('cnpj')
    cpfADM = request.args.get('cpfADM')
    if request.method == 'POST' and all(key in request.form for key in ['nome', 'fone', 'oab', 'email', 'senha']):
        nome = request.form['nome']
        fone = request.form['fone']
        oab = request.form['oab']
        email = request.form['email']
        senha = request.form['senha']
        imagem = request.files.get('imagem')

        # Verificação se o email já está registrado
        if Login.query.filter_by(email=email).first():
            msg = 'Email já registrado!'
        else:
            if imagem and allowed_file(imagem.filename):
                filename = secure_filename(imagem.filename)
                unique_filename = str(uuid.uuid4()) + os.path.splitext(filename)[1]
                imagem.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))
                imagem_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            else:
                imagem_path = None

            try:
                novo_adm = ADM(nome=nome, fone=fone, oab=oab, email=email, senha=senha, cnpj=cnpj, cpfADM=cpfADM, imagem=imagem_path)
                novo_login = Login(email=email, senha=senha)
                db.session.add(novo_adm)
                db.session.add(novo_login)
                db.session.commit()
                msg = 'Administrador cadastrado com sucesso!'
                return redirect(url_for('home'))
            except IntegrityError:
                db.session.rollback()
                msg = 'Erro ao registrar o administrador. Verifique os dados e tente novamente.'
            except DataError:
                db.session.rollback()
                msg = 'Erro nos dados fornecidos. Verifique os campos e tente novamente.'
            except SQLAlchemyError as e:
                db.session.rollback()
                msg = str(e)
    return render_template('cadastroADM.html', msg=msg, cnpj=cnpj, cpfADM=cpfADM)





if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
