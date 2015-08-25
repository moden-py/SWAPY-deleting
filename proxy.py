# GUI object/properties browser. 
# Copyright (C) 2011 Matiychuk D.
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

import pywinauto
import sys, os
import time
import wx
import thread
import exceptions
import platform
import warnings
from const import *

'''
proxy module for pywinauto 
'''


pywinauto.timings.Timings.window_find_timeout = 1

def resource_path(filename):
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller >= 1.6
        ###os.chdir(sys._MEIPASS)
        filename = os.path.join(sys._MEIPASS, filename)
    elif '_MEIPASS2' in os.environ:
        # PyInstaller < 1.6 (tested on 1.5 only)
        ###os.chdir(os.environ['_MEIPASS2'])
        filename = os.path.join(os.environ['_MEIPASS2'], filename)
    else:
        ###os.chdir(sys.path.dirname(sys.argv[0]))
        filename = os.path.join(os.path.dirname(sys.argv[0]), filename)
    return filename

class SWAPYObject(object):
    '''
    Base proxy class for pywinauto objects.
    
    '''
    def __init__(self, pwa_obj):
        '''
        Constructor
        '''
        #original pywinauto object
        self.pwa_obj = pwa_obj
        default_sort_key = lambda name: name[0].lower()
        self.subitems_sort_key = default_sort_key
        
    def GetProperties(self):
        '''
        Return dict of original + additional properies
        Can be owerridden for non pywinauto obects
        '''
        properties = {}
        properties.update(self._get_properies())
        properties.update(self._get_additional_properties())
        return properties
        
    def Get_subitems(self):
        '''
        Return list of children - [(control_text, swapy_obj),...]
        Can be owerridden for non pywinauto obects
        '''
        subitems = []
        subitems += self._get_children()
        '''
        for control in children:
            try:
                texts = control.Texts()
            except exceptions.RuntimeError:
                texts = ['Unknown control name2!'] #workaround
            while texts.count(''):
                texts.remove('')
            c_name = ', '.join(texts)
            if not c_name:
                #nontext_controlname = pywinauto.findbestmatch.GetNonTextControlName(control, children)[0]
                top_level_parent = control.TopLevelParent().Children()
                nontext_controlname = pywinauto.findbestmatch.GetNonTextControlName(control, top_level_parent)[0]
                if nontext_controlname:
                  c_name = nontext_controlname
                else:
                  c_name = 'Unknown control name1!'
            subitems.append((c_name, self._get_swapy_object(control)))
        '''
        subitems += self._get_additional_children()
        subitems.sort(key=self.subitems_sort_key)
        #encode names
        subitems_encoded = []
        for (name, obj) in subitems:
            name = name.encode('cp1251', 'replace')
            subitems_encoded.append((name, obj))
        return subitems_encoded
        
    def Exec_action(self, action_id):
        '''
        Execute action on the control
        '''
        action = ACTIONS[action_id]
        #print('self.pwa_obj.'+action+'()')
        exec('self.pwa_obj.'+action+'()')
        return 0
        
    def Get_actions(self):
        '''
        return allowed actions for this object. [(id,action_name),...]
        '''
        allowed_actions = []
        try:
            obj_actions = dir(self.pwa_obj.WrapperObject())
        except:
            obj_actions = dir(self.pwa_obj)
        for id, action in ACTIONS.items():
            if action in obj_actions:
                allowed_actions.append((id,action))
        allowed_actions.sort(key=lambda name: name[1].lower())
        return allowed_actions
        
    def Get_code(self, action_id):
        '''
        Generate code for pywinauto module
        '''
        action = ACTIONS[action_id]
        code = "\
ctrl = window['"+self._get_additional_properties()['Access names'][0].encode('unicode-escape', 'replace')+"']\n\
ctrl."+action+"()\n"
        return code
        
    def Highlight_control(self): 
        if self._check_visibility():
          thread.start_new_thread(self._highlight_control,(3,))
        return 0
        
        
    def _get_properies(self):
        '''
        Get original pywinauto's object properties
        '''
        #print type(self.pwa_obj)
        try:
            properties = self.pwa_obj.GetProperties()
        except exceptions.RuntimeError:
            properties = {} #workaround
        return properties
        
    def _get_additional_properties(self):
        '''
        Get additonal useful properties, like a handle, process ID, etc.
        Can be overridden by derived class
        '''
        additional_properties = {}
        pwa_app = pywinauto.application.Application()
        #-----Access names
        try:
            #parent_obj = self.pwa_obj.Parent()
            parent_obj = self.pwa_obj.TopLevelParent()
        except:
            pass
        else:
            try:
                #all_controls = parent_obj.Children()
                all_controls = [pwa_app.window_(handle=ch) for ch in pywinauto.findwindows.find_windows(parent=parent_obj.handle, top_level_only=False)]
            except:
                pass
            else:
                access_names = []
                uniq_names = pywinauto.findbestmatch.build_unique_dict(all_controls)
                for uniq_name, obj in uniq_names.items():
                    if uniq_name != '' and obj.WrapperObject() == self.pwa_obj:
                      access_names.append(uniq_name)
                access_names.sort(key=len)
                additional_properties.update({'Access names' : access_names})
        #-----
        
        #-----pwa_type
        additional_properties.update({'pwa_type' : str(type(self.pwa_obj))})
        #---
        
        #-----handle
        try:
            additional_properties.update({'handle' : str(self.pwa_obj.handle)})
        except:
            pass
        #---
        return additional_properties
        
    def _get_children(self):
        '''
        Return original pywinauto's object children & names
        [(control_text, swapy_obj),...]
        '''
        def _get_name_control(control):
          try:
              texts = control.Texts()
          except exceptions.WindowsError:
            texts = ['Unknown control name2!'] #workaround for WindowsError: [Error 0] ...
          except exceptions.RuntimeError:
            texts = ['Unknown control name3!'] #workaround for RuntimeError: GetButtonInfo failed for button with command id 256
          while texts.count(''):
            texts.remove('')
          text = ', '.join(texts)
          if not text:
            u_names = []
            for uniq_name, obj in uniq_names.items():
              if uniq_name != '' and obj.WrapperObject() == control:
              #if uniq_name != '' and obj == control:
                u_names.append(uniq_name)
            if u_names:
              u_names.sort(key=len)
              name = u_names[-1]
            else:
              name = 'Unknown control name1!'
          else:
            name = text
          return (name, self._get_swapy_object(control))
        
        pwa_app = pywinauto.application.Application()
        try:
          parent_obj = self.pwa_obj.TopLevelParent()
        except pywinauto.controls.HwndWrapper.InvalidWindowHandle:
          #For non visible windows
          #...
          #InvalidWindowHandle: Handle 0x262710 is not a vaild window handle
          parent_obj = self.pwa_obj
        children = self.pwa_obj.Children()
        visible_controls = [pwa_app.window_(handle=ch) for ch in pywinauto.findwindows.find_windows(parent=parent_obj.handle, top_level_only=False)]
        uniq_names = pywinauto.findbestmatch.build_unique_dict(visible_controls)
        #uniq_names = pywinauto.findbestmatch.build_unique_dict(children)
        names_children = map(_get_name_control, children)
        return names_children
        
        
    def _get_additional_children(self):
        '''
        Get additonal children, like for a menu, submenu, subtab, etc.
        Should be owerriden in derived classes of non standart pywinauto object
        '''
        return []
        
    def _get_pywinobj_type(self, obj):
        '''
        Check self pywinauto object type
        '''
        if type(obj) == pywinauto.application.WindowSpecification:
            return 'window'
        elif type(obj) == pywinauto.controls.menuwrapper.Menu:
            return 'menu'
        elif type(obj) == pywinauto.controls.menuwrapper.MenuItem:
            return 'menu_item'
        elif type(obj) == pywinauto.controls.win32_controls.ComboBoxWrapper:
            return 'combobox'
        elif type(obj) == pywinauto.controls.common_controls.ListViewWrapper:
            return 'listview'
        elif type(obj) == pywinauto.controls.common_controls.TabControlWrapper:
            return 'tab'
        elif type(obj) == pywinauto.controls.common_controls.ToolbarWrapper:
            return 'toolbar'
        elif type(obj) == pywinauto.controls.common_controls._toolbar_button:
            return 'toolbar_button'
        elif type(obj) == pywinauto.controls.common_controls.TreeViewWrapper:
            return 'tree_view'
        elif type(obj) == pywinauto.controls.common_controls._treeview_element:
            return 'tree_item'
        elif 1==0:
            return 'other'
        else:
            return 'unknown'
        
    def _get_swapy_object(self, pwa_obj):
        pwa_type = self._get_pywinobj_type(pwa_obj)
        #print pwa_type
        if pwa_type == 'smt_NEW':
            return smt_NEW(pwa_obj)
        if pwa_type == 'window':
            return Pwa_window(pwa_obj)
        if pwa_type == 'menu':
            return Pwa_menu(pwa_obj)
        if pwa_type == 'menu_item':
            return Pwa_menu_item(pwa_obj)
        if pwa_type == 'combobox':
            return Pwa_combobox(pwa_obj)
        if pwa_type == 'listview':
            return Pwa_listview(pwa_obj)
        if pwa_type == 'tab':
            return Pwa_tab(pwa_obj)
        if pwa_type == 'toolbar':
            return Pwa_toolbar(pwa_obj)
        if pwa_type == 'toolbar_button':
            return Pwa_toolbar_button(pwa_obj)
        if pwa_type == 'tree_view':
            return Pwa_tree(pwa_obj)
        if pwa_type == 'tree_item':
            return Pwa_tree_item(pwa_obj)
        else:
            return SWAPYObject(pwa_obj)
            
    def _highlight_control(self, repeat = 1):
        while repeat > 0:
            repeat -= 1
            self.pwa_obj.DrawOutline('red', thickness=1)
            time.sleep(0.3)
            self.pwa_obj.DrawOutline(colour=0xffffff, thickness=1)
            time.sleep(0.2)
        return 0
        
    def _check_visibility(self):
        '''
        Check control/window visibility.
        Return pwa.IsVisible() or False if fails
        '''
        is_visible = False
        try:
            is_visible = self.pwa_obj.IsVisible()
        except:
            pass
        return is_visible
        
    def _check_actionable(self):
        '''
        Check control/window Actionable.
        Return True or False if fails
        '''
        try:
            self.pwa_obj.VerifyActionable()
        except:
            is_actionable = False
        else:
            is_actionable = True
        return is_actionable
        
    def _check_existence(self):
        '''
        Check control/window Exists.
        Return True or False if fails
        '''

        try:
            handle_ = self.pwa_obj.handle
            obj = pywinauto.application.WindowSpecification({'handle': handle_})
        except:
            is_exist = False
        else:
            is_exist = obj.Exists()
        return is_exist
        
        

