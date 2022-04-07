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
import subprocess
import sys

from qgis.core import Qgis, QgsApplication
from PyQt5 import uic
from PyQt5.QtWidgets import QAction, QMessageBox, QPushButton

from .h3_dependency_guard import IS_H3_PRESENT

if IS_H3_PRESENT:
    from .processing.provider import H3Provider
    from .processing.utilities import getVersionH3Bindings
else:
    pass

def classFactory(iface):
    return H3Toolkit(iface)


H3InstallHelperDialog = uic.loadUi(os.path.join(os.path.dirname(__file__), 'h3InstallHelperDialog.ui'))

class H3Toolkit:
    pluginName = 'H3 Toolkit'

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
        # disconnect signals
        #self.aboutAction.triggered.disconnect()
        #self.installHelpAction.triggered.disconnect()

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
            '''

        QMessageBox.information(self.iface.mainWindow(), windowTitle, aboutString)

    def installHelpWindow(self):
        def setsometext():
            commandOutput = None
            statusMessage = '<b><font color=\"Green\">Successfully ran the install command. Please restart QGIS (or deactivate/activate the plugin) to finish setup.</font></b>'
            try:
                outputBytes = subprocess.check_output(
                    (sys.executable, '-m', 'pip', 'install', 'h3<=3.99'),
                    stderr=subprocess.STDOUT
                )
                commandOutput = outputBytes.decode('utf-8')
            except subprocess.CalledProcessError as e:
                outputUtf8 = e.output.decode('utf-8')
                commandOutput = f'ERROR: return code "{e.returncode}"\n{outputUtf8}'
                statusMessage = '<b><font color=\"Red\">An error occured.</font></b>'

            H3InstallHelperDialog.textEdit.setText(commandOutput)
            H3InstallHelperDialog.labelStatus.setText(statusMessage)

        H3InstallHelperDialog.pushButton.clicked.connect(setsometext)
        return H3InstallHelperDialog.exec()