from datetime import datetime
import time
import os

INSTANCE_TIME = os.environ.get('START_TIME')
def initLogger():
    print("init logger")
    os.environ['START_TIME'] = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    time.sleep(1)

def log (menssagem, nivel="INFO"):
    INSTANCE_TIME=os.environ.get('START_TIME')
    time = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    textoLog = f"{time} - {nivel} menssagem: {menssagem}\n"
    print(textoLog)
    f = open(f"logs/{INSTANCE_TIME}_seletor.txt", "a")
    f.write(textoLog)
    f.close()
