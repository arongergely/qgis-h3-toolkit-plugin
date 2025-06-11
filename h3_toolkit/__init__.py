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
from .h3_dependency_guard import IS_H3_PRESENT, H3_VERSION

if IS_H3_PRESENT:
    if H3_VERSION.startswith('4'):
        from .processing.provider import H3Provider
        from .processing.utilities import getVersionH3Bindings
    elif H3_VERSION.startswith('3'):
        from .processing.v3.provider import H3Provider
        from .processing.v3.utilities import getVersionH3Bindings
    else:
        raise RuntimeError(f'Unsupported H3 lib version: \'{H3_VERSION}\'. Supported versions: v4.x or v3.x')
else:
    pass


def classFactory(iface):
    return H3Toolkit(iface)


class H3Toolkit:
    pluginName = 'H3 Toolkit'
    pluginIconPath = os.path.join(os.path.dirname(__file__), 'h3_logo.svg')

    def __init__(self, iface, is_h3lib_present=IS_H3_PRESENT):
        self.iface = iface
        self.provider = None
        self.menuName = None
        self.isH3LibPresent = is_h3lib_present
        self.h3LibVersions = getVersionH3Bindings() if self.isH3LibPresent else None

    def initProcessing(self):
        self.provider = H3Provider(self.pluginIconPath)
        print(self.pluginIconPath)
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
              To start using the plugin you have to install the H3 Library for Python (<a href="https://h3geo.org/">https://h3geo.org/</a>) available as the PyPi package 'h3'. 
              The plugin is tested with h3 version v4.2.2. However it supports all v4.x and v3.x versions of h3.  
            </p>
            <p>To install h3 in the Python environment of QGIS, try the following command within the <a href="https://docs.qgis.org/3.34/en/docs/user_manual/plugins/python_console.html">QGIS Python Console</a>:</p>
            <pre>!python -m pip install 'h3&gt;=3.0.0'</pre>
            <p> Alternatively you can try the (<a href="https://plugins.qgis.org/plugins/a00_qpip/">QPIP plugin</a>) to install it with a click of a button.<p>
            <p>If the above does not work, please refer to the QGIS documentation on how to install Python packages, and the H3 documentation: <a href="https://h3geo.org/docs/installation">https://h3geo.org/docs/installation</a></p>
            <p>
              <b>WARNING: While h3 is a small package without other Python sub-dependencies, managing dependencies is your responsibility and comes at your own risk. We strive to make it easier, but this does not place any liability on us in case you break your environment. You are in charge, not the plugin. Please be careful and do your due diligence before attempting the above.</b>
            </p>
            <p>
              Once the package install completed, please reload the plugin (or restart QGIS) to start using it.<br><br>
              Enjoy!
            </p>
            '''

        QMessageBox.information(self.iface.mainWindow(), windowTitle, helpString)
