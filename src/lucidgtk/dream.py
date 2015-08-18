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

from gi.repository import Gtk, Gio, GLib, Gdk

from cStringIO import StringIO
import numpy as np
import scipy.ndimage as nd
import scipy.misc as sm
import PIL.Image
from google.protobuf import text_format

import caffe
from caffe.proto import caffe_pb2

import os
from os.path import basename

from gi.repository.GdkPixbuf import Pixbuf

import json
import cv2

from lucidgtk.DeepDream import DeepDream
from lucidgtk.SettingsWindow import SettingsWindow
from lucidgtk.VideoWindow import VideoWindow
from lucidgtk.SequencerWindow import Sequencer, SequencerWindow
from lucidgtk.Media import LucidImage, LucidVid
from lucidgtk.GlobalMenu import GlobalMenu

class DreamWindow(Gtk.Window):

	def __init__(self, *args, **kwargs):
		for key in kwargs:
			setattr(self, key, kwargs[key])
		Gtk.Window.__init__(self, title=self.package+' | v'+self.version)
		self.set_icon_name('lucid-gtk')
		self.connect("delete-event", Gtk.main_quit)
		self.settings = Gio.Settings('org.rebelweb.dreamer')
		self.adjustments = Gio.Settings('org.rebelweb.dreamer.adjustments')
		self.string = self.strings()
	
	def run(self):
		self.set_border_width(10)
		self.grid = Gtk.Grid()
		self.add(self.grid)

		self.wakeup = False 
		self.fps = False # if not set then output videos default to settings obj. value
		self.settingsErr = None

		self.DD = DeepDream()
		self.LucidImage = LucidImage(self)
		self.LucidVid = LucidVid(self)
		
		self.vidWin = False
		self.settingsWin = False
		self.sequencerWin = False
		
		GlobalMenu(self)
		loading = self.loading()
		
		if self.DD.initcaffe(self) is False:
			self.do_config_error('Caffe could not start. Please review the model and deploy file settings')
			return

		if self.proj_folder_set() is False:
			self.do_config_error('Please set the locations for project files to be stored')
			return

		if self.media_folders_set() is False:
			self.do_config_error('Please set the locations for deepdream images and videos to be stored')
			return

		self._Sequencer = Sequencer(self)
		self.sequences = self._Sequencer.get_sequences()		   
		self.sequence = None		   
		self.mode = 'image'

		self.do_top_bar()
		self.do_adjustments_bar()
		self.do_info_bar()
		self.set_image(self.LucidImage.tempImagePath)
		self.do_bottom_bar()
		self.do_status_bar()
		self.do_notifications_bar()
		self.show_all()
		self.closeNotifierBtn.hide()
		self.wakeBtn.hide()
		loading.destroy()

	def do_notifications_bar(self):
		self.notifierBar = Gtk.Box()
		self.notifier = Gtk.Label('')
		self.notifierBar.add(self.notifier)
		self.closeNotifierBtn = Gtk.Button('OK')
		self.notifierBar.add(self.closeNotifierBtn)
		self.closeNotifierBtn.connect("clicked", self.close_notifier)
		self.grid.attach_next_to(self.notifierBar, self.topBar, Gtk.PositionType.TOP, 1, 3)
	
	def close_notifier(self, btn):
		btn.hide()
		self.notifier.set_text('')
		
	def notify(self, msg, color='green'):
		self.closeNotifierBtn.show()
		self.notifier.set_markup('<span foreground="'+color+'">'+msg+'</span>')
	
	def sequencer_win(self,b):
		if self.sequencerWin:
			self.sequencerWin.show()
		else:
			self.sequencerWin = SequencerWindow(self)
		
	def loading(self):
		loading = Gtk.Label('Lucid-GTK now loading...')
		loading.set_markup('<span foreground="green" weight="heavy">Lucid-GTK now loading...</span>')
		self.grid.add(loading)
		self.show_all()
		while Gtk.events_pending():
			Gtk.main_iteration_do(True)
		return loading
	
	def strings(self):
		return {
			'ready':'Ready to dream. Counting electric sheep',
			'dreaming':'DREAMING. DO NOT DISTURB!...',
			'waking': 'OK, OK, I\'ll wake at the end of this dream loop!'
		}
	
	def media_folders_set(self):
		if os.path.isdir(self.settings.get_string('im-dir')) and os.path.isdir(self.settings.get_string('vid-dir')):
			return True
		return False
	
	def proj_folder_set(self):
		if os.path.isdir(self.settings.get_string('proj-dir')):
			return True
		return False
	
	def do_config_error(self, msg):
		self.settingsErr = msg
		label = Gtk.Label("")
		label.set_markup('<span foreground="white" background="red" weight="heavy">CONFIGURATION ERROR: '+msg+'</span>')
		self.grid.add(label)
		self.show_all()
		SettingsWindow(self)
	
	def make_layer_select(self):
		layer_store = Gtk.ListStore(str)
		
		layers = self.DD.get_layer_names()
		for layer in layers:
			layer_store.append([layer])

		self.layer_combo = Gtk.ComboBox.new_with_model(layer_store)
		renderer_text = Gtk.CellRendererText()
		self.layer_combo.pack_start(renderer_text, True)
		self.layer_combo.add_attribute(renderer_text, "text", 0)
		self.layer_combo.set_active(0)
		return self.layer_combo
	
	
	def enable_buttons(self, v=True):
		self.fBtn.set_sensitive(v)
		self.dreamBtn.set_sensitive(v)
		self.inpCombo.set_sensitive(v)
		self.outpCombo.set_sensitive(v)	
	

	def get_selected_layer(self):
		tree_iter = self.layer_combo.get_active_iter()
		if tree_iter != None:
			model = self.layer_combo.get_model()
			return model[tree_iter][0]
		else:
			raise Exception("No output layer is set!")
			return False

	def do_status_bar(self):
		self.statusBar = Gtk.Box(spacing=10)
		label = Gtk.Label("Status: ")
		label.set_markup('<span size="larger">Status: </span>')
		self.statusBar.add(label)
		self.status = Gtk.Label("Ready")
		self.set_status(self.string['ready'], fg='blue')
		self.statusBar.add(self.status)
		self.grid.attach_next_to(self.statusBar, self.bottBar, Gtk.PositionType.BOTTOM, 1, 3)
		
	
	def do_info_bar(self):
		self.infoBar = Gtk.Box(spacing=10)
		self.infoLabel = Gtk.Label("")
		self.infoBar.add(self.infoLabel)
		self.grid.attach_next_to(self.infoBar, self.adjBar, Gtk.PositionType.BOTTOM, 1, 3)
	
	def set_info(self, msg):
		self.infoLabel.set_markup('<span color="green">'+msg+'</span>')
	   
	def on_settings_clicked(self,btn):
		if self.settingsWin:
			self.settingsWin.show()
		else:
			self.settingsWin = SettingsWindow(self)
	
	
	def on_vidbtn_clicked(self):
		if self.vidWin:
			self.vidWin.show()
		else:
			self.vidWin = VideoWindow(self)
	
	def set_status(self, msg, fg=None, bg=None, size='larger', weight=None, targ=False):
		if targ==False:
			targ = self.status
		string = ' '
		if fg!=None:
			string += 'foreground="'+fg+'" '
		if bg!=None:
			string += 'background="'+bg+'" '
		if size!=None:
			string += 'size="'+size+'" '
		if weight!=None:
			string += 'weight="'+weight+'" '
		
		targ.set_markup('<span'+string+'>'+msg+'</span>')
	
	def do_adjustments_bar(self):
		self.adjBar = Gtk.Box()
		ADJ = self.adjustments
		S = self.settings
		
		nloops = S.get_int('n-loops')
		self.loopLabel, self.loopSpin = self.spin_factory(
				'Loops:',
				Gtk.Adjustment(
					nloops, 
					ADJ.get_int('loops-min'), 
					ADJ.get_int('loops-max'), 
					ADJ.get_int('loops-incr'), 
					0, 
					0
				),
				nloops,
				self.set_loops_val
			)
		
		iter_val = S.get_int('n-iterations')
		label, self.iterSpin = self.spin_factory(
				'Iterations:',
				Gtk.Adjustment(
					iter_val, 
					ADJ.get_int('incr-min'), 
					ADJ.get_int('incr-max'), 
					ADJ.get_int('incr-incr'), 
					10, 
					0
				),
				iter_val,
				self.set_iter_val
			)
		
		octv_val = S.get_int('n-octaves')
		label, self.octaveSpin = self.spin_factory(
				'Octaves:',
				Gtk.Adjustment(
					octv_val, 
					ADJ.get_int('octv-min'), 
					ADJ.get_int('octv-max'), 
					ADJ.get_int('octv-incr'), 
					0, 
					0
				),
				octv_val,
				self.set_octv_val
			)
		
		
		octv_scale = S.get_double('octave-scale')
		label, self.scaleSpin = self.spin_factory(
				'Scale:',
				Gtk.Adjustment(
					octv_scale, 
					ADJ.get_double('scale-min'), 
					ADJ.get_double('scale-max'), 
					ADJ.get_double('scale-incr'), 
					0, 
					0
				),
				octv_scale,
				self.set_scale_val,
				[0.01, ADJ.get_int('scale-dp')]
			)
		
		zoom_scale = S.get_double('zoom-scale')
		self.zoomLabel, self.zoomSpin = self.spin_factory(
				'Zoom:',
				Gtk.Adjustment(
					zoom_scale, 
					ADJ.get_double('zoom-min'), 
					ADJ.get_double('zoom-max'), 
					ADJ.get_double('zoom-incr'), 
					0, 
					0
				),
				zoom_scale,
				self.set_zoom_val,
				[0.01, ADJ.get_int('zoom-dp')]
			)
		
		deg_val = S.get_double('rot-deg')
		self.degLabel, self.degSpin = self.spin_factory(
				'Rotation:',
				Gtk.Adjustment(
					deg_val, 
					ADJ.get_double('rot-min'), 
					ADJ.get_double('rot-max'), 
					ADJ.get_double('rot-incr'), 
					0, 
					0
				),
				deg_val,
				self.set_deg_val,
				[0.10, ADJ.get_int('rot-dp')]
			)
		
		self.grid.attach_next_to(self.adjBar, self.topBar, Gtk.PositionType.BOTTOM, 1, 3)
	
	def spin_factory(self, text, adjustment, value, callback, cfg=False):
		label = Gtk.Label(text)
		self.adjBar.add(label)
		spin = Gtk.SpinButton()
		if cfg == False:
			spin.set_adjustment(adjustment)
		else:
			spin.configure(adjustment,cfg[0],cfg[1])
		spin.set_value(value)
		spin.set_numeric(1)
		spin.connect("value-changed", callback)
		self.adjBar.pack_start(spin, False, False, 0)
		return label, spin
	
	def on_inp_combo_changed(self, combo):
		tree_iter = combo.get_active_iter()
		if tree_iter != None:
			model = combo.get_model()
			v = model[tree_iter][0]
			if v==1:
				self.dreamBtn.show()
				self.loopSpin.show()
				self.zoomSpin.show()
				self.degSpin.show()
				self.zoomLabel.show()
				self.degLabel.show()
				self.loopLabel.show()
				self.seqCombo.show()
			elif v==2:
				self.dreamBtn.hide()
				self.loopSpin.hide()
				self.zoomSpin.hide()
				self.degSpin.hide()
				self.zoomLabel.hide()
				self.degLabel.hide()
				self.loopLabel.hide()
				self.seqCombo.hide()
				
	
	def do_top_bar(self):
		self.topBar = Gtk.Box()
		
		label = Gtk.Label("Input type:")
		self.topBar.add(label)
		inp_store = Gtk.ListStore(int, str)
		inp_store.append([1, "Image"])
		inp_store.append([2, "Video"])
		self.inpCombo = Gtk.ComboBox.new_with_model(inp_store)
		renderer_text = Gtk.CellRendererText()
		self.inpCombo.pack_start(renderer_text, True)
		self.inpCombo.add_attribute(renderer_text, "text", 1)
		self.inpCombo.set_active(0)
		self.topBar.pack_start(self.inpCombo, False, False, True)
		
		
		self.fBtn = Gtk.Button("Select")
		self.fBtn.connect("clicked", self.on_fBtn_clicked)
		self.topBar.pack_start(self.fBtn, False, False, 0)
		
		self.wakeBtn = Gtk.Button('WAKE UP!')
		self.wakeBtn.connect("clicked", self.on_wake_clicked)
		self.topBar.pack_start(self.wakeBtn, False, False, 0)
		self.topBar.set_child_packing(self.wakeBtn, False, True, 0, 1)
		
		self.seq_store = Gtk.ListStore(str)
		self._Sequencer.set_seq_liststore(self.seq_store)
		
		self.seqCombo = Gtk.ComboBox.new_with_model(self.seq_store)
		renderer_text = Gtk.CellRendererText()
		self.seqCombo.pack_start(renderer_text, True)
		self.seqCombo.add_attribute(renderer_text, "text", 0)
		self.seqCombo.set_active(0)
		self.topBar.pack_start(self.seqCombo, False, False, True)
		self.topBar.set_child_packing(self.seqCombo, False, True, 0, 1)
		self.seqCombo.connect("changed", self._Sequencer.set_sequence)
		
		
		self.dreamBtn = Gtk.Button('START DREAMING')
		self.dreamBtn.connect("clicked", self.on_dream_clicked)
		self.topBar.pack_start(self.dreamBtn, False, False, 0)
		self.topBar.set_child_packing(self.dreamBtn, False, True, 0, 1)
		
		self.inpCombo.connect("changed", self.on_inp_combo_changed)
		
		self.grid.attach(self.topBar,1,1,2,1)
	
	  
	
	def on_wake_clicked(self, btn):
		self.set_status(self.string['waking'], fg='black', bg='orange', weight='heavy')
		self.wakeup = True
		while Gtk.events_pending():
			Gtk.main_iteration_do(True)
	
	def set_octv_val(self, btn):
		self.settings.set_int('n-octaves',btn.get_value())
	
	def set_deg_val(self, btn):
		self.settings.set_double('rot-deg',btn.get_value())
		
	def set_zoom_val(self, btn):
		self.settings.set_double('zoom-scale',btn.get_value())
	
	def set_iter_val(self, btn):
		self.settings.set_int('n-iterations',btn.get_value())
	
	def set_scale_val(self, btn):
		self.settings.set_double('octave-scale',btn.get_value())
	
	def set_loops_val(self, btn):
		self.settings.set_int('n-loops',btn.get_value())
		
	def set_autosave(self, btn):
		self.settings.set_boolean('auto-save',self.autoSaveBtn.get_active())
	
	def do_bottom_bar(self):
		self.bottBar = Gtk.Box()
		self.grid.attach_next_to(self.bottBar, self.scrollWin, Gtk.PositionType.BOTTOM, 1, 3)
		
		label = Gtk.Label("Output Layer:")
		self.bottBar.add(label)
		self.bottBar.pack_start(self.make_layer_select(), False, False, True)
		
		label = Gtk.Label("Save as:")
		self.bottBar.add(label)
		
		self.imageName = Gtk.Entry()
		self.imageName.set_text("myImageName")
		self.bottBar.pack_start(self.imageName, True, True, 0)
		
		outp_store = Gtk.ListStore(int, str)
		outp_store.append([0, "DON'T SAVE"])
		outp_store.append([1, ".JPG"])
		outp_store.append([2, ".AVI"])
		outp_store.append([3, ".JPG & .AVI"])
		self.outpCombo = Gtk.ComboBox.new_with_model(outp_store)
		renderer_text = Gtk.CellRendererText()
		self.outpCombo.pack_start(renderer_text, True)
		self.outpCombo.add_attribute(renderer_text, "text", 1)
		self.outpCombo.set_active(0)
		self.bottBar.pack_start(self.outpCombo, False, False, True)
		
		
	def set_image(self, im):
		self.scrollWin = Gtk.ScrolledWindow()
		self.imContainer = Gtk.Layout()
		self.scrollWin.add(self.imContainer)
		self.scrollWin.set_size_request(800,500)
		self.scrollWin.set_policy(Gtk.PolicyType.ALWAYS, Gtk.PolicyType.AUTOMATIC)
		
		self.grid.attach_next_to(self.scrollWin, self.infoBar, Gtk.PositionType.BOTTOM, 1, 3)
		
		self.im = Gtk.Image()
		self.imContainer.add(self.im)
		
		self.LucidImage.display_image(im)
		
			

	def init_outp_video(self):
		img = self.DD.prepare_image()
		self.LucidVid.h, self.LucidVid.w = img.shape[:2]	
		return self.LucidVid.init_outp_vid()

	def is_outp_set(self):
		if self.get_output_mode() == 0:
			dialog = NoOutpDialog(self)
			response = dialog.run()
			if response == Gtk.ResponseType.OK:
				ret = True
			elif response == Gtk.ResponseType.CANCEL:
				ret = False
			dialog.destroy()
			return ret
		else:
			return True
	
	def on_dream_clicked(self, button):
		if self.is_outp_set() == False:
			return
		self.mode = 'image'
		self.enable_buttons(False)
		self.set_status(self.string['dreaming'],fg='white',bg='blue',weight='heavy')
		self.wakeBtn.show()	
		while Gtk.events_pending():
			Gtk.main_iteration_do(True)
		
		tree_iter = self.outpCombo.get_active_iter()
		if tree_iter != None:
			model = self.outpCombo.get_model()
			outpType = model[tree_iter][0]
			
		if outpType > 1:
			vidOut = self.init_outp_video()
			# add the first unprocessed frame
			self.LucidVid.write_frame()
			
		if self.sequence != None:
			self.loopSpin.set_value(int(self.sequence.keys()[-1]))
			
		for i in xrange(int(self.loopSpin.get_value())):
			if self.wakeup:
				break
			
			if self.sequence != None and str(i+1) in self.sequence:
				self._Sequencer.do_seq_adjust(str(i+1))
			
			self.loop = i
			
			img = self.DD.prepare_image()
			img = self.LucidImage.zoom_and_rotate(img)
			
			self.DD.deepdream(self.DD.net, img)
			
			if outpType > 1:
				self.LucidVid.write_frame()
				
			if outpType == 1 or outpType == 3:
				self.LucidImage.save_image()

		self.set_info("")
		self.set_status(self.string['ready'], fg='blue') 
		
		if outpType > 1:
			self.LucidVid.close_session()  
		self.wakeup = False		
		self.wakeBtn.hide()
		self.enable_buttons()
		
	def on_about_clicked(self, item):
		dialog = AboutDialog(self)
		dialog.run()
		dialog.destroy()
		
	def on_help_clicked(self, item):
		dialog = HelpDialog(self)
		dialog.run()
		dialog.destroy()
	
	def on_fBtn_clicked(self, btn):
		t = self.get_input_mode()
		if t is 1:
			self.on_fselect_clicked()
		elif t is 2:
			self.on_vidbtn_clicked()
			
	def get_input_mode(self):
		tree_iter = self.inpCombo.get_active_iter()
		if tree_iter != None:
			model = self.inpCombo.get_model()
			return model[tree_iter][0]
		
	def get_output_mode(self):
		tree_iter = self.outpCombo.get_active_iter()
		if tree_iter != None:
			model = self.outpCombo.get_model()
			return model[tree_iter][0]
		
	
	def on_fselect_clicked(self):
		dialog = ImageChooser(self)
		
		response = dialog.run()
		if response == Gtk.ResponseType.OK:
		
			pname = dialog.get_filename()
			self.LucidImage.display_image(pname)
			fname = basename(pname)
			nm = os.path.splitext(fname)[0]
			self.imageName.set_text(nm)
			self.settings.set_string('im-name', nm)
		elif response == Gtk.ResponseType.CANCEL:
			print("Cancel clicked")

		dialog.destroy()

