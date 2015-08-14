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

class SequencerWindow(Gtk.Window):

	def __init__(self, mainWin):
		self.mainWin = mainWin
		self.settings = Gio.Settings('org.rebelweb.dreamer')
		Gtk.Window.__init__(self, title="Lucid-GTK Sequencer")
		self.set_border_width(10)
		self.vbox = Gtk.VBox()
		self.box = Gtk.Box()
		self.vbox.add(self.box)
		
		self.fJson = self.settings.get_string('proj-dir')+'/.lucid.seq.json'
		self.sequences = self.get_sequences()
		self.unsaved = {}

		self.do_save_bar()
		self.do_adjustments_bar()
		self.do_viewscreen()
		self.display_adjustments()
		
		self.add(self.vbox)
		self.show_all()

	def get_sequences(self):
		if os.path.isfile(self.fJson):
			d = open(self.fJson,'r').read()
			j = json.loads(d)
			return j
		else:
			return {}
	
	def do_viewscreen(self):
		self.vs = Gtk.VBox()
		label = Gtk.Label("ORDER:")
		self.vs.add(label)
		self.box.add(self.vs)
		
	def do_adjustments_bar(self):
		self.adjBar = Gtk.VBox()

		ADJ = self.mainWin.adjustments
		S = self.settings
		self.unsaved[1] = {}
		self.loopLabel = Gtk.Label("Adjust @ loop:")
		self.adjBar.add(self.loopLabel)
		adjustment = Gtk.Adjustment(1, ADJ.get_int('loops-min'), ADJ.get_int('loops-max'), ADJ.get_int('loops-incr'), 0, 0)
		self.loopSpin = Gtk.SpinButton()
		self.loopSpin.set_adjustment(adjustment)
		self.loopSpin.set_value(1)
		self.loopSpin.set_numeric(1)
		self.adjBar.pack_start(self.loopSpin, False, False, 0)
		
		iter_val = S.get_int('n-iterations')
		label = Gtk.Label("Iterations:")
		self.adjBar.add(label)
		adjustment = Gtk.Adjustment(iter_val, ADJ.get_int('incr-min'), ADJ.get_int('incr-max'), ADJ.get_int('incr-incr'), 10, 0)
		self.iterSpin = Gtk.SpinButton()
		self.iterSpin.set_adjustment(adjustment)
		self.iterSpin.set_value(iter_val)
		self.iterSpin.set_numeric(1)
		self.adjBar.pack_start(self.iterSpin, False, False, 0)
		self.unsaved[1]['iters'] = iter_val
		
		octv_val = S.get_int('n-octaves')
		label = Gtk.Label("Octaves:")
		self.adjBar.add(label)
		adjustment = Gtk.Adjustment(octv_val, ADJ.get_int('octv-min'), ADJ.get_int('octv-max'), ADJ.get_int('octv-incr'), 0, 0)
		self.octaveSpin = Gtk.SpinButton()
		self.octaveSpin.set_adjustment(adjustment)
		self.octaveSpin.set_value(octv_val)
		self.octaveSpin.set_numeric(1)
		self.adjBar.pack_start(self.octaveSpin, False, False, 0)
		self.unsaved[1]['octaves'] = octv_val
		
		octv_scale = S.get_double('octave-scale')
		label = Gtk.Label("Scale:")
		self.adjBar.add(label)
		adjustment = Gtk.Adjustment(octv_scale, ADJ.get_double('scale-min'), ADJ.get_double('scale-max'), ADJ.get_double('scale-incr'), 0, 0)
		self.scaleSpin = Gtk.SpinButton()
		self.scaleSpin.configure(adjustment,0.01,ADJ.get_int('scale-dp'))
		self.scaleSpin.set_value(octv_scale)
		self.scaleSpin.set_numeric(1)
		self.adjBar.pack_start(self.scaleSpin, False, False, 0)
		self.unsaved[1]['scale'] = octv_scale
		
		zoom_scale = S.get_double('zoom-scale')
		self.zoomLabel = Gtk.Label("Zoom:")
		self.adjBar.add(self.zoomLabel)
		adjustment = Gtk.Adjustment(zoom_scale, ADJ.get_double('zoom-min'), ADJ.get_double('zoom-max'), ADJ.get_double('zoom-incr'), 0, 0)
		self.zoomSpin = Gtk.SpinButton()
		self.zoomSpin.configure(adjustment,0.01,ADJ.get_int('zoom-dp'))
		self.zoomSpin.set_value(zoom_scale)
		self.zoomSpin.set_numeric(1)
		self.adjBar.pack_start(self.zoomSpin, False, False, 0)
		self.unsaved[1]['zoom'] = zoom_scale

		label = Gtk.Label("Zoom transition:")
		self.adjBar.add(label)
		zoomTrans_store = Gtk.ListStore(int, str)
		zoomTrans_store.append([0, "None"])
		zoomTrans_store.append([1, "Increment"])
		self.zoomTrans = Gtk.ComboBox.new_with_model(zoomTrans_store)
		renderer_text = Gtk.CellRendererText()
		self.zoomTrans.pack_start(renderer_text, True)
		self.zoomTrans.add_attribute(renderer_text, "text", 1)
		self.zoomTrans.set_active(0)
		self.adjBar.pack_start(self.zoomTrans, False, False, 0)
		self.unsaved[1]['zoom-trans'] = 0

		deg_val = S.get_double('rot-deg')
		self.degLabel = Gtk.Label("Rotation:")
		self.adjBar.add(self.degLabel)
		adjustment = Gtk.Adjustment(deg_val, ADJ.get_double('rot-min'), ADJ.get_double('rot-max'), ADJ.get_double('rot-incr'), 0, 0)
		self.degSpin = Gtk.SpinButton()
		self.degSpin.configure(adjustment,0.10,ADJ.get_int('rot-dp'))
		self.degSpin.set_value(deg_val)
		self.degSpin.set_numeric(1)
		self.adjBar.pack_start(self.degSpin, False, False, 0)
		self.unsaved[1]['deg'] = round(deg_val,3)
		
		
		label = Gtk.Label("Rotate transition:")
		self.adjBar.add(label)
		degTrans_store = Gtk.ListStore(int, str)
		degTrans_store.append([0, "None"])
		degTrans_store.append([1, "Increment"])
		self.degTrans = Gtk.ComboBox.new_with_model(zoomTrans_store)
		renderer_text = Gtk.CellRendererText()
		self.degTrans.pack_start(renderer_text, True)
		self.degTrans.add_attribute(renderer_text, "text", 1)
		self.degTrans.set_active(0)
		self.adjBar.pack_start(self.degTrans, False, False, 0)
		self.unsaved[1]['deg-trans'] = 0
		
		self.addBtn = Gtk.Button("Add")
		self.addBtn.connect("clicked", self.on_add_clicked)
		self.adjBar.pack_start(self.addBtn, False, False, 0)

		self.box.add(self.adjBar)
		
		
	def on_add_clicked(self, btn):
		self.unsaved[int(self.loopSpin.get_value())] = {
			'iters':self.iterSpin.get_value(),
			'octaves':self.octaveSpin.get_value(),
			'scale':self.scaleSpin.get_value(),
			'zoom':self.zoomSpin.get_value(),
			'deg':round(self.degSpin.get_value(),3),
			'zoom-trans':self.get_trans(self.zoomTrans),
			'deg-trans':self.get_trans(self.degTrans)
			}
		self.display_adjustments()
	
	def get_trans(self, obj):
		tree_iter = obj.get_active_iter()
		if tree_iter != None:
			model = obj.get_model()
			return model[tree_iter][0]
		return False
	
	def display_adjustments(self):
		
		S = self.unsaved
		for w in self.vs.get_children():
			w.destroy()
		for key in sorted(S.iterkeys()):
			box = Gtk.Box()
			
			label = Gtk.Label('@ FRAME '+str(int(key))+' :: ')
			box.add(label)
			
			label = Gtk.Label('iters: '+str(S[key]['iters'])+' | ')
			box.add(label)
			
			label = Gtk.Label('octaves: '+str(S[key]['octaves'])+' | ')
			box.add(label)
			
			label = Gtk.Label('scale: '+str(S[key]['scale'])+' | ')
			box.add(label)
			
			label = Gtk.Label('zoom: '+str(S[key]['zoom'])+' | ')
			box.add(label)
			
			label = Gtk.Label('rotation: '+str(round(S[key]['deg'],3))+' | ')
			box.add(label)
			
			self.vs.add(box)
			self.vs.set_child_packing(box,False,False,5,0)	
			
			box = Gtk.Box()
			
			label = Gtk.Label('zoom transition: '+str(S[key]['zoom-trans'])+' | ')
			box.add(label)
			
			label = Gtk.Label('rotation transition: '+str(S[key]['deg-trans'])+' | ')
			box.add(label)
			self.vs.add(box)
			self.vs.set_child_packing(box,False,False,5,0)	
			
		self.vs.show_all()
			
	def do_save_bar(self):
		box = Gtk.Box()
		self.seqName = Gtk.Entry()
		self.seqName.set_text("my-sequence-name")
		box.add(self.seqName)
		
		self.saveBtn = Gtk.Button("Save")
		self.saveBtn.connect("clicked", self.on_save_clicked)
		box.pack_start(self.saveBtn, False, False, 0)
		
		self.vbox.add(box)
        
	def on_save_clicked(self,btn):
		nm = self.seqName.get_text()
		self.sequences[nm] = self.unsaved
		target = open(self.fJson, 'w')
		target.truncate()
		target.write(json.dumps(self.sequences))
		self.mainWin.sequences = self.sequences 
		self.mainWin.set_seq_liststore(self.mainWin.seq_store)
		self.mainWin.seqCombo.set_active(0)
		self.destroy()
