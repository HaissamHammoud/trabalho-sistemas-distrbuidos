from flask import Flask, request,jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from  random import randint
from datetime import datetime, timedelta
import time
import requests
from logger import *

URL_GERENCIADOR ="http://localhost:5000"
URL_SELETOR  = "http://localhost:5001"
SECRET_TO_SELETOR= ""
HOST = "127.0.0.1"
PORT = 5020
NOME = "MANOEL"
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


@app.before_first_request
def create_tables():
    db.create_all()


class usuarioBloqueado(db.Model):
    id: int

    id = db.Column(db.Integer, primary_key=True)
    desbloqueio = db.Column(db.DateTime, unique=False, nullable=False)
    nbloqueios = db.Column(db.Integer, nullable=False)
def connectToSeletor(url, numberOfTry=0, maxRetry = 3):
    global SECRET_TO_SELETOR
    url_to_seletor = HOST+":"+str(PORT)
    log(f"url to servidor = {url_to_seletor}")

    try:
        request_obj = {'ip': HOST+":"+str(PORT)}
        request_url = url + "/usercheck"
        x = requests.post(request_url, json = request_obj )
        x = x.json()

        if x["status"] == "400":
            request_obj = {'ip': HOST +":"+str(PORT), "nome": NOME}
            request_url = url + "/validador"
            
            x = requests.post(request_url, json = request_obj )
            log(x.content)
            content_json = x.json()
            if content_json["status"] == "200":
                log("Cadastrado ao seletor com sucesso")
                SECRET_TO_SELETOR = content_json["secret"]
            else:
                SECRET_TO_SELETOR = content_json["secret"]
                return 1

        else:
            request_url = url + "/ativa"
            x = requests.post(request_url, json = request_obj )
            content_json = x.json()
            SECRET_TO_SELETOR = content_json["secret"]
            log("Conectado ao Seletor com sucesso")
            
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

def getHora():
    #retorna a hora do sistema do gerenciador
    url = URL_GERENCIADOR + "/hora"
    hora = requests.get(url)
    timeObject = hora.json()["tempo"]
    result = datetime.strptime(timeObject, "%m/%d/%Y, %H:%M:%S")
    log(f"tempo do servidor atualizado {result} : ")
    return result

def horarioValido(horarioTransacao):
    horario = getHora()
    horarioTransacao = horarioTransacao[:horarioTransacao.rfind('.')]
    horarioTransacao = datetime.strptime(horarioTransacao, "%m/%d/%Y, %H:%M:%S")
    if horario > horarioTransacao:
        return True
    else:
        return False

def saldoValido(valorTransacao, idUsuario):
    endpoint = URL_GERENCIADOR + f"/clientes/{idUsuario}"
    response = requests.get(endpoint)
    response_json = response.json()
    saldo = int(response_json[response_json.find("qtdMoeda: ") + 10:-1])
    if valorTransacao > saldo:
        return False
    else:
        return True

def comportamentoValido(id_usuario):
        endpoint = URL_GERENCIADOR + f"/transacoes"
        tempo = datetime.now() - timedelta(minutes=5)
        log("Verificando comportamento invalido")
        response = requests.get(endpoint)
        response_json = response.json()
        response_json = response_json[1:-1]
        responses = response_json.split(" , ")
        log("AAAAaaaAAAAaaaaAAAAaaa")
        transacoes_usuario = []
        transacoes_status = []
        transacoes_usuario = [transacoes_usuario+1 for transacoes in responses if (transacoes[(transacoes.find("remetente: ") + 11):(transacoes.find(",",transacoes.find("remetente: ") + 11))]) == id_usuario and (transacoes[(transacoes.find("horario: ") + 9):(transacoes.find(",",transacoes.find("horario: ") + 9))]) > tempo ]
        transacoes_status = [transacoes_status+1 for transacoes in transacoes_usuario if (transacoes[(transacoes.find("status: ") + 8):(transacoes.find(",",transacoes.find("status: ") + 8))]) != 1]
            
        if len(transacoes_status) >= 4 :
            return False
        else:
            return True