class VirtualSWAPYObject(SWAPYObject):
    def __init__(self, parent, index):
        self.parent = parent
        self.index = index
        self.pwa_obj = self
        self._check_visibility = self.parent._check_visibility
        self._check_actionable = self.parent._check_actionable
        self._check_existence = self.parent._check_existence
        
    def Select(self):
        self.parent.pwa_obj.Select(self.index)
    
    def Get_code(self, action_id):
        '''
        Generate code for pywinauto module
        '''
        action = ACTIONS[action_id]
        arg = ""
        try:
            arg = "'"+self.index.encode('unicode-escape', 'replace')+"'"
        except:
            arg = str(self.index)
        code = "\
ctrl."+action+"("+arg+")\n"
        return code
    
    def _get_properies(self):
        return {}
    
    def Get_subitems(self):
        return []
        
    def Highlight_control(self): 
        pass
        return 0
    '''
    def Get_code(self, action_id):
        
        return '#---Not implemented yet.---\n'
    '''
        
    
class PC_system(SWAPYObject):
    handle = 0
    
    def Get_subitems(self):
        '''
        returns [(window_text, swapy_obj),...]
        '''
        #windows--------------------
        windows = []
        try_count = 3
        app = pywinauto.application.Application()
        for i in range(try_count):
          try:
            handles = pywinauto.findwindows.find_windows()
          except exceptions.OverflowError: # workaround for OverflowError: array too large
            time.sleep(1)
          except exceptions.MemoryError:# workaround for MemoryError
            time.sleep(1)
          else:
            break
        else:
          #TODO: add swapy exception: Could not get windows list
          handles = []
        #we have to find taskbar in windows list
        warnings.filterwarnings("ignore", category=FutureWarning) #ignore future warning in taskbar module
        from pywinauto import taskbar
        taskbar_handle = taskbar.TaskBarHandle()
        for w_handle in handles:
            wind = app.window_(handle=w_handle)
            if w_handle == taskbar_handle:
                texts = ['TaskBar']
            else:
                texts = wind.Texts()
            while texts.count(''):
                texts.remove('')
            title = ', '.join(texts)
            if not title:
                title = 'Window#%s' % w_handle
            title = title.encode('cp1251', 'replace')
            windows.append((title, self._get_swapy_object(wind)))
        windows.sort(key=lambda name: name[0].lower())
        #-----------------------
        
        #smt new----------------
        #------------------------
        return windows

    def _get_properies(self):
        info = { 'Platform' : platform.platform(), \
                'Processor' : platform.processor(), \
                'PC name' : platform.node() }
                
        return info
        
    def Get_actions(self):
        '''
        No actions for PC_system
        '''
        return []
        
    def Get_code(self, action_id):
        '''
        No code for PC_system
        '''
        return ''
        
    def Highlight_control(self): 
        pass
        return 0
        
    def _check_visibility(self):
        return True
        
    def _check_actionable(self):
        return True
        
    def _check_existence(self):
        return True

