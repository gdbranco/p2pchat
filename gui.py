from Tkinter import *
import tkMessageBox

class App(Frame):
    def __init__(self,root):
        Frame.__init__(self,root)
        self.root = root
        self.client_list=[]
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
        Chat = Frame(self.root)
        self.hello = Label(Chat, text = "Ola {0}".format(self.nick))
        self.hello.grid(row=0,column=0,sticky=W+N+S)
        self.rcvChats = Text(Chat, bg = "white", width = 60, height=30, state=DISABLED)
        self.clients = Listbox(Chat, bg = "white", width = 30, height = 15)
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

        Chat.grid(row=1,column=0)

    def handleSendChat(self,event=None):
        msg = self.chatVar.get()
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

    def refreshClients(self):
        cleanClients()
        counter = 0
        for client in client_list:
            addClient(client,counter)
            counter+=1
        self.clients.after(5000,self.refreshClients())

    def addClient(self,client,counter):
        self.clients.insert(counter,client)

    def cleanClients(self):
        self.clients.delete(1.0,END)

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

root = Tk()
app = App(root)
root.mainloop()
