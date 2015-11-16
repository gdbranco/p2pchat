#Trabalho de TR2 - Bordim - 2/2015
#Membros: Guilherme Branco, Pedro Henrique, Samuel Pala
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

#Funcao utilizada para pegar o endereco IP a partir de uma interface, retorna o endereco IP
def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    try:
        addr = socket.inet_ntoa(fcntl.ioctl(s.fileno(),0x8915,struct.pack('256s', ifname[:15]))[20:24])
    except IOError:
        addr = "";
    if addr=="":
        return False, addr
    return True,addr

#Funcao para filtrar a lista baseadando numa funcao filtro
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

#Metodo de janela de conexao com interface
    def ConnectWindow(self):
        self.root.title("p2p chat")
        parentFrame = (self.root)

#Cria uma label na interface
        self.usernameLabel = Label(parentFrame,text="Nick")
        self.usernameLabel.grid(row=0,sticky=E)
#Cria uma variavel String para receber o que for digitado no campo de entrada
        self.nickVar = StringVar()
#Cria o campo de entrada para inserir o nick do usuario
        self.usernameField = Entry(parentFrame, textvariable = self.nickVar)
        self.usernameField.bind('<Return>',self.connect)
        self.usernameField.focus_set()
        self.usernameField.grid(row=0,column=1)
#Botao para se conectar a rede
        self.connectBt = Button(parentFrame,text="Connect",command=self.connect)
        self.connectBt.grid(columnspan=2)
        
#Janela principal do chat, possui janela de chat, lista de usuarios e de grupos
    def main_window(self):
        Chat = Frame(self.root)
#Label de "welcome" para ususario
        self.hello = Label(Chat, text = "Ola {0} - {1}".format(self.nick,time.strftime("%H:%M")))
        self.hello.grid(row=0,column=0,sticky=W+N+S)
#Scrollbar para janela de chat
        self.scrollbar = Scrollbar(Chat)
#Janela de texto para guardar as mensagens
        self.rcvChats = Text(Chat, bg = "white", width = 60, height=30, state=DISABLED,yscrollcommand=self.scrollbar.set)
        self.rcvChats.grid(row=1,column=0,sticky=W+N+S)
        self.scrollbar.config(command=self.rcvChats.yview)
        self.scrollbar.grid(row=1,column=1,sticky=N+S+W)
#Janela de lista de clientes
        self.clients = Listbox(Chat, bd=0,selectmode = "EXTENDED",bg = "white", width = 30, height = 15)
        self.clients.grid(row=1,column=2,sticky=W+N)
        self.clients.bind('<Button-1>',self.onSelect)
#Janela de lista de grupos
        self.groups = Listbox(Chat, bg = "white", width = 30, height = 15)
        self.groups.grid(row=1,column=2,sticky=W+S)
        self.groups.bind('<Button-1>',self.onSelectGrp)
#Variavel para guardar a msg inserida pelo usuario
        self.chatVar = StringVar()
#Campo para inserir a mensagem ao chat
        self.chatField = Entry(Chat, width = 52,textvariable=self.chatVar)
        self.chatField.bind('<Return>',self.handleSendChat)
        self.chatField.grid(row=2,column=0)
#Botao para enviar mensagem
        self.sendButton = Button(Chat, text = "Enviar", width = 3, command = self.handleSendChat)
        self.sendButton.grid(row=2,column=1,sticky=W+S)
#Botao para criar um grupo de ususarios
        self.GroupsB = Button(Chat, text = "Criar grupo", width = 7, command = self.GUICreateGroup)
        self.GroupsB.grid(row=2, column=2,sticky=W+S)
        self.refreshClients()
        self.refreshChat()
        self.refreshGroups()
#Threads basicas para funcionamento do programa, como KEEPALIVE e RCV, assim como o chat principal
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
    
#Interface para criacao de grupos multicast
    def GUICreateGroup(self):
        self.GroupWindow = Toplevel(height=300,width=250)
#Label para inserir nome do gruop
        grpnameLbl = Label(self.GroupWindow, text = "Nome do Grupo")
        grpnameLbl.grid(row=0)
#Variavel para guardar o nome do grupo
        self.grpnameVar = StringVar()
#Campo para inserir o nome do grupo
        self.grpnameField = Entry(self.GroupWindow, width = 20,textvariable=self.grpnameVar)
        self.grpnameField.focus_set()
        self.grpnameField.grid(row=0,column=1)
#Cria a lista de membros do grupo
        for client in client_list:
            self.check_list.append(Variable())
            self.check_list[-1].set(0)
            l = Checkbutton(self.GroupWindow, text = client.ID, variable = self.check_list[-1])
            l.grid()
#Envia as informacoes para os membros do grupo
        applyb = Button(self.GroupWindow, text = "Aplicar", command = self.createGroup)
        applyb.grid(column=1)
    
#Passa as informacoes obtidas pela interface para a criacao de um grupo
    def createGroup(self):
        grpname = self.grpnameVar.get()
        if grpname == "":
            self.ErrorDialog("Impossivel criar grupo sem nome")
        else:
            members=[]
            for x in range(len(client_list)):
                if self.check_list[x].get():
                    members.append(client_list[x].ID)
