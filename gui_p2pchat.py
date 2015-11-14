import socket
import struct
import threading
from threading import Lock
import time
import fcntl
from collections import defaultdict
from Tkinter import *

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

MCAST_GRP = '224.1.1.1'
MCAST_PORT = 5007
CHAT_PORT = 8001
sair = 0
mutex = Lock()

def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(s.fileno(),0x8915,struct.pack('256s', ifname[:15]))[20:24])

def pertence(lista,filtro):
    i=0
    for x in lista:
        if filtro(x):
            return True,i
        i+=1
    return False,-1

class App(Frame):
    def __init__(self,root):
        Frame.__init__(self,root)
        self.root = root
        self.client_list=[]
        self.posicao = None 
        self.chat_history = defaultdict(list)
        self.MY_IP = get_ip_address('eth0') 
        self.ConnectWindow()

    def ConnectWindow(self):
        self.root.title("p2p chat")
        parentFrame = (self.root)

        self.usernameLabel = Label(parentFrame,text="Nick")
        self.usernameLabel.grid(row=0,sticky=E)
        
        self.nickVar = StringVar()
        self.usernameField = Entry(parentFrame, textvariable = self.nickVar)
        self.usernameField.bind('<Return>',self.connect)
        self.usernameField.grid(row=0,column=1)
        self.connectBt = Button(parentFrame,text="Connect",command=self.connect)
        self.connectBt.grid(columnspan=2)
        
    def main_window(self):
        ScreenSizeX = self.root.winfo_screenwidth()
        ScreenSizeY = self.root.winfo_screenheight()
        self.FrameSizeX = 675
        self.FrameSizeY = 500
        FramePosX = (ScreenSizeX - self.FrameSizeX)/2
        FramePosY = (ScreenSizeY - self.FrameSizeY)/2
        self.root.geometry("{0}x{1}+{2}+{3}".format(self.FrameSizeX,self.FrameSizeY,FramePosX,FramePosY))
        self.current = None
        Chat = Frame(self.root)
        self.hello = Label(Chat, text = "Ola {0}".format(self.nick))
        self.hello.grid(row=0,column=0,sticky=W+N+S)
        self.rcvChats = Text(Chat, bg = "white", width = 60, height=30, state=DISABLED)
        self.clients = Listbox(Chat, selectmode = "EXTENDED",bg = "white", width = 30, height = 15)
        # self.clients.bind("<Button-1>",self.onSelect)
        self.groups = Listbox(Chat, bg = "white", width = 30, height = 15)
        self.rcvChats.grid(row=1,column=0,sticky=W+N+S)
        self.clients.grid(row=1,column=1,sticky=E+N)
        self.groups.grid(row=1,column=1,stick=E+S)
        self.chatVar = StringVar()
        self.chatField = Entry(Chat, width = 52,textvariable=self.chatVar)
        self.chatField.bind('<Return>',self.handleSendChat)
        sendButton = Button(Chat, text = "Enviar", width = 26, command = self.handleSendChat)
        self.chatField.grid(row=2,column=0)
        sendButton.grid(row=2,column=1,columnspan=2)
        self.refreshClients()
        self.refreshChat()
        self.onSelect()

        thr1 = threading.Thread(target = self.mcast_rcv)
        thr2 = threading.Thread(target = self.mcast_hello)
        thr3 = threading.Thread(target = self.chat_rcv)
        thr1.setDaemon(True)
        thr2.setDaemon(True)
        thr3.setDaemon(True)
        thr1.start()
        thr2.start()
        thr3.start()

        Chat.grid(row=1,column=0)
    
    def onSelect(self):
        # value = widget.get(selection)
        # print value
        now = self.clients.curselection()
        if now!=self.current:
            self.sel_has_changed(now)
            self.current = now
        self.after(250, self.onSelect)

    def sel_has_changed(self,selection):
        try:
            # self.who = value = self.clients.get(selection[0])
            self.posicao = selection[0]
        except IndexError:
            pass

    def handleSendChat(self,event=None):
        try:
            msg = self.chatVar.get()
            msg = "[{2}]:{3} - {0} - {1}".format(time.strftime("%d/%m/%Y"),time.strftime("%H:%M"),self.client_list[self.posicao].ID,msg)
            self.chat_history[self.client_list[self.posicao].IP].append(msg)
            self.send_message(msg,self.posicao)
        except TypeError:
            pass
        self.chatField.delete(0,END)
        self.chatField.insert(0,"")

    def addChat(self,msg):
        self.rcvChats.config(state=NORMAL)
        self.rcvChats.insert(END,msg+"\n")
        self.rcvChats.config(state=DISABLED)

    def cleanChat(self):
        self.rcvChats.config(state=NORMAL)
        self.rcvChats.delete(1.0,END)
        self.rcvChats.config(state=DISABLED)

    def refreshChat(self):
        self.cleanChat()
        try:
            historico = self.read_chathist(self.posicao)
            for msg in historico:
                self.addChat(msg)
        except (IndexError,TypeError):
            pass
        self.clients.after(300,self.refreshChat)

    def refreshClients(self):
        self.cleanClients()
        for client in self.client_list:
            self.addClient(client)
        self.clients.after(2000,self.refreshClients)

    def addClient(self,client):
        self.clients.insert(END,client.ID)

    def cleanClients(self):
        self.clients.delete(0,END)

    def ErrorDialog(self,erromsg):
        Error = Toplevel(height=100,width=100)
        label = Label(Error, text = "Erro! {0}".format(erromsg))
        label.grid(columnspan=2)
        quitb = Button(Error, text = "Ok",command = Error.destroy)
        quitb.grid(columnspan=2)
    def ConnectedDialog(self):
        Dialog = Toplevel(height=100,width=100)
        label = Label(Dialog, text = "Ola {0}, bem-vindo ao chat".format(self.nick))
        label.grid(columnspan=2)
        quit = Button(Dialog, text= "Ok",command = Dialog.destroy)
        quit.grid(columnspan=2)
    def connect(self,event=None):
        self.nick = self.nickVar.get()
        if self.nick == "":
            self.ErrorDialog("Necessario inserir um nick para continuar...")
        else:
            self.ConnectedDialog();
            self.usernameField.grid_forget()
            self.usernameLabel.grid_forget()
            self.connectBt.grid_forget()
            self.main_window()
    def mcast_rcv(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((MCAST_GRP, MCAST_PORT))
        mreq = struct.pack("4sl", socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)

        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

        while not sair:
            data, addr =  sock.recvfrom(1024)
            cliente = Client(addr[0],data)
            existe, posicao = pertence (self.client_list,lambda x: x.IP == cliente.IP)
            if not existe: 
                self.client_list.append(cliente)
                thr=threading.Thread(target = self.client_list[-1].decrementaTTL)
                thr.setDaemon(True)
                thr.start()
            else:
                self.client_list[self.posicao].resetTTL()

    def mcast_hello(self):
        while not sair:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
            sock.sendto(self.nick, (MCAST_GRP, MCAST_PORT))
            time.sleep(10);

    def send_message(self,msg,posicao):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
        sock.sendto(msg, (self.client_list[posicao].getIP(), CHAT_PORT))

    def read_chathist(self,posicao):
        return self.chat_history[self.client_list[posicao].IP]

    def chat_rcv(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
        sock.bind((self.MY_IP, CHAT_PORT))
        while True:
            data, addr = sock.recvfrom(1024) # buffer size is 1024 bytes
            self.chat_history[addr[0]].append(data)

root = Tk()
app = App(root)
root.mainloop()