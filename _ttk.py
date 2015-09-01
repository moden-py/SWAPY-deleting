# GUI object/properties browser on Tk.
# Copyright (C) 2015 Matiychuk D.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public License
# as published by the Free Software Foundation; either version 2.1
# of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the
#    Free Software Foundation, Inc.,
#    59 Temple Place,
#    Suite 330,
#    Boston, MA 02111-1307 USA


from abc import ABCMeta, abstractmethod
import pickle
import Tkinter
import tkMessageBox
import ttk

import proxy


def hello():
    print "hello!"
    tkMessageBox.showinfo("hello!")


class SWAPYControl(object):
    """
    Base class for SWAPY's window control. Abstract class.
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def _swapy_draw(self):
        #Draw the control on the main window
        pass

    @abstractmethod
    def _swapy_init(self):
        #Init the events
        pass


class ObjectsBrowser(ttk.Treeview, SWAPYControl):
    """
    Objects browser based on ttk.Treeview + custom map for item-value.
    The reason - as in the ttk.Treeview.insert("", "end", text="text", values=(swapy_object, ))
    values can be only str or int not a custom instance
    """

    def __init__(self, *args, **kwargs):
        super(ObjectsBrowser, self).__init__(*args, **kwargs)
        istance_value = {}

    def _swapy_draw(self):
        #Required method. Draw treeview
        self.pack(fill=Tkinter.BOTH, expand=True)

    def _swapy_init(self):
        #Adds the root object
        self.delete(*self.get_children(''))
        root_obj = proxy.PC_system(None)
        item = self.insert("", "end", text=root_obj.GetProperties()['PC name'], values=(123, ))


class ViewController(object):
    def __init__(self, prnt):
        self.prnt = prnt

        self._show_mainwindow()
        self.objects_browser = ObjectsBrowser(self._objects_browser_frame, show='tree')

        self.show_all()
        self.bind_all()
        self.objects_browser._swapy_init()

    def show_all(self):
        self.objects_browser._swapy_draw()
        self._show_editor()
        self._show_properties()
        self._show_menu()

    def bind_all(self):
        # self._bind_objects_browser()
        self._bind_menu()

    def _show_mainwindow(self):
        self.prnt.geometry('800x600')
        root.minsize(640, 480)
        self.prnt.wm_title("SWAPY on ttk")
        self.prnt.iconbitmap("swapy_dog_head.ico")

        #frames
        self._objects_browser_frame = Tkinter.LabelFrame(self.prnt, text='Objects browser')
        self._objects_browser_frame.pack(side=Tkinter.LEFT, fill=Tkinter.BOTH, expand=True)

        _right_frame = Tkinter.Frame(self.prnt)
        _right_frame.pack(side=Tkinter.RIGHT, fill=Tkinter.BOTH, expand=True)

        self._editor_frame = Tkinter.LabelFrame(_right_frame, text='Editor')
        self._editor_frame.pack(side=Tkinter.TOP, fill=Tkinter.BOTH, expand=True)
        self._properties_frame = Tkinter.LabelFrame(_right_frame, text='Properties')
        self._properties_frame.pack(side=Tkinter.BOTTOM, fill=Tkinter.BOTH, expand=True)

    def _show_editor(self):
        self.editor = Tkinter.Text(self._editor_frame,
                                   height=7,
                                   width=7,
                                   font='Arial 14',
                                   wrap=Tkinter.WORD,
                                   )
        self.editor.pack(side=Tkinter.LEFT, fill=Tkinter.BOTH, expand=True)

        yscrollbar = Tkinter.Scrollbar(self._editor_frame)
        yscrollbar.pack(side=Tkinter.RIGHT, fill=Tkinter.Y)

        self.editor.config(yscrollcommand=yscrollbar.set)
        yscrollbar.config(command=self.editor.yview)

    def _show_properties(self):
        self.properties = ttk.Treeview(self._properties_frame)
        self.properties.pack(side=Tkinter.TOP, fill=Tkinter.BOTH, expand=True)

    def _show_menu(self):
        self.menu = Tkinter.Menu(self.prnt)
        self.prnt.config(menu=self.menu)

    # def _bind_objects_browser(self):
    #     self.objects_browser.bind("<Button-3>", self.on_right_click_objects_browser)
    #     self.objects_browser.bind('<<TreeviewOpen>>', self.on_item_expand_objects_browser)

    def _bind_menu(self):
        filemenu = Tkinter.Menu(self.menu, tearoff=False)
        #filemenu.add_command(label="Open", command=self._init_objects_browser)
        filemenu.add_command(label="Save", command=hello)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=root.quit)
        self.menu.add_cascade(label="File", menu=filemenu)
    #
    # def on_right_click_objects_browser(self, event):
    #     item = self.objects_browser.identify('item', event.x, event.y)
    #     value = pickle.loads(self.objects_browser.item(item)['values'][0])
    #     print type(value), value
    #
    # def on_item_expand_objects_browser(self, event):
    #     def _update(item, obj):
    #         self.objects_browser.delete(*self.objects_browser.get_children(item))
    #         subitems = obj.Get_subitems()
    #         for i_name, i_obj in subitems:
    #             self.objects_browser.insert(item, "end", text=i_name, values=(i_obj))
    #
    #     tree_item = self.objects_browser.selection()
    #     obj = self.objects_browser.item(tree_item)['values'][0]
    #
    #     print type(obj)
    #
    #     if not obj._check_existence():
    #       self._init_objects_browser()
    #       root_item = self.objects_browser.get_children()[0]
    #       tree_item = root_item
    #       obj = self.objects_browser.item(tree_item)['values'][0]
    #     #self.prop_updater.props_update(obj)
    #     #self.tree_updater.tree_update(tree_item, obj)
    #     _update(tree_item, obj)
    #     obj.Highlight_control()


def demo():
    x = 0
    root = Tkinter.Tk()
    root.geometry('800x600')
    root.wm_title("SWAPY on ttk")
    root.iconbitmap("swapy_dog_head.ico")

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
    root = Tkinter.Tk()
    view_controller = ViewController(root)
    root.mainloop()