class Pwa_window(SWAPYObject):
    def _get_additional_children(self):
        '''
        Add menu object as children
        '''
        additional_children = []
        menu = self.pwa_obj.Menu()
        if menu:
            menu_child = [('!Menu', self._get_swapy_object(menu))]
            additional_children += menu_child
        return additional_children
        
    def Get_code(self, action_id):
        '''
        winod code
        '''
        action = ACTIONS[action_id]
        code = "\
w_handle = pywinauto.findwindows.find_windows(title=u'"+ self.pwa_obj.WindowText().encode('unicode-escape', 'replace') +"', class_name='"+ self.pwa_obj.Class() +"')[0]\n\
window = pwa_app.window_(handle=w_handle)\n\
window."+action+"()\n"
        return code
        
class Pwa_menu(SWAPYObject):

    def _check_visibility(self):
        is_visible = False
        try:
            is_visible = self.pwa_obj.ctrl.IsVisible()
        except:
            pass
        return is_visible
        
    def _check_actionable(self):
        try:
            self.pwa_obj.ctrl.VerifyActionable()
        except:
            is_actionable = False
        else:
            is_actionable = True
        return is_actionable
        
    def _check_existence(self):
        try:
            self.pwa_obj.ctrl.handle
        except:
            is_exist = False
        else:
            is_exist = True
        return is_exist

    def _get_additional_children(self):
        '''
        Add submenu object as children
        '''
        #print(dir(self.pwa_obj))
        #print(self.pwa_obj.is_main_menu)
        #print(self.pwa_obj.owner_item)
        
        self.subitems_sort_key = lambda obj: obj[1].pwa_obj.Index() #sorts items by indexes
        additional_children = []
        menu_items = self.pwa_obj.Items()
        for menu_item in menu_items:
            item_text = menu_item.Text()
            if item_text == '':
                if menu_item.Type() == 2048:
                    item_text = '-----Separator-----'
                else:
                    item_text = 'Index: %d' % menu_item.Index()
            menu_item_child = [(item_text, self._get_swapy_object(menu_item))]
            additional_children += menu_item_child
        return additional_children
        
    def _get_children(self):
        '''
        Return original pywinauto's object children
        
        '''
        return []
        
    def Highlight_control(self): 
        pass
        return 0
        