class HelpDialog(Gtk.MessageDialog):

	def __init__(self, parent):
		Gtk.MessageDialog.__init__(self, parent, 0, Gtk.MessageType.INFO, Gtk.ButtonsType.OK, "Lucid-GTK Help")
		self.format_secondary_text("Lucid-GTK is currently in Beta and documentation is lacking, a usage screencast can be found at http://rebelweb.co.uk/lucid-gtk or for bug reporting you can create an 'issue' at https://github.com/carl-codling/LucidGTK/issues")

class AboutDialog(Gtk.MessageDialog):

	def __init__(self, parent):
		Gtk.MessageDialog.__init__(self, parent, 0, Gtk.MessageType.INFO, Gtk.ButtonsType.OK, "About Lucid-GTK")
		box = self.get_content_area()
		label = Gtk.Label()
		label.set_markup('<span weight="heavy">'+parent.package+'</span>')
		box.add(label)
		label = Gtk.Label()
		label.set_markup('<span weight="light">'+parent.version+'</span>')
		box.add(label)
		im = Gtk.Image()
		pb = Pixbuf.new_from_file(parent.LucidImage.get_lucid_icon(256))
		im.set_from_pixbuf(pb)
		box.add(im)
		label = Gtk.Label('Author: Carl Codling | lucid@rebelweb.co.uk')
		box.add(label)
		
		self.show_all()

