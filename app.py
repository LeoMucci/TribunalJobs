from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError, DataError, IntegrityError
from flask_mail import Mail, Message
import re, os
from werkzeug.utils import secure_filename
import uuid
import random

app = Flask(__name__)
app.secret_key = 'tribunaljobs'

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:081314@localhost/tribunaljobs'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_PATH'] = 1024 * 1024

# Configurações do Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'tribunaljobs@gmail.com'
app.config['MAIL_PASSWORD'] = "rkpy dxuj niwp rqrc"
app.config['MAIL_DEFAULT_SENDER'] = 'tribunaljobs@gmail.com'

mail = Mail(app)
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
    imagem = db.Column(db.String(255))

class Advogados(db.Model):
    __tablename__ = 'advogados'
    IdAdv = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome = db.Column(db.String(255), nullable=False)
    cpf = db.Column(db.String(11), nullable=False, unique=True)
    fone = db.Column(db.String(20))
    oab = db.Column(db.String(20))
    email = db.Column(db.String(255), nullable=False, unique=True)
    senha = db.Column(db.String(255), nullable=False)
    imagem = db.Column(db.String(255))  # Campo para armazenar o caminho da imagem
    IdADM = db.Column(db.Integer, db.ForeignKey('ADM.IdADM'))
    IdEmpresa = db.Column(db.String(14), db.ForeignKey('Empresa.cnpj'))

    adm = db.relationship('ADM', backref='advogados')
    empresa = db.relationship('Empresa', backref='advogados')

class Cliente(db.Model):
    __tablename__ = 'cliente'
    IdCliente = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome = db.Column(db.String(255), nullable=False)
    cpf = db.Column(db.String(11), nullable=False, unique=True)
    fone = db.Column(db.String(20))
    email = db.Column(db.String(255), nullable=False)
    dtNascimento = db.Column(db.Date, nullable=False)
    causa = db.Column(db.Text)
    IdAdv = db.Column(db.Integer, db.ForeignKey('advogados.IdAdv'))
    imagem = db.Column(db.String(255))

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
                return redirect(url_for('Home'))
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

@app.route('/Home')
def Home():
    if 'loggedin' in session:
        adm = ADM.query.filter_by(email=session['email']).first()
        if adm:
            role = "Administrador"
            return render_template('home.html', user=adm, role=role)

        advogado = Advogados.query.filter_by(email=session['email']).first()
        if advogado:
            role = "Advogado"
            return render_template('home.html', user=advogado, role=role)

        return "Erro: Usuário não encontrado."
    return redirect(url_for('login'))

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    msg = ''
    if request.method == 'POST' and all(key in request.form for key in ['nomeEmpresa', 'cnpj', 'contato', 'cpfADM']):
        nomeEmpresa = request.form['nomeEmpresa']
        cnpj = request.form['cnpj']
        contato = request.form['contato']
        cpfADM = request.form['cpfADM']

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

        if Login.query.filter_by(email=email).first():
            msg = 'Email já registrado!'
        else:
            if imagem and allowed_file(imagem.filename):
                filename = secure_filename(imagem.filename)
                unique_filename = str(uuid.uuid4()) + os.path.splitext(filename)[1]
                imagem.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))
                imagem_path = os.path.join('static/uploads', unique_filename)
            else:
                imagem_path = None

            try:
                novo_adm = ADM(nome=nome, fone=fone, oab=oab, email=email, senha=senha, cnpj=cnpj, cpfADM=cpfADM, imagem=imagem_path)
                novo_login = Login(email=email, senha=senha)
                db.session.add(novo_adm)
                db.session.add(novo_login)
                db.session.commit()
                msg = 'Administrador cadastrado com sucesso!'
                return redirect(url_for('login'))
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

