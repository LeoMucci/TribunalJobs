from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError, DataError, IntegrityError
from flask_mail import Mail, Message
import re, os
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from flask import flash
import uuid
import random
import openai

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
    cpfADM = db.Column(db.String(14), nullable=False, unique=True)

class ADM(db.Model):
    __tablename__ = 'ADM'
    IdADM = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome = db.Column(db.String(255), nullable=False)
    fone = db.Column(db.String(20))
    oab = db.Column(db.String(20))
    email = db.Column(db.String(255), nullable=False)
    senha = db.Column(db.String(255), nullable=False)
    cnpj = db.Column(db.String(14), db.ForeignKey('Empresa.cnpj'))
    cpfADM = db.Column(db.String(14), db.ForeignKey('Empresa.cpfADM'))
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
    descricaoCausa = db.Column(db.Text)  # Novo campo
    IdAdvogado = db.Column(db.Integer, db.ForeignKey('advogados.IdAdv'), nullable=True)
    IdADM = db.Column(db.Integer, db.ForeignKey('ADM.IdADM'), nullable=True)
    imagem = db.Column(db.String(255))


class Conversas(db.Model):
    __tablename__ = 'Conversas'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('Login.IdUser'), nullable=True)
    mensagem = db.Column(db.Text, nullable=False)
    resposta = db.Column(db.Text, nullable=False)
    data_hora = db.Column(db.DateTime, default=db.func.current_timestamp())

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

