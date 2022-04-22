from typing import Iterator

from qgis.core import (
    QgsGeometry,
    QgsFeatureIterator
)
import h3


def singlepartGeometries(featureIterator: QgsFeatureIterator) -> Iterator[QgsGeometry]:
    """
    Generator function. Takes a QgsFeatureIterator and yields the geometry of each feature as QgsGeometry.
    In case of multipart geometries, yields each part as a separate singlepart geometry.
    """
    for f in featureIterator:
        geom = f.geometry()
        if geom.isMultipart():
            for part in geom.asGeometryCollection():
                yield part
        else:
            yield geom


def getVersionH3Bindings():
    return h3.versions()
