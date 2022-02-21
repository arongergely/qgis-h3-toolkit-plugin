from qgis.core import QgsProcessingProvider
from qgis.PyQt.QtGui import QIcon

from .create_h3_grid import CreateH3GridProcessingAlgorithm
from .create_h3_grid_within_polygon import CreateH3GridWithinPolygonProcessingAlgorithm

class H3Provider(QgsProcessingProvider):
    def loadAlgorithms(self, *args, **kwargs):
        self.addAlgorithm(CreateH3GridProcessingAlgorithm())
        self.addAlgorithm(CreateH3GridWithinPolygonProcessingAlgorithm())
        # add additional algorithms here
        # self.addAlgorithm(MyOtherAlgorithm())

    def id(self, *args, **kwargs):
        return 'H3'

    def name(self, *args, **kwargs):
        return 'H3'

    def icon(self):
        return QIcon()#QIcon(os.path.join(os.path.dirname(__file__), 'h3_logo.svg'))