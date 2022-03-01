from qgis.core import QgsProcessingProvider
from qgis.PyQt.QtGui import QIcon

from .algorithms import (
    CreateH3GridProcessingAlgorithm,
    CreateH3GridInsidePolygonsProcessingAlgorithm
)


class H3Provider(QgsProcessingProvider):
    def loadAlgorithms(self, *args, **kwargs):
        self.addAlgorithm(CreateH3GridProcessingAlgorithm())
        self.addAlgorithm(CreateH3GridInsidePolygonsProcessingAlgorithm())
        # add additional algorithms here
        # self.addAlgorithm(MyOtherAlgorithm())

    def id(self, *args, **kwargs):
        return 'h3'

    def name(self, *args, **kwargs):
        return 'H3'

    def icon(self):
        return QIcon()#QIcon(os.path.join(os.path.dirname(__file__), 'h3_logo.svg'))