class Pwa_menu_item(Pwa_menu):

    def _check_actionable(self):
        if self.pwa_obj.State() == 3: #grayed
            is_actionable = False
        else:
            is_actionable = True
        return is_actionable

    def _get_additional_children(self):
        '''
        Add submenu object as children
        '''
        #print(dir(self.pwa_obj))
        #print(self.pwa_obj.menu)
        #print self.get_menuitems_path()
        
        additional_children = []
        submenu = self.pwa_obj.SubMenu()
        if submenu:
            submenu_child = [(self.pwa_obj.Text()+' submenu', self._get_swapy_object(submenu))]
            additional_children += submenu_child
        return additional_children
        
    def get_menuitems_path(self):
        '''
        Compose menuitems_path for GetMenuPath. Example "#0 -> Save As", "Tools -> #0 -> Configure"
        '''
        path = []
        owner_item = self.pwa_obj
        
        while owner_item:
            text = owner_item.Text()
            if not text:
                text = '#%d' % owner_item.Index()
            path.append(text)
            menu = owner_item.menu
            owner_item = menu.owner_item
        return '->'.join(path[::-1])
        
    def Get_code(self, action_id):
        '''
        Generate code for pywinauto module
        '''
        action = ACTIONS[action_id]
        code = "\
window.MenuItem(u'"+self.get_menuitems_path().encode('unicode-escape', 'replace')+"')."+action+"()\n\
"
        return code
        
