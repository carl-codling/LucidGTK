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

import cv2
import PIL.Image
import numpy as np
import os
from os.path import basename
import math

class VideoWindow(Gtk.Window):

    def __init__(self, mainWin):
        self.mainWin = mainWin
        self.settings = Gio.Settings('org.rebelweb.dreamer')
        Gtk.Window.__init__(self, title="DeepDreamsGTK Video Loader")
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
        self.fpsBox.pack_start(self.fpsSpin, False, False, 0)
        self.vidContainer.pack_start(self.fpsBox, True, True, 0)
        
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

    def select_video(self, btn):
        dialog = Gtk.FileChooserDialog("Please choose a video file", self,
            Gtk.FileChooserAction.OPEN,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
        
        md = self.settings.get_string('vid-search-dir')
        
        if len(md) > 0 and os.path.isdir(md):
            dialog.set_current_folder(md)
        
        self.add_filters(dialog)

        response = dialog.run()
        
        if response == Gtk.ResponseType.OK:
            
            self.path = dialog.get_filename()
            fname = basename(self.path)
            nm = os.path.splitext(fname)[0]
            self.mainWin.imageName.set_text(nm)
            
            cap = cv2.VideoCapture(self.path)
            fps = cap.get(5)
        
            # It seems that opencv can't read the fps on certain videos and return NaN. In this instance default to 30
            if math.isnan(fps):
                fps = self.settings.get_int('fps')
                self.fpsNotify.set_markup('<span foreground="red" background="white" weight="light">!! Failed to retrieve frame rate from source !!</span>')
                
            cap.release()
            
            self.fpsSpin.set_value(fps)
            
            self.dreamBtn.set_sensitive(True)
            
        elif response == Gtk.ResponseType.CANCEL:
            print("Cancel clicked")

        dialog.destroy()

    def add_filters(self, dialog):
        filter_JPEG = Gtk.FileFilter()
        filter_JPEG.set_name("Videos")
        filter_JPEG.add_mime_type("video/mp4")
        filter_JPEG.add_mime_type("video/x-flv")
        filter_JPEG.add_mime_type("video/MP2T")
        filter_JPEG.add_mime_type("video/3gpp")
        filter_JPEG.add_mime_type("video/quicktime")
        filter_JPEG.add_mime_type("video/x-msvideo")
        filter_JPEG.add_mime_type("video/x-ms-wmv")
        filter_JPEG.add_mime_type("video/ogg")
        filter_JPEG.add_mime_type("video/webm")
        filter_JPEG.add_mime_type("application/x-mpegURL")
        dialog.add_filter(filter_JPEG)
        
    
    def dream(self,btn):
    
        self.mainWin.wakeBtn.show()
         
        tree_iter = self.mainWin.outpCombo.get_active_iter()
        if tree_iter != None:
            model = self.mainWin.outpCombo.get_model()
            outpType = model[tree_iter][0]
        
        
        self.mainWin.mode = 'video'
        self.hide()
        self.cap = cv2.VideoCapture(self.path)
        cap = self.cap
        
        w = int(cap.get(3))
        h = int(cap.get(4))
        bytesize = int(cap.get(3)) * int(cap.get(4)) * 3
        limit = int(self.mainWin.settings.get_int('max-bytes'))
        (w, h) = self.mainWin.get_shrink_dimensions(w, h, bytesize, limit)
        cap.set(3, w)
        cap.set(4, h)
        
        if outpType > 1:
            fourcc = cv2.cv.CV_FOURCC(*'XVID')
            fps = self.fpsSpin.get_value()
            fname = self.mainWin.make_new_fname(dirSetting='vid-dir', extension='.avi')
            out = cv2.VideoWriter(fname,fourcc, fps, (w,h))
            
        self.mainWin.loop = 0
        self.mainWin.enable_buttons(False)
        while(True):
            if self.mainWin.wakeup:
    	        break
    	    
            self.mainWin.set_notif('<span foreground="white" background="blue" weight="heavy">%s</span>'%self.mainWin.string['dreaming'])
            
            # Capture frame-by-frame
            ret, frame = cap.read()
            
            if frame is None:
                break
            
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            src = PIL.Image.fromarray(frame)
            size = w,h
            src = src.resize(size, PIL.Image.ANTIALIAS)
            
            if self.mainWin.loop>0:
                overl = PIL.Image.open(self.mainWin.tempImagePath)
                image = PIL.Image.blend(src, overl, self.continuitySpin.get_value())
            else:
                image = src
            imname = self.mainWin.tempImagePath
            
            image.save(imname)
            self.mainWin.display_image(imname)
                
            img = self.mainWin.prepare_image()
            
            self.mainWin.deepdream(self.mainWin.net, img)
            
            if outpType == 1 or outpType == 3:
        	    self.mainWin.save_image()
        	    
            if outpType > 1:  
                imgout = self.mainWin.prepare_image()
                imgout = np.uint8(np.clip(imgout, 0, 255)) 
                imgout = cv2.cvtColor(imgout, cv2.COLOR_RGB2BGR) 
                out.write(imgout)
            
            self.mainWin.loop += 1
        cap.release()
        if outpType > 1:
            out.release()
        cv2.destroyAllWindows()
        
        self.mainWin.wakeBtn.hide()
        self.mainWin.wakeup = False
        self.mainWin.enable_buttons()
        self.mainWin.set_info("")
        self.mainWin.set_notif('<span foreground="blue">%s</span>'%self.mainWin.string['ready'])






