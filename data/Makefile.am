SUBDIRS = icons

gsettings_SCHEMAS = org.rebelweb.dreamer.gschema.xml

@GSETTINGS_RULES@
gschemas.compiled: $(gsettings_SCHEMAS:.xml=.valid)
	$(AM_V_GEN) $(GLIB_COMPILE_SCHEMAS) --targetdir=. .

EXTRA_DIST = $(gsettings_SCHEMAS)

all-local: gschemas.compiled
