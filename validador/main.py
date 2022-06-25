from flask import Flask, redirect , render_template, request,jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from  random import randint
from datetime import datetime
import time
import requests
from logger import *

app = Flask(__name__)

#indica o tempo de inicialização da instância
initLogger()
log("Iniciando a instancia")
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///teste2.db'
sessao = "validador-" + (datetime.now().strftime("%Y-%m-%d-%H-%M-%S"))  
log("Conectando ao banco de dados")
db = SQLAlchemy(app)
migrate = Migrate(app, db)
log("Conectando ao gerenciador")
url = "http://localhost:5000/seletor/validadorjh/127.0.0.1"
# x = requests.post(url, json = "")

def connectToGerenciador(url, numberOfTry=0, maxRetry = 3):
    try:
        x = requests.post(url, json = "")
    except:
        if numberOfTry*5 >= maxRetry * 5:
            log( f"nao foi possivel se conectar ao gerenciador, numero de tentativas: {numberOfTry}","ERROR")
        else:
            time.sleep(5 * numberOfTry)
            log("Não foi possivel conectar ao servidor, tentando conectar novamente")
            connectToGerenciador(url, numberOfTry+1)

connectToGerenciador(url)

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
    url = "http://localhost:5000/hora"
    hora = requests.get(url)
    timeObject = hora.json()["tempo"]
    result = datetime.strptime(timeObject, "%m/%d/%Y, %H:%M:%S")
    log(f"tempo so servidor atualizado {result}: ")
    return result

def validarHorario(horarioTransacao):
    horario = getHora()
    if horario > datetime.strptime(horarioTransacao, "%m/%d/%Y, %H:%M:%S"):
        return 0
    else:
        return 1


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

@app.route('/validar', methods=['POST'])
def validar():
    """
    1 - Verifica se o tempo da transação é valida
    2 - Verifica se o saldo do consumidor é o suficiente (faz a requisição para o gerenciador)
    3 - Verifica se o consumidor contem uma transação ao menor 4 transações com o status
        0 ou 2 dentro de 5 minutos caso isso aconteça deve bloquear o usuario usando tabela
        ou logs

    X - No retorno deve retornar uma chave recebida pelo seletor no cadastro
    
    2 - envia as transações para s validadores validarem
    3 - verifica se todos entregaram a resposta correta
    4 - toma as decições necessarias dependendo do resultado
"""
    request_data = request.get_json()
    horario = request_data['horario']
    valor = request_data['valor']
    id_usuario = request_data['id_usuario']
    log(f"validar: Usuario de id {id_usuario} valor: {valor}")
    isValidTime = validarHorario(horario)

    if isValidTime == 0:
        banirUsuario("Tempo unvalido",request_data)
        return jsonify(['"status": "403, "message": "horario invalido"'])

    aprovarTransacao(request_data)
    return {"status":"valid"}

if __name__ == '__main__':
    app.run(debug=True, port=5001)