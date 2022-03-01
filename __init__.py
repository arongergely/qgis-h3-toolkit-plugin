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

from qgis.core import QgsApplication
from PyQt5.QtWidgets import QAction, QMessageBox

from .processing.provider import H3Provider
from .processing.utilities import getVersionH3Bindings

def classFactory(iface):
    return H3Toolbox(iface)


class H3Toolbox:
    pluginName = 'H3 Toolbox'
    def __init__(self, iface):
        self.iface = iface
        self.provider = None

    def initProcessing(self):
        self.provider = H3Provider()
        QgsApplication.processingRegistry().addProvider(self.provider)

    def initGui(self):
        self.initProcessing()

        # About window
        self.aboutAction = QAction('About', self.iface.mainWindow())
        self.iface.addPluginToMenu('H3 Toolbar Plugin', self.aboutAction)
        self.aboutAction.triggered.connect(self.aboutWindow)

    def unload(self):
        QgsApplication.processingRegistry().removeProvider(self.provider)
        self.iface.removePluginMenu('H3 Toolbar Plugin', self.aboutAction)

    def aboutWindow(self):
        windowTitle = f'About {self.pluginName} plugin'
        libversions = getVersionH3Bindings()
        aboutString = f'''
            <h4>Developer</h4>
            <p>
              Aron Gergely</a>
            </p>
            <h4>H3 Library versions</h4>
            <p>
              C: {libversions['c']}<br>
              Python bindings: {libversions['python']}
            </p>
            '''

        QMessageBox.information(self.iface.mainWindow(), windowTitle, aboutString)
