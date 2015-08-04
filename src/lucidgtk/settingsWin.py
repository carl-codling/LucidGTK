# 
# Copyright (C) 2015 Carl Codling
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


from gi.repository import Gtk, Gio, GLib

import json


class SettingsWindow(Gtk.Window):

    def __init__(self, mainWin):
        self.mainWin = mainWin
        self.settings = Gio.Settings('org.rebelweb.dreamer')
        
        Gtk.Window.__init__(self, title="Lucid-GTK Settings")
        
        self.set_border_width(10)
        
        self.table = Gtk.Table(7, 7, True)
        
        # ROW 1
        
        
        
        # ROW 2
        label = Gtk.Label("Caffe Model File:")
        self.table.attach(label, 0, 1, 1, 2)
        
        self.modelf = Gtk.Label(self.settings.get_string('model-file'))
        self.table.attach(self.modelf, 1, 6, 1, 2)
        
        self.modelfBtn = Gtk.Button('Change')
        self.modelfBtn.connect("clicked", self.on_modelfBtn_clicked)
        self.table.attach(self.modelfBtn, 6, 7, 1, 2)
        
        # ROW 3
        label = Gtk.Label("Caffe Deploy File:")
        self.table.attach(label, 0, 1, 2, 3)
        
        self.deploy = Gtk.Label(self.settings.get_string('deploy-prototxt'))
        self.table.attach(self.deploy, 1, 6, 2, 3)
        
        self.deployBtn = Gtk.Button('Change')
        self.deployBtn.connect("clicked", self.on_deployBtn_clicked)
        self.table.attach(self.deployBtn, 6, 7, 2, 3)
        
        # ROW 4
        
        label = Gtk.Label("Max. bytes of input image:")
        self.table.attach(label, 0, 1, 3, 4)
        
        
        adjustment = Gtk.Adjustment(self.settings.get_int('max-bytes'), 30000, 10000000, 1000, 0, 0)
        self.maxbyt = Gtk.SpinButton()
        self.maxbyt.set_adjustment(adjustment)
        self.maxbyt.set_value(self.settings.get_int('max-bytes'))
        self.maxbyt.set_numeric(1)
        self.table.attach(self.maxbyt, 1, 6, 3, 4)
        
        # ROW 5
        label = Gtk.Label("Save images in:")
        self.table.attach(label, 0, 1, 4, 5)
        
        self.imdir = Gtk.Label(self.settings.get_string('im-dir'))
        self.table.attach(self.imdir, 1, 6, 4, 5)
        
        self.imdirBtn = Gtk.Button('Change')
        self.imdirBtn.connect("clicked", self.on_imdirBtn_clicked)
        self.table.attach(self.imdirBtn, 6, 7, 4, 5)
        
        # ROW 6
        label = Gtk.Label("Save videos in:")
        self.table.attach(label, 0, 1, 5, 6)
        
        self.viddir = Gtk.Label(self.settings.get_string('vid-dir'))
        self.table.attach(self.viddir, 1, 6, 5, 6)
        
        self.viddirBtn = Gtk.Button('Change')
        self.viddirBtn.connect("clicked", self.on_viddirBtn_clicked)
        self.table.attach(self.viddirBtn, 6, 7, 5, 6)
        
        #ROW 7
        self.save = Gtk.Button('Save')
        self.save.connect("clicked", self.on_save_clicked)
        self.table.attach(self.save, 3, 4, 6, 7)
        self.cancel = Gtk.Button('Cancel')
        self.cancel.connect("clicked", self.on_cancel_clicked)
        self.table.attach(self.cancel, 4, 5, 6, 7)
        
        self.add(self.table)
        self.show_all()
    
    def on_save_clicked(self, btn):
        self.settings.set_string('im-dir',self.imdir.get_text())
        self.settings.set_string('vid-dir',self.viddir.get_text())
        self.settings.set_string('deploy-prototxt',self.deploy.get_text())
        self.settings.set_string('model-file',self.modelf.get_text())
        self.destroy()
        self.mainWin.grid.destroy()
        while Gtk.events_pending():
            Gtk.main_iteration_do(True)
        self.mainWin.__init__()
        self.mainWin.show_all()
        
    def on_cancel_clicked(self, btn):
        self.destroy()
    
    def on_imdirBtn_clicked(self, btn):
        self.folder_chooser(self.imdir, 'im-dir')
        
    def on_viddirBtn_clicked(self, btn):
        self.folder_chooser(self.viddir, 'vid-dir')
        
    def on_deployBtn_clicked(self, btn):
        self.file_chooser(self.deploy, 'deploy-prototxt')
        
    def on_modelfBtn_clicked(self, btn):
        self.file_chooser(self.modelf, 'model-file')
        
    def file_chooser(self, target, key):
        dialog = Gtk.FileChooserDialog("Please choose a file", self,
            Gtk.FileChooserAction.OPEN,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_OPEN, Gtk.ResponseType.OK))

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
        
            t = dialog.get_filename()
            target.set_text(t)
            
        dialog.destroy()
    
    def folder_chooser(self, target, key):
        dialog = Gtk.FileChooserDialog("Please choose a folder", self,
            Gtk.FileChooserAction.SELECT_FOLDER,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             "Select", Gtk.ResponseType.OK))
        dialog.set_default_size(800, 400)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            t = dialog.get_filename() 
            target.set_text(t)

        dialog.destroy()
	
        
