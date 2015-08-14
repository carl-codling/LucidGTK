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
import os
from os.path import basename

class SettingsWindow(Gtk.Window):

    def __init__(self, mainWin):
		self.mainWin = mainWin
		self.settings = Gio.Settings('org.rebelweb.dreamer')

		Gtk.Window.__init__(self, title="Lucid-GTK Settings")

		self.set_border_width(10)

		self.box = Gtk.VBox()

		self.table = Gtk.Table(10, 6, True)

		self.notifBox = Gtk.Box()
		self.notif = Gtk.Label("")
		self.notifBox.add(self.notif)
		self.box.add(self.notifBox)

		if self.mainWin.settingsErr != None:
			self.display_err(self.mainWin.settingsErr)

		self.box.add(self.table)

		self.table.set_col_spacings(5)
		self.table.set_row_spacings(5)
		self.table.set_homogeneous(False)

		# ROW 1

		label = Gtk.Label("Max. bytes of input image:")
		self.table.attach(label, 0, 1, 0, 1)

		adjustment = Gtk.Adjustment(self.settings.get_int('max-bytes'), 30000, 10000000, 1000, 0, 0)
		self.maxbyt = Gtk.SpinButton()
		self.maxbyt.set_adjustment(adjustment)
		self.maxbyt.set_value(self.settings.get_int('max-bytes'))
		self.maxbyt.set_numeric(1)
		self.table.attach(self.maxbyt, 1, 2, 0, 1)


		label = Gtk.Label("Default FPS:")
		self.table.attach(label, 2, 3, 0, 1)

		adjustment = Gtk.Adjustment(self.settings.get_int('fps'), 10, 3000, 5, 0, 0)
		self.fps = Gtk.SpinButton()
		self.fps.set_adjustment(adjustment)
		self.fps.set_value(self.settings.get_int('fps'))
		self.fps.set_numeric(1)
		self.table.attach(self.fps, 3, 4, 0, 1)


		# ROW 2
		label = Gtk.Label("Caffe Models directory:")
		self.table.attach(label, 0, 1, 1, 2)

		self.modeldir = Gtk.Label(self.settings.get_string('models-dir'))
		self.table.attach(self.modeldir, 1, 5, 1, 2)

		self.modeldirBtn = Gtk.Button('Change')
		self.modeldirBtn.connect("clicked", self.on_modelDirBtn_clicked)
		self.table.attach(self.modeldirBtn, 5, 6, 1, 2)


		# ROW 3
		label = Gtk.Label("Caffe Model File:")
		self.table.attach(label, 0, 1, 2, 3)

		self.modelf = Gtk.Label(self.settings.get_string('model-file'))
		self.table.attach(self.modelf, 1, 5, 2, 3)

		self.modelfBtn = Gtk.Button('Change')
		self.modelfBtn.connect("clicked", self.on_modelfBtn_clicked)
		self.table.attach(self.modelfBtn, 5, 6, 2, 3)

		# ROW 4
		label = Gtk.Label("Caffe Deploy File:")
		self.table.attach(label, 0, 1, 3, 4)

		self.deploy = Gtk.Label(self.settings.get_string('deploy-prototxt'))
		self.table.attach(self.deploy, 1, 5, 3, 4)

		self.deployBtn = Gtk.Button('Change')
		self.deployBtn.connect("clicked", self.on_deployBtn_clicked)
		self.table.attach(self.deployBtn, 5, 6, 3, 4)


		# ROW 5
		label = Gtk.Label("Save images in:")
		self.table.attach(label, 0, 1, 4, 5)

		self.imdir = Gtk.Label(self.settings.get_string('im-dir'))
		self.table.attach(self.imdir, 1, 5, 4, 5)

		self.imdirBtn = Gtk.Button('Change')
		self.imdirBtn.connect("clicked", self.on_imdirBtn_clicked)
		self.table.attach(self.imdirBtn, 5, 6, 4, 5)

		# ROW 6
		label = Gtk.Label("Save videos in:")
		self.table.attach(label, 0, 1, 5, 6)

		self.viddir = Gtk.Label(self.settings.get_string('vid-dir'))
		self.table.attach(self.viddir, 1, 5, 5, 6)

		self.viddirBtn = Gtk.Button('Change')
		self.viddirBtn.connect("clicked", self.on_viddirBtn_clicked)
		self.table.attach(self.viddirBtn, 5, 6, 5, 6)

		# ROW 7
		label = Gtk.Label("Find images in:")
		self.table.attach(label, 0, 1, 6, 7)

		self.imsrchdir = Gtk.Label(self.settings.get_string('im-search-dir'))
		self.table.attach(self.imsrchdir, 1, 5, 6, 7)

		self.imsrchdirBtn = Gtk.Button('Change')
		self.imsrchdirBtn.connect("clicked", self.on_imsrchdirBtn_clicked)
		self.table.attach(self.imsrchdirBtn, 5, 6, 6, 7)

		# ROW 8
		label = Gtk.Label("Find videos in:")
		self.table.attach(label, 0, 1, 7, 8)

		self.vidsrchdir = Gtk.Label(self.settings.get_string('vid-search-dir'))
		self.table.attach(self.vidsrchdir, 1, 5, 7, 8)

		self.vidsrchdirBtn = Gtk.Button('Change')
		self.vidsrchdirBtn.connect("clicked", self.on_vidsrchdirBtn_clicked)
		self.table.attach(self.vidsrchdirBtn, 5, 6, 7, 8)

		#ROW 9
		label = Gtk.Label("Save project data in:")
		self.table.attach(label, 0, 1, 8, 9)

		self.projdir = Gtk.Label(self.settings.get_string('proj-dir'))
		self.table.attach(self.projdir, 1, 5, 8, 9)

		self.projdirBtn = Gtk.Button('Change')
		self.projdirBtn.connect("clicked", self.on_projdirBtn_clicked)
		self.table.attach(self.projdirBtn, 5, 6, 8, 9)

		#ROW 10
		self.save = Gtk.Button('Save')
		self.save.connect("clicked", self.on_save_clicked)
		self.table.attach(self.save, 2, 3, 9, 10)
		self.cancel = Gtk.Button('Cancel')
		self.cancel.connect("clicked", self.on_cancel_clicked)
		self.table.attach(self.cancel, 3, 4, 9, 10)

		self.add(self.box)
		self.show_all()
    
    def display_err(self, s):
		self.notif.set_markup('<span foreground="white" background="red" weight="heavy">'+str(s)+'</span>')
    
    def on_save_clicked(self, btn):
        self.settings.set_string('models-dir',self.modeldir.get_text())
        self.settings.set_string('im-search-dir',self.imsrchdir.get_text())
        self.settings.set_string('vid-search-dir',self.vidsrchdir.get_text())
        self.settings.set_string('im-dir',self.imdir.get_text())
        self.settings.set_string('vid-dir',self.viddir.get_text())
        self.settings.set_string('deploy-prototxt',self.deploy.get_text())
        self.settings.set_string('model-file',self.modelf.get_text())
        self.settings.set_string('proj-dir',self.projdir.get_text())
        self.settings.set_int('fps',self.fps.get_value())
        self.settings.set_int('max-bytes',self.maxbyt.get_value())
        self.destroy()
        self.mainWin.grid.destroy()
        while Gtk.events_pending():
            Gtk.main_iteration_do(True)
        self.mainWin.run()
        
    def on_cancel_clicked(self, btn):
        self.destroy()
    
    def on_imdirBtn_clicked(self, btn):
        md = self.settings.get_string('im-dir')
        folder = False
        if len(md) > 0 and os.path.isdir(md):
            folder = md 
        self.folder_chooser(self.imdir, 'im-dir', folder)
        
    def on_viddirBtn_clicked(self, btn):
        md = self.settings.get_string('vid-dir')
        folder = False
        if len(md) > 0 and os.path.isdir(md):
            folder = md 
        self.folder_chooser(self.viddir, 'vid-dir', folder)
    
    def on_imsrchdirBtn_clicked(self, btn):
        md = self.settings.get_string('im-search-dir')
        folder = False
        if len(md) > 0 and os.path.isdir(md):
            folder = md 
        self.folder_chooser(self.imsrchdir, 'im-search-dir', folder)
        
    def on_vidsrchdirBtn_clicked(self, btn):
        md = self.settings.get_string('vid-search-dir')
        folder = False
        if len(md) > 0 and os.path.isdir(md):
            folder = md 
        self.folder_chooser(self.vidsrchdir, 'vid-search-dir', folder)
         
    def on_projdirBtn_clicked(self, btn):
        md = self.settings.get_string('proj-dir')
        folder = False
        if len(md) > 0 and os.path.isdir(md):
            folder = md 
        self.folder_chooser(self.projdir, 'proj-dir', folder)
        
    def on_deployBtn_clicked(self, btn):
        md = self.settings.get_string('models-dir')
        folder = False
        if len(md) > 0 and os.path.isdir(md):
            folder = md 
        self.file_chooser(self.deploy, 'deploy-prototxt', folder, '.prototxt')
        
    def on_modelfBtn_clicked(self, btn):
        md = self.settings.get_string('models-dir')
        folder = False
        if len(md) > 0 and os.path.isdir(md):
            folder = md 
        self.file_chooser(self.modelf, 'model-file', folder, '.caffemodel')
    
    def on_modelDirBtn_clicked(self, btn):
        self.folder_chooser(self.modeldir, 'models-dir', False)
    
       
    def file_chooser(self, target, key, folder, fext):
		dialog = Gtk.FileChooserDialog("Please choose a file", self,
			Gtk.FileChooserAction.OPEN,
			(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
			 Gtk.STOCK_OPEN, Gtk.ResponseType.OK))

		if folder != False:
			dialog.set_current_folder(folder)

		response = dialog.run()
		if response == Gtk.ResponseType.OK:
			t = dialog.get_filename()
			fname = basename(t)
			fparts = os.path.splitext(fname)
			print fname, fparts, len(fparts)
			if len(fparts)==2 and fparts[1]==fext:
				target.set_text(t)
				self.display_err('')
			else:
				self.display_err('Sorry, that was nat a valid '+fext+' file')
		dialog.destroy()
    
    def folder_chooser(self, target, key, folder):
        dialog = Gtk.FileChooserDialog("Please choose a folder", self,
            Gtk.FileChooserAction.SELECT_FOLDER,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             "Select", Gtk.ResponseType.OK))
        dialog.set_default_size(800, 400)
        
        if folder != False:
            dialog.set_current_folder(folder)
            
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            t = dialog.get_filename() 
            target.set_text(t)
            self.display_err('')

        dialog.destroy()
	
        
