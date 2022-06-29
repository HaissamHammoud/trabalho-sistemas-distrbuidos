from flask import Flask, jsonify, redirect , render_template, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from  random import randint
from logger import *
import requests
import json
app = Flask(__name__)

SECRET = "segredosecreto"

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

class Validador(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ip = db.Column(db.String(20), unique=True) 
    nome = db.Column(db.String(20), unique=False, nullable=False)
    stack = db.Column(db.Float())
    ativo = db.Column(db.Boolean())

    def __repr__(self):
        return f"{{nome: {self.nome} ip: {self.ip}, stack: {self.stack}, ativo: {self.ativo} }}"

@app.route('/validador', methods=['POST'])
def createValidador():
    request_data = request.get_json()
    _ip = request_data['ip']
    _nome = request_data['nome']
    try:
        validador = Validador(nome = _nome, ip = _ip, stack=0, ativo=True)
        db.session.add(validador)
        db.session.commit() 
    except:
        db.session.rollback()
        validador = Validador.query.get(_ip)
        if validador is not None:
            return {"status": "200", "secret": "segredosecreto"}
        else:
            return {"status": "400"}
    log(f"Validador {_nome} cadastrado com sucesso")
    return {"status": "200", "secret": "segredosecreto", "Message": "Validador registrado com sucesso"}

@app.route('/delete/<int:_id>', methods=['DELETE'])
def deleteUser(_id):
    validador = Validador.query.get(_id)
    if not validador:
        return {"status":"403", "message":"not found"}
    db.session.delete(validador)
    db.session.commit()
    return {"status": "ok", "message":"Usuario removido com sucesso"}
    
@app.route('/usercheck', methods=['POST'])
def checkUser():
    request_data = request.get_json()
    _ip = request_data['ip']
    validador = Validador.query.filter_by(ip=_ip).first()
    if not validador:
        return {"status":"400"}
    return {"status":"200"}

@app.route('/user/<int:_id>', methods=['GET'])
def getUser(_id):
    validador = Validador.query.get(_id)
    if validador is None:
        return {"status":"403", "message":"not found"}
    return str(validador)


@app.route('/ativa', methods=['POST'])
def ativaValidador():
    request_data = request.get_json()
    _ip = request_data['ip']
    validador = Validador.query.filter_by(ip=_ip).first()
    db.session.commit()
    validador.ativo = True
    db.session.commit()
    log(f"Validador com ip: {_ip} agora esta ativado")
    return {"secret": "segredosecreto"}

@app.route('/user', methods=['GET'])
def listaValidadores():
    if(request.method == 'GET'):
        validador = Validador.query.all()
        return jsonify(str(validador))

@app.route('/statusfinal', methods=['POST'])
def recompensa():
    request_data = request.get_json()
    transacao_id = request_data['transacao']
    status = request_data['status']
    f = open("logs/transacao"+str(transacao_id)+".txt", "r")
    resultados = f.read().split("\n")
    del resultados[-1]
    for result in resultados:
        resultado = json.loads(result)
        validadores = Validador.query.filter_by(ip=resultado["ip"]).all()
        for validador in validadores:
            if str(resultado["status"]) == str(status):
                validador.stack +=20
            else:
                validador.stack -=20
            db.session.commit()
    f.close()
    return {"mensagem": "Alterado com sucesso"}


@app.route('/validar', methods=['POST'])
def validar():
    result = 0
    # 0 - Formata os dados da transacao
    request_data = request.get_json()
    # 1 - Busca os validadores disponives
    validadores = Validador.query.filter_by(ativo=True).all()
    # 2 - Envia para os validadores disponiveis as informações recebidas pelos gerenciadores
    respostas = []
    try:
        for validador in validadores:
            validador = validador.__dict__
            host_validador = validador["ip"]
            resposta = requests.post("http://"+host_validador+"/validar", json = request_data, timeout=20)
            respostas.append(resposta.json())
    except requests.Timeout:
        log(f"Timeout na conecção do validador com ip {host_validador}")
    except requests.ConnectionError:
        log(f"Conecção interrompida no validador com ip {host_validador}")

    # 4 - Verifica se o token retornado é o token gerado na criacao
    f = open(f"logs/transacao{request_data['id']}.txt", "a")
    for resp in respostas:
        if resp["segredo"] == SECRET:
            if resp["status_transacao"] == "1":
                result +=1
            elif resp["status_transacao"] == "2":
                result -=1
            data = '{"ip": "'+resp["ip"]+'","status": "'+ resp["status_transacao"]+'"}'
        else:
            data = '{"ip": "'+resp["ip"]+'","status": -1}'
        
        f.write(data+"\n")
    f.close()
    # 5 - Retorna as informações para o gerenciador
    if result >=0: 
        log("Transacao concluida com status 1")
        return jsonify([{"valor":"1"}])
    else:
        log("Transacao concluida com status 2")
        return jsonify([{"valor":"2"}])

if __name__ == '__main__':
    db.create_all()
    validadores = Validador.query.filter_by(ativo=True)
    for validador in validadores:
        validador.ativo = False
        db.session.commit() 
    app.run(port=5001)