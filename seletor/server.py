from flask import Flask, redirect , render_template, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from  random import randint
from logger import *
import requests
app = Flask(__name__)

SECRET = "sergredosecreto"

initLogger()
log("Iniciando a instancia")
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///teste2.db'
db = SQLAlchemy(app)
migrate = Migrate(app, db)
url = "http://localhost:5000/seletor/validadorjh/127.0.0.1"
x = requests.post(url, json = "")

@app.before_first_request
def create_tables():
    db.create_all()

def getHora():
    #retorna a hora do sistema do gerenciador
    url = "http://localhost:5000/hora"
    hora = request.get(url)
    return hora


class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(20), unique=False, nullable=False)
    saldo = db.Column(db.Float())
    def __repr__(self):
        return f"{{Nome : {self.nome}, Saldo: {self.saldo} }}"

class Validador(db.Model):
    ip = db.Column(db.String(20), primary_key=True) 
    stack = db.Column(db.Float())

    def __repr__(self):
        return f"{{ ip: {ip}, stack: {stack } }}" 
    
# @app.route('/createuser', methods=['POST'])
# def createUser():
#     request_data = request.get_json()
#     _nome = request_data['nome']
#     _saldo = request_data['valor']
#     usuario = Usuario(nome = _nome, saldo=_saldo)
#     db.session.add(usuario)
#     db.session.commit()
#     return {"status": "ok", "message": "Usuario criado com sucesso"}

@app.route('/validador', methods=['POST'])
def createValidador():
    request_data = request.get_json()
    _ip = request_data['ip']
    _stack = 0
    try:
        validador = Validador(ip = _ip, stack=_stack)
        db.session.add(validador)
        db.session.commit() 
    except:
        db.session.rollback()
        validador = Validador.query.get(_ip)
        if validador is not None:
            return {"status": "200", "secret": "segredosecreto"}
        else:
            return {"status": "400"}

    return {"status": "200", "secret": "segredosecreto", "Message": "Validador registrado com sucesso"}

# @app.route('/updateuser/<int:_id>', methods=['PUT'])
# def updateUser(_id):
#     request_data = request.get_json()
#     _nome = request_data['nome']
#     _saldo = request_data['valor']
#     num_rows_updated = Usuario.query.filter_by(id=_id).update(dict(nome=_nome, saldo=_saldo))
#     db.session.commit()
#     return {"status": "200", "message": "usuario atualizado com sucesso"}

@app.route('/delete/<int:_id>', methods=['DELETE'])
def deleteUser(_id):
    usuario = Usuario.query.get(_id)
    if usuario is None:
        return {"status":"403", "message":"not found"}
    db.session.delete(usuario)
    db.session.commit()
    return {"status": "ok", "message":"Usuario removido com sucesso"}
    

@app.route('/get/<int:_id>', methods=['GET'])
def getUser(_id):
    usuario = Usuario.query.get(_id)

    if usuario is None:
        return {"status":"403", "message":"not found"}
    return str(usuario)

def elect(names, number_values):
    print(number_values)
    value = randint(0, number_values-1)
    return value

#talvez não precise mais
# @app.route('/eleger', methods=['PUT'])
# def eleger():
#     usuarios = Usuario.query.all()
#     size = len(usuarios)
#     elected = elect(usuarios, size)
#     print(usuarios[elected])
#     return str(usuarios[elected]) 


@app.route('/validar', methods=['POST'])
def validar():
    # 1 - Busca os validadores disponives
    # 2 - Envia para os validadores disponiveis as informações recebidas pelos gerenciadores
    # 3 - Recebe as informações recebida
    # 4 - Verifica se o token retornado é o token gerado na criacao
    # 4 - Retorna as informações para o gerenciador
    requests.post()
    request_data = request.get_json()
    key = request_data['key']
    login = request_data['name']
    valor = request_data['valor']
    print(login + str(valor) + login)
    if key == login + str(valor) + login:
        return {"status": "valid"}
    return {"status":"invalid"}

if __name__ == '__main__':
    app.run(debug=True, port=5001)