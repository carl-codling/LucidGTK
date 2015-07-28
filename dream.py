#!/usr/bin/python
from gi.repository import Gtk

from cStringIO import StringIO
import numpy as np
import scipy.ndimage as nd
import scipy.misc as sm
import PIL.Image
from google.protobuf import text_format

import caffe
import os
from os.path import basename

from gi.repository.GdkPixbuf import Pixbuf


import json

from settingsWin import SettingsWindow

def objective_L2(dst):
    dst.diff[:] = dst.data

class DreamWindow(Gtk.Window):

    def __init__(self):
        self.init_settings()
        
        

        model_path = str(self.settings['Model Path']) # substitute your path here
        net_fn   = model_path + str(self.settings['deploy.prototxt'])
        param_fn = model_path + str(self.settings['caffemodel'])
        
        # Patching model to be able to compute gradients.
        # Note that you can also manually add "force_backward: true" line to "deploy.prototxt".
        model = caffe.io.caffe_pb2.NetParameter()
        text_format.Merge(open(net_fn).read(), model)
        model.force_backward = True
        open('tmp.prototxt', 'w').write(str(model))

        self.net = caffe.Classifier('tmp.prototxt', param_fn,
                               mean = np.float32([104.0, 116.0, 122.0]), # ImageNet mean, training set dependent
                               channel_swap = (2,1,0)) # the reference model has channels in BGR order instead of RGB
        
        Gtk.Window.__init__(self, title="Lucid - GTK Deep Dreamer")
        self.set_border_width(10)
        self.grid = Gtk.Grid()
        self.add(self.grid)
        self.do_top_bar()
        self.do_info_bar()
        self.set_image('DEFAULT.JPG')
        self.do_bottom_bar()
        self.do_notif_bar()
        
    
    def check_im_size(self, pb):
        ch = pb.get_n_channels()
        w = pb.get_width()
        h = pb.get_height()
        bytesize = pb.get_byte_length()
        limit = int(self.settings['Max Image Bytes'])
        
        if bytesize > limit:
            
            while bytesize > limit:
                w = (float(w)*0.99)
                h = (float(h)*0.99)
                bytesize = float(ch) * w * h
            pbnew = pb.scale_simple(w, h, 3)
            pbnew.savev("temp.jpg","jpeg", ["quality"], ["80"])
            self.imagef = "temp.jpg"
            return pbnew
        return pb
    
    def showarray(self, a, fmt='jpeg'):
        a = np.uint8(np.clip(a, 0, 255))
        f = StringIO()
        image = PIL.Image.fromarray(a)
        image.save('temp.jpg')
        self.reset_image('temp.jpg')
    
    def make_step(self, net, step_size=1.5, jitter=32, clip=True, objective=objective_L2):
        
        end = self.settings['output layer']
        
        src = net.blobs['data'] # input image is stored in Net's 'data' blob
        dst = net.blobs[end]

        ox, oy = np.random.randint(-jitter, jitter+1, 2)
        src.data[0] = np.roll(np.roll(src.data[0], ox, -1), oy, -2) # apply jitter shift

        net.forward(end=end)
        objective(dst)  # specify the optimization objective
        net.backward(start=end)
        g = src.diff[0]
        # apply normalized ascent step to the input image
        src.data[:] += step_size/np.abs(g).mean() * g

        src.data[0] = np.roll(np.roll(src.data[0], -ox, -1), -oy, -2) # unshift image

        if clip:
            bias = net.transformer.mean['data']
            src.data[:] = np.clip(src.data, -bias, 255-bias)

    def deepdream(self, net, base_img,  
                  clip=True, **step_params):
        # prepare base images for all octaves
        octaves = [self.preprocess(net, base_img)]
        for i in xrange(self.octaveSpin.get_value_as_int()-1):
            octaves.append(nd.zoom(octaves[-1], (1, 1.0/self.scaleSpin.get_value(),1.0/self.scaleSpin.get_value()), order=1))
        
        src = net.blobs['data']
        detail = np.zeros_like(octaves[-1]) # allocate image for network-produced details
        for octave, octave_base in enumerate(octaves[::-1]):
            h, w = octave_base.shape[-2:]
            if octave > 0:
                # upscale details from the previous octave
                h1, w1 = detail.shape[-2:]
                detail = nd.zoom(detail, (1, 1.0*h/h1,1.0*w/w1), order=1)

            src.reshape(1,3,h,w) # resize the network's input image size
            src.data[0] = octave_base+detail
            for i in xrange(self.iterSpin.get_value_as_int()):
                self.make_step(net, clip=clip, **step_params)
                
                # visualization
                vis = self.deprocess(net, src.data[0])
                if not clip: # adjust image contrast if clipping is disabled
                    vis = vis*(255.0/np.percentile(vis, 99.98))
                self.showarray(vis)
                self.set_info("Loop: "+str(self.loop+1)+" | Octave: "+str(octave+1)+" | Iter: "+str(i+1))
                while Gtk.events_pending():
                	Gtk.main_iteration_do(True)
            # extract details produced on the current octave
            detail = src.data[0]-octave_base
            
        # returning the resulting image
        if self.autoSaveBtn.get_active():
        	self.save_image()
        self.set_info("")
        self.set_notif('<span foreground="blue">Ready</span>')
        return self.deprocess(net, src.data[0])
    
    # a couple of utility functions for converting to and from Caffe's input image layout
    def preprocess(self, net, img):
        return np.float32(np.rollaxis(img, 2)[::-1]) - net.transformer.mean['data']
    def deprocess(self, net, img):
        return np.dstack((img + net.transformer.mean['data'])[::-1])
    
    def do_notif_bar(self):
    	self.notifBar = Gtk.Box(spacing=10)
    	label = Gtk.Label("Status: ")
        label.set_markup('<span size="larger">Status: </span>')
        self.notifBar.add(label)
        self.notif = Gtk.Label("Ready")
        self.notif.set_markup('<span foreground="blue" size="larger">Ready</span>')
        self.notifBar.add(self.notif)
        self.grid.attach_next_to(self.notifBar, self.bottBar, Gtk.PositionType.BOTTOM, 1, 3)
        
        settingsBtn = Gtk.Button('Settings')
        settingsBtn.connect("clicked", self.on_settings_clicked)
        settingsBtn.set_alignment(1,0)
        self.notifBar.pack_start(settingsBtn, False, False, 0)
        self.notifBar.set_child_packing(settingsBtn, False, True, 0, 1)
    
    def do_info_bar(self):
        self.infoBar = Gtk.Box(spacing=10)
        self.infoLabel = Gtk.Label("")
        self.infoBar.add(self.infoLabel)
        self.grid.attach_next_to(self.infoBar, self.topBar, Gtk.PositionType.BOTTOM, 1, 3)
    
    def set_info(self, msg):
    	self.infoLabel.set_markup('<span color="green">'+msg+'</span>')
       
    def on_settings_clicked(self,btn):
        SettingsWindow()
    
    def set_notif(self, msg):
    	self.notif.set_markup('<span size="larger">'+msg+'</span>')
    
    def do_top_bar(self):
    	self.topBar = Gtk.Box()
        logo = Gtk.Image()
        pb = Pixbuf.new_from_file('lucid.png')
        logo.set_from_pixbuf(pb)
        self.topBar.pack_start(logo, False, False, 0)
        
        label = Gtk.Label("Iterations:")
        self.topBar.add(label)
        adjustment = Gtk.Adjustment(7, 1, 37, 1, 10, 0)
        self.iterSpin = Gtk.SpinButton()
        self.iterSpin.set_adjustment(adjustment)
        self.iterSpin.set_value(7)
        self.iterSpin.set_numeric(1)
        self.topBar.pack_start(self.iterSpin, False, False, 0)
        
        label = Gtk.Label("Octaves:")
        self.topBar.add(label)
        adjustment = Gtk.Adjustment(3, 1, 23, 1, 0, 0)
        self.octaveSpin = Gtk.SpinButton()
        self.octaveSpin.set_adjustment(adjustment)
        self.octaveSpin.set_value(3)
        self.octaveSpin.set_numeric(1)
        self.topBar.pack_start(self.octaveSpin, False, False, 0)
        
        label = Gtk.Label("Scale:")
        self.topBar.add(label)
        adjustment = Gtk.Adjustment(1.4, 1.00, 1.90, 0.1, 0, 0)
        self.scaleSpin = Gtk.SpinButton()
        self.scaleSpin.configure(adjustment,0.01,2)
        self.scaleSpin.set_value(1.4)
        self.scaleSpin.set_numeric(1)
        self.topBar.pack_start(self.scaleSpin, False, False, 0)

        button2 = Gtk.Button("PHOTO")
        button2.connect("clicked", self.on_fselect_clicked)
        self.topBar.pack_start(button2, False, False, 0)
        
        self.button1 = Gtk.Button('DREAM')
        self.button1.connect("clicked", self.on_dream_clicked)
        self.topBar.pack_start(self.button1, False, False, 0)
        
        self.grid.attach(self.topBar,1,1,2,1)
    
    
    def do_bottom_bar(self):
    	self.bottBar = Gtk.Box()
    	self.grid.attach_next_to(self.bottBar, self.scrollWin, Gtk.PositionType.BOTTOM, 1, 3)
    	
    	label = Gtk.Label("Loops:")
        self.bottBar.add(label)
        adjustment = Gtk.Adjustment(1, 1, 10, 1, 0, 0)
        self.loopSpin = Gtk.SpinButton()
        self.loopSpin.set_adjustment(adjustment)
        self.loopSpin.set_value(1)
        self.loopSpin.set_numeric(1)
        self.bottBar.pack_start(self.loopSpin, False, False, 0)
    	
    	label = Gtk.Label("Auto Save:")
        self.bottBar.add(label)
        self.autoSaveBtn = Gtk.CheckButton()
        self.bottBar.pack_start(self.autoSaveBtn, False, False, 0)
        
        self.imageName = Gtk.Entry()
        self.imageName.set_text("myImageName")
        self.bottBar.pack_start(self.imageName, True, True, 0)
        
    	self.saveBtn = Gtk.Button("SAVE")
        self.saveBtn.connect("clicked", self.save_image)
        self.bottBar.pack_start(self.saveBtn, False, False, 0)
    
    def init_settings(self):
        with open('settings.json') as data_file:    
            self.settings = json.load(data_file)
    
    
    	
    def set_image(self, im):
        self.scrollWin = Gtk.ScrolledWindow()
        self.imContainer = Gtk.Layout()
        self.scrollWin.add(self.imContainer)
        self.scrollWin.set_size_request(800,500)
        self.scrollWin.set_policy(Gtk.PolicyType.ALWAYS, Gtk.PolicyType.AUTOMATIC)
        
        self.grid.attach_next_to(self.scrollWin, self.infoBar, Gtk.PositionType.BOTTOM, 1, 3)
        
    	self.imagef = im
    	self.im = Gtk.Image()
    	self.pb = Pixbuf.new_from_file(im)
        self.pb = self.check_im_size(self.pb)
    	self.im.set_from_pixbuf(self.pb)
        self.imContainer.add(self.im)
        self.imContainer.set_size(self.pb.get_width(),self.pb.get_height())
    
    def reset_image(self, im):
    	self.imagef = im
    	pb = Pixbuf.new_from_file(im)
        pb = self.check_im_size(pb)
        self.imContainer.set_size(pb.get_width(),pb.get_height())
    	self.im.set_from_pixbuf(pb)
        
    def save_image(self,a=0):
    	image = PIL.Image.open('temp.jpg')
    	fCount = len([name for name in os.listdir('outputImages') if os.path.isfile(os.path.join('outputImages', name))])
    	imName = self.imageName.get_text()+'_'+str(fCount)+'.jpg'
    	image.save('outputImages/'+imName, optimize=True)
    	self.set_notif('<span foreground="black" background="yellow">Current dream state saved to <span foreground="blue">'+imName+'</span></span>')
    
    def on_dream_clicked(self, button):
    	for i in xrange(int(self.loopSpin.get_value())):
    	    self.loop = i
            self.set_notif('<span foreground="white" background="red" weight="heavy">COMPUTER IS DREAMING. DO NOT DISTURB!...</span>')
            img = self.prepare_image()
            self.deepdream(self.net, img)

    
    def on_fselect_clicked(self, widget):
        dialog = Gtk.FileChooserDialog("Please choose a file", self,
            Gtk.FileChooserAction.OPEN,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_OPEN, Gtk.ResponseType.OK))

        self.add_filters(dialog)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
        
            pname = dialog.get_filename()
            self.reset_image(pname)
            fname = basename(pname)
            self.imageName.set_text(os.path.splitext(fname)[0])
        elif response == Gtk.ResponseType.CANCEL:
            print("Cancel clicked")

        dialog.destroy()

    def add_filters(self, dialog):
        filter_JPEG = Gtk.FileFilter()
        filter_JPEG.set_name("JPEG")
        filter_JPEG.add_mime_type("image/pjpeg")
        filter_JPEG.add_mime_type("image/jpeg")
        dialog.add_filter(filter_JPEG)

        filter_PNG = Gtk.FileFilter()
        filter_PNG.set_name("PNG")
        filter_PNG.add_mime_type("image/png")
        dialog.add_filter(filter_PNG)

        filter_GIF = Gtk.FileFilter()
        filter_GIF.set_name("GIF")
        filter_GIF.add_mime_type("image/gif")
        dialog.add_filter(filter_GIF)

        filter_any = Gtk.FileFilter()
        filter_any.set_name("All images")
        filter_any.add_mime_type("image/png")
        filter_any.add_mime_type("image/gif")
        filter_any.add_mime_type("image/pjpeg")
        filter_any.add_mime_type("image/jpeg")
        dialog.add_filter(filter_any)
        
    def prepare_image(self):
    	return np.float32(PIL.Image.open(self.imagef))
    	

win = DreamWindow()
win.connect("delete-event", Gtk.main_quit)
win.show_all()
Gtk.main()
