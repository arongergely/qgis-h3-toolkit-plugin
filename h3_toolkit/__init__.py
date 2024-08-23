#-----------------------------------------------------------
# Copyright (C) 2022 Aron Gergely
#-----------------------------------------------------------
# Licensed under the terms of GNU GPL 2
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#---------------------------------------------------------------------
import os

from qgis.core import Qgis, QgsApplication
from PyQt5.QtWidgets import QAction, QMessageBox, QPushButton

# Check if h3 dependency is installed, handle gracefully if not
from .h3_dependency_guard import IS_H3_PRESENT

if IS_H3_PRESENT:
    from .processing.provider import H3Provider
    from .processing.utilities import getVersionH3Bindings
else:
    pass


def classFactory(iface):
    return H3Toolkit(iface)


class H3Toolkit:
    pluginName = 'H3 Quadkey Toolkit'

    def __init__(self, iface, is_h3lib_present=IS_H3_PRESENT):
        self.iface = iface
        self.provider = None
        self.menuName = None
        self.isH3LibPresent = is_h3lib_present
        self.h3LibVersions = getVersionH3Bindings() if self.isH3LibPresent else None

    def initProcessing(self):
        self.provider = H3Provider()
        QgsApplication.processingRegistry().addProvider(self.provider)

    def initGui(self):
        if self.isH3LibPresent:
            self.initProcessing()
        else:
            # Handle gracefully if h3 is not installed
            widget = self.iface.messageBar().createMessage(
                f'{self.pluginName} plugin',
                'H3 library not found. Click on "Help Me Install" for help'
            )
            button = QPushButton(widget)
            button.setText('Help Me Install')
            button.pressed.connect(self.installHelpWindow)
            widget.layout().addWidget(button)
            self.iface.messageBar().pushWidget(widget, level=Qgis.Warning, duration=60)

        self.menuName = f'{self.pluginName} Plugin'

        # add About window
        self.aboutAction = QAction('About', self.iface.mainWindow())
        self.iface.addPluginToMenu(f'{self.pluginName} Plugin', self.aboutAction)

        # add install help window
        self.installHelpAction = QAction('Install Help', self.iface.mainWindow())
        self.iface.addPluginToMenu(f'{self.pluginName} Plugin', self.installHelpAction)

        # connect signals
        self.aboutAction.triggered.connect(self.aboutWindow)
        self.installHelpAction.triggered.connect(self.installHelpWindow)

    def unload(self):
        QgsApplication.processingRegistry().removeProvider(self.provider)
        self.iface.removePluginMenu(f'{self.pluginName} Plugin', self.aboutAction)
        self.iface.removePluginMenu(f'{self.pluginName} Plugin', self.installHelpAction)

    def aboutWindow(self):
        windowTitle = f'About {self.pluginName} plugin'
        libversions = self.h3LibVersions if self.isH3LibPresent else {'c': 'not installed', 'python': 'not installed'}
        aboutString = f'''
            <h4>Developer</h4>
            <p>
              Aron Gergely</a>
            </p>
            <h4>H3 Library versions</h4>
            <p>
              C (core): {libversions['c']}<br>
              Python bindings: {libversions['python']}
            </p>
            <hr/>
            <p>
              H3 Library © 2022 Uber Technologies, Inc. Licensed under Apache 2.0
            </p>
            <p>
              <a href="https://h3geo.org/">https://h3geo.org/</a>
            </p>
            '''

        QMessageBox.information(self.iface.mainWindow(), windowTitle, aboutString)

    def installHelpWindow(self):
        windowTitle = 'H3 Library Install Help'
        helpString = '''
            <p>
              To start using the plugin you have to install the H3 Library for Python (<a href="https://h3geo.org/">https://h3geo.org/</a>).<br><br>
              It is available as the Python package 'h3', which has to be installed into the Python environment of QGIS.
            </p>
            <p>
              Please refer to the H3 documentation on how to install: <a href="https://h3geo.org/docs/installation">https://h3geo.org/docs/installation</a>
            </p>
            <p>
              <b>NOTE: The plugin is tested with h3 version the 3.7.x. However it should work with all 3.x versions of h3</b>
            </p>
            You will also need to install the Mercantile package (<a href="https://github.com/geospatial-jeff/mercantile">https://github.com/geospatial-jeff/mercantile</a>).

            To ensure it is installed in your QGIS Python environment, you can open terminal and type:

            /Applications/QGIS.app/Contents/MacOS/bin/python3.9 -m pip install mercantile

            Note: you need to find the python path of your QGIS Python environment in your system.

            <p>
            </p>
            <p>
              Once the package install completed, please  reload the plugin (or restart QGIS) to start using it.<br><br>
              Enjoy!
            </p>
            '''

        QMessageBox.information(self.iface.mainWindow(), windowTitle, helpString)
