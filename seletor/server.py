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

@app.route('/validar', methods=['POST'])
def validar():
    # 0 - Formata os dados d transacao
    request_data = request.get_json()
    obj = {
        id_usuario : request_data['remetente'],
        valor : request_data['valor'],
        status : request_data['status'],
        id_transacao : request_data["id"],
    }

    # 1 - Busca os validadores disponives
    
    validadores = Validador.query.all()
    # 2 - Envia para os validadores disponiveis as informações recebidas pelos gerenciadores
    respostas = []
    for validador in validadores:
        host_validador = validador["ip"]
        resposta = requests.post(host_validador+"/validar",obj.json())
        respostas.append(resposta)
    # 4 - Verifica se o token retornado é o token gerado na criacao
    for resp in respostas:
        if resp["segredo"] != f"{SECRET}":
            return {"status":"2"}

    # 4 - Retorna as informações para o gerenciador
    request_data = request.get_json()
    key = request_data['key']
    login = request_data['name']
    valor = request_data['valor']
    print(login + str(valor) + login)
    if key == login + str(valor) + login:
        return {"status": "1"}
    return {"status":"2"}

if __name__ == '__main__':
    app.run(debug=True, port=5001)