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
import collections


class SequencerWindow(Gtk.Window):

	def __init__(self, mainWin):
		self.mainWin = mainWin
		self.DD = mainWin.DD
		self.settings = Gio.Settings('org.rebelweb.dreamer')
		Gtk.Window.__init__(self, title="Lucid-GTK Sequencer")
		self.mainWin.hide()
		self.connect("delete-event", self.on_close)
		self.set_border_width(10)
		self.vbox = Gtk.VBox()
		self.box = Gtk.Box()
		
		self.add(self.vbox)
		self.fJson = self.settings.get_string('proj-dir')+'/.lucid.seq.json'
		self.sequences = mainWin._Sequencer.get_sequences()
		self.unsaved = {}

		self.do_save_bar()
		self.do_adjustments_bar()
		self.do_viewscreen()
		self.vbox.add(self.box)
		self.display_adjustments()
		
		self.show_all()
		
	def on_close(self,a,b):
		self.destroy()
		self.mainWin.show()
		
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
		
		box = Gtk.Box(homogeneous = True)
		self.loopLabel = Gtk.Label("Adjust @ loop:")
		box.add(self.loopLabel)
		adjustment = Gtk.Adjustment(1, ADJ.get_int('loops-min'), ADJ.get_int('loops-max'), 25, 0, 0)
		self.loopSpin = Gtk.SpinButton()
		self.loopSpin.set_adjustment(adjustment)
		self.loopSpin.set_value(1)
		self.loopSpin.set_numeric(1)
		self.loopSpin.set_increments(24,99)
		box.add(self.loopSpin)
		self.loopSpin.connect("changed", self.focus_row_from_spin)
		self.adjBar.pack_start(box, False, False, 0)

		box = Gtk.Box(homogeneous = True)
		iter_val = S.get_int('n-iterations')
		label = Gtk.Label("Iterations:")
		box.add(label)
		adjustment = Gtk.Adjustment(iter_val, ADJ.get_int('incr-min'), ADJ.get_int('incr-max'), ADJ.get_int('incr-incr'), 10, 0)
		self.iterSpin = Gtk.SpinButton()
		box.add(self.iterSpin)
		self.iterSpin.set_adjustment(adjustment)
		self.iterSpin.set_value(iter_val)
		self.iterSpin.set_numeric(1)
		btn = Gtk.Button(">")
		btn.connect("clicked", self.insert_val, 'iters', self.iterSpin)
		box.add(btn)
		self.adjBar.pack_start(box, False, False, 0)

		box = Gtk.Box(homogeneous = True)
		octv_val = S.get_int('n-octaves')
		label = Gtk.Label("Octaves:")
		box.add(label)
		adjustment = Gtk.Adjustment(octv_val, ADJ.get_int('octv-min'), ADJ.get_int('octv-max'), ADJ.get_int('octv-incr'), 0, 0)
		self.octaveSpin = Gtk.SpinButton()
		box.add(self.octaveSpin)
		self.octaveSpin.set_adjustment(adjustment)
		self.octaveSpin.set_value(octv_val)
		self.octaveSpin.set_numeric(1)
		btn = Gtk.Button(">")
		btn.connect("clicked", self.insert_val, 'octaves', self.octaveSpin)
		box.add(btn)
		self.adjBar.pack_start(box, False, False, 0)

		box = Gtk.Box(homogeneous = True)
		octv_scale = S.get_double('octave-scale')
		label = Gtk.Label("Scale:")
		box.add(label)
		adjustment = Gtk.Adjustment(octv_scale, ADJ.get_double('scale-min'), ADJ.get_double('scale-max'), ADJ.get_double('scale-incr'), 0, 0)
		self.scaleSpin = Gtk.SpinButton()
		box.add(self.scaleSpin)
		self.scaleSpin.configure(adjustment,0.01,ADJ.get_int('scale-dp'))
		self.scaleSpin.set_value(octv_scale)
		self.scaleSpin.set_numeric(1)
		btn = Gtk.Button(">")
		btn.connect("clicked", self.insert_val, 'scale', self.scaleSpin)
		box.add(btn)
		self.adjBar.pack_start(box, False, False, 0)

		box = Gtk.Box(homogeneous = True)
		zoom_scale = S.get_double('zoom-scale')
		self.zoomLabel = Gtk.Label("Zoom:")
		box.add(self.zoomLabel)
		adjustment = Gtk.Adjustment(zoom_scale, ADJ.get_double('zoom-min'), ADJ.get_double('zoom-max'), ADJ.get_double('zoom-incr'), 0, 0)
		self.zoomSpin = Gtk.SpinButton()
		box.add(self.zoomSpin)
		self.zoomSpin.configure(adjustment,0.01,ADJ.get_int('zoom-dp'))
		self.zoomSpin.set_value(zoom_scale)
		self.zoomSpin.set_numeric(1)
		btn = Gtk.Button(">")
		btn.connect("clicked", self.insert_val, 'zoom', self.zoomSpin)
		box.add(btn)
		self.adjBar.pack_start(box, False, False, 0)
		
		box = Gtk.Box(homogeneous = True)
		label = Gtk.Label("Zoom Transition:")
		box.add(label)
		zoomTrans_store = Gtk.ListStore(int, str)
		zoomTrans_store.append([0, "None"])
		zoomTrans_store.append([1, "Increment"])
		self.zoomTrans = Gtk.ComboBox.new_with_model(zoomTrans_store)
		box.add(self.zoomTrans)
		renderer_text = Gtk.CellRendererText()
		self.zoomTrans.pack_start(renderer_text, True)
		self.zoomTrans.add_attribute(renderer_text, "text", 1)
		self.zoomTrans.set_active(0)
		btn = Gtk.Button(">")
		btn.connect("clicked", self.insert_actv, 'zoom-trans','zoom', self.zoomTrans, self.zoomSpin)
		box.add(btn)
		self.adjBar.pack_start(box, False, False, 0)

		box = Gtk.Box(homogeneous = True)
		deg_val = S.get_double('rot-deg')
		self.degLabel = Gtk.Label("Rotation:")
		box.add(self.degLabel)
		adjustment = Gtk.Adjustment(deg_val, ADJ.get_double('rot-min'), ADJ.get_double('rot-max'), ADJ.get_double('rot-incr'), 0, 0)
		self.degSpin = Gtk.SpinButton()
		box.add(self.degSpin)
		self.degSpin.configure(adjustment,0.10,ADJ.get_int('rot-dp'))
		self.degSpin.set_value(deg_val)
		self.degSpin.set_numeric(1)
		btn = Gtk.Button(">")
		btn.connect("clicked", self.insert_val, 'deg', self.degSpin)
		box.add(btn)
		self.adjBar.pack_start(box, False, False, 0)


		box = Gtk.Box(homogeneous = True)
		label = Gtk.Label("Rot. Transition:")
		box.add(label)
		degTrans_store = Gtk.ListStore(int, str)
		degTrans_store.append([0, "None"])
		degTrans_store.append([1, "Increment"])
		self.degTrans = Gtk.ComboBox.new_with_model(degTrans_store)
		box.add(self.degTrans)
		renderer_text = Gtk.CellRendererText()
		self.degTrans.pack_start(renderer_text, True)
		self.degTrans.add_attribute(renderer_text, "text", 1)
		self.degTrans.set_active(0)
		btn = Gtk.Button(">")
		btn.connect("clicked", self.insert_actv, 'deg-trans','deg', self.degTrans, self.degSpin)
		box.add(btn)
		self.adjBar.pack_start(box, False, False, 0)

		box = Gtk.Box(homogeneous = True)
		label = Gtk.Label("Output Layer:")
		box.add(label)
		box.add(self.make_layer_select())
		self.adjBar.pack_start(box, False, False, True)
		
		box = Gtk.Box(homogeneous = True)
		label = Gtk.Label(" ")
		box.add(label)
		btn = Gtk.Button(">")
		btn.connect("clicked", self.insert_layer)
		box.add(btn)
		self.adjBar.pack_start(box, False, False, 0)
		self.set_default_first_row()
		self.box.add(self.adjBar)
	
	def set_default_first_row(self):
		S = self.settings
		self.unsaved[1] = {}
		self.unsaved[1]['iters'] = S.get_int('n-iterations')
		self.unsaved[1]['layer'] = 0
		self.unsaved[1]['deg-trans'] = 0
		self.unsaved[1]['deg'] = round(S.get_double('rot-deg'),3)
		self.unsaved[1]['zoom-trans'] = 0
		self.unsaved[1]['zoom'] = S.get_double('zoom-scale')
		self.unsaved[1]['scale'] = S.get_double('octave-scale')
		self.unsaved[1]['octaves'] = S.get_int('n-octaves')
	
	def insert_val(self, btn, col, valobj):
		row = int(self.loopSpin.get_value())
		val = valobj.get_value()
		if row not in self.unsaved:
			self.unsaved[row] = {}
		self.unsaved[row][col] = val
		self.display_adjustments()
	
	def insert_actv(self, btn, col, col2, valobj, valobj2):
		row = int(self.loopSpin.get_value())
		val = valobj.get_active()
		val2 = valobj2.get_value()
		if row not in self.unsaved:
			self.unsaved[row] = {}
		self.unsaved[row][col] = val
		self.unsaved[row][col2] = val2
		self.display_adjustments()
	
	def insert_layer(self, btn):
		row = int(self.loopSpin.get_value())
		val = self.layer_combo.get_active()
		if row not in self.unsaved:
			self.unsaved[row] = {}
		self.unsaved[row]['layer'] = val
		self.display_adjustments()
	
	
		
	def make_layer_select(self):
		layer_store = Gtk.ListStore(int, str)
		net = self.DD.net
		l = list(net._layer_names)
		blobs = list(net.blobs)
		layers = [val for val in l if val in blobs]

		# Remove googlenet layers that are causing core dumped crash
		bad_layers = ['pool5/7x7_s1','loss3/classifier','prob']
		i = 0
		for layer in layers:
			if layer not in bad_layers:
				layer_store.append([i,layer])
				i+=1

		self.layer_combo = Gtk.ComboBox.new_with_model(layer_store)
		renderer_text = Gtk.CellRendererText()
		self.layer_combo.pack_start(renderer_text, True)
		self.layer_combo.add_attribute(renderer_text, "text", 1)
		self.layer_combo.set_active(0)
		return self.layer_combo
		
	def on_add_clicked(self, btn):
		self.unsaved[int(self.loopSpin.get_value())] = {
			'iters':self.iterSpin.get_value(),
			'octaves':self.octaveSpin.get_value(),
			'scale':self.scaleSpin.get_value(),
			'zoom':self.zoomSpin.get_value(),
			'deg':round(self.degSpin.get_value(),3),
			'zoom-trans':self.get_trans(self.zoomTrans),
			'deg-trans':self.get_trans(self.degTrans),
			'layer':self.get_trans(self.layer_combo)
			}
		self.display_adjustments()
	
	def get_trans(self, obj):
		tree_iter = obj.get_active_iter()
		if tree_iter != None:
			model = obj.get_model()
			return model[tree_iter][0]
		return False
	
	def display_adjustments(self):
		lastEntry = {
			'iters':None,
			'octaves':None,
			'scale':None,
			'zoom':None,
			'deg':None,
			'zoom-trans':None,
			'deg-trans':None,
			'layer':None
			}
		S = self.unsaved
		for w in self.vs.get_children():
			w.destroy()
		
		sortedKeys = sorted(S.iterkeys())
		tableRowN = int(sortedKeys[-1])
		if tableRowN<100:
			tableRowN = 100
		self.grid = Gtk.Table(tableRowN,11, False)
		
		self.scrollWin = Gtk.ScrolledWindow()
		self.scrollWin.add(self.grid)
		self.scrollWin.set_size_request(800,500)	

		self.grid.attach(Gtk.Label('@ Frame'),0,1,0,1)
		self.grid.attach(Gtk.Label('Iterations:'),1,2,0,1)
		self.grid.attach(Gtk.Label('Octaves:'),2,3,0,1)
		self.grid.attach(Gtk.Label('Scale:'),3,4,0,1)
		self.grid.attach(Gtk.Label('Zoom'),4,5,0,1)
		self.grid.attach(Gtk.Label('Transition'),5,6,0,1)
		self.grid.attach(Gtk.Label('Rotation'),6,7,0,1)
		self.grid.attach(Gtk.Label('Transition'),7,8,0,1)
		self.grid.attach(Gtk.Label('Layer'),8,9,0,1)
		self.grid.set_col_spacings(10)
		self.grid.set_row_spacings(10)
		i = 1
		zoom_transitions = {}
		active_zoom_transition = False
		deg_transitions = {}
		active_deg_transition = False
		for key in sorted(S.iterkeys()):
			
			btn = Gtk.Button(str(int(key)))
			self.grid.attach(btn,0,1,int(key), int(key)+1)
			btn.rowid = key	
			btn.connect("clicked", self.focus_row_from_btn)
			
			if 'iters' in S[key] and S[key]['iters'] != lastEntry['iters']:
				label = Gtk.Label(str(S[key]['iters']))
				self.grid.attach(label,1,2,int(key), int(key)+1)
				lastEntry['iters'] = S[key]['iters']
			
			if  'octaves' in S[key] and S[key]['octaves'] != lastEntry['octaves']:
				label = Gtk.Label(str(S[key]['octaves']))
				self.grid.attach(label,2,3,int(key), int(key)+1)
				lastEntry['octaves'] = S[key]['octaves']
			
			if  'scale' in S[key] and S[key]['scale'] != lastEntry['scale']:
				label = Gtk.Label(str(S[key]['scale']))
				self.grid.attach(label,3,4,int(key), int(key)+1)
				lastEntry['scale'] = S[key]['scale']
			
			if  'zoom' in S[key] and S[key]['zoom'] != lastEntry['zoom']:
				label = Gtk.Label(str(S[key]['zoom']))
				self.grid.attach(label,4,5,int(key), int(key)+1)
				lastEntry['zoom'] = S[key]['zoom']
				if active_zoom_transition != False:
					zoom_transitions[active_zoom_transition]['breaks'].append(int(key))
			
			if  'zoom-trans' in S[key] and S[key]['zoom-trans'] != lastEntry['zoom-trans']:
				label = Gtk.Label()
				label.set_markup('<span background="#ffffff">'+str(S[key]['zoom-trans'])+'</span>')
				self.grid.attach(label,5,6,int(key), int(key)+1)
				lastEntry['zoom-trans'] = S[key]['zoom-trans']
				if S[key]['zoom-trans'] == 0:
					active_zoom_transition = False
				else:
					zoom_transitions[key] = {'type':S[key]['zoom-trans'],'breaks':[]}
					active_zoom_transition = key
			
			if  'deg' in S[key] and S[key]['deg'] != lastEntry['deg']:
				label = Gtk.Label(str(round(S[key]['deg'],3)))
				self.grid.attach(label,6,7,int(key), int(key)+1)
				lastEntry['deg'] = S[key]['deg']
				if active_deg_transition != False:
					deg_transitions[active_deg_transition]['breaks'].append(int(key))
					
			if  'deg-trans' in S[key] and S[key]['deg-trans'] != lastEntry['deg-trans']:
				label = Gtk.Label(str(S[key]['deg-trans']))
				self.grid.attach(label,7,8,int(key), int(key)+1)
				lastEntry['deg-trans'] = S[key]['deg-trans']
				if S[key]['deg-trans'] == 0:
					active_deg_transition = False
				else:
					deg_transitions[key] = {'type':S[key]['deg-trans'],'breaks':[]}
					active_deg_transition = key
			
			if  'layer' in S[key] and S[key]['layer'] != lastEntry['layer']:
				label = Gtk.Label(S[key]['layer'])
				self.grid.attach(label,8,9,int(key), int(key)+1)
				lastEntry['layer'] = S[key]['layer']
			if i>1:
				btn = Gtk.Button('x')
				self.grid.attach(btn,9,10,int(key), int(key)+1)	
				btn.rowid = key	
				btn.connect("clicked", self.delete_row)
			else:
				i+=1
		self.display_transitions(zoom_transitions,'zoom')	
		self.display_transitions(deg_transitions,'deg')	
		self.vs.add(self.scrollWin)
		self.vs.show_all()
		self.vs.set_child_packing(self.grid,False,False,5,0)
			
	def display_transitions(self, trans, typ):
		for k in trans.iterkeys():
			start = k
			for end in trans[k]['breaks']:
				self.display_transition(int(start), end, typ)
				start = end
	
	def display_transition(self, start, end, typ):
		trans_start = self.unsaved[start][typ]
		trans_end = self.unsaved[end][typ]
		trans_dif = trans_end - trans_start
		span = end - start
		for i in xrange(start+1, end):
			pos = i-start
			zoom = trans_start + (pos*(trans_dif/span))
			label = Gtk.Label()
			label.set_markup('<span weight="light" foreground="#999999">'+str(round(zoom,3))+'</span>')
			if typ == 'zoom':
				self.grid.attach(label,5,6,i,i+1)	
			elif typ == 'deg':
				self.grid.attach(label,7,8,i,i+1)	
				
	
	def delete_row(self,btn):
		self.unsaved.pop(btn.rowid, None)
		self.display_adjustments()
	
	def focus_row_from_spin(self, spin):
		v = spin.get_value()
		if v == 1:
			spin.set_increments(24,99)
		else:
			spin.set_increments(25,100)
		self.focus_row(v)
	
	def focus_row_from_btn(self, btn):
		self.focus_row(btn.rowid)
		self.loopSpin.set_value(btn.rowid)
	
	def focus_row(self, row):
		for i in xrange(1,int(row)+1):
			if i in self.unsaved:
				if 'iters' in self.unsaved[i]:
					self.iterSpin.set_value(self.unsaved[i]['iters'])
				if 'octaves' in self.unsaved[i]:
					self.octaveSpin.set_value(self.unsaved[i]['octaves'])
				if 'scale' in self.unsaved[i]:
					self.scaleSpin.set_value(self.unsaved[i]['scale'])
				if 'zoom' in self.unsaved[i]:
					self.zoomSpin.set_value(self.unsaved[i]['zoom'])
				if 'deg' in self.unsaved[i]:
					self.degSpin.set_value(self.unsaved[i]['deg'])
				if 'zoom-trans' in self.unsaved[i]:
					self.zoomTrans.set_active(int(self.unsaved[i]['zoom-trans']))
				if 'deg-trans' in self.unsaved[i]:
					self.degTrans.set_active(int(self.unsaved[i]['deg-trans']))
				if 'layer' in self.unsaved[i]:
					self.layer_combo.set_active(self.unsaved[i]['layer'])
	
	def do_save_bar(self):
		box = Gtk.Box()
		
		self.delBtn = Gtk.Button("Delete")
		self.delBtn.connect("clicked", self.on_del_clicked)
		box.pack_start(self.delBtn, False, False, 0)
		box.set_child_packing(self.delBtn, False, True, 0, 1)

		self.saveBtn = Gtk.Button("Save")
		self.saveBtn.connect("clicked", self.on_save_clicked)
		box.pack_start(self.saveBtn, False, False, 0)
		box.set_child_packing(self.saveBtn, False, True, 0, 1)

		name_store = Gtk.ListStore(str)
		for key in sorted(self.sequences.iterkeys()):
			name_store.append([key])
		self.seqName = Gtk.ComboBox.new_with_model_and_entry(name_store)
		self.seqName.connect("changed", self.load_saved_seq)
		self.seqName.set_entry_text_column(0)

		box.add(self.seqName)
		box.set_child_packing(self.seqName, False, True, 0, 1)
				
		self.vbox.add(box)
		
	def load_saved_seq(self, combo):
		tree_iter = combo.get_active_iter()
		if tree_iter != None:
			model = combo.get_model()
			name = model[tree_iter][0]
			out = {}
			for item in self.sequences[name].iterkeys():
				out[int(item)] = self.sequences[name][item]
			self.unsaved = out
			self.display_adjustments()
			self.focus_row(1)
	
	def on_save_clicked(self,btn):
		nm = self.get_seq_entry_name()
		self.sequences[nm] = self.unsaved
		self.save_to_json()
		
	def save_to_json(self):
		win = self.mainWin
		target = open(self.fJson, 'w')
		target.truncate()
		target.write(json.dumps(self.sequences))
		target.close()
		win.sequences = win._Sequencer.get_sequences()
		win._Sequencer.set_seq_liststore(win.seq_store)
		win.seqCombo.set_active(0)
	
	def get_seq_entry_name(self):
		tree_iter = self.seqName.get_active_iter()
		if tree_iter != None:
			model = self.seqName.get_model()
			return model[tree_iter][0]
		else:
			entry = self.seqName.get_child()
			return entry.get_text()
	
	def on_del_clicked(self, btn):
		nm = self.get_seq_entry_name()
		self.sequences.pop(nm, None)
		self.save_to_json()
		self.unsaved = {}
		self.set_default_first_row()
		self.display_adjustments()

