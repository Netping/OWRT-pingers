SECTION="NetPing modules"
CATEGORY="Base"
TITLE="OWRT_pingers"

PKG_NAME="OWRT_pingers"
PKG_VERSION="V0.1"
PKG_RELEASE=3

MODULE_FILES=pingers.py
MODULE_FILES_DIR=/etc/netping_pingers/

CONF_FILE=pingerconf
CONF_DIR=/etc/config/

.PHONY: all install

all: install

install:
	mkdir $(MODULE_FILES_DIR)
	cp $(CONF_FILE) $(CONF_DIR)
	for f in $(MODULE_FILES); do cp $${f} $(MODULE_FILES_DIR); done

clean:
	rm -f $(CONF_DIR)$(CONF_FILE)
	rm -rf $(MODULE_FILES_DIR)
