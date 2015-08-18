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

UI_INFO = """
<ui>
  <menubar name='MenuBar'>
	  <menu action='EditMenu'>
		<menuitem action='ShowPrefs' />
	  </menu>
	  <menu action='ToolsMenu'>
		  <menuitem action='ShowSequencer' />
	  </menu>
	  <menu action='HelpMenu'>
		<menuitem action='ShowHelp' />
		<menuitem action='ShowAbout' />
	  </menu>
	  </menubar>
</ui>
"""

class GlobalMenu():
	
	def __init__(self, mainWin):
		self.mainWin = mainWin
		
		action_group = Gtk.ActionGroup("lucid_actions")
		self.add_main_menu_actions(action_group)
		uimanager = self.create_ui_manager()
		uimanager.insert_action_group(action_group)
		menubar = uimanager.get_widget("/MenuBar")
		mainWin.grid.add(menubar)

	def create_ui_manager(self):
		uimanager = Gtk.UIManager()

		uimanager.add_ui_from_string(UI_INFO)

		accelgroup = uimanager.get_accel_group()
		self.mainWin.add_accel_group(accelgroup)
		return uimanager
			
	def add_main_menu_actions(self, action_group):
		
		win = self.mainWin
		
		action_edit = Gtk.Action("EditMenu", "Edit", None, None)
		action_group.add_action(action_edit)

		action_prefs = Gtk.Action("ShowPrefs", "Preferences", None, None)
		action_group.add_action(action_prefs)
		action_prefs.connect("activate", win.on_settings_clicked)
		
		action_edit = Gtk.Action("ToolsMenu", "Tools", None, None)
		action_group.add_action(action_edit)

		action_seq = Gtk.Action("ShowSequencer", "Sequencer", None, None)
		action_group.add_action(action_seq)
		action_seq.connect("activate", win.sequencer_win)
		
		action_helpmenu = Gtk.Action("HelpMenu", "Help", None, None)
		action_group.add_action(action_helpmenu)

		action_about = Gtk.Action("ShowHelp", "Help", None, None)
		action_group.add_action(action_about)
		action_about.connect("activate", win.on_help_clicked)
		
		action_about = Gtk.Action("ShowAbout", "About", None, None)
		action_group.add_action(action_about)
		action_about.connect("activate", win.on_about_clicked)
		

	