@app.before_request
def load_user_data():
    if 'loggedin' in session:
        email = session.get('email')
        adm = ADM.query.filter_by(email=email).first()
        advogado = Advogados.query.filter_by(email=email).first()
        if adm:
            session['user_info'] = {
                "name": adm.nome,
                "role": "Administrador",
                "image_url": adm.imagem or "https://via.placeholder.com/40"
            }
        elif advogado:
            session['user_info'] = {
                "name": advogado.nome,
                "role": "Advogado",
                "image_url": advogado.imagem or "https://via.placeholder.com/40"
            }

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
        advogado = Advogados.query.filter_by(email=session['email']).first()
        clientes = []

        # Obter os clientes associados ao administrador ou advogado logado
        if adm:
            role = "Administrador"
            clientes = Cliente.query.filter_by(IdADM=adm.IdADM).all()
            return render_template('home.html', user=adm, role=role, clientes=clientes)
        
        elif advogado:
            role = "Advogado"
            clientes = Cliente.query.filter_by(IdAdvogado=advogado.IdAdv).all()
            return render_template('home.html', user=advogado, role=role, clientes=clientes)

        return "Erro: Usuário não encontrado."
    return redirect(url_for('login'))

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    msg = ''
    if request.method == 'POST':
        nomeEmpresa = request.form.get('nomeEmpresa', '')
        cnpj = request.form.get('cnpj', '')
        contato = request.form.get('telefone', '')  # Capturando o campo "telefone" do formulário
        cpfADM = request.form.get('cpfADM', '')

        if not re.match(r'^\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}$', cnpj):
            msg = 'CNPJ inválido. Deve estar no formato XX.XXX.XXX/XXXX-XX.'
        elif not re.match(r'^\d{3}\.\d{3}\.\d{3}-\d{2}$', cpfADM):
            msg = 'CPF do Administrador inválido. Deve estar no formato XXX.XXX.XXX-XX.'
        else:
            try:
                nova_empresa = Empresa(nomeEmpresa=nomeEmpresa, cnpj=cnpj, contato=contato, cpfADM=cpfADM)
                db.session.add(nova_empresa)
                db.session.commit()

                # Passa a mensagem de sucesso para o redirecionamento
                return redirect(url_for('cadastroADM', cnpj=cnpj, cpfADM=cpfADM, success_msg=f"A Empresa {nomeEmpresa} foi cadastrada com sucesso! Agora, cadastre o Administrador da empresa."))
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

                # Mensagem de sucesso
                flash(f"Administrador {nome} foi cadastrado com sucesso!")
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
    email_usuario = session.get('email')
    IdAdvogado = None
    IdADM = None
    cpf_editable = False  # Inicializar como False

    # Verificar se o usuário logado é um Advogado ou ADM e definir a FK correspondente
    if email_usuario:
        advogado = Advogados.query.filter_by(email=email_usuario).first()
        if advogado:
            IdAdvogado = advogado.IdAdv
            cpfAdv = advogado.cpf  # CPF do advogado logado
        else:
            adm = ADM.query.filter_by(email=email_usuario).first()
            if adm:
                IdADM = adm.IdADM
                cpfAdv = adm.cpfADM  # CPF do ADM logado
                cpf_editable = True  # Permitir edição do CPF para ADM

    if request.method == 'POST' and all(key in request.form for key in ['nome', 'cpf', 'fone', 'email', 'dtNascimento', 'causa']):
        nome = request.form['nome']
        cpf = request.form['cpf']
        fone = request.form['fone']
        email = request.form['email']
        dtNascimento = request.form['dtNascimento']
        causa = request.form['causa']
        descricaoCausa = request.form['descricaoCausa']

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
                # Criar o novo cliente com o ID do advogado ou ADM
                novo_cliente = Cliente(
                    nome=nome,
                    cpf=cpf,
                    fone=fone,
                    email=email,
                    dtNascimento=dtNascimento,
                    causa=causa,
                    descricaoCausa=descricaoCausa,
                    IdAdvogado=IdAdvogado if IdAdvogado else None,  # FK para Advogado, ou None se não for aplicável
                    IdADM=IdADM if IdADM else None,                   # FK para ADM, ou None se não for aplicável
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

    return render_template('CadastroCliente.html', msg=msg, msg_type=msg_type, cpfAdv=cpfAdv, cpf_editable=cpf_editable)

@app.route('/TJHome', methods=['GET', 'POST'])
def TJHome():
    email_usuario = session.get('email')
    clientes = []
    msg = ''  # Mensagem para exibir o resultado da operação

    if email_usuario:
        advogado = Advogados.query.filter_by(email=email_usuario).first()
        adm = ADM.query.filter_by(email=email_usuario).first()

        # Obter o termo de busca
        search_query = request.args.get('search', '')

        # Se o termo de busca está vazio, retorna todos os clientes
        if advogado:
            if search_query:
                clientes = Cliente.query.filter(
                    Cliente.IdAdvogado == advogado.IdAdv,
                    (Cliente.nome.ilike(f'%{search_query}%') | Cliente.cpf.ilike(f'%{search_query}%'))
                ).all()
            else:
                clientes = Cliente.query.filter_by(IdAdvogado=advogado.IdAdv).all()
        elif adm:
            if search_query:
                clientes = Cliente.query.filter(
                    Cliente.IdADM == adm.IdADM,
                    (Cliente.nome.ilike(f'%{search_query}%') | Cliente.cpf.ilike(f'%{search_query}%'))
                ).all()
            else:
                clientes = Cliente.query.filter_by(IdADM=adm.IdADM).all()

        # Verifica se o formulário de exclusão foi enviado
        if request.method == 'POST' and 'excluir' in request.form:
            cliente_id = request.form['id_cliente']  # Obtém o ID do cliente a ser excluído
            cliente = Cliente.query.get_or_404(cliente_id)
            try:
                db.session.delete(cliente)  # Exclui o cliente
                db.session.commit()  # Comita a transação
                flash('Cliente excluído com sucesso!', 'success')  # Flash de sucesso
            except SQLAlchemyError as e:
                db.session.rollback()  # Caso ocorra erro, faz rollback
                flash(f'Erro ao excluir cliente: {str(e)}', 'error')  # Flash de erro

            return redirect(url_for('TJHome'))  # Redireciona para a página home

    return render_template('TJHome.html', clientes=clientes, msg=msg)



load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route('/TJDuvidas')
def TJDuvidas():
    if 'loggedin' in session:
        user_id = session['id']
        conversas = Conversas.query.filter_by(usuario_id=user_id).order_by(Conversas.data_hora.desc()).limit(10).all()

        # Buscar as informações do usuário logado
        adm = ADM.query.filter_by(IdADM=user_id).first()
        if adm:
            role = "Administrador"
            user_info = {
                "name": adm.nome,
                "role": role,
                "image_url": adm.imagem or "https://via.placeholder.com/40"
            }
        else:
            advogado = Advogados.query.filter_by(IdAdv=user_id).first()
            if advogado:
                role = "Advogado"
                user_info = {
                    "name": advogado.nome,
                    "role": role,
                    "image_url": advogado.imagem or "https://via.placeholder.com/40"
                }
            else:
                return "Erro: Usuário não encontrado."

        return render_template('TJDuvidas.html', conversas=conversas, user=user_info)

    return redirect(url_for('login'))


@app.route('/api/chat', methods=['POST'])
def chat_api():
    data = request.get_json()
    user_message = data.get('message')
    user_id = session.get('id')  # Pega o ID do usuário logado

    if not user_message:
        return jsonify({"error": "Mensagem vazia"}), 400

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Você é um assistente que só pode tirar dúvidas jurídicas."},
                {"role": "user", "content": user_message}
            ]
        )
        ai_response = response['choices'][0]['message']['content']

        # Salvar a conversa no banco de dados
        nova_conversa = Conversas(usuario_id=user_id, mensagem=user_message, resposta=ai_response)
        db.session.add(nova_conversa)
        db.session.commit()

        return jsonify({"response": ai_response})
    except Exception as e:
        print(f"Erro ao chamar a API do OpenAI: {e}")
        return jsonify({"error": "Desculpe, ocorreu um erro ao tentar obter uma resposta."}), 500
