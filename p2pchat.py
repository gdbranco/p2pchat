import socket
import struct
import threading
import time

class Client:
	def __init__(self, _IP, _ID):
		self.ID = _ID
		self.IP = _IP
		self.TTL = 30
        def __str__(self):
            return "ID = {0}\tIP = {1}\tTTL={2} ".format(self.ID,self.IP,self.TTL)
	def resetTTL():
		self.TTL = 30

client_list = []
nick = ""
sair = 0

MCAST_GRP = '224.1.1.1'
MCAST_PORT = 5007

def pertence(lista,filtro):
    i=0
    for x in lista:
        if filtro(x):
            return True,i
        i+=1
    return False,-1

def main():
	thr1 = threading.Thread(target = mcast_rcv)
	thr1.start()
	
	thr2 = threading.Thread(target = mcast_hello)
	thr2.start()

def mcast_rcv():
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
	sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	sock.bind(('', MCAST_PORT))  # use MCAST_GRP instead of '' to listen only
								# to MCAST_GRP, not all groups on MCAST_PORT
	mreq = struct.pack("4sl", socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)

	sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

	while not sair:
		data, addr =  sock.recvfrom(1024)
		print data, "from: ",  addr
                cliente = Client(addr[0],data)
                existe, posicao = pertence (client_list,lambda x: x.IP == cliente.IP)
                if not existe: 
                    client_list.append(cliente)
                else:
                    print posicao
                    client_list[posicao].TTL = 30
                for x in client_list:
                    print x

def mcast_hello():
    global nick
    nick = raw_input("Digite seu nick: ")
    # thr3 = threading.Thread(target = client_loop)
    # thr3.start()
    while not sair:
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
	sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
	sock.sendto(nick, (MCAST_GRP, MCAST_PORT))
        time.sleep(5);

def client_loop():
    global sair
    while not sair:
        print "Ola {0}\n".format(nick)
        print "0.Sair\n"
        opcao = int(input("Insira uma opcao : "))
        if(opcao==0):
            sair = 1
	
if __name__ == "__main__":
    main()
