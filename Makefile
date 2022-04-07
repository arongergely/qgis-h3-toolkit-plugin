PLUGIN_ZIP_NAME = h3_toolkit_plugin

zip:
	@echo "Making zip."
	@echo "-----------"
	rm -f $(PLUGIN_ZIP_NAME).zip
	zip -9r -x Makefile /.idea* /.git* /*__pycache__* @ $(PLUGIN_ZIP_NAME).zip ./h3_toolkit
