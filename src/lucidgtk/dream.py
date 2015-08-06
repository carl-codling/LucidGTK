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

from lucidgtk.settingsWin import SettingsWindow
from lucidgtk.VideoWindow import VideoWindow

def objective_L2(dst):
    dst.diff[:] = dst.data

class DreamWindow(Gtk.Window):

    def __init__(self, *args, **kwargs):
        for key in kwargs:
            setattr(self, key, kwargs[key])
            
        self.settings = Gio.Settings('org.rebelweb.dreamer')
        Gtk.Window.__init__(self, title='Lucid-GTK')
        self.set_icon_name('lucid-gtk')
        self.iconify()
        
        #self.set_title("%s v%s" % (self.package, self.version))
        self.set_border_width(10)
        self.grid = Gtk.Grid()
        self.add(self.grid)
        
        
        if self.initcaffe() is False:
            self.do_config_error('Caffe could not start. Please review the model and deploy file settings')
            return
        
        if self.media_folders_set() is False:
            self.do_config_error('Please set the locations for deepdream images and videos to be stored')
            return
                   
        self.mode = 'image'
        
        
        self.do_top_bar()
        self.do_info_bar()
        self.set_image('.temp/temp.jpg')
        self.do_bottom_bar()
        self.do_notif_bar()
    
    def media_folders_set(self):
        if os.path.isdir(self.settings.get_string('im-dir')) and os.path.isdir(self.settings.get_string('vid-dir')):
            return True
        return False
    
    def do_config_error(self, msg):
        label = Gtk.Label("")
        label.set_markup('<span foreground="white" background="red" weight="heavy">CONFIGURATION ERROR: '+msg+'</span>')
        self.grid.add(label)
        SettingsWindow(self)
       
    def initcaffe(self):
        net_fn   = str(self.settings.get_string('deploy-prototxt'))
        param_fn = str(self.settings.get_string('model-file'))
        
        # Patching model to be able to compute gradients.
        # Note that you can also manually add "force_backward: true" line to "deploy.prototxt".
        model = caffe.io.caffe_pb2.NetParameter()
        text_format.Merge(open(net_fn).read(), model)
        model.force_backward = True
        open('tmp.prototxt', 'w').write(str(model))
        
        try:
            self.net = caffe.Classifier('tmp.prototxt', param_fn, mean = np.float32([104.0, 116.0, 122.0]), channel_swap = (2,1,0))
            return True
        except:
            print 'ERROR in caffe model config'
            return False
    
    def make_layer_select(self):
        layer_store = Gtk.ListStore(str)
        l = list(self.net._layer_names)
        blobs = list(self.net.blobs)
        layers = [val for val in l if val in blobs]
        #layers = list(set(l).intersection(blobs))
        
        for layer in layers:
            layer_store.append([layer])

        self.layer_combo = Gtk.ComboBox.new_with_model(layer_store)
        #layer_combo.connect("changed", self.on_country_combo_changed)
        renderer_text = Gtk.CellRendererText()
        self.layer_combo.pack_start(renderer_text, True)
        self.layer_combo.add_attribute(renderer_text, "text", 0)
        self.layer_combo.set_active(0)
        return self.layer_combo
    
    
    def enable_buttons(self, v=True):
        self.settingsBtn.set_sensitive(v)
        self.fileBtn.set_sensitive(v)
        self.vidBtn.set_sensitive(v)
        self.dreamBtn.set_sensitive(v)
        self.saveBtn.set_sensitive(v)
        self.iterSpin.set_sensitive(v)
        self.octaveSpin.set_sensitive(v)
        self.scaleSpin.set_sensitive(v)
        self.loopSpin.set_sensitive(v)
        self.layer_combo.set_sensitive(v)
    
    def get_shrink_dimensions(self, w, h, bytesize, limit, ch=3):
        while bytesize > limit:
            w = (float(w)*0.99)
            h = (float(h)*0.99)
            bytesize = float(ch) * w * h
        return int(w), int(h)
    
    
    def check_im_size(self, pb):
	    ch = pb.get_n_channels()
	    w = pb.get_width()
	    h = pb.get_height()
	    bytesize = pb.get_byte_length()
	    limit = int(self.settings.get_int('max-bytes'))
	    
	    if bytesize > limit:
	        w, h = self.get_shrink_dimensions(w, h, bytesize, limit, ch=ch)
	        pbnew = pb.scale_simple(w, h, 3)
	        pbnew.savev(".temp/temp.jpg","jpeg", ["quality"], ["80"])
	        self.imagef = ".temp/temp.jpg"
	        return pbnew
	    return pb
    
    def showarray(self, a, fmt='jpeg', impath='.temp/temp.jpg'):
        a = np.uint8(np.clip(a, 0, 255))
        image = PIL.Image.fromarray(a)
        image.save(impath)
        self.reset_image(impath)
    
    def make_step(self, net, step_size=1.5, jitter=32, clip=True, objective=objective_L2):
       
        tree_iter = self.layer_combo.get_active_iter()
        if tree_iter != None:
            model = self.layer_combo.get_model()
            end = model[tree_iter][0]
        else:
            raise Exception("No output layer is set!")
            return
        
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
                if self.mode is 'image':
                    self.set_info("Loop: "+str(self.loop+1)+" | Octave: "+str(octave+1)+" | Iter: "+str(i+1))
                elif self.mode is 'video':
                    self.set_info("Frame: "+str(self.loop+1)+"/"+str(int(self.vidWin.cap.get(7)))+" | Octave: "+str(octave+1)+" | Iter: "+str(i+1))
                while Gtk.events_pending():
                	Gtk.main_iteration_do(True)
            # extract details produced on the current octave
            detail = src.data[0]-octave_base
            
        # returning the resulting image
        if self.autoSaveBtn.get_active():
        	self.save_image()
        self.set_info("")
        self.set_notif('<span foreground="blue">Ready to dream. Counting electric sheep</span>')
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
        self.notif.set_markup('<span foreground="blue" size="larger">Ready to dream. Counting electric sheep</span>')
        self.notifBar.add(self.notif)
        self.grid.attach_next_to(self.notifBar, self.bottBar, Gtk.PositionType.BOTTOM, 1, 3)
        
        self.settingsBtn = Gtk.Button('Settings')
        self.settingsBtn.connect("clicked", self.on_settings_clicked)
        self.settingsBtn.set_alignment(1,0)
        self.notifBar.pack_start(self.settingsBtn, False, False, 0)
        self.notifBar.set_child_packing(self.settingsBtn, False, True, 0, 1)
    
    def do_info_bar(self):
        self.infoBar = Gtk.Box(spacing=10)
        self.infoLabel = Gtk.Label("")
        self.infoBar.add(self.infoLabel)
        self.grid.attach_next_to(self.infoBar, self.topBar, Gtk.PositionType.BOTTOM, 1, 3)
    
    def set_info(self, msg):
    	self.infoLabel.set_markup('<span color="green">'+msg+'</span>')
       
    def on_settings_clicked(self,btn):
        SettingsWindow(self)
    
    
    def on_vidbtn_clicked(self,btn):
        self.vidWin = VideoWindow(self)
    
    def set_notif(self, msg):
    	self.notif.set_markup('<span size="larger">'+msg+'</span>')
    
    def do_top_bar(self):
    	self.topBar = Gtk.Box()
        #logo = Gtk.Image()
        #pb = Pixbuf.new_from_file('src/lucidgtk/lucid-logo.png')
        #logo.set_from_pixbuf(pb)
        #self.topBar.pack_start(logo, False, False, 0)
        
        iter_val = self.settings.get_int('n-iterations')
        label = Gtk.Label("Iterations:")
        self.topBar.add(label)
        adjustment = Gtk.Adjustment(iter_val, 1, 37, 1, 10, 0)
        self.iterSpin = Gtk.SpinButton()
        self.iterSpin.set_adjustment(adjustment)
        self.iterSpin.set_value(iter_val)
        self.iterSpin.set_numeric(1)
        self.iterSpin.connect("value-changed", self.set_iter_val)
        self.topBar.pack_start(self.iterSpin, False, False, 0)
        
        octv_val = self.settings.get_int('n-octaves')
        label = Gtk.Label("Octaves:")
        self.topBar.add(label)
        adjustment = Gtk.Adjustment(octv_val, 1, 23, 1, 0, 0)
        self.octaveSpin = Gtk.SpinButton()
        self.octaveSpin.set_adjustment(adjustment)
        self.octaveSpin.set_value(octv_val)
        self.octaveSpin.set_numeric(1)
        self.octaveSpin.connect("value-changed", self.set_octv_val)
        self.topBar.pack_start(self.octaveSpin, False, False, 0)
        
        octv_scale = self.settings.get_double('octave-scale')
        label = Gtk.Label("Scale:")
        self.topBar.add(label)
        adjustment = Gtk.Adjustment(octv_scale, 1.00, 1.90, 0.1, 0, 0)
        self.scaleSpin = Gtk.SpinButton()
        self.scaleSpin.configure(adjustment,0.01,2)
        self.scaleSpin.set_value(octv_scale)
        self.scaleSpin.set_numeric(1)
        self.scaleSpin.connect("value-changed", self.set_scale_val)
        self.topBar.pack_start(self.scaleSpin, False, False, 0)
        
        zoom_scale = self.settings.get_double('zoom-scale')
        label = Gtk.Label("Zoom:")
        self.topBar.add(label)
        adjustment = Gtk.Adjustment(zoom_scale, 0.00, 0.10, 0.01, 0, 0)
        self.zoomSpin = Gtk.SpinButton()
        self.zoomSpin.configure(adjustment,0.01,2)
        self.zoomSpin.set_value(zoom_scale)
        self.zoomSpin.set_numeric(1)
        self.zoomSpin.connect("value-changed", self.set_zoom_val)
        self.topBar.pack_start(self.zoomSpin, False, False, 0)
        
        deg_val = self.settings.get_double('rot-deg')
        label = Gtk.Label("Rotation:")
        self.topBar.add(label)
        adjustment = Gtk.Adjustment(deg_val, 0.0, 10.0, 0.1, 0, 0)
        self.degSpin = Gtk.SpinButton()
        self.degSpin.configure(adjustment,0.1,1)
        self.degSpin.set_value(deg_val)
        self.degSpin.set_numeric(1)
        self.degSpin.connect("value-changed", self.set_deg_val)
        self.topBar.pack_start(self.degSpin, False, False, 0)
        
        label = Gtk.Label("Layer:")
        self.topBar.add(label)
        self.topBar.pack_start(self.make_layer_select(), False, False, True)

        self.fileBtn = Gtk.Button("PHOTO")
        self.fileBtn.connect("clicked", self.on_fselect_clicked)
        self.topBar.pack_start(self.fileBtn, False, False, 0)
        
        self.vidBtn = Gtk.Button("VIDEO")
        self.vidBtn.connect("clicked", self.on_vidbtn_clicked)
        self.topBar.pack_start(self.vidBtn, False, False, 0)
        
        self.dreamBtn = Gtk.Button('DREAM')
        self.dreamBtn.connect("clicked", self.on_dream_clicked)
        self.topBar.pack_start(self.dreamBtn, False, False, 0)
        
        self.grid.attach(self.topBar,1,1,2,1)
        
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
    	
    	nloops = self.settings.get_int('n-loops')
    	label = Gtk.Label("Loops:")
        self.bottBar.add(label)
        adjustment = Gtk.Adjustment(nloops, 1, 50, 1, 0, 0)
        self.loopSpin = Gtk.SpinButton()
        self.loopSpin.set_adjustment(adjustment)
        self.loopSpin.set_value(nloops)
        self.loopSpin.set_numeric(1)
        self.loopSpin.connect("value-changed", self.set_loops_val)
        self.bottBar.pack_start(self.loopSpin, False, False, 0)
    	
    	label = Gtk.Label("Auto Save:")
        self.bottBar.add(label)
        self.autoSaveBtn = Gtk.CheckButton()
        self.autoSaveBtn.set_active(self.settings.get_boolean('auto-save'))
        self.autoSaveBtn.connect("toggled", self.set_autosave)
        self.bottBar.pack_start(self.autoSaveBtn, False, False, 0)
        
        self.imageName = Gtk.Entry()
        self.imageName.set_text("myImageName")
        self.bottBar.pack_start(self.imageName, True, True, 0)
        
    	self.saveBtn = Gtk.Button("SAVE")
        self.saveBtn.connect("clicked", self.save_image)
        self.bottBar.pack_start(self.saveBtn, False, False, 0)
    
    	
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
    	image = PIL.Image.open('.temp/temp.jpg')
    	fp = self.make_new_fname()
    	image.save(fp, optimize=True)
    	self.set_notif('<span foreground="black" background="yellow">Current dream state saved to <span foreground="blue">'+fp+'</span></span>')
    
    def make_new_fname(self):
        fp = self.settings.get_string('im-dir')+'/'+self.imageName.get_text()+'.jpg'
        if os.path.isfile(fp):
            i = 0
            while True:
                fp = self.settings.get_string('im-dir')+'/'+self.imageName.get_text()+'_'+str(i)+'.jpg'
                if os.path.isfile(fp)==False:
                    break
                i += 1
        return fp
    
    def on_dream_clicked(self, button):
        self.mode = 'image'
        self.enable_buttons(False)
    	for i in xrange(int(self.loopSpin.get_value())):
    	    self.loop = i
            self.set_notif('<span foreground="white" background="red" weight="heavy">COMPUTER IS DREAMING. DO NOT DISTURB!...</span>')
            img = self.prepare_image()
            
            r = self.settings.get_double('rot-deg')
            if r>0:
                img = nd.interpolation.rotate(img, r, reshape=False)
            
            z = self.settings.get_double('zoom-scale')
            if z>0:
                h,w = img.shape[:2]
                img = nd.affine_transform(img, [1-z,1-z,1], [h*z/2,w*z/2,0], order=1)
            
            outp = self.deepdream(self.net, img)
        self.enable_buttons()

    
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
            nm = os.path.splitext(fname)[0]
            self.imageName.set_text(nm)
            self.settings.set_string('im-name', nm)
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
