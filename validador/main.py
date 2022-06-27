from flask import Flask, redirect , render_template, request,jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from  random import randint
from datetime import datetime
import time
import requests
from logger import *

URL_GERENCIADOR ="http://localhost:5000"
URL_SELETOR  = "http://localhost:5001"
SECRET_TO_SELETOR= ""
HOST = "127.0.0.1"
PORT = 5019
app = Flask(__name__)

#indica o tempo de inicialização da instância
initLogger()
log("Iniciando a instancia")
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///teste2.db'
sessao = "validador-" + (datetime.now().strftime("%Y-%m-%d-%H-%M-%S"))  
log("Conectando ao banco de dados")
db = SQLAlchemy(app)
migrate = Migrate(app, db)
url = URL_SELETOR 

def connectToSeletor(url, numberOfTry=0, maxRetry = 3):
    url_to_seletor = HOST+":"+str(PORT)
    log(f"url to servidor = {url_to_seletor}")
    request_obj = {'ip': HOST+":"+str(PORT)}
    request_url = url + "/validador"
    try:
        x = requests.post(request_url, json = request_obj )
        print("mensagemseletor:", x.content)
        log(x.content)
        content_json = x.json()
        # SECRET_TO_SELETOR = x.content["secret"]
        log("status")
        print(content_json["status"])
        if content_json["status"] == "200":
            log("Conectado ao seletor com sucesso")
            SECRET_TO_SELETOR = content_json["secret"]
        else:
            SECRET_TO_SELETOR = content_json["secret"]
            return 1
    except:
        if numberOfTry*5 >= maxRetry * 5:
            log( f"nao foi possivel se conectar ao gerenciador, numero de tentativas: {numberOfTry}","ERROR")
        else:
            time.sleep(5 * numberOfTry)
            log("Não foi possivel conectar ao servidor, tentando conectar novamente")
            connectToSeletor(url, numberOfTry+1)

connectToSeletor(URL_SELETOR)

@app.before_first_request
def create_tables():
    db.create_all()

# def log(nivel, mensagem):
#     time = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
#     textoLog = f"{time} - {nivel} menssagem: {menssagem}"
#     print(textLog)
#     f = open(f"logs/{INSTANCE_TIME}_validador.txt", "a")
#     f.write(textlog)
#     f.close()
#     # abre um arquivo de log caso necessario
#     # escreve a string de mensagem no formato "%Y-%m-%d-%H-%M-%S nivel mensagem


class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(20), unique=False, nullable=False)
    saldo = db.Column(db.Float())
  
    def __repr__(self):
        return f"{{Nome : {self.nome}, Saldo: {self.saldo} }}"

def getHora():
    #retorna a hora do sistema do gerenciador
    url = URL_GERENCIADOR + "/hora"
    hora = requests.get(url)
    timeObject = hora.json()["tempo"]
    result = datetime.strptime(timeObject, "%m/%d/%Y, %H:%M:%S")
    log(f"tempo so servidor atualizado {result}: ")
    return result

def horarioValido(horarioTransacao):
    horario = getHora()
    if horario > datetime.strptime(horarioTransacao, "%m/%d/%Y, %H:%M:%S"):
        return True
    else:
        return False

def saldoValido(valorTransacao, idUsuario):
    endpoint = URL_GERENCIADOR + f"/clientes/{idUsuario}"
    response = requests.get(endpoint)
    response_json = response.json()
    saldo = response_json["qtdMoeda"]
    if valorTransacao > saldo:
        return False
    else:
        return True

def comportamentoValido(id_usuario):
        endpoint = URL_GERENCIADOR + f"/transacoes"
        respose = requests.get(endpoint)
        response_json = response.json()
        tempo = datetime.now() - timedelta(minutes=5)
        transacoes_usuario = [x for transacoes in response_json if transacoes["remetende"] == id_usuario and transacoes["horario"] > tempo ]
        transacoes_status = [ x for transacoes in transacoes_usuario if transacoes["status"] != 1]
        if transacoes_status.count() >= 4 :
            return False
        else:
            return True


def banirUsuario(motivo, transacao):
    id_usuario = transacao["id_usuario"]
    id_transacao = transacao["id_transacao"]
    horario = transacao["horario"]
    ## Essa função devera banir o usuario dependendo da infracao cometida
    log(f"Tempo passado pelo usuario de id {id_usuario} para transacao {id_transacao} e invalido","WARN")
    log(f"Usuario de id: {id_usuario} banido por: 20 sec","WARN")
    return motivo

def aprovarTransacao(transacao):
    id_usuario = transacao["id_usuario"]
    id_transacao = transacao["id_transacao"]
    horario = transacao["horario"]
    ## Essa função devera banir o usuario dependendo da infracao cometida
    log(f"Usuario {id_usuario} teve a transacao {id_transacao} aprovada")

def 
@app.route('/validar', methods=['POST'])
def validar():

    request_data = request.get_json()
    horario = request_data['horario']
    valor = request_data['valor']
    id_usuario = request_data['id_usuario']
    log(f"validar: Usuario de id {id_usuario} valor: {valor}")
    if not saldoValido(valor, id_usuario):
        return jsonify(['"status": "403, "message": "Saldo insuficiente","status_transacao": "2"']) 
    isValidTime = horarioValido(horario)
    if not horarioValido(horario):
        banirUsuario("Tempo unvalido",request_data)
        return jsonify(['"status": "403, "message": "horario invalido", "status_transacao": "2"'])
    if not comportamentoValido(id_usuario):
        banirUsuario("Tempo unvalido",request_data)
        return jsonify(['"status": "403, "message": "comportamento suspeito", "status_transacao": "2"'])

    aprovarTransacao(request_data)
    return jsonify([f'"status": "200", "status_transacao": "1", "segredo": "{SECRET_TO_SELETOR}"'])

if __name__ == '__main__':
    app.run(debug=True, port=PORT)