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
        global current_sel
        global current_name
        while(self.TTL>0):
            time.sleep(1)
            self.TTL -= 1
        existe, posicao = pertence(client_list,lambda x: x.IP == self.IP)
        client_list.pop(posicao)
        if current_sel != ():
            if current_sel[0] == posicao:
                current_sel = ()
                current_name = ""
    def getIP(self):
        return self.IP
    def getID(self):
        return self.ID
    def getTTL(self):
        return self.TTL

MCAST_GRP = '224.1.1.1'
MCAST_PORT = 5007
CHAT_PORT = 8001
mutex = Lock()
client_list=[]
current_sel = ()
current_name = ""

def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    try:
        addr = socket.inet_ntoa(fcntl.ioctl(s.fileno(),0x8915,struct.pack('256s', ifname[:15]))[20:24])
    except IOError:
        addr = "";
    if addr=="":
        return False, addr
    return True,addr

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
        self.posicao = 0 
        self.chat_history = defaultdict(list)
        up,self.MY_IP = get_ip_address('wlan0') 
        if(up==False):
            up,self.MY_IP = get_ip_address('eth0')
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
        Chat = Frame(self.root)
        self.hello = Label(Chat, text = "Ola {0} - {1}".format(self.nick,time.strftime("%H:%M")))
        self.hello.grid(row=0,column=0,sticky=W+N+S)
        self.rcvChats = Text(Chat, bg = "white", width = 60, height=30, state=DISABLED)
        self.clients = Listbox(Chat, selectmode = "EXTENDED",bg = "white", width = 30, height = 15)
        self.groups = Listbox(Chat, bg = "white", width = 30, height = 15)
        self.rcvChats.grid(row=1,column=0,sticky=W+N+S)
        self.clients.grid(row=1,column=1,sticky=E+N)
        self.clients.bind('<Button-1>',self.onSelect)
        self.groups.grid(row=1,column=1,sticky=E+S)
        self.GroupsB = Button(Chat, text = "Criar grupo", width = 10, command = self.GUICreateGroup)
        self.GroupsB.grid(row=2, column=1,sticky=E+S)
        self.chatVar = StringVar()
        self.chatField = Entry(Chat, width = 52,textvariable=self.chatVar)
        self.chatField.bind('<Return>',self.handleSendChat)
        self.sendButton = Button(Chat, text = "Enviar", width = 10, command = self.handleSendChat)
        self.chatField.grid(row=2,column=0)
        self.sendButton.grid(row=2,column=1,sticky=W+S)
        self.refreshClients()
        self.refreshChat()

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
    
    def GUICreateGroup(self):
        GroupWindow = Toplevel(height=300,width=250)

        quitb = Button(GroupWindow, text = "Ok",command = GroupWindow.destroy)
        applyb = Button(GroupWindow, text = "Aplicar", command = self.createGroup)
        applyb.grid(row=1,column=0)
        quitb.grid(row=1,column=1)
        grpnameLbl = Label(GroupWindow, text = "Nome do Grupo")
        grpnameLbl.grid(row=0)
        self.grpnameVar = StringVar()
        grpnameField = Entry(GroupWindow, width = 52,textvariable=self.grpnameVar)
        grpnameField.grid(row=0,column=1)
        for x in range(len(client_list)):
            l = Checkbutton(GroupWindow, text = client_list[x].ID, variable = client_list[x])
            l.grid()
    
    def createGroup(self):
        grpname = self.grpnameVar.get()
        print "Grupo " + grpname
        print "Integrantes : "
        for client in client_list:
            if client_list.get():
                print client.ID
        print "----"
        print "Criado com sucesso!"

    def onSelect(self,event):
        global current_sel
        now = self.clients.curselection()
        if now!=current_sel:
            self.sel_has_changed(now)
            current_sel = now

    def sel_has_changed(self,selection):
        global current_name
        try:
            if selection != ():
                self.posicao = int(selection[0])
                current_name = client_list[self.posicao].ID
                print client_list[self.posicao]
        except IndexError as e:
            print "sel_has_changed exception :" + str(e)

    def handleSendChat(self,event=None):
        try:
            if client_list !=[]:
                if current_name != "":
                    msg = self.chatVar.get()
                    msg = "[{2}]:{3} - {0} - {1}".format(time.strftime("%d/%m/%Y"),time.strftime("%H:%M"),self.nick,msg)
                    existe, posicao = pertence(client_list,lambda x: x.ID == current_name)
                    self.chat_history[client_list[posicao].IP].append(msg)
                    self.send_message(msg,posicao)
                    print "Mensagem enviada a " + client_list[posicao].ID + ":" + client_list[posicao].IP
                else:
                    self.ErrorDialog("Nenhum usuario selecionado")
        except (TypeError,IndexError) as e:
            print "handlesendchat exception :" + str(e)
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
            if client_list != [] and current_name != "":
                print "Abrindo conversa com " + current_name
                self.addChat("Voce esta conversando com {0}".format(current_name))
                existe, posicao = pertence(client_list,lambda x: x.ID == current_name)
                historico = self.read_chathist(posicao)
                for msg in historico:
                    self.addChat(msg)
        except (IndexError,TypeError) as e:
            print "refreshchat exception :" + str(e)
            print "posicao foi " + posicao
        self.clients.after(500,self.refreshChat)

    def refreshClients(self):
        self.cleanClients()
        for client in client_list:
            self.addClient(client)
        self.clients.after(1000,self.refreshClients)

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

        while True:
            data, addr =  sock.recvfrom(1024)
            print "Msg recebida : " + data
            cliente = Client(addr[0],data)
            existe, posicao = pertence (client_list,lambda x: x.IP == cliente.IP)
            if not existe: 
                if self.MY_IP != cliente.IP and self.nick != cliente.ID:
                    client_list.append(cliente)
                    print "Cliente {0}:{1} conectou".format(cliente.ID,cliente.IP)
                    thr=threading.Thread(target = client_list[-1].decrementaTTL)
                    thr.setDaemon(True)
                    thr.start()
            else:
                try:
                    client_list[posicao].resetTTL()
                except (TypeError,IndexError) as e:
                    print "mcast_rcv exception :" + str(e)

    def mcast_hello(self):
        while True:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
            sock.sendto(self.nick, (MCAST_GRP, MCAST_PORT))
            time.sleep(20);

    def send_message(self,msg,posicao):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
        sock.sendto(msg, (client_list[posicao].getIP(), CHAT_PORT))

    def read_chathist(self,posicao):
        return self.chat_history[client_list[posicao].IP]

    def chat_rcv(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
        sock.bind((self.MY_IP, CHAT_PORT))
        while True:
            data, addr = sock.recvfrom(1024) # buffer size is 1024 bytes
            self.chat_history[addr[0]].append(data)

root = Tk()
app = App(root)
root.mainloop()
