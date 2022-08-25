import os

from qgis.core import QgsProcessingProvider
from qgis.PyQt.QtGui import QIcon

from .algorithms import (
    CreateH3GridProcessingAlgorithm,
    CreateH3GridInsidePolygonsProcessingAlgorithm,
    CountPointsOnH3GridProcessingAlgorithm
)


class H3Provider(QgsProcessingProvider):
    def loadAlgorithms(self, *args, **kwargs):
        self.addAlgorithm(CreateH3GridProcessingAlgorithm())
        self.addAlgorithm(CreateH3GridInsidePolygonsProcessingAlgorithm())
        self.addAlgorithm(CountPointsOnH3GridProcessingAlgorithm())

    def id(self, *args, **kwargs):
        return 'h3'

    def name(self, *args, **kwargs):
        return 'H3'

    def icon(self):
        #TODO: OS agnostic path to the logo. (does not work for Windows)
        return QIcon(os.path.join(os.path.dirname(__file__), '../h3_logo.svg'))
