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

import PIL.Image
import os
from os.path import basename
import math

class VideoWindow(Gtk.Window):

	def __init__(self, mainWin):
		self.mainWin = mainWin
		self.DD = mainWin.DD
		self.LucidVid = mainWin.LucidVid
		self.LucidImage = mainWin.LucidImage
		self.settings = Gio.Settings('org.rebelweb.dreamer')
		Gtk.Window.__init__(self, title="DeepDreamsGTK Video Loader")
		self.mainWin.hide()
		self.connect("delete-event", self.on_close)
		self.set_border_width(10)

		self.vidContainer = Gtk.VBox(spacing=10)
		

		vidBtn = Gtk.Button("Select a video")
		vidBtn.connect("clicked", self.select_video)
		self.vidContainer.pack_start(vidBtn, False, False, 0)

		self.fpsBox = Gtk.VBox()
		label = Gtk.Label("Frame rate:")
		self.fpsBox.add(label)
		self.fpsNotify = Gtk.Label("")
		self.fpsBox.add(self.fpsNotify)
		adjustment = Gtk.Adjustment(self.settings.get_int('fps'), 5, 300, 1, 0, 0)
		self.fpsSpin = Gtk.SpinButton()
		self.fpsSpin.set_adjustment(adjustment)
		self.fpsSpin.set_value(self.settings.get_int('fps'))
		self.fpsSpin.set_numeric(1)
		self.fpsSpin.connect("changed", self.updFPS)
		self.fpsBox.pack_start(self.fpsSpin, False, False, 0)
		self.vidContainer.pack_start(self.fpsBox, True, True, 0)
		
		label = Gtk.Label("Start frame:")
		self.vidContainer.add(label)
		adjustment = Gtk.Adjustment(0, 0, 10000, 1, 0, 0)
		self.strtFrmSpin = Gtk.SpinButton()
		self.strtFrmSpin.set_adjustment(adjustment)
		self.strtFrmSpin.set_value(0)
		self.strtFrmSpin.set_numeric(1)
		self.strtFrmSpin.connect("changed", self.updEndFrmSpin)
		self.vidContainer.pack_start(self.strtFrmSpin, False, False, 0)
		
		label = Gtk.Label("End frame:")
		self.vidContainer.add(label)
		adjustment = Gtk.Adjustment(0, 0, 10000, 1, 0, 0)
		self.endFrmSpin = Gtk.SpinButton()
		self.endFrmSpin.set_adjustment(adjustment)
		self.endFrmSpin.set_value(0)
		self.endFrmSpin.set_numeric(1)
		self.endFrmSpin.connect("changed", self.updStrtFrmSpin)
		self.vidContainer.pack_start(self.endFrmSpin, False, False, 0)
		
		label = Gtk.Label("Continuity:")
		self.vidContainer.add(label)
		label = Gtk.Label()
		label.set_markup('<span foreground="green" weight="light">% of previous to overlay on each consecutive frame</span>')
		self.vidContainer.add(label)

		adjustment = Gtk.Adjustment(0.50, 0.05, 0.95, 0.01, 0, 0)
		self.continuitySpin = Gtk.SpinButton()
		self.continuitySpin.configure(adjustment,0.01,2)
		self.continuitySpin.set_adjustment(adjustment)
		self.continuitySpin.set_value(0.50)
		self.continuitySpin.set_numeric(1)
		self.vidContainer.pack_start(self.continuitySpin, False, False, 0)

		self.dreamBtn = Gtk.Button("START DREAMING")
		self.dreamBtn.connect("clicked", self.dream)
		self.dreamBtn.set_sensitive(False)
		self.vidContainer.pack_start(self.dreamBtn, False, False, 0)

		self.add(self.vidContainer)
		self.show_all()
	
	def updFPS(self, spin):
		self.LucidVid.fps = spin.get_value()
	
	def updEndFrmSpin(self, spin):
		strt = spin.get_value()
		s,e = self.endFrmSpin.get_range()
		if s!=strt+1:
			self.endFrmSpin.set_range(strt+1,e)
		
	
	def updStrtFrmSpin(self, spin):
		end = spin.get_value()
		s,e = self.strtFrmSpin.get_range()
		if e != end-1:
			self.strtFrmSpin.set_range(s,end-1)
	
	def select_video(self, btn):
		dialog = VideoChooser(self)
		response = dialog.run()
		
		if response == Gtk.ResponseType.OK:
			
			self.path = dialog.get_filename()
			fname = basename(self.path)
			nm = os.path.splitext(fname)[0]
			self.mainWin.imageName.set_text(nm)
			
			self.LucidVid.init_input_vid(self.path)
		
			total_frames = self.LucidVid.nframes
			self.strtFrmSpin.set_range(0,total_frames-1)
			self.strtFrmSpin.set_value(0)
			self.endFrmSpin.set_range(1,total_frames)
			self.endFrmSpin.set_value(total_frames)
			
			fps = self.LucidVid.fps
		
			# It seems that opencv can't read the fps on certain videos and returns NaN. In this instance set to default
			if math.isnan(fps):
				fps = self.settings.get_int('fps')
				self.mainWin.set_status(
					'!! Failed to retrieve frame rate from source !!',
					fg = 'red',
					bg = 'white',
					weight = 'light',
					targ = self.fpsNotify
				)
			
			self.fpsSpin.set_value(fps)
			
			self.dreamBtn.set_sensitive(True)
		
		dialog.destroy()


	def dream(self,btn):
	
		self.mainWin.wakeBtn.show()
		self.mainWin.mode = 'video'
		self.hide()
		self.mainWin.show()
		
		outpType = self.mainWin.get_output_mode()
		
		if outpType > 1:
			out = self.LucidVid.init_outp_vid()
			
		self.mainWin.loop = 0
		self.mainWin.enable_buttons(False)
		while(True):
			if self.mainWin.loop >= self.strtFrmSpin.get_value():
				if self.mainWin.loop >= self.endFrmSpin.get_value():
					break
					
				if self.mainWin.wakeup:
					break
				
				self.mainWin.set_status(self.mainWin.string['dreaming'], fg='white', bg='blue', weight='heavy')
				
				# Capture frame-by-frame
				frame = self.LucidVid.get_next_frame()
				
				if frame is None:
					break
				
				src = self.LucidVid.resize_frame(frame)
				
				if self.mainWin.loop>0:
					overl = PIL.Image.open(self.LucidImage.tempImagePath)
					image = PIL.Image.blend(src, overl, self.continuitySpin.get_value())
				else:
					image = src
				
				imname = self.LucidImage.tempImagePath
				image.save(imname)
				self.LucidImage.display_image(imname)
					
				img = self.DD.prepare_image()
				
				self.DD.deepdream(self.DD.net, img)
				
				if outpType == 1 or outpType == 3:
					self.LucidImage.save_image()
					
				if outpType > 1:  
					self.LucidVid.write_frame(colorSwitch='RGB2BGR')
			
			self.mainWin.loop += 1
		self.LucidVid.close_session()
		
		self.mainWin.wakeBtn.hide()
		self.mainWin.wakeup = False
		self.mainWin.enable_buttons()
		self.mainWin.set_info("")
		self.mainWin.set_status(self.mainWin.string['ready'], fg='blue')

	def on_close(self,a,b):
		self.destroy()
		self.mainWin.vidWin = False
		self.mainWin.show()
		self.LucidVid.close_session()


class VideoChooser(Gtk.FileChooserDialog):

	def __init__(self, parent):
		Gtk.FileChooserDialog.__init__(self, "Please choose a video file", parent,
			Gtk.FileChooserAction.OPEN,
			(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
			 Gtk.STOCK_OPEN, Gtk.ResponseType.OK))

		md = parent.settings.get_string('vid-search-dir')
		
		if len(md) > 0 and os.path.isdir(md):
			self.set_current_folder(md)
		
		self.add_filters()
		self.show_all()
	
	def add_filters(self):
		filter_vids = Gtk.FileFilter()
		filter_vids.set_name("Videos")
		filter_vids.add_mime_type("video/mp4")
		filter_vids.add_mime_type("video/x-flv")
		filter_vids.add_mime_type("video/MP2T")
		filter_vids.add_mime_type("video/3gpp")
		filter_vids.add_mime_type("video/quicktime")
		filter_vids.add_mime_type("video/x-msvideo")
		filter_vids.add_mime_type("video/x-ms-wmv")
		filter_vids.add_mime_type("video/ogg")
		filter_vids.add_mime_type("video/webm")
		filter_vids.add_mime_type("application/x-mpegURL")
		self.add_filter(filter_vids)