def banido(id_usuario):
    usuario = (usuarioBloqueado.query.filter_by(id=id_usuario))
    if usuario is not None:
        return False
    else:
        if usuario.desbloqueio <= DateTime.now():
            usuario.delete()
            db.commit()
            log(f"Usuario {id_usuario} ja esta Banido")
            return False
        return True

def banirUsuario(motivo, transacao):
    id_usuario = transacao["remetente"]
    id_transacao = transacao["id"]
    if (Seletor.query.filter_by(id=id_usuario).first()) is not None:
        usuario = (usuarioBloqueado.query.filter_by(id=id).first())
        usuario.nbloqueios = usuario.nbloqueios + 1
        usuario.desbloqueio = usuario.desbloqueio + timedelta(0,(5 * usuario.nbloqueios))
        db.session.commit()
        log(f"Usuario {id_usuario} Banido")
        return 1
    else:
        _id = id_usuario
        _bloqueio = datetime.now() + timedelta(0,5)
        _nbloqueios = 1
        usuario = usuarioBloqueado(
            id = id_usuario, 
            bloqueio = datetime.now(),
            nbloqueios = _nbloqueios)
        db.session.add(usuario)
        db.session.commit()
        logger.log(f"Usuario {id_usuario} Banido")
        return 1

    usuario = usuarioBloqueado(id = id_usuario, desbloqueio= datetime.now())
    ## Essa função devera banir o usuario dependendo da infracao cometida
    log(f"Tempo passado pelo usuario de id {id_usuario} para transacao {id_transacao} e invalido","WARN")
    log(f"Usuario de id: {id_usuario} banido por: 20 sec","WARN")

def aprovarTransacao(transacao):
    id_usuario = transacao["remetente"]
    id_transacao = transacao["id"]
    log(f"Usuario {id_usuario} teve a transacao {id_transacao} aprovada")

@app.route('/validar', methods=['POST'])
def validar():
    request_data = request.get_json()
    if request_data["status"] != 0:
        return jsonify({"status": "403", "message": "Transacao ja foi realizada","status_transacao": "2", "segredo": SECRET_TO_SELETOR, "ip": HOST+":"+str(PORT)})
    horario = request_data['horario']
    valor = request_data['valor']
    id_usuario = request_data['remetente']
    log(f"validar: Usuario de id {id_usuario} valor: {valor}")
    if banido(id_usuario):
        if not comportamentoValido(id_usuario):
            banirUsuario("comportamento invalido",request_data)
            log(f"usuario {id_usuario} esta banidoe teve seu tempo de espera aumentado")
            return jsonify({"status": "403", "message": "comportamento suspeito", "status_transacao": "2", "segredo": SECRET_TO_SELETOR})
        return jsonify({"status": "403", "message": "Usuario esta banido temoporariamente", "status_transacao": "2", "segredo": SECRET_TO_SELETOR})
    if not comportamentoValido(id_usuario):
        banirUsuario("comportamento invalido",request_data)
        return jsonify({"status": "403", "message": "comportamento suspeito", "status_transacao": "2", "segredo": SECRET_TO_SELETOR})
    if not saldoValido(valor, id_usuario):
        log(f"usuario {id_usuario} não possui saldo para efetuar transacao")
        return jsonify({"status": "403", "message": "Saldo insuficiente","status_transacao": "2", "segredo": SECRET_TO_SELETOR, "ip": HOST+":"+str(PORT)}) 
    if not horarioValido(horario):
        return jsonify({"status": "403", "message": "horario invalido", "status_transacao": "2", "segredo": SECRET_TO_SELETOR, "ip": HOST+":"+str(PORT)})
    

    aprovarTransacao(request_data)
    logger.log(f"transacao aprovada")
    return jsonify({"status": "200", "status_transacao": "1", "segredo": SECRET_TO_SELETOR, "ip": HOST+":"+str(PORT)})

if __name__ == '__main__':
    db.create_all()
    app.run(port=PORT)