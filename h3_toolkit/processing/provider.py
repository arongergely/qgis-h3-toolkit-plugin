import os

from qgis.core import QgsProcessingProvider
from qgis.PyQt.QtGui import QIcon
 
from .algorithms import (
    CreateH3GridProcessingAlgorithm,
    CreateH3GridInsidePolygonsProcessingAlgorithm,
    CountPointsOnH3GridProcessingAlgorithm,
)

class H3Provider(QgsProcessingProvider):

    def __init__(self, iconPath: str):
        super().__init__()
        if not os.path.isfile(iconPath):
            raise FileNotFoundError(f'H3Provider: icon file not found: {iconPath}')
        self._iconPath = iconPath
        # Cache the QIcon, not to reconstruct it on every call to icon()
        self._icon = QIcon(self._iconPath)

    def loadAlgorithms(self):
        self.addAlgorithm(CreateH3GridProcessingAlgorithm())
        self.addAlgorithm(CreateH3GridInsidePolygonsProcessingAlgorithm())
        self.addAlgorithm(CountPointsOnH3GridProcessingAlgorithm())

    def id(self):
        return 'h3'

    def name(self):
        return 'H3'

    def svgIconPath(self):
        return self._iconPath

    def svgIconPath(self):
        return self._iconPath
