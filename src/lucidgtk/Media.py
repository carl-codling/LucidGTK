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

from gi.repository import Gtk
import os
from os.path import basename
import PIL.Image
import scipy.ndimage as nd
from gi.repository.GdkPixbuf import Pixbuf


import cv2
import numpy as np
import json
import time

class LucidImage():
	
	def __init__(self, mainWin):
		self.mainWin = mainWin
		self.settings = mainWin.settings
		self.tempImagePath = self.get_temp_im_path()
		projdir = self.settings.get_string('proj-dir')
		self.recentJSON = projdir+'/.lucidgtk.recent.images.json'
		self.recent = self.load_recent()
	
	def zoom_and_rotate(self, img):
		r = self.settings.get_double('rot-deg')
		if r>0 or r<0:
			img = nd.interpolation.rotate(img, r, reshape=False)
		
		z = self.settings.get_double('zoom-scale')
		if z>0:
			h,w = img.shape[:2]
			img = nd.affine_transform(img, [1-z,1-z,1], [h*z/2,w*z/2,0], order=1)
		return img
	
	def load_recent(self):
		if os.path.isfile(self.recentJSON) == False:
			return []
		d = open(self.recentJSON,'r').read()
		return json.loads(d)
		
	def add_recent(self, path):
		if path in self.recent:
			self.recent.remove(path)
		self.recent.insert(0, path)
		if len(self.recent) > 10:
			del self.recent[-1]
		self.save_recent()
		self.load_recent()
		
	def save_recent(self):
		target = open(self.recentJSON, 'w')
		target.truncate()
		target.write(json.dumps(self.recent))
		target.close()
	
	def get_lucid_icon(self, size):
		icon_theme = Gtk.IconTheme.get_default()
		icon_info = icon_theme.lookup_icon("lucid-gtk", size, 0)
		return icon_info.get_filename()

	def get_temp_im_path(self):
		imdir = self.settings.get_string('proj-dir')
		impath = imdir+'/.lucidgtk-temp.jpeg'
		if os.path.isdir(imdir) == False:
			os.makedirs(imdir)
		if os.path.isfile(impath) == False:
			im = PIL.Image.open(self.get_lucid_icon(256))
			base_im = PIL.Image.new('RGB', (400,400), "white")
			base_im.paste(im, (72, 72), im)
			base_im.save(impath, 'jpeg')
		return impath

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

	def display_image(self, im):
		self.imagef = im
		pb = Pixbuf.new_from_file(im)
		if pb.get_n_channels()>3:
			self.mainWin.notify('Sorry, Lucid-GTK doesn\'t currently support images with an alpha channel (such as PNG with transparency).\nIn order to use this image you need to flatten it to RGB in an image editor', color='red')
			return
		pb = self.check_im_size(pb)
		self.mainWin.imContainer.set_size(pb.get_width(),pb.get_height())
		self.mainWin.im.set_from_pixbuf(pb)
		
	def save_image(self,a=0):
		image = PIL.Image.open(self.tempImagePath)
		fp = self.make_new_fname()
		image.save(fp)

	def make_new_fname(self, dirSetting='im-dir', extension='.jpg'):
		win = self.mainWin
		d = self.settings.get_string(dirSetting)+'/'+win.imageName.get_text()
		
		if os.path.isdir(d) == False:
			os.makedirs(d)
		fp = d+'/'+win.imageName.get_text()+extension
		if os.path.isfile(fp):
			i = 0
			while True:
				fp = d+'/'+win.imageName.get_text()+'_'+str(i)+extension
				if os.path.isfile(fp)==False:
					break
				i += 1
		return fp


class LucidVid():

	def __init__(self, mainWin):
		self.mainWin = mainWin
		self.settings = mainWin.settings
		self.DD = mainWin.DD
		self.LucidImage = mainWin.LucidImage
		self.set_defaults()
		projdir = self.settings.get_string('proj-dir')
		self.recentJSON = projdir+'/.lucidgtk.recent.vids.json'
		self.recent = self.load_recent()
	
	def load_recent(self):
		if os.path.isfile(self.recentJSON) == False:
			return []
		d = open(self.recentJSON,'r').read()
		return json.loads(d)
		
	def add_recent(self, path):
		if path in self.recent:
			self.recent.remove(path)
		self.recent.insert(0, path)
		if len(self.recent) > 10:
			del self.recent[-1]
		self.save_recent()
		self.load_recent()
		
	def save_recent(self):
		target = open(self.recentJSON, 'w')
		target.truncate()
		target.write(json.dumps(self.recent))
		target.close()
	
	def set_defaults(self):
		self.cap = None
		self.outvid = None
		self.w = None
		self.h = None
		self.fps = None
		self.nframes = None
		self.first_frame = None
		self.vid_loaded = False
		
	def get_frame_by_index(self, i):
		self.cap.set(1,i)
		ret, frame = self.cap.read()
		return self.BGR2RGB(frame)
		
	def write_frame(self, colorSwitch='BGR2RGB'):
		imgout = self.DD.prepare_image()
		imgout = np.uint8(np.clip(imgout, 0, 255))
		if colorSwitch == 'BGR2RGB':
			imgout = cv2.cvtColor(imgout, cv2.COLOR_BGR2RGB)
		if colorSwitch == 'RGB2BGR':
			imgout = cv2.cvtColor(imgout, cv2.COLOR_RGB2BGR)
		self.outvid.write(imgout)

	def init_input_vid(self, path):
		self.cap = cv2.VideoCapture(path)
		cap = self.cap
		w = int(cap.get(3))
		h = int(cap.get(4))
		bytesize = int(cap.get(3)) * int(cap.get(4)) * 3
		limit = int(self.settings.get_int('max-bytes'))
		(w, h) = self.LucidImage.get_shrink_dimensions(w, h, bytesize, limit)
		cap.set(3, w)
		cap.set(4, h)
		self.w = w
		self.h = h
		self.nframes = cap.get(7)
		self.fps = cap.get(5)
		frame = self.get_next_frame()
		self.first_frame = frame
		frame = self.resize_frame(frame)
		imname = self.LucidImage.tempImagePath
		frame.save(imname)
		self.LucidImage.display_image(imname)
		self.vid_loaded = True
		return cap

	def init_outp_vid(self):
		if self.fps == None:
			self.fps = self.settings.get_int('fps')
		fourcc = cv2.cv.CV_FOURCC(*'XVID')
		fname = self.LucidImage.make_new_fname(dirSetting='vid-dir', extension='.avi')
		self.outvid = cv2.VideoWriter(fname,fourcc, self.fps, (self.w,self.h))
		return self.outvid

	def resize_frame(self, frame):
		src = PIL.Image.fromarray(frame)
		return src.resize((self.w, self.h), PIL.Image.ANTIALIAS)
	
	def close_session(self):
		if self.cap != None:
			self.cap.release()
		if self.outvid != None:
			self.outvid.release()
		cv2.destroyAllWindows()
		self.set_defaults()
		
	def BGR2RGB(self, img):
		return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
		
	def get_next_frame(self):
		ret, frame = self.cap.read()
		if frame is None:
			return None
		return self.BGR2RGB(frame)
		
