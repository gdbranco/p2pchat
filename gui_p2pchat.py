import socket
import struct
import threading
from threading import Lock
import time
import fcntl
from collections import defaultdict
from Tkinter import *
from random import randint
import os
import json

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

class Group:
    def __init__(self, _members=[], _IP="", _name=""):
        self.members = _members
        self.IP = _IP
        self.name = _name
    def __str__(self):
        s = "\n".join(map(str,self.members))
        return "Nome = {0}\tIP = {1}\nMembers:\n{2}".format(self.name,self.IP,s)
    def getIP(self):
        return self.IP
    def getName(self):
        return self.name
    def getMembers(self):
        return self.members

MCAST_GRP = '224.1.1.1'
MCAST_PORT = 5007
CHAT_PORT = 8001
mutex = Lock()
client_list=[]
group_list=[]
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
        self.check_list = []
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
        self.usernameField.focus_set()
        self.usernameField.grid(row=0,column=1)
        self.connectBt = Button(parentFrame,text="Connect",command=self.connect)
        self.connectBt.grid(columnspan=2)
        
    def main_window(self):
        Chat = Frame(self.root)
        self.hello = Label(Chat, text = "Ola {0} - {1}".format(self.nick,time.strftime("%H:%M")))
        self.hello.grid(row=0,column=0,sticky=W+N+S)
        self.scrollbar = Scrollbar(Chat)
        self.rcvChats = Text(Chat, bg = "white", width = 60, height=30, state=DISABLED,yscrollcommand=self.scrollbar.set)
        self.rcvChats.grid(row=1,column=0,sticky=W+N+S)
        self.scrollbar.config(command=self.rcvChats.yview)
        self.scrollbar.grid(row=1,column=1,sticky=N+S+W)
        self.clients = Listbox(Chat, selectmode = "EXTENDED",bg = "white", width = 30, height = 15)
        self.clients.grid(row=1,column=2,sticky=W+N)
        self.clients.bind('<Button-1>',self.onSelect)
        self.groups = Listbox(Chat, bg = "white", width = 30, height = 15)
        self.groups.grid(row=1,column=2,sticky=W+S)
        self.groups.bind('<Button-1>',self.onSelectGrp)
        self.chatVar = StringVar()
        self.chatField = Entry(Chat, width = 52,textvariable=self.chatVar)
        self.chatField.bind('<Return>',self.handleSendChat)
        self.chatField.grid(row=2,column=0)
        self.sendButton = Button(Chat, text = "Enviar", width = 3, command = self.handleSendChat)
        self.sendButton.grid(row=2,column=1,sticky=W+S)
        self.GroupsB = Button(Chat, text = "Criar grupo", width = 7, command = self.GUICreateGroup)
        self.GroupsB.grid(row=2, column=2,sticky=W+S)
        self.refreshClients()
        self.refreshChat()
        self.refreshGroups()

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
        self.GroupWindow = Toplevel(height=300,width=250)

        grpnameLbl = Label(self.GroupWindow, text = "Nome do Grupo")
        grpnameLbl.grid(row=0)
        self.grpnameVar = StringVar()
        self.grpnameField = Entry(self.GroupWindow, width = 20,textvariable=self.grpnameVar)
        self.grpnameField.focus_set()
        self.grpnameField.grid(row=0,column=1)
        for client in client_list:
            self.check_list.append(Variable())
            self.check_list[-1].set(0)
            l = Checkbutton(self.GroupWindow, text = client.ID, variable = self.check_list[-1])
            l.grid()
        applyb = Button(self.GroupWindow, text = "Aplicar", command = self.createGroup)
        applyb.grid(column=1)
    
    def createGroup(self):
        grpname = self.grpnameVar.get()
        if grpname == "":
            self.ErrorDialog("Impossivel criar grupo sem nome")
        else:
            members=[]
            for x in range(len(client_list)):
                if self.check_list[x].get():
                    members.append(client_list[x].ID)
            s = "true"
            ip = str(randint(224,230)) + '.' +str(randint(0,255)) + '.' +str(randint(0,255)) + '.' +str(randint(0,255)) 
            grupo = Group(members,ip,grpname)
            print grupo
            print "Criado com sucesso!"
            for nome in members:
                existe, posicao = pertence(client_list, lambda x: x.ID == nome)
                msg = "GROUP: " + grupo.IP + ' ' + grupo.name + ' ' + json.dumps(grupo.members)
                self.send_message(msg,posicao)
            group_list.append(grupo)
            for x in range(len(client_list)):
                self.check_list[x].set(0)
            self.grpnameField.delete(0,END)
            self.grpnameField.insert(0,"")
            self.GroupWindow.destroy()

    def onSelect(self,event):
        global current_sel
        now = self.clients.curselection()
        if now!=current_sel:
            self.sel_has_changed(now)
            current_sel = now

    def onSelectGrp(self,event):
        global current_sel
        now = self.groups.curselection()
        if now!=current_sel:
            self.sel_has_changedGrp(now)
            current_sel = now

    def sel_has_changedGrp(self,selection):
        global current_name
        try:
            if selection != ():
                self.posicao = int(selection[0])
                current_name = group_list[self.posicao].name
                self.chatField.focus_set()
                print group_list[self.posicao]
        except IndexError as e:
            print "sel_has_changed exception :" + str(e)

    def sel_has_changed(self,selection):
        global current_name
        try:
            if selection != ():
                self.posicao = int(selection[0])
                current_name = client_list[self.posicao].ID
                self.chatField.focus_set()
                print client_list[self.posicao]
        except IndexError as e:
            print "sel_has_changed exception :" + str(e)

    def handleSendChat(self,event=None):
        try:
            if client_list !=[]:
                if current_name != "":
                    msg = self.chatVar.get()
                    try:
                        msg = "[{2}]:{3} - {0} - {1}".format(time.strftime("%d/%m/%Y"),time.strftime("%H:%M"),self.nick,msg)
                        existe, posicao = pertence(client_list,lambda x: x.ID == current_name)
                        if existe:
                            self.chat_history[client_list[posicao].IP].append(msg)
                            self.send_message("CHAT: " + msg,posicao)
                            print "Mensagem enviada a " + client_list[posicao].ID + ":" + client_list[posicao].IP
                        else:
                            existe,posicao = pertence(group_list,lambda x: x.name == current_name)
                            self.chat_history[group_list[posicao].IP].append(msg)
                            self.grp_send(msg,posicao)
                    except UnicodeError as e:
                        print "handlesendchat exception : " + str(e)
                        self.ErrorDialog("Caracter nao ascii presente na msg")
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
                self.addChat("Voce esta conversando com {0}".format(current_name))
                existe, posicao = pertence(client_list,lambda x: x.ID == current_name)
                if not existe:
                    existe, posicao = pertence(group_list, lambda x: x.name == current_name)
                historico = self.read_chathist(posicao)
                for msg in historico:
                    self.addChat(msg)
                self.rcvChats.yview(END)
        except (IndexError,TypeError) as e:
            print "refreshchat exception :" + str(e)
            print "posicao foi " + posicao
        self.clients.after(500,self.refreshChat)

    def refreshClients(self):
        self.cleanClients()
        for client in client_list:
            self.addClient(client)
        self.clients.after(1000,self.refreshClients)

    def refreshGroups(self):
        self.cleanGroups();
        for group in group_list:
            self.addGroup(group)
        self.groups.after(1000,self.refreshGroups)

    def addGroup(self,group):
        self.groups.insert(END,group.name)

    def cleanGroups(self):
        self.groups.delete(0,END)

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
        quit.focus_set()
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
            print "Mensagem hello recebida : " + data
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
            text = data.split()
            if(text[0] == 'CHAT:'):
                print 'Mensagem chat recebida'
                del text[0]
                data = ' '.join(text)
                self.chat_history[addr[0]].append(data)
            elif(text[0] == 'GROUP:'):
                print 'Mensagem grupo recebida'
                grupo = Group()
                grupo.IP = text[1]
                grupo.name = text[2]
                del text[0:3]
                text = ' '.join(text)
                grupo.members = json.loads(text)
                group_list.append(grupo)
                thrd = threading.Thread(target = self.grp_rcv, args=[grupo.IP])
                thrd.setDaemon(True)
                thrd.start()

    def grp_rcv(self,IP):
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
	sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	sock.bind((IP, MCAST_PORT))
	mreq = struct.pack("4sl", socket.inet_aton(IP), socket.INADDR_ANY)
	sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
	while True:
		data, addr =  sock.recvfrom(1024)
		self.chat_history[IP].append(data)

    def grp_send(self,msg,posicao):
	IP = group_list[posicao].IP
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
	sock.sendto(msg, (IP, MCAST_PORT))

root = Tk()
app = App(root)
root.mainloop()
