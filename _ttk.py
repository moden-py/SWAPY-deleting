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
from Tkinter import BOTH, BOTTOM, DISABLED, END, HORIZONTAL, LEFT, NORMAL, RIGHT, TOP, WORD, X, Y,\
    Frame, LabelFrame, Menu, Scrollbar, Text, Tk
import tkFileDialog
from ttk import Treeview, Progressbar
import proxy


class SWAPYControl(object):
    """
    Base class for SWAPY's window control. Abstract class.
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def swapy_draw(self):
        # Draw the control on the main window
        pass

    @abstractmethod
    def swapy_init(self):
        # Init the events
        pass

    def _swapy_get_parent(self):
        # Returns the wizard parrent.
        parent_name = self.winfo_parent()
        parent = self._nametowidget(parent_name)
        return parent


class SWAPYMenu(Menu):
    """
    Class for window/popup menu.
    """
    def __init__(self, swapy_callback, *args, **kwargs):
        Menu.__init__(self, *args, **kwargs)
        self.swapy_callback = swapy_callback

    def swapy_attach_menu(self, event):
        self.post(event.x_root, event.y_root)

    def swapy_add_item(self, label, menu_id, state=NORMAL, *args):
        self.add_command(label=label, state=state, command=lambda: self.swapy_callback(menu_id, *args))

    def swapy_clear(self):
        # Removes all the menu items.
        self.delete(0, END)


class ObjectsBrowser(Treeview, SWAPYControl):
    """
    Objects browser based on Treeview + custom map for item-value.
    The reason - as in the Treeview.insert("", "end", text="text", values=(swapy_object, ))
    values can be only str or int not a custom instance.
    """
    def __init__(self, *args, **kwargs):
        super(ObjectsBrowser, self).__init__(*args, **kwargs)
        self._swapy_instances_values = {}  # Map for tree_id - pwa_object

    def swapy_draw(self):
        # Required method. Draw treeview.
        self.pack(fill=BOTH, expand=True)

    def swapy_init(self):
        # Clear old then adds the root object.
        self._swapy_instances_values = {}
        self.delete(*self.get_children(''))
        pwa = proxy.PC_system(None)
        root_tree_item = self.swapy_add_item("", text=pwa.GetProperties()['PC name'], value=pwa)
        self.swapy_update_item(root_tree_item)
        self.item(root_tree_item, open=True)
        return root_tree_item, pwa

    def swapy_add_item(self, parent, text, value):
        # Adds a tree_id, map the value.
        new_item = self.insert(parent, "end", text=text)
        self._swapy_instances_values.update({new_item: value})
        return new_item

    def swapy_update_item(self, item):
        # Clear & update children of the item.
        pwa = self.swapy_get_value(item)
        if not pwa._check_existence():
            item, pwa = self.swapy_init()
        texts_values = pwa.Get_subitems()
        children_items = self.get_children(item)
        self.delete(*children_items)
        for child in children_items:
            self._swapy_instances_values.pop(child)
        for text, value in texts_values:
            self.swapy_add_item(item, text, value)

    def swapy_get_value(self, item):
        # Extracrs a value of the tree item.
        return self._swapy_instances_values[item]


class Editor(Text, SWAPYControl):
    """
    Text editor + scrolls
    """
    def swapy_draw(self):
        # Required method. Draw text editor.
        self.pack(side=LEFT, fill=BOTH, expand=True)

        yscrollbar = Scrollbar(self._swapy_get_parent())
        yscrollbar.pack(side=RIGHT, fill=Y)

        self.config(yscrollcommand=yscrollbar.set)
        yscrollbar.config(command=self.yview)

    def swapy_init(self):
        # Clear, add header code.
        self.delete('1.0', END)
        self.swapy_add_line("import pywinauto",
                            "pwa_app = pywinauto.application.Application()",
                            )

    def swapy_add_line(self, *lines):
        # Adds new line.
        for line in lines:
            self.insert(END, line + '\n')


class Properties(Treeview, SWAPYControl):
    """
    Properties viewer
    """
    def swapy_draw(self):
        # Required method. Draw properties viewer.
        self["columns"] = ("value",)
        self.heading("#0", text="Property")
        self.heading("value", text="Value")
        self.pack(side=TOP, fill=BOTH, expand=True)

    def swapy_init(self):
        # Clear all properties.
        self.delete(*self.get_children(''))

    def swapy_add_properties(self, properties):
        # Add a bunch of properties.
        self.swapy_init()
        properties = [(n, v) for n, v in properties.iteritems()]
        for name, value in sorted(properties):
            self.insert('', END, text=name, values=(str(value),))


class MainWindow(object):
    """
    Main SWAPY window.
    """
    def __init__(self, prnt):
        self.prnt = prnt

        self._show_mainwindow()
        self.objects_browser = ObjectsBrowser(self._objects_browser_frame,
                                              show='tree',
                                              selectmode='browse')
        self.editor = Editor(self._editor_frame,
                             height=7,
                             width=7,
                             font='Arial 9',
                             wrap=WORD,
                             )
        self.properties = Properties(self._properties_frame,
                                     selectmode='browse')
        self.main_menu = SWAPYMenu(None, self.prnt, tearoff=0)
        self.objects_browser_popup_menu = SWAPYMenu(self.make_pwa_action, self.prnt, tearoff=0)
        self.properties_popup_menu = SWAPYMenu(self.properties_clipboard_actions, self.prnt, tearoff=0)
        self.editor_popup_menu = SWAPYMenu(self.editor_clipboard_actions, self.prnt, tearoff=0)

        self.draw_all()
        self.bind_all()
        self.init_all()

    def init_all(self):
        # Set ready state.
        self.objects_browser.swapy_init()
        self.editor.swapy_init()
        self.properties.swapy_init()

    def draw_all(self):
        # Draws all controls.
        self.objects_browser.swapy_draw()
        self.editor.swapy_draw()
        self.properties.swapy_draw()
        self.prnt.config(menu=self.main_menu)

    def bind_all(self):
        # Bind control's & menu events.
        self.objects_browser.bind("<Button-3>", self.on_right_click_objects_browser)
        self.objects_browser.bind('<<TreeviewSelect>>', self.on_item_select_objects_browser)
        self.properties.bind("<Button-3>", self.on_right_click_properties)
        self.editor.bind("<Button-3>", self.on_right_click_editor)
        self._bind_main_menu()

    def _show_mainwindow(self):
        # Draw main window.
        self.prnt.geometry('800x600')
        self.prnt.minsize(640, 480)
        self.prnt.wm_title("SWAPY on ttk")
        self.prnt.iconbitmap("swapy_dog_head.ico")

        progressbar = Progressbar(self.prnt, orient=HORIZONTAL, length=640)
        progressbar.pack(side="bottom", expand=False)
        progressbar.start()

        # frames
        self._objects_browser_frame = LabelFrame(self.prnt, text='Objects browser')
        self._objects_browser_frame.pack(side=LEFT, fill=BOTH, expand=True)

        # _right_frame = Frame(self.prnt)
        # _right_frame.pack(side=RIGHT, fill=BOTH, expand=True)

        self._editor_frame = LabelFrame(self.prnt, text='Editor')
        self._editor_frame.pack(side=TOP, fill=BOTH, expand=True)
        self._properties_frame = LabelFrame(self.prnt, text='Properties')
        self._properties_frame.pack(side=BOTTOM, fill=BOTH, expand=True)

    def _bind_main_menu(self):
        # Bind main menu events.
        filemenu = SWAPYMenu(self.main_menu_actions, self.prnt, tearoff=0)
        filemenu.swapy_add_item("Refresh", 401)
        filemenu.swapy_add_item("Save", 402)
        filemenu.add_separator()
        filemenu.swapy_add_item("Exit", 403)
        self.main_menu.add_cascade(label="File", menu=filemenu)

    # Event handlers
    def on_right_click_objects_browser(self, event):
        # Draw Rclick popup with actions on objects browser.
        self.objects_browser_popup_menu.swapy_clear()
        item = self.objects_browser.identify('item', event.x, event.y)
        pwa = self.objects_browser.swapy_get_value(item)

        if pwa._check_existence():
            actions = pwa.Get_actions()
            if actions:
                for menu_id, action_name in actions:
                    state = NORMAL if pwa._check_actionable() else DISABLED
                    self.objects_browser_popup_menu.swapy_add_item(action_name, menu_id, state, pwa)
            else:
                self.objects_browser_popup_menu.swapy_add_item('No actions', 0, state=DISABLED)
        else:
            self.objects_browser.swapy_update_item(item)
        self.objects_browser_popup_menu.swapy_attach_menu(event)

    def on_item_select_objects_browser(self, event):
        # Update properties browser when select an item in the tree.
        item = self.objects_browser.selection()[0]  # Only one item may be selected.
        self.objects_browser.swapy_update_item(item)
        pwa = self.objects_browser.swapy_get_value(item)
        properties = pwa.GetProperties()
        self.properties.swapy_add_properties(properties)
        pwa.Highlight_control()

    def on_right_click_properties(self, event):
        # Draw properties popup.
        self.properties_popup_menu.swapy_clear()
        item = self.properties.identify('item', event.x, event.y)
        self.properties_popup_menu.swapy_add_item('Copy all', 201, None, item)
        self.properties_popup_menu.add_separator()
        self.properties_popup_menu.swapy_add_item('Copy property', 202, None, item)
        self.properties_popup_menu.swapy_add_item('Copy value', 203, None, item)
        self.properties_popup_menu.swapy_attach_menu(event)

    def on_right_click_editor(self, event):
        # Draw editor's popup.
        self.editor_popup_menu.swapy_clear()
        self.editor_popup_menu.swapy_add_item('Cut', 301, None, "<<Cut>>")
        self.editor_popup_menu.swapy_add_item('Copy', 302, None, "<<Copy>>")
        self.editor_popup_menu.swapy_add_item('Paste', 303, None, "<<Paste>>")
        self.editor_popup_menu.swapy_attach_menu(event)

    # Menu actions
    def make_pwa_action(self, menu_id, pwa):
        # Call pywinauto the method on the object.
        code = pwa.Get_code(menu_id)
        self.editor.swapy_add_line(code)
        pwa.Exec_action(menu_id)

    def properties_clipboard_actions(self, menu_id, item):
        # Copy properties to clipboard.
        self.prnt.clipboard_clear()
        clipdata = ''
        if menu_id == 201:  # Copy all
            children = [self.properties.item(child) for child in self.properties.get_children()]
            clipdata = '\n'.join(["%s : %s" % (child['text'], child['values'][0]) for child in children])
        elif menu_id == 202:  # Copy property
            clipdata = self.properties.item(item)['text']
        elif menu_id == 203:  # Copy value
            clipdata = self.properties.item(item)['values'][0]
        else:
            # Unknow id
            pass
        self.prnt.clipboard_append(clipdata)

    def editor_clipboard_actions(self, *args):
        # Copy/Paste/Cut from editor to clipboard
        self.editor.event_generate(args[1])

    def main_menu_actions(self, menu_id):
        if menu_id == 401:  # Refresh
            self.objects_browser.swapy_init()
            self.editor.swapy_init()
            self.properties.swapy_init()
        elif menu_id == 402:  # Save
            f = tkFileDialog.asksaveasfile(mode='w', defaultextension=".py")
            if f is None:
                return
            text2save = str(self.editor.get(1.0, END))
            f.write(text2save)
            f.close()
        elif menu_id == 403:  # Exit
            self.prnt.quit()


# def demo():
#     x = 0
#     root = Tk()
#     root.geometry('800x600')
#     root.wm_title("SWAPY on ttk")
#     root.iconbitmap("swapy_dog_head.ico")
#
#     tree = Treeview(root, show='tree')
#     id2 = tree.insert("", 1, "dir2", text="Dir 2")
#     tree.insert(id2, "end", "dir 2", text="sub dir 2", values=(x))
#     tree.pack(side='left')
#
#     text = Text(root, height=7, width=7, font='Arial 14', wrap=WORD)
#     text.pack(side='top')
#
#     table = Treeview(root)
#     table["columns"]=("one","two")
#     table.column("one", width=100)
#     table.column("two", width=100)
#     table.heading("#0", text="coulmn A")
#     table.heading("one", text="coulmn A")
#     table.heading("two", text="column B")
#     table.insert("" , 0,    text="Line 1", values=("1A","1b"))
#     table.insert("" , 0,    text="Line 2", values=("0A","2b"))
#     table.pack(side='bottom')
#
#
#     menubar = Menu(root)
#     filemenu = Menu(menubar, tearoff=0)
#     filemenu.add_command(label="Open", command=hello)
#     filemenu.add_command(label="Save", command=hello)
#     filemenu.add_separator()
#     filemenu.add_command(label="Exit", command=root.quit)
#     menubar.add_cascade(label="File", menu=filemenu)
#     # display the menu
#     root.config(menu=menubar)
#
#     progressbar = Progressbar(orient=HORIZONTAL, length=1000, mode='determinate', value=20, variable=30, maximum=100)
#     progressbar.pack(side="bottom")
#     progressbar.start()
#
#
#
#     # create a popup menu
#     menu = Menu(root, tearoff=0)
#     menu.add_command(label="Undo", command=hello)
#     menu.add_command(label="Redo", command=hello)
#     def popup(event):
#         menu.post(event.x_root, event.y_root)
#
#     # attach popup to frame
#     table.bind("<Button-3>", popup)
#
#
#     root.mainloop()


if __name__ == "__main__":
    root = Tk()
    view_controller = MainWindow(root)
    root.mainloop()
