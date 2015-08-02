#!/usr/bin/python
from gi.repository import Gtk

import cv2
import PIL.Image
import numpy as np
import os
from os.path import basename
import math

class VideoWindow(Gtk.Window):

    def __init__(self, mainWin):
        self.mainWin = mainWin
        Gtk.Window.__init__(self, title="DeepDreamsGTK Video Loader")
        self.set_border_width(10)
        
        self.vidContainer = Gtk.VBox(spacing=10)
          
        vidBtn = Gtk.Button("Select a video")
        vidBtn.connect("clicked", self.select_video)
        self.vidContainer.pack_start(vidBtn, False, False, 0)
        
        self.vidName = Gtk.Entry()
        self.vidName.set_text("myVideoName")
        self.vidContainer.pack_start(self.vidName, True, True, 0)
        
        self.fpsBox = Gtk.VBox()
        label = Gtk.Label("Frame rate:")
        self.fpsBox.add(label)
        self.fpsNotify = Gtk.Label("")
        self.fpsBox.add(self.fpsNotify)
        adjustment = Gtk.Adjustment(30, 5, 300, 1, 0, 0)
        self.fpsSpin = Gtk.SpinButton()
        self.fpsSpin.set_adjustment(adjustment)
        self.fpsSpin.set_value(30)
        self.fpsSpin.set_numeric(1)
        self.fpsBox.pack_start(self.fpsSpin, False, False, 0)
        self.vidContainer.pack_start(self.fpsBox, True, True, 0)
        
        label = Gtk.Label("Continuity:")
        self.vidContainer.add(label)
        adjustment = Gtk.Adjustment(0.50, 0.05, 0.95, 0.01, 0, 0)
        self.continuitySpin = Gtk.SpinButton()
        self.continuitySpin.configure(adjustment,0.01,2)
        self.continuitySpin.set_adjustment(adjustment)
        self.continuitySpin.set_value(0.50)
        self.continuitySpin.set_numeric(1)
        self.vidContainer.pack_start(self.continuitySpin, False, False, 0)
          
        self.dreamBtn = Gtk.Button("DREAMIFY")
        self.dreamBtn.connect("clicked", self.dream)
        self.dreamBtn.set_sensitive(False)
        self.vidContainer.pack_start(self.dreamBtn, False, False, 0)
        
        self.add(self.vidContainer)
        self.show_all()
        self.fpsBox.hide()

    def select_video(self, btn):
        dialog = Gtk.FileChooserDialog("Please choose a video file", self,
            Gtk.FileChooserAction.OPEN,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_OPEN, Gtk.ResponseType.OK))

        self.add_filters(dialog)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            
            self.fpsBox.show()
            
            self.path = dialog.get_filename()
            
            cap = cv2.VideoCapture(self.path)
            fps = cap.get(5)
        
            # It seems that opencv can't read the fps on certain videos and return NaN. In this instance default to 30
            if math.isnan(fps):
                fps = 25
                self.fpsNotify.set_markup('<span foreground="red" background="white" weight="light">!! Failed to retrieve frame rate from source !!</span>')
                
            cap.release()
            
            self.fpsSpin.set_value(fps)
            
            fname = basename(self.path)
            self.vidName.set_text(os.path.splitext(fname)[0])
            
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
        
    def make_new_fname(self):
        fp = 'videoOutput/'+self.vidName.get_text()+'.avi'
        if os.path.isfile(fp):
            i = 0
            while True:
                fp = 'videoOutput/'+self.vidName.get_text()+'_'+str(i)+'.avi'
                if os.path.isfile(fp)==False:
                    break
                i += 1
        return fp
    
    def dream(self,btn):
        self.mainWin.mode = 'video'
        self.hide()
        self.cap = cv2.VideoCapture(self.path)
        cap = self.cap
        fourcc = cv2.cv.CV_FOURCC(*'XVID')
        w = int(cap.get(3))
        h = int(cap.get(4))
        print w, h
        bytesize = int(cap.get(3)) * int(cap.get(4)) * 3
        limit = int(self.mainWin.settings['Max Image Bytes'])
        (w, h) = self.mainWin.get_shrink_dimensions(w, h, bytesize, limit)
        cap.set(3, w)
        cap.set(4, h)
        fps = self.fpsSpin.get_value()
        
        out = cv2.VideoWriter(self.make_new_fname(),fourcc, fps, (w,h))
        self.mainWin.loop = 0
        self.mainWin.enable_buttons(False)
        while(True):
            self.mainWin.set_notif('<span foreground="white" background="purple" weight="heavy">MACHINE IS DREAMING IN TECHNICOLOR MOVING PICTURES!...</span>')
            
            # Capture frame-by-frame
            ret, frame = cap.read()
            
            if frame is None:
                break
            
            src = PIL.Image.fromarray(frame)
            size = w,h
            src = src.resize(size, PIL.Image.ANTIALIAS)
            
            if self.mainWin.loop>0:
                overl = PIL.Image.open('.temp/temp.jpg')
                image = PIL.Image.blend(src, overl, self.continuitySpin.get_value())
            else:
                image = src
            imname = '.temp/temp.jpg'
            image.save(imname)
            self.mainWin.reset_image(imname)
                
            img = self.mainWin.prepare_image()
            
            self.mainWin.deepdream(self.mainWin.net, img)
            imgout = self.mainWin.prepare_image()
            imgout = np.uint8(np.clip(imgout, 0, 255))
            out.write(imgout)
            
            self.mainWin.loop += 1
        cap.release()
        out.release()
        cv2.destroyAllWindows()
        self.mainWin.enable_buttons()
        self.mainWin.set_notif('<span foreground="blue">Ready to dream. Counting electric sheep</span>')