class Pwa_combobox(SWAPYObject):
    def _get_additional_children(self):
        '''
        Add ComboBox items as children
        '''
        additional_children = []
        items_texts = self.pwa_obj.ItemTexts()
        for item_name in items_texts:
            additional_children += [(item_name, virtual_combobox_item(self, item_name))]
        return additional_children
    
class virtual_combobox_item(VirtualSWAPYObject):

    def _get_properies(self):
        index = None
        text = self.index
        for i, name in enumerate(self.parent.pwa_obj.ItemTexts()):
            if name == text:
                index = i
                break
        return {'Index' : index, 'Text' : text.encode('unicode-escape', 'replace')}
        
class Pwa_listview(SWAPYObject):
    def _get_additional_children(self):
        '''
        Add SysListView32 items as children
        '''
        additional_children = []
        for index in range(self.pwa_obj.ItemCount()):
            item = self.pwa_obj.GetItem(index)
            additional_children += [(item['text'], virtual_listview_item(self, index))]
        return additional_children
    
class virtual_listview_item(VirtualSWAPYObject):

    def _get_properies(self):
        item_properties = {'Index' : self.index}
        for index, item_props in enumerate(self.parent.pwa_obj.Items()):
            if index == self.index:
                item_properties.update(item_props)
                break
        return item_properties

class Pwa_tab(SWAPYObject):
    def _get_additional_children(self):
        '''
        Add TabControl items as children
        '''
        additional_children = []
        for index in range(self.pwa_obj.TabCount()):
            text = self.pwa_obj.GetTabText(index)
            additional_children += [(text, virtual_tab_item(self, index))]
        return additional_children
    
class virtual_tab_item(VirtualSWAPYObject):

    def _get_properies(self):
        item_properties = {'Index' : self.index}
        return item_properties

