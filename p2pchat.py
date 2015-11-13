import socket
import struct
import threading
from threading import Lock
import time
import fcntl
from collections import defaultdict

class Client:
    def __init__(self, _IP, _ID):
        self.ID = _ID
        self.IP = _IP
        self.TTL = 30
    def __str__(self):
        return "ID = {0}\tIP = {1}\tTTL={2} ".format(self.ID,self.IP,self.TTL)
    def resetTTL(self):
        self.TTL = 30
    def decrementaTTL(self):
        while(self.TTL>0):
            time.sleep(1)
            self.TTL -= 1
        existe, posicao = pertence(client_list,lambda x: x.IP == self.IP)
        client_list.pop(posicao)
    def getIP(self):
        return self.IP
    def getID(self):
        return self.ID
    def getTTL(self):
        return self.TTL

def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(s.fileno(),0x8915,struct.pack('256s', ifname[:15]))[20:24])

chat_history = defaultdict(list)
client_list = []
MY_nick = ""
MY_IP = get_ip_address('eth0')
sair = 0
mutex = Lock()

MCAST_GRP = '224.1.1.1'
MCAST_PORT = 5007
CHAT_PORT = 8001

def main():
    global MY_nick
    MY_nick = raw_input("Digite seu nick: ")
    thr1 = threading.Thread(target = mcast_rcv)
    thr2 = threading.Thread(target = mcast_hello)
    thr3 = threading.Thread(target = client_loop)
    thr4 = threading.Thread(target = chat_rcv)
    thr1.setDaemon(True)
    thr2.setDaemon(True)
    thr3.setDaemon(True)
    thr4.setDaemon(True)
    thr1.start()
    thr2.start()
    thr3.start()
    thr4.start()
    try:
        while not sair:
            pass
    except EOFError:
        return

def pertence(lista,filtro):
    i=0
    for x in lista:
        if filtro(x):
            return True,i
        i+=1
    return False,-1

def mcast_rcv():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((MCAST_GRP, MCAST_PORT))
    mreq = struct.pack("4sl", socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)

    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    while not sair:
        data, addr =  sock.recvfrom(1024)
        cliente = Client(addr[0],data)
        existe, posicao = pertence (client_list,lambda x: x.IP == cliente.IP)
        if not existe: 
            client_list.append(cliente)
            thr=threading.Thread(target = client_list[-1].decrementaTTL)
            thr.setDaemon(True)
            thr.start()
        else:
            client_list[posicao].resetTTL()

def mcast_hello():
    while not sair:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        sock.sendto(MY_nick, (MCAST_GRP, MCAST_PORT))
        time.sleep(10);

def show_user_list():
    print "---------------Lista---------------"
    for x in client_list:
        print x
    print "-----------------------------------"


def client_loop():
    global sair
    while not sair:
        print "\nOla {0}".format(MY_nick)
        print "1.Mostrar lista de clientes"
        print "2.Abrir conversa"
        print "0.Sair"
        opcao = int(input("Insira uma opcao : "))
        if(opcao==0):
            mutex.acquire()
            sair = 1
            mutex.release()
        elif(opcao==1):
            show_user_list()
        elif(opcao==2):
            voltar = 0
            who = raw_input("Abrir conversa com quem?")
            existe, posicao = pertence(client_list, lambda x: x.ID == who)
            if existe:
                while not voltar:
                    print "1.Mandar mensagem"
                    print "2.Ler mensagem"
                    print "0.Voltar"
                    opcao_sub = int(input("Insirau uma opcao : "))
                    if(opcao_sub==0):
                        voltar=1
                    elif(opcao_sub==1):
                        msg = raw_input("Insira sua mensagem : ")
                        msg = "[{2}]:{3} - {0} - {1}".format(time.strftime("%d/%m/%Y"),time.strftime("%H:%M"),client_list[posicao].ID,msg)
                        chat_history[client_list[posicao].IP].append(msg)
                        send_message(msg,posicao)
                    elif(opcao_sub==2):
                        historico = read_chathist(posicao)
                        for msg in historico:
                            print msg
            else:
                print "Erro! Usuario inexistente."

def send_message(msg,posicao):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
    sock.sendto(msg, (client_list[posicao].getIP(), CHAT_PORT))

def read_chathist(posicao):
    return chat_history[client_list[posicao].IP]

def chat_rcv():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
    sock.bind((MY_IP, CHAT_PORT))
    while True:
        data, addr = sock.recvfrom(1024) # buffer size is 1024 bytes
        chat_history[addr[0]].append(data)

if __name__ == "__main__":
    main()
