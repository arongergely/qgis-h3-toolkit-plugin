import os

from qgis.core import QgsProcessingProvider
from qgis.PyQt.QtGui import QIcon

from .algorithms import (
    CreateH3GridProcessingAlgorithm,
    CreateH3GridInsidePolygonsProcessingAlgorithm,
    CountPointsOnH3GridProcessingAlgorithm
)

class H3Provider(QgsProcessingProvider):
    def __init__(self, iconPath, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.iconPath = iconPath

    def loadAlgorithms(self, *args, **kwargs):
        self.addAlgorithm(CreateH3GridProcessingAlgorithm())
        self.addAlgorithm(CreateH3GridInsidePolygonsProcessingAlgorithm())
        self.addAlgorithm(CountPointsOnH3GridProcessingAlgorithm())

    def id(self, *args, **kwargs):
        return 'h3'

    def name(self, *args, **kwargs):
        return 'H3'

    def svgIconPath(self):
        return self.iconPath

    def icon(self):
        return QIcon(self.svgIconPath())
