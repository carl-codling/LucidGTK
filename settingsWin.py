#!/usr/bin/python
from gi.repository import Gtk

import json


class SettingsWindow(Gtk.Window):

    def __init__(self, mainWin):
        self.mainWin = mainWin
        self.load_settings()
        Gtk.Window.__init__(self, title="DeepDreamsGTK Settings")
        self.settingWidgets = {}
        self.set_border_width(10)
        
        self.settingsContainer = Gtk.VBox(spacing=10, homogeneous=True)
        
        for key,item in self.settings.iteritems():
            self.build_item(key,item)
            
        saveBtn = Gtk.Button("SAVE & RELOAD")
        saveBtn.connect("clicked", self.save_settings)
        self.settingsContainer.pack_start(saveBtn, False, False, 0)
        
        self.add(self.settingsContainer)
        self.show_all()
 
    def load_settings(self):
        with open('settings.json') as data_file:    
            self.settings = json.load(data_file)
        print type(self.settings)
            
    def build_item(self, key,item):
        row = Gtk.Box(spacing=5)
        label = Gtk.Label(key)
        row.add(label)
        
        entry = Gtk.Entry()
        entry.set_text(item)
        row.add(entry)
        self.settingsContainer.pack_start(row, True, True, 0)
        self.settingWidgets[key] = entry
    
    def save_settings(self,btn):
        data = {}
        for key,item in self.settingWidgets.iteritems():
            data[key] = item.get_text()
        with open('settings.json', 'w') as fp:
            json.dump(data, fp)
        self.destroy()
        self.mainWin.grid.destroy()
        self.mainWin.__init__()
        self.mainWin.show_all()
	
        