@app.route('/EsqueciSenha', methods=['GET', 'POST'])
def EsqueciSenha():
    msg = ''
    if request.method == 'POST' and 'cpf' in request.form:
        cpf = request.form['cpf']
        print(f"CPF recebido: {cpf}")  # Debug: imprimir o CPF recebido
        adm = ADM.query.filter_by(cpfADM=cpf).first()
        print(f"ADM encontrado: {adm}")  # Debug: imprimir se encontrou um ADM

        if adm:
            email = adm.email
            session['email'] = email  # Armazenar o email na sessão
            print(f"E-mail do ADM: {email}")  # Debug: imprimir o e-mail encontrado
        else:
            msg = 'CPF não encontrado.'
            print(msg)  # Debug: imprimir mensagem de erro
            return render_template('EsqueciSenha.html', msg=msg)

        # Gerar código de verificação
        codigo_verificacao = ''.join(random.choices('0123456789', k=4))
        print(f"Código de verificação gerado: {codigo_verificacao}")  # Debug: imprimir o código gerado

        # Enviar e-mail com código de verificação
        try:
            msg_email = Message('Código de Verificação - Tribunal Jobs', recipients=[email])
            msg_email.body = f'Seu código de verificação é: {codigo_verificacao}'
            mail.send(msg_email)
            session['codigo_verificacao'] = codigo_verificacao
            session['cpf'] = cpf
            return redirect(url_for('EsqueciSenhaVerificacao'))
        except Exception as e:
            msg = f'Erro ao enviar o e-mail: {str(e)}'
            print(msg)  # Debug: imprimir mensagem de erro de envio de e-mail
    return render_template('EsqueciSenha.html', msg=msg)

def mask_email(email):
    local, domain = email.split('@')
    if len(local) > 3:
        masked_local = local[:3] + '*' * (len(local) - 3)
    else:
        masked_local = '*' * len(local)
    return f"{masked_local}@{domain}"

