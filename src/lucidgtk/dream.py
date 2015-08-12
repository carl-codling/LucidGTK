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

from lucidgtk.settingsWin import SettingsWindow
from lucidgtk.VideoWindow import VideoWindow

UI_INFO = """
<ui>
  <menubar name='MenuBar'>
      <menu action='EditMenu'>
        <menuitem action='ShowPrefs' />
      </menu>
      <menu action='HelpMenu'>
        <menuitem action='ShowHelp' />
        <menuitem action='ShowAbout' />
      </menu>
  </menubar>
</ui>
"""


def objective_L2(dst):
    dst.diff[:] = dst.data

class DreamWindow(Gtk.Window):

    def __init__(self, *args, **kwargs):
        for key in kwargs:
            setattr(self, key, kwargs[key])
        Gtk.Window.__init__(self, title=self.package+' | v'+self.version)
        self.set_icon_name('lucid-gtk')
        self.connect("delete-event", Gtk.main_quit)
        self.settings = Gio.Settings('org.rebelweb.dreamer')
        self.string = self.strings()
    
    def run(self):        

        self.set_border_width(10)
        self.grid = Gtk.Grid()
        self.add(self.grid)

        self.wakeup = False 
        self.fps = False # if not set then output videos default to settings obj. value

        if self.initcaffe() is False:
            self.do_config_error('Caffe could not start. Please review the model and deploy file settings')
            return

        if self.media_folders_set() is False:
            self.do_config_error('Please set the locations for deepdream images and videos to be stored')
            return
                   
        self.mode = 'image'

        self.do_menu_bar()

        self.do_top_bar()
        self.do_adjustments_bar()
        self.do_info_bar()
        self.tempImagePath = self.get_temp_im_path()
        self.set_image(self.tempImagePath)
        self.do_bottom_bar()
        self.do_notif_bar()

        self.show_all()
        self.wakeBtn.hide()
        
    def get_lucid_icon(self, size):
        icon_theme = Gtk.IconTheme.get_default()
        icon_info = icon_theme.lookup_icon("lucid-gtk", size, 0)
        return icon_info.get_filename()
    
    def get_resource_path(self,rel_path):
        dir_of_py_file = os.path.dirname(__file__)
        rel_path_to_resource = os.path.join(dir_of_py_file, rel_path)
        abs_path_to_resource = os.path.abspath(rel_path_to_resource)
        return abs_path_to_resource
        
    def do_menu_bar(self):
		action_group = Gtk.ActionGroup("my_actions")
		self.add_main_menu_actions(action_group)
		uimanager = self.create_ui_manager()
		uimanager.insert_action_group(action_group)
		menubar = uimanager.get_widget("/MenuBar")
		self.grid.add(menubar)
    
    def create_ui_manager(self):
        uimanager = Gtk.UIManager()

        uimanager.add_ui_from_string(UI_INFO)

        accelgroup = uimanager.get_accel_group()
        self.add_accel_group(accelgroup)
        return uimanager
            
    def add_main_menu_actions(self, action_group):
		
		action_edit = Gtk.Action("EditMenu", "Edit", None, None)
		action_group.add_action(action_edit)

		action_prefs = Gtk.Action("ShowPrefs", "Preferences", None, None)
		action_group.add_action(action_prefs)
		action_prefs.connect("activate", self.on_settings_clicked)

		action_helpmenu = Gtk.Action("HelpMenu", "Help", None, None)
		action_group.add_action(action_helpmenu)

		action_about = Gtk.Action("ShowHelp", "Help", None, None)
		action_group.add_action(action_about)
		action_about.connect("activate", self.on_help_clicked)
		
		action_about = Gtk.Action("ShowAbout", "About", None, None)
		action_group.add_action(action_about)
		action_about.connect("activate", self.on_about_clicked)
		

    def on_about_clicked(self, item):
        dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.INFO, Gtk.ButtonsType.OK, "About Lucid-GTK")
        box = dialog.get_content_area()
        label = Gtk.Label()
        label.set_markup('<span weight="heavy">'+self.package+'</span>')
        box.add(label)
        label = Gtk.Label()
        label.set_markup('<span weight="light">'+self.version+'</span>')
        box.add(label)
        im = Gtk.Image()
        pb = Pixbuf.new_from_file(self.get_lucid_icon(256))
        im.set_from_pixbuf(pb)
        box.add(im)
        label = Gtk.Label('Author: Carl Codling | lucid@rebelweb.co.uk')
        box.add(label)
        
        dialog.show_all()
        dialog.run()
        dialog.destroy()
        
    def on_help_clicked(self, item):
		dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.INFO, Gtk.ButtonsType.OK, "Lucid-GTK Help")
		dialog.format_secondary_text("Lucid-GTK is currently in Beta and documentation is lacking, a usage screencast can be found at http://rebelweb.co.uk/lucid-gtk or for bug reporting you can create an 'issue' at https://github.com/carl-codling/LucidGTK/issues")
		dialog.run()
		dialog.destroy()
	
    def get_temp_im_path(self):
        imdir = self.settings.get_string('im-dir')+'/.temp'
        impath = imdir+'/lucidgtk-temp.jpeg'
        if os.path.isdir(imdir) == False:
            os.makedirs(imdir)
        if os.path.isfile(impath) == False:
            im = PIL.Image.open(self.get_lucid_icon(256))
            base_im = PIL.Image.new('RGB', (400,400), "white")
            base_im.paste(im, (72, 72), im)
            base_im.save(impath, 'jpeg')
        return impath
    
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
    
    def do_config_error(self, msg):
        label = Gtk.Label("")
        label.set_markup('<span foreground="white" background="red" weight="heavy">CONFIGURATION ERROR: '+msg+'</span>')
        self.grid.add(label)
        SettingsWindow(self)
       
    def initcaffe(self):
        net_fn   = str(self.settings.get_string('deploy-prototxt'))
        param_fn = str(self.settings.get_string('model-file'))
        
        model = caffe.io.caffe_pb2.NetParameter()
        try:
            text_format.Merge(open(net_fn).read(), model)
        except:
            print 'ERROR in caffe model config'
            return False
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
        
        # Remove googlenet layers that are causing core dumped crash
        bad_layers = ['pool5/7x7_s1','loss3/classifier','prob']
        
        for layer in layers:
            if layer not in bad_layers:
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
	        pbnew.savev(self.tempImagePath,"jpeg", ["quality"], ["80"])
	        self.imagef = self.tempImagePath
	        return pbnew
	    return pb
    
    def showarray(self, a, fmt='jpeg'):
		impath=self.tempImagePath
		a = np.uint8(np.clip(a, 0, 255))
		image = PIL.Image.fromarray(a)
		image.save(impath)
		self.display_image(impath)
    
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
            detail = src.data[0]-octave_base
            
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
        self.notif.set_markup('<span foreground="blue" size="larger">%s</span>'%self.string['ready'])
        self.notifBar.add(self.notif)
        self.grid.attach_next_to(self.notifBar, self.bottBar, Gtk.PositionType.BOTTOM, 1, 3)
        
    
    def do_info_bar(self):
        self.infoBar = Gtk.Box(spacing=10)
        self.infoLabel = Gtk.Label("")
        self.infoBar.add(self.infoLabel)
        self.grid.attach_next_to(self.infoBar, self.adjBar, Gtk.PositionType.BOTTOM, 1, 3)
    
    def set_info(self, msg):
    	self.infoLabel.set_markup('<span color="green">'+msg+'</span>')
       
    def on_settings_clicked(self,btn):
        SettingsWindow(self)
    
    
    def on_vidbtn_clicked(self):
        self.vidWin = VideoWindow(self)
    
    def set_notif(self, msg):
    	self.notif.set_markup('<span size="larger">'+msg+'</span>')
    
    def do_adjustments_bar(self):
        self.adjBar = Gtk.Box()
        
        nloops = self.settings.get_int('n-loops')
    	self.loopLabel = Gtk.Label("Loops:")
        self.adjBar.add(self.loopLabel)
        adjustment = Gtk.Adjustment(nloops, 1, 99999, 1, 0, 0)
        self.loopSpin = Gtk.SpinButton()
        self.loopSpin.set_adjustment(adjustment)
        self.loopSpin.set_value(nloops)
        self.loopSpin.set_numeric(1)
        self.loopSpin.connect("value-changed", self.set_loops_val)
        self.adjBar.pack_start(self.loopSpin, False, False, 0)
    	
        iter_val = self.settings.get_int('n-iterations')
        label = Gtk.Label("Iterations:")
        self.adjBar.add(label)
        adjustment = Gtk.Adjustment(iter_val, 1, 37, 1, 10, 0)
        self.iterSpin = Gtk.SpinButton()
        self.iterSpin.set_adjustment(adjustment)
        self.iterSpin.set_value(iter_val)
        self.iterSpin.set_numeric(1)
        self.iterSpin.connect("value-changed", self.set_iter_val)
        self.adjBar.pack_start(self.iterSpin, False, False, 0)
        
        octv_val = self.settings.get_int('n-octaves')
        label = Gtk.Label("Octaves:")
        self.adjBar.add(label)
        adjustment = Gtk.Adjustment(octv_val, 1, 23, 1, 0, 0)
        self.octaveSpin = Gtk.SpinButton()
        self.octaveSpin.set_adjustment(adjustment)
        self.octaveSpin.set_value(octv_val)
        self.octaveSpin.set_numeric(1)
        self.octaveSpin.connect("value-changed", self.set_octv_val)
        self.adjBar.pack_start(self.octaveSpin, False, False, 0)
        
        octv_scale = self.settings.get_double('octave-scale')
        label = Gtk.Label("Scale:")
        self.adjBar.add(label)
        adjustment = Gtk.Adjustment(octv_scale, 1.00, 1.90, 0.1, 0, 0)
        self.scaleSpin = Gtk.SpinButton()
        self.scaleSpin.configure(adjustment,0.01,2)
        self.scaleSpin.set_value(octv_scale)
        self.scaleSpin.set_numeric(1)
        self.scaleSpin.connect("value-changed", self.set_scale_val)
        self.adjBar.pack_start(self.scaleSpin, False, False, 0)
        
        zoom_scale = self.settings.get_double('zoom-scale')
        self.zoomLabel = Gtk.Label("Zoom:")
        self.adjBar.add(self.zoomLabel)
        adjustment = Gtk.Adjustment(zoom_scale, 0.00, 0.10, 0.01, 0, 0)
        self.zoomSpin = Gtk.SpinButton()
        self.zoomSpin.configure(adjustment,0.01,2)
        self.zoomSpin.set_value(zoom_scale)
        self.zoomSpin.set_numeric(1)
        self.zoomSpin.connect("value-changed", self.set_zoom_val)
        self.adjBar.pack_start(self.zoomSpin, False, False, 0)
        
        deg_val = self.settings.get_double('rot-deg')
        self.degLabel = Gtk.Label("Rotation:")
        self.adjBar.add(self.degLabel)
        adjustment = Gtk.Adjustment(deg_val, -10.00, 10.00, 0.10, 0, 0)
        self.degSpin = Gtk.SpinButton()
        self.degSpin.configure(adjustment,0.10,2)
        self.degSpin.set_value(deg_val)
        self.degSpin.set_numeric(1)
        self.degSpin.connect("value-changed", self.set_deg_val)
        self.adjBar.pack_start(self.degSpin, False, False, 0)
        
        self.grid.attach_next_to(self.adjBar, self.topBar, Gtk.PositionType.BOTTOM, 1, 3)
    
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
            elif v==2:
                self.dreamBtn.hide()
                self.loopSpin.hide()
                self.zoomSpin.hide()
                self.degSpin.hide()
                self.zoomLabel.hide()
                self.degLabel.hide()
                self.loopLabel.hide()
                
    
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
        
        self.dreamBtn = Gtk.Button('START DREAMING')
        self.dreamBtn.connect("clicked", self.on_dream_clicked)
        self.topBar.pack_start(self.dreamBtn, False, False, 0)
        self.topBar.set_child_packing(self.dreamBtn, False, True, 0, 1)
        
        self.inpCombo.connect("changed", self.on_inp_combo_changed)
        
        self.grid.attach(self.topBar,1,1,2,1)
        
    def on_wake_clicked(self, btn):
		self.set_notif('<span foreground="black" background="orange" weight="heavy">%s</span>'%self.string['waking'])
		while Gtk.events_pending():
			Gtk.main_iteration_do(True)
		self.wakeup = True
    
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
        
    	self.imagef = im
    	self.im = Gtk.Image()
    	self.pb = Pixbuf.new_from_file(im)
        self.pb = self.check_im_size(self.pb)
    	self.im.set_from_pixbuf(self.pb)
        self.imContainer.add(self.im)
        self.imContainer.set_size(self.pb.get_width(),self.pb.get_height())
    
    def display_image(self, im):
    	self.imagef = im
    	pb = Pixbuf.new_from_file(im)
        pb = self.check_im_size(pb)
        self.imContainer.set_size(pb.get_width(),pb.get_height())
    	self.im.set_from_pixbuf(pb)
        
    def save_image(self,a=0):
    	image = PIL.Image.open(self.tempImagePath)
    	fp = self.make_new_fname()
    	image.save(fp, optimize=True)
    	
    def make_new_fname(self, dirSetting='im-dir', extension='.jpg'):
        fp = self.settings.get_string(dirSetting)+'/'+self.imageName.get_text()+extension
        if os.path.isfile(fp):
            i = 0
            while True:
                fp = self.settings.get_string(dirSetting)+'/'+self.imageName.get_text()+'_'+str(i)+extension
                if os.path.isfile(fp)==False:
                    break
                i += 1
        return fp
    
    def init_outp_video(self):
        fourcc = cv2.cv.CV_FOURCC(*'XVID')
        if self.fps == False:
            fps = self.settings.get_int('fps')
        else:
            fps = self.fps
        img = self.prepare_image()
        h,w = img.shape[:2]    
        return cv2.VideoWriter(self.make_new_fname(dirSetting='vid-dir', extension='.avi'),fourcc, fps, (w,h))
    
    def on_dream_clicked(self, button):
        self.mode = 'image'
        self.enable_buttons(False)
        self.set_notif('<span foreground="white" background="blue" weight="heavy">%s</span>'%self.string['dreaming'])
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
            imgout = self.prepare_image()
            imgout = np.uint8(np.clip(imgout, 0, 255))
            imgout = cv2.cvtColor(imgout, cv2.COLOR_BGR2RGB)
            vidOut.write(imgout)
        
    	for i in xrange(int(self.loopSpin.get_value())):
    	    if self.wakeup:
    	        break
    	    
    	    self.loop = i
            
            img = self.prepare_image()
            
            r = self.settings.get_double('rot-deg')
            if r>0 or r<0:
                img = nd.interpolation.rotate(img, r, reshape=False)
            
            z = self.settings.get_double('zoom-scale')
            if z>0:
                h,w = img.shape[:2]
                img = nd.affine_transform(img, [1-z,1-z,1], [h*z/2,w*z/2,0], order=1)
            
            outp = self.deepdream(self.net, img)
            
            if outpType > 1:
                imgout = self.prepare_image()
                imgout = np.uint8(np.clip(imgout, 0, 255))
                imgout = cv2.cvtColor(imgout, cv2.COLOR_BGR2RGB)
                vidOut.write(imgout)
                
            if outpType == 1 or outpType == 3:
        	    self.save_image()

        self.set_info("")
        self.set_notif('<span foreground="blue">%s</span>'%self.string['ready']) 
        
        if outpType > 1:
            vidOut.release()
            cv2.destroyAllWindows()   
        self.wakeup = False        
        self.wakeBtn.hide()
        self.enable_buttons()

    def on_fBtn_clicked(self, combo):
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
    
    
    def on_fselect_clicked(self):
        dialog = Gtk.FileChooserDialog("Please choose a file", self,
            Gtk.FileChooserAction.OPEN,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_OPEN, Gtk.ResponseType.OK))

        self.add_filters(dialog)
        
        md = self.settings.get_string('im-search-dir')
        
        if len(md) > 0 and os.path.isdir(md):
            dialog.set_current_folder(md) 
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
        
            pname = dialog.get_filename()
            self.display_image(pname)
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
    	


