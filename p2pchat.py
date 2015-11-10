import socket
import struct
import threading
import time

class Client:
	def __init__(self, _IP, _ID):
		self.ID = _ID
		self.IP = _IP
		self.TTL = 30
	def resetTTL():
		self.TTL = 30

client_list = {}

MCAST_GRP = '224.1.1.1'
MCAST_PORT = 5007

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

	while True:
		data, addr =  sock.recvfrom(1024)
		print data, "from: ",  addr

def mcast_hello():
    msg = raw_input("Digite seu nick: ")
    while True:
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
	sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
	sock.sendto(msg, (MCAST_GRP, MCAST_PORT))
        time.sleep(20);
	
if __name__ == "__main__":
	main()