class Sequencer():
	
	def __init__(self, mainWin):
		self.mainWin = mainWin

	def get_sequences(self):
		jf = self.mainWin.settings.get_string('proj-dir')+'/.lucid.seq.json'
		if os.path.isfile(jf):
			d = open(jf,'r').read()
			return json.loads(d)
		else:
			return {}
	
	def set_seq_liststore(self, store):
		store.clear()
		store.append(['On the fly'])
		for k in self.mainWin.sequences.iterkeys():
			store.append([k])
		store.append(['Manage Sequences'])

	def set_sequence(self, combo):
		tree_iter = combo.get_active_iter()
		if tree_iter != None:
			model = combo.get_model()
			seq = model[tree_iter][0]
			if seq == 'On the fly':
				self.mainWin.sequence = None
			elif seq == 'Manage Sequences':
				self.mainWin.sequencer_win(False)
				self.mainWin.sequence = None
				self.mainWin.seqCombo.set_active(0)
			else:
				self.build_sequence(self.mainWin.sequences[seq])
		
	
	def get_seq_key(self,key):
		try:
			return int(key)
		except ValueError:
			return key

	def build_sequence(self,seq):
		S = collections.OrderedDict(sorted(seq.items(), key=lambda t: self.get_seq_key(t[0])))
		
		lastEntry = {
			'zoom':None,
			'deg':None,
			'zoom-trans':None,
			'deg-trans':None
			}
		zoom_transitions = {}
		active_zoom_transition = False
		deg_transitions = {}
		active_deg_transition = False
		for key in S.iterkeys():
			if  'zoom' in S[key] and S[key]['zoom'] != lastEntry['zoom']:
				lastEntry['zoom'] = S[key]['zoom']
				if active_zoom_transition != False:
					zoom_transitions[active_zoom_transition]['breaks'].append(int(key))
			
			if  'zoom-trans' in S[key] and S[key]['zoom-trans'] != lastEntry['zoom-trans']:
				lastEntry['zoom-trans'] = S[key]['zoom-trans']
				if S[key]['zoom-trans'] == 0:
					active_zoom_transition = False
				else:
					zoom_transitions[key] = {'type':S[key]['zoom-trans'],'breaks':[]}
					active_zoom_transition = key
			
			if  'deg' in S[key] and S[key]['deg'] != lastEntry['deg']:
				lastEntry['deg'] = S[key]['deg']
				if active_deg_transition != False:
					deg_transitions[active_deg_transition]['breaks'].append(int(key))
					
			if  'deg-trans' in S[key] and S[key]['deg-trans'] != lastEntry['deg-trans']:
				lastEntry['deg-trans'] = S[key]['deg-trans']
				if S[key]['deg-trans'] == 0:
					active_deg_transition = False
				else:
					deg_transitions[key] = {'type':S[key]['deg-trans'],'breaks':[]}
					active_deg_transition = key
		
		
		self.build_transitions(zoom_transitions,'zoom',S)	
		self.build_transitions(deg_transitions,'deg',S)
		self.mainWin.sequence = collections.OrderedDict(sorted(S.items(), key=lambda t: self.get_seq_key(t[0])))

	
	def build_transitions(self, trans, typ, seq):
		for k in trans.iterkeys():
			start = k
			for end in trans[k]['breaks']:
				self.build_transition(start, str(end), typ, seq)
				start = str(end)
					
	def build_transition(self, start, end, typ, seq):
		
		trans_start = seq[start][typ]
		trans_end = seq[end][typ]
		trans_dif = trans_end - trans_start
		span = int(end) - int(start)
		for i in xrange(int(start)+1, int(end)):
			pos = i-int(start)
			val = trans_start + (pos*(trans_dif/span))
			if str(i) not in seq:
				seq[str(i)] = {}
			seq[str(i)][typ] = val

	def do_seq_adjust(self, i):
		if i in self.mainWin.sequence:
			if 'iters' in self.mainWin.sequence[i]:
				self.mainWin.iterSpin.set_value(self.mainWin.sequence[i]['iters'])
			if 'octaves' in self.mainWin.sequence[i]:
				self.mainWin.octaveSpin.set_value(self.mainWin.sequence[i]['octaves'])
			if 'scale' in self.mainWin.sequence[i]:
				self.mainWin.scaleSpin.set_value(self.mainWin.sequence[i]['scale'])
			if 'zoom' in self.mainWin.sequence[i]:
				self.mainWin.zoomSpin.set_value(self.mainWin.sequence[i]['zoom'])
			if 'deg' in self.mainWin.sequence[i]:
				self.mainWin.degSpin.set_value(self.mainWin.sequence[i]['deg'])
			if 'layer' in self.mainWin.sequence[i]:
				self.mainWin.layer_combo.set_active(int(self.mainWin.sequence[i]['layer']))
