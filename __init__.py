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


def classFactory(iface):
    return H3Toolbox()


class H3Toolbox:
    def __init__(self):
        self.provider = None

    def initProcessing(self):
        self.provider = H3Provider()
        QgsApplication.processingRegistry().addProvider(self.provider)

    def initGui(self):
        self.initProcessing()

    def unload(self):
        QgsApplication.processingRegistry().removeProvider(self.provider)