class Pwa_toolbar(SWAPYObject):

    def _get_additional_children(self):
        '''
        Add button objects as children
        '''
        additional_children = []
        buttons_count = self.pwa_obj.ButtonCount()
        for button_index in range(buttons_count):
          try:
            button_text = self.pwa_obj.Button(button_index).info.text
            button_object = self._get_swapy_object(self.pwa_obj.Button(button_index))
          except exceptions.RuntimeError:
            #button_text = ['Unknown button name1!'] #workaround for RuntimeError: GetButtonInfo failed for button with index 0
            pass #ignore the button
          else:
            button_item = [(button_text, button_object)]
            additional_children += button_item
        return additional_children
        
    def _get_children(self):
        '''
        Return original pywinauto's object children
        
        '''
        return []
        
class Pwa_toolbar_button(SWAPYObject):
    
    def _check_visibility(self):
        is_visible = False
        try:
            is_visible = self.pwa_obj.toolbar_ctrl.IsVisible()
        except:
            pass
        return is_visible
        
    def _check_actionable(self):
        try:
            self.pwa_obj.toolbar_ctrl.VerifyActionable()
        except:
            is_actionable = False
        else:
            is_actionable = True
        return is_actionable
        
    def _check_existence(self):
        try:
            handle_ = self.pwa_obj.toolbar_ctrl.handle
            obj = pywinauto.application.WindowSpecification({'handle': handle_})
        except:
            is_exist = False
        else:
            is_exist = obj.Exists()
        return is_exist
        
    def _get_children(self):
        return []
        
    def _get_properies(self):
        o = self.pwa_obj
        props = {'IsCheckable' : o.IsCheckable(),
                 'IsChecked' : o.IsChecked(),
                 'IsEnabled': o.IsEnabled(),
                 'IsPressable' : o.IsPressable(),
                 'IsPressed' : o.IsPressed(),
                 'Rectangle' : o.Rectangle(),
                 'State' : o.State(),
                 'Style' : o.Style(),
                 'index' : o.index,}
        return props
        
    def Highlight_control(self): 
        pass
        return 0
        
    def Get_code(self, action_id):
        '''
        Generate code for pywinauto module
        '''
        action = ACTIONS[action_id]
        arg = str(self.pwa_obj.index)
        code = "\
ctrl.Button("+arg+")."+action+"()\n"
        return code
        
class Pwa_tree(SWAPYObject):

    def _get_additional_children(self):
        '''
        Add roots object as children
        '''
        
        additional_children = []
        roots = self.pwa_obj.Roots()
        for root in roots:
            root_text = root.Text()
            obj = self._get_swapy_object(root)
            obj.path = [root_text]
            root_item = [(root_text, obj)]
            additional_children += root_item
        return additional_children
        
    def Highlight_control(self): 
        pass
        return 0

class Pwa_tree_item(SWAPYObject):

    def _get_properies(self):
        o = self.pwa_obj
        props = {'Rectangle' : o.Rectangle(),
                 'State' : o.State(),
                 'Text' : o.Text(),}
        return props

    def _check_visibility(self):
        return True
        
    def _check_existence(self):
        return True
        
    def _check_actionable(self):
        return True
        
    def _get_children(self):
        return []
        
    def Highlight_control(self): 
        pass
        return 0
    
    def _get_additional_children(self):
        '''
        Add sub tree items object as children
        '''
        
        additional_children = []
        sub_items = self.pwa_obj.Children()
        for item in sub_items:
            item_text = item.Text()
            obj = self._get_swapy_object(item)
            obj.path = self.path + [item_text]
            sub_item = [(item_text, obj)]
            additional_children += sub_item
        return additional_children
    
    def Get_code(self, action_id):
        '''
        Generate code for pywinauto module
        '''
        action = ACTIONS[action_id]
        code = "\
ctrl.GetItem("+str(self.path)+")."+action+"()\n"
        return code        