@app.route('/EsqueciSenhaVerificacao', methods=['GET', 'POST'])
def EsqueciSenhaVerificacao():
    msg = ''
    email = session.get('email')
    masked_email = mask_email(email)  # Mascarar o e-mail aqui
    if request.method == 'POST':
        codigo_digitado = ''.join([request.form.get(f'code{i}') for i in range(1, 5)])
        if codigo_digitado == session.get('codigo_verificacao'):
            return redirect(url_for('EsqueciSenhaNovaSenha'))
        else:
            msg = 'Código de verificação incorreto.'
    return render_template('EsqueciSenhaVerificacao.html', msg=msg, email=masked_email)

@app.route('/reenviar_codigo', methods=['POST'])
def reenviar_codigo():
    email = session.get('email')
    if email:
        # Gerar novo código de verificação
        codigo_verificacao = ''.join(random.choices('0123456789', k=4))
        session['codigo_verificacao'] = codigo_verificacao
        try:
            msg_email = Message('Novo Código de Verificação - Tribunal Jobs', recipients=[email])
            msg_email.body = f'Seu novo código de verificação é: {codigo_verificacao}'
            mail.send(msg_email)
            return jsonify({'msg': 'Novo código enviado para o seu e-mail.'})
        except Exception as e:
            return jsonify({'msg': f'Erro ao enviar o e-mail: {str(e)}'})
    else:
        return jsonify({'msg': 'E-mail não encontrado na sessão.'})

@app.route('/EsqueciSenhaNovaSenha', methods=['GET', 'POST'])
def EsqueciSenhaNovaSenha():
    msg = ''
    if request.method == 'POST':
        nova_senha = request.form.get('nova_senha')
        confirmacao_senha = request.form.get('confirmacao_senha')
        
        if nova_senha and confirmacao_senha:
            if nova_senha == confirmacao_senha:
                cpf = session.get('cpf')
                if cpf:
                    adm = ADM.query.filter_by(cpfADM=cpf).first()
                    if adm:
                        login = Login.query.filter_by(email=adm.email).first()
                        if login:
                            login.senha = nova_senha
                            adm.senha = nova_senha
                            db.session.commit()
                            msg = 'Senha atualizada com sucesso!'
                            return redirect(url_for('EsqueciSenhaConcluido'))
                        else:
                            msg = 'Erro ao encontrar o login associado.'
                    else:
                        msg = 'Erro ao encontrar o administrador associado.'
                else:
                    msg = 'CPF não encontrado na sessão.'
            else:
                msg = 'As senhas não coincidem.'
        else:
            msg = 'Preencha todos os campos.'
    return render_template('EsqueciSenhaNovaSenha.html', msg=msg)

@app.route('/EsqueciSenhaConcluido')
def EsqueciSenhaConcluido():
    return render_template('EsqueciSenhaConcluido.html')

@app.route('/TJDuvidasClientes')
def TJDuvidasClientes():
    return render_template('TJDuvidasClientes.html')


@app.route('/EditarCliente/<int:id>', methods=['GET', 'POST'])
def EditarCliente(id):
    cliente = Cliente.query.get_or_404(id)
    msg = ''

    if request.method == 'POST':
        cliente.nome = request.form['nome']
        cliente.cpf = request.form['cpf']
        cliente.email = request.form['email']
        cliente.fone = request.form['fone']
        cliente.dtNascimento = request.form['dtNascimento']
        cliente.causa = request.form['causa']
        cliente.descricaoCausa = request.form['descricaoCausa']  # Atualizar o campo aqui

        try:
            db.session.commit()
            msg = 'Cliente atualizado com sucesso!'
            
        except SQLAlchemyError as e:
            db.session.rollback()
            msg = f'Erro ao atualizar cliente: {str(e)}'

    return render_template('EditarCliente.html', cliente=cliente, msg=msg)