#Gera um IP dentro da faixa de IPs multicast para o grupo funcionar
            ip = str(randint(224,230)) + '.' +str(randint(0,255)) + '.' +str(randint(0,255)) + '.' +str(randint(0,255)) 
            grupo = Group(members,ip,grpname)
            for nome in members:
                existe, posicao = pertence(client_list, lambda x: x.ID == nome)
                msg = "GROUP: " + grupo.IP + ' ' + grupo.name + ' ' + json.dumps(grupo.members)
                self.send_message(msg,posicao)
                print "Msg criar grupo para " + client_list[posicao].ID + ":" + client_list[posicao].IP 
            print grupo
            group_list.append(grupo)
#Thread para listening do grupo
            thrd = threading.Thread(target = self.grp_rcv, args=[grupo.IP])
            thrd.setDaemon(True)
            thrd.start()
#Reseta informacoes de criacao para o proximo grupo ser criado corretamente
            del self.check_list[:]
            self.grpnameField.delete(0,END)
            self.grpnameField.insert(0,"")
            self.GroupWindow.destroy()

#Os proximos quatro metodos servem para trocar a selecao atual na lista de grupos ou clientes
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

#Handle para enviar mensagens ao chat, tanto para grupo ou para clientes 1-1
    def handleSendChat(self,event=None):
        try:
#Primeiro deve-se checar se ha algum cliente selecionado
            if client_list !=[]:
                if current_name != "":
                    msg = self.chatVar.get()
                    try:
#Gera a mensagem no padrao do chat e adiciona o dado que o usuario digitou
                        msg = "[{2}]:{3} - {0} - {1}".format(time.strftime("%d/%m/%Y"),time.strftime("%H:%M"),self.nick,msg)
                        existe, posicao = pertence(client_list,lambda x: x.ID == current_name)
                        if existe:
#Adiciona a msg para seu proprio historico
                            self.chat_history[client_list[posicao].IP].append(msg)
#Envia a mensagem ao cliente selecionado
                            self.send_message("CHAT: " + msg,posicao)
                            print "Mensagem enviada a " + client_list[posicao].ID + ":" + client_list[posicao].IP
                        else:
#Se o selecionado nao eh um cliente, deve ser um grupo e envia a mensagem para o grupo selecionado
                            existe,posicao = pertence(group_list,lambda x: x.name == current_name)
                            self.grp_send(msg,posicao)
                            print "Mensagem enviada a " + group_list[posicao].name + ":" + group_list[posicao].IP
#Checa se houve caracteres nao ascii na mensagem
                    except UnicodeError as e:
                        print "handlesendchat exception : " + str(e)
                        self.ErrorDialog("Caracter nao ascii presente na msg")
#Checa se algum cliente foi selecionado
                else:
                    self.ErrorDialog("Nenhum usuario selecionado")
        except (TypeError,IndexError) as e:
            print "handlesendchat exception :" + str(e)
#Reseta o campo de inserir mensagem para conter uma string vazia
        self.chatField.delete(0,END)
        self.chatField.insert(0,"")

#Adicona mensagem a interface de chat
    def addChat(self,msg):
        self.rcvChats.config(state=NORMAL)
        self.rcvChats.insert(END,msg+"\n")
        self.rcvChats.config(state=DISABLED)
#Limpa a interface de chat
    def cleanChat(self):
        self.rcvChats.config(state=NORMAL)
        self.rcvChats.delete(1.0,END)
        self.rcvChats.config(state=DISABLED)
#Atualiza a interface de chat para conter novas mensagens recebidas
    def refreshChat(self):
        self.cleanChat()
        try:
#Checa se esta conversando com alguem selecionado
            if client_list != [] and current_name != "":
                self.addChat("Voce esta conversando com {0}".format(current_name))
                existe, posicao = pertence(client_list,lambda x: x.ID == current_name)
                if existe:
                    IP = client_list[posicao].IP
                else:
                    existe, posicao = pertence(group_list, lambda x: x.name == current_name)
                    IP = group_list[posicao].IP
#Busca o historico de mensagens do cliente selecionado
                historico = self.read_chathist(IP)
                for msg in historico:
                    self.addChat(msg)
#Coloca a posicao da janela de chat para a ultima mensagem recebida
                self.rcvChats.yview(END)
        except (IndexError,TypeError) as e:
            print "refreshchat exception :" + str(e)
            print "posicao foi " + posicao
#Chama a funcao de atualizar o chat a cada 500ms
        self.clients.after(500,self.refreshChat)
#Atualiza a interface de lista de clientes
    def refreshClients(self):
        self.cleanClients()
        for client in client_list:
            self.addClient(client)
        self.clients.after(1000,self.refreshClients)
#Atualiza a interface de lista de grupos
    def refreshGroups(self):
        self.cleanGroups();
        for group in group_list:
            self.addGroup(group)
        self.groups.after(1000,self.refreshGroups)
#Adiciona grupo a interface de lista de grupos
    def addGroup(self,group):
        self.groups.insert(END,group.name)
