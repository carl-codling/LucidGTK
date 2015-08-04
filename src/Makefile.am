SUBDIRS = lucidgtk

bin_SCRIPTS = lucid-gtk
CLEANFILES = $(bin_SCRIPTS)
EXTRA_DIST = lucid-gtk.in

do_substitution = sed -e 's,[@]pythondir[@],$(pythondir),g' \
	-e 's,[@]PACKAGE[@],$(PACKAGE),g' \
	-e 's,[@]VERSION[@],$(VERSION),g' 

lucid-gtk: lucid-gtk.in Makefile
	$(do_substitution) < $(srcdir)/lucid-gtk.in > lucid-gtk
	chmod +x lucid-gtk