@app.route('/GerenciaAdv', methods=['GET', 'POST'])
def GerenciaAdv():
    email_usuario = session.get('email')
    advogados = []  # Lista que irá armazenar os advogados filtrados
    msg = ''  # Mensagem para exibir o resultado da operação

    if email_usuario:
        # Busca o advogado ou administrador relacionado ao e-mail do usuário
        advogado = Advogados.query.filter_by(email=email_usuario).first()
        adm = ADM.query.filter_by(email=email_usuario).first()

        # Se o formulário for do tipo POST e houver um ID de advogado a ser excluído
        if request.method == 'POST' and 'excluir_id' in request.form:
            advogado_id = request.form['excluir_id']
            advogado_a_excluir = Advogados.query.get(advogado_id)
            if advogado_a_excluir:
                try:
                    db.session.delete(advogado_a_excluir)  # Deleta o advogado
                    db.session.commit()  # Confirma a exclusão
                    msg = "Advogado excluído com sucesso!"  # Mensagem de sucesso
                except Exception as e:
                    db.session.rollback()  # Rollback em caso de erro
                    msg = f"Ocorreu um erro ao excluir o advogado: {str(e)}"  # Mensagem de erro

        # Obter o termo de busca
        search_query = request.args.get('search', '')

        # Se o termo de busca está vazio, retorna todos os advogados
        if advogado:
            if search_query:
                # Filtra os advogados associados ao advogado logado, com base no nome ou OAB
                advogados = Advogados.query.filter(
                    Advogados.IdAdv == advogado.IdAdv,
                    (Advogados.nome.ilike(f'%{search_query}%') | Advogados.oab.ilike(f'%{search_query}%'))
                ).all()
            else:
                # Retorna todos os advogados relacionados ao advogado logado
                advogados = Advogados.query.filter_by(IdAdv=advogado.IdAdv).all()
        elif adm:
            if search_query:
                # Filtra os advogados associados ao administrador, com base no nome ou OAB
                advogados = Advogados.query.filter(
                    Advogados.IdADM == adm.IdADM,
                    (Advogados.nome.ilike(f'%{search_query}%') | Advogados.oab.ilike(f'%{search_query}%'))
                ).all()
            else:
                # Retorna todos os advogados relacionados ao administrador logado
                advogados = Advogados.query.filter_by(IdADM=adm.IdADM).all()

    return render_template('GerenciaAdv.html', advogados=advogados, msg=msg)


@app.route('/editar_advogado/<int:id>', methods=['GET', 'POST'])
def editar_advogado(id):
    # Busca o advogado no banco de dados
    advogado = Advogados.query.get_or_404(id)
    
    if request.method == 'POST':
        # Atualiza os campos com os dados do formulário
        advogado.nome = request.form['nome']
        advogado.email = request.form['email']
        advogado.senha = request.form['senha']
        advogado.cpf = request.form['cpf']
        advogado.oab = request.form['oab']
        advogado.fone = request.form['fone']
        
        # Se o arquivo de imagem foi enviado, atualiza o campo de imagem
        if 'file' in request.files:
            imagem = request.files['file']
            if imagem:
                # Salve a imagem no diretório desejado e obtenha o caminho
                # Exemplo de como salvar:
                imagem_path = 'static/images/' + imagem.filename
                imagem.save(imagem_path)
                advogado.imagem = imagem_path

        try:
            db.session.commit()  # Salva as alterações no banco de dados
            flash('Advogado atualizado com sucesso!', 'success')
            return redirect(url_for('GerenciaAdv'))  # Redireciona para a página de listagem de advogados
        except Exception as e:
            db.session.rollback()  # Rollback em caso de erro
            flash(f'Ocorreu um erro ao atualizar o advogado: {str(e)}', 'error')
    
    # Preenche o formulário com os dados do advogado
    return render_template('EditarAdvogado.html', advogado=advogado)



if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