@app.route('/CadastroAdvogado', methods=['GET', 'POST'])
def cadastro_advogado():
    msg = ''
    msg_type = ''
    IdADM = session.get('id')
    adm = ADM.query.filter_by(IdADM=IdADM).first()
    IdEmpresa = None
    if adm:
        empresa = Empresa.query.filter_by(cpfADM=adm.cpfADM).first()
        if empresa:
            IdEmpresa = empresa.cnpj
    
    if request.method == 'POST' and all(key in request.form for key in ['nome', 'cpf', 'fone', 'oab', 'email', 'senha']):
        nome = request.form['nome']
        cpf = request.form['cpf']
        fone = request.form['fone']
        oab = request.form['oab']
        email = request.form['email']
        senha = request.form['senha']
        
        # Processar a imagem do advogado
        imagem = request.files.get('file')
        imagem_path = None
        if imagem and allowed_file(imagem.filename):
            filename = secure_filename(imagem.filename)
            unique_filename = str(uuid.uuid4()) + os.path.splitext(filename)[1]
            imagem_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            imagem.save(imagem_path)
            imagem_path = f'static/uploads/{unique_filename}'  # Caminho relativo para salvar no banco de dados

        # Verificar se o email ou CPF já existe na tabela Advogados ou Login
        if Advogados.query.filter((Advogados.email == email) | (Advogados.cpf == cpf)).first() or Login.query.filter_by(email=email).first():
            msg = 'Email ou CPF já registrado!'
            msg_type = "error"
        else:
            try:
                # Cadastrar novo advogado com a imagem
                novo_advogado = Advogados(nome=nome, cpf=cpf, fone=fone, oab=oab, email=email, senha=senha, IdADM=IdADM, IdEmpresa=IdEmpresa, imagem=imagem_path)
                
                # Cadastrar email e senha na tabela Login
                novo_login = Login(email=email, senha=senha)
                
                db.session.add(novo_advogado)
                db.session.add(novo_login)
                db.session.commit()
                
                msg = 'Advogado cadastrado com sucesso!'
                msg_type = "success"
            except IntegrityError:
                db.session.rollback()
                msg = 'Erro ao registrar o advogado. Verifique os dados e tente novamente.'
                msg_type = "error"
            except DataError:
                db.session.rollback()
                msg = 'Erro nos dados fornecidos. Verifique os campos e tente novamente.'
                msg_type = "error"
            except SQLAlchemyError as e:
                db.session.rollback()
                msg = str(e)
                msg_type = "error"
    return render_template('CadastroAdvogado.html', msg=msg, msg_type=msg_type, IdADM=IdADM, IdEmpresa=IdEmpresa)

@app.route('/CadastroCliente', methods=['GET', 'POST'])
def CadastroCliente():
    msg = ''
    msg_type = ''
    if request.method == 'POST' and all(key in request.form for key in ['nome', 'cpf', 'fone', 'email', 'dtNascimento', 'causa', 'IdAdv']):
        nome = request.form['nome']
        cpf = request.form['cpf']
        fone = request.form['fone']
        email = request.form['email']
        dtNascimento = request.form['dtNascimento']
        causa = request.form['causa']
        IdAdv = request.form['IdAdv']

        # Verificar se o ID do advogado informado existe
        advogado = Advogados.query.filter_by(IdAdv=IdAdv).first()
        if not advogado:
            msg = 'ID do Advogado não encontrado. Verifique e tente novamente.'
            msg_type = 'error'
        else:
            # Processar a imagem do cliente
            imagem = request.files.get('file')
            imagem_path = None
            if imagem and allowed_file(imagem.filename):
                filename = secure_filename(imagem.filename)
                unique_filename = str(uuid.uuid4()) + os.path.splitext(filename)[1]
                imagem_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                imagem.save(imagem_path)
                imagem_path = f'static/uploads/{unique_filename}'

            # Verificar se o CPF já existe
            if Cliente.query.filter_by(cpf=cpf).first():
                msg = 'CPF já registrado!'
                msg_type = 'error'
            else:
                try:
                    novo_cliente = Cliente(
                        nome=nome,
                        cpf=cpf,
                        fone=fone,
                        email=email,
                        dtNascimento=dtNascimento,
                        causa=causa,
                        IdAdv=IdAdv,
                        imagem=imagem_path
                    )
                    db.session.add(novo_cliente)
                    db.session.commit()
                    msg = 'Cliente cadastrado com sucesso!'
                    msg_type = 'success'
                except IntegrityError:
                    db.session.rollback()
                    msg = 'Erro ao registrar o cliente. Verifique os dados e tente novamente.'
                    msg_type = 'error'
                except DataError:
                    db.session.rollback()
                    msg = 'Erro nos dados fornecidos. Verifique os campos e tente novamente.'
                    msg_type = 'error'
                except SQLAlchemyError as e:
                    db.session.rollback()
                    msg = str(e)
                    msg_type = 'error'

    return render_template('CadastroCliente.html', msg=msg, msg_type=msg_type)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
