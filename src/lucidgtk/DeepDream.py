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
import numpy as np
import scipy.ndimage as nd
import caffe
from caffe.proto import caffe_pb2
from google.protobuf import text_format
import PIL.Image

def objective_L2(dst):
		dst.diff[:] = dst.data
		
class DeepDream():
	
	def initcaffe(self, win):
		
		self.win = win
		self.LucidImage = win.LucidImage
		
		net_fn   = str(win.settings.get_string('deploy-prototxt'))
		param_fn = str(win.settings.get_string('model-file'))
		
		model = caffe.io.caffe_pb2.NetParameter()
		try:
			text_format.Merge(open(net_fn).read(), model)
		except:
			print 'ERROR in caffe model config'
			return False
		model.force_backward = True
		tmprototxt = win.settings.get_string('proj-dir')+'/.tmp.prototxt'
		open(tmprototxt, 'w').write(str(model))
		
		try:
			self.net = caffe.Classifier(
					tmprototxt, 
					param_fn, 
					mean = np.float32([104.0, 116.0, 122.0]), 
					channel_swap = (2,1,0)
				)
			return True
		except:
			print 'ERROR in caffe model config'
			return False

	
	def make_step(self, net, step_size=1.5, jitter=32, clip=True, objective=objective_L2):
		
		end = self.win.get_selected_layer()

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

	def deepdream(self, net, base_img, clip=True, **step_params):
		
		win = self.win
		
		# prepare base images for all octaves
		octaves = [self.preprocess(net, base_img)]
		for i in xrange(win.octaveSpin.get_value_as_int()-1):
			octaves.append(nd.zoom(octaves[-1], (1, 1.0/win.scaleSpin.get_value(),1.0/win.scaleSpin.get_value()), order=1))
		
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
			for i in xrange(win.iterSpin.get_value_as_int()):
				self.make_step(net, clip=clip, **step_params)
				
				# visualization
				vis = self.deprocess(net, src.data[0])
				if not clip: # adjust image contrast if clipping is disabled
					vis = vis*(255.0/np.percentile(vis, 99.98))
				self.showarray(vis)
				if win.mode is 'image':
					win.set_info("Loop: "+str(win.loop+1)+" | Octave: "+str(octave+1)+" | Iter: "+str(i+1))
				elif win.mode is 'video':
					win.set_info("Frame: "+str(win.loop+1)+"/"+str(int(win.LucidVid.cap.get(7)))+" | Octave: "+str(octave+1)+" | Iter: "+str(i+1))
				while Gtk.events_pending():
					Gtk.main_iteration_do(True)
			detail = src.data[0]-octave_base
			
		return self.deprocess(net, src.data[0])
		
	def showarray(self, a, fmt='jpeg'):
		impath=self.LucidImage.tempImagePath
		a = np.uint8(np.clip(a, 0, 255))
		image = PIL.Image.fromarray(a)
		image.save(impath)
		self.LucidImage.display_image(impath)
	
	def prepare_image(self):
		return np.float32(PIL.Image.open(self.LucidImage.imagef))
		
	def get_layer_names(self):
		outp = []
		l = list(self.net._layer_names)
		blobs = list(self.net.blobs)
		layers = [val for val in l if val in blobs]
		
		# Remove googlenet layers that are causing core dumped crash
		bad_layers = ['pool5/7x7_s1','loss3/classifier','prob']
		
		for layer in layers:
			if layer not in bad_layers:
				outp.append(layer)
		return outp
	
	# a couple of utility functions for converting to and from Caffe's input image layout
	def preprocess(self, net, img):
		return np.float32(np.rollaxis(img, 2)[::-1]) - net.transformer.mean['data']
	def deprocess(self, net, img):
		return np.dstack((img + net.transformer.mean['data'])[::-1])
