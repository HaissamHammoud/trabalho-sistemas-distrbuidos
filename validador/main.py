from flask import Flask, redirect , render_template, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from  random import randint
from datetime import datetime
import time
import requests
from logger import *

initLogger()
app = Flask(__name__)

#indica o tempo de inicialização da instância

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

def getHora():
    #retorna a hora do sistema do gerenciador
    url = "http://localhost:5000/hora"
    hora = request.get(url)
    return hora

def validarHorario(horarioTransacao):
    horario = getHora()
    if horario > horarioTransacao:
        return 0
    else:
        return 1


class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(20), unique=False, nullable=False)
    saldo = db.Column(db.Float())
  
    def __repr__(self):
        return f"{{Nome : {self.nome}, Saldo: {self.saldo} }}"


@app.route('/validar', methods=['POST'])
def validar():

    """
        Json que vira no body da função será
        {
            horario : datetime,
            valor   : decimal,
            id_usuario : int
        }

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
    key = request_data['key']
    login = request_data['name']
    valor = request_data['valor']
    print(login + str(valor) + login)
    if key == login + str(valor) + login:
        return {"status": "valid"}
    return {"status":"invalid"}

if __name__ == '__main__':
    app.run(debug=True, port=5001)