class ImageChooser(Gtk.FileChooserDialog):

	def __init__(self, parent):
		Gtk.FileChooserDialog.__init__(self, "Please choose an image file", parent,
			Gtk.FileChooserAction.OPEN,
			(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
			 Gtk.STOCK_OPEN, Gtk.ResponseType.OK))

		md = parent.settings.get_string('im-search-dir')
		
		if len(md) > 0 and os.path.isdir(md):
			self.set_current_folder(md)
		
		self.add_filters()
		self.show_all()
	
	def add_filters(self):
		filter_JPEG = Gtk.FileFilter()
		filter_JPEG.set_name("JPEG")
		filter_JPEG.add_mime_type("image/pjpeg")
		filter_JPEG.add_mime_type("image/jpeg")
		self.add_filter(filter_JPEG)

		filter_PNG = Gtk.FileFilter()
		filter_PNG.set_name("PNG")
		filter_PNG.add_mime_type("image/png")
		self.add_filter(filter_PNG)

		filter_GIF = Gtk.FileFilter()
		filter_GIF.set_name("GIF")
		filter_GIF.add_mime_type("image/gif")
		self.add_filter(filter_GIF)

		filter_any = Gtk.FileFilter()
		filter_any.set_name("All images")
		filter_any.add_mime_type("image/png")
		filter_any.add_mime_type("image/gif")
		filter_any.add_mime_type("image/pjpeg")
		filter_any.add_mime_type("image/jpeg")
		self.add_filter(filter_any)
		
 
class NoOutpDialog(Gtk.Dialog):

	def __init__(self, parent):
		Gtk.Dialog.__init__(self, "No output set", parent, 0,
			(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
			 Gtk.STOCK_OK, Gtk.ResponseType.OK))

		self.set_default_size(150, 100)

		label = Gtk.Label("Are you sure you want to run with no output image or video set?")

		box = self.get_content_area()
		box.add(label)
		self.show_all()
