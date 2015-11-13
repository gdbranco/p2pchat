from Tkinter import *
import tkMessageBox

class App(Frame):
    def __init__(self,master):
        Frame.__init__(self,master)
        self.grid()
        self.create_widgets()

    def create_widgets(self):
        self.username = Label(self,text="Nick")
        self.username.grid(row=0,sticky=E)
        self.entrada = Entry(self)
        self.entrada.grid(row=0,column=1)
        self.connect = Button(self,text="Connect",command=self.connect)
        self.connect.grid(columnspan=2)

    def ErrorDialog(self,erromsg):
        Error = Toplevel(height=100,width=100)
        label = Label(Error, text = "Erro! {0}".format(erromsg))
        label.grid(columnspan=2)
        quitb = Button(Error, text = "Ok",command = Error.destroy)
        quitb.grid(columnspan=2)
    def ConnectedDialog(self,nick):
        Dialog = Toplevel(height=100,width=100)
        label = Label(Dialog, text = "Ola {0}, bem-vindo ao chat".format(nick))
        label.grid(columnspan=2)
        quit = Button(Dialog, text= "Ok",command = Dialog.destroy)
        quit.grid(columnspan=2)
    def connect(self):
        nick = self.entrada.get()
        if nick == "":
            self.ErrorDialog("Necessario inserir um nick para continuar...")
        else:
            self.ConnectedDialog(nick);

root = Tk()
root.title("p2p chat")
app = App(root)
root.mainloop()
