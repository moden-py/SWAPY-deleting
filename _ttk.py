import ttk
import tkMessageBox
import Tkinter

class Window(ttk.Frame):
    pass

def hello():
    print "hello!"
    tkMessageBox.showinfo("hello!")


def demo():
    x = 0
    root = Tkinter.Tk()
    root.geometry('800x600')
    root.wm_title("SWAPY on ttk")
    root.iconbitmap("swapy_dog_head.ico")

    wondow = Window(root)
    wondow.pack()

    tree = ttk.Treeview(root, show='tree')
    id2 = tree.insert("", 1, "dir2", text="Dir 2")
    tree.insert(id2, "end", "dir 2", text="sub dir 2", values=(x))
    tree.pack(side='left')

    text = Tkinter.Text(root, height=7, width=7, font='Arial 14', wrap=Tkinter.WORD)
    text.pack(side='top')

    table = ttk.Treeview(root)
    table["columns"]=("one","two")
    table.column("one", width=100)
    table.column("two", width=100)
    table.heading("#0", text="coulmn A")
    table.heading("one", text="coulmn A")
    table.heading("two", text="column B")
    table.insert("" , 0,    text="Line 1", values=("1A","1b"))
    table.insert("" , 0,    text="Line 2", values=("0A","2b"))
    table.pack(side='bottom')


    menubar = Tkinter.Menu(root)
    filemenu = Tkinter.Menu(menubar, tearoff=0)
    filemenu.add_command(label="Open", command=hello)
    filemenu.add_command(label="Save", command=hello)
    filemenu.add_separator()
    filemenu.add_command(label="Exit", command=root.quit)
    menubar.add_cascade(label="File", menu=filemenu)
    # display the menu
    root.config(menu=menubar)

    progressbar = ttk.Progressbar(orient=Tkinter.HORIZONTAL, length=1000, mode='determinate', value=20, variable=30, maximum=100)
    progressbar.pack(side="bottom")
    progressbar.start()



    # create a popup menu
    menu = Tkinter.Menu(root, tearoff=0)
    menu.add_command(label="Undo", command=hello)
    menu.add_command(label="Redo", command=hello)
    def popup(event):
        menu.post(event.x_root, event.y_root)

    # attach popup to frame
    table.bind("<Button-3>", popup)


    root.mainloop()


if __name__ == "__main__":
    demo()