#Limpa a interface de grupos
    def cleanGroups(self):
        self.groups.delete(0,END)
#Adiciona cliente a interface de lista de clientes
    def addClient(self,client):
        self.clients.insert(END,client.ID)
#Limpa a interface de lista de clientes
    def cleanClients(self):
        self.clients.delete(0,END)
#Abre uma janela de erro quando ha algum problema
    def ErrorDialog(self,erromsg):
        self.Error = Toplevel(height=100,width=100)
        label = Label(self.Error, text = "Erro! {0}".format(erromsg))
        label.grid(columnspan=2)
        quitb = Button(self.Error, text = "Ok",command = self.Error.destroy)
        quitb.grid(columnspan=2)
        quitb.focus_set()
        quitb.bind('<Return>',self.destroyError)
#Destroi a janela de erro ao clicar enter ou OK
    def destroyError(self,event=None):
        self.Error.destroy()
#Abre janela de mensagem de conectado
    def ConnectedDialog(self):
        self.Dialog = Toplevel(height=100,width=100)
        label = Label(self.Dialog, text = "Ola {0}, bem-vindo ao chat".format(self.nick))
        label.grid(columnspan=2)
        quit = Button(self.Dialog, text= "Ok",command = self.Dialog.destroy)
        quit.focus_set()
        quit.bind('<Return>',self.destroyCDialog)
        quit.grid(columnspan=2)
#Destroi a janela de mensagem de conectado ao apertar ENTER ou OK
    def destroyCDialog(self,event=None):
        self.Dialog.destroy()
#Interface para checar se o usuario inseriu um nick e pode-se conectar ao chat
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
#Listen multicast para resetar TTL ou inserir novos clientes ao chat
    def mcast_rcv(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((MCAST_GRP, MCAST_PORT))
        mreq = struct.pack("4sl", socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)

        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

        while True:
            data, addr =  sock.recvfrom(1024)
            print "Mensagem hello recebida : " + data
#Cria o cliente recebido pelo listener
            cliente = Client(addr[0],data)
            existe, posicao = pertence (client_list,lambda x: x.IP == cliente.IP)
            if not existe: 
                if self.MY_IP != cliente.IP and self.nick != cliente.ID:
#Adiciona o cliente a lista e roda uma thread para decrementar seu TTL
                    client_list.append(cliente)
                    print "Cliente {0}:{1} conectou".format(cliente.ID,cliente.IP)
                    thr=threading.Thread(target = client_list[-1].decrementaTTL)
                    thr.setDaemon(True)
                    thr.start()
            else:
#Se o cliente ja existe reseta o TTL do mesmo
                try:
                    client_list[posicao].resetTTL()
                except (TypeError,IndexError) as e:
                    print "mcast_rcv exception :" + str(e)
#Envia mensagem keepalive periodicamente(10s)
    def mcast_hello(self):
        while True:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 32)
            sock.sendto(self.nick, (MCAST_GRP, MCAST_PORT))
            time.sleep(10);

#Envia uma mensagem ao cliente na posicao dada na lista
    def send_message(self,msg,posicao):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
        sock.sendto(msg, (client_list[posicao].getIP(), CHAT_PORT))
#Retorna historico do chat de um IP dado
    def read_chathist(self,IP):
        return self.chat_history[IP]
#Listener para recebidas mensagens de cliente 1-1 ou chats grupos multicast
    def chat_rcv(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
        sock.bind((self.MY_IP, CHAT_PORT))
        while True:
            data, addr = sock.recvfrom(1024) # buffer size is 1024 bytes
            text = data.split()
#Checa se a mensagem pertence ao chat 1-1 ou criacao de grupo
            if(text[0] == 'CHAT:'):
                print 'Mensagem chat recebida'
                del text[0]
                data = ' '.join(text)
                self.chat_history[addr[0]].append(data)
            elif(text[0] == 'GROUP:'):
                print 'Mensagem criar grupo recebida'
                grupo = Group()
                grupo.IP = text[1]
                grupo.name = text[2]
                del text[0:3]
                text = ' '.join(text)
                grupo.members = json.loads(text)
                group_list.append(grupo)
#Se for uma mensagem para criacao de grupo, cria uma thread para listener de mensagens do grupo
                thrd = threading.Thread(target = self.grp_rcv, args=[grupo.IP])
                thrd.setDaemon(True)
                thrd.start()
#Listener para ouvir um determinado IP dado
    def grp_rcv(self,IP):
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
	sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	sock.bind((IP, MCAST_PORT))
	mreq = struct.pack("4sl", socket.inet_aton(IP), socket.INADDR_ANY)
	sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
	while True:
		data, addr =  sock.recvfrom(1024)
                print 'Mensagem grupo recebida'
		self.chat_history[IP].append(data)
#Envia mensagem para um grupo na determinada posicao da lista
    def grp_send(self,msg,posicao):
	IP = group_list[posicao].IP
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
	sock.sendto(msg, (IP, MCAST_PORT))

root = Tk()
app = App(root)
root.mainloop()
