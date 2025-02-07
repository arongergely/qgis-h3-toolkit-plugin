from typing import Iterator

from qgis.core import (
    QgsGeometry,
    QgsPointXY,
    QgsFeatureIterator
)
import h3


def yield_small_singleparts(feature_iterator: QgsFeatureIterator) -> Iterator[QgsGeometry]:
    return yield_small_polygons(yield_singleparts(feature_iterator))

def yield_small_polygons(iterator: Iterator[QgsGeometry]) -> Iterator[QgsGeometry]:
    """
    Generator function. Takes a QgsFeatureIterator and yield its features, splitting them
    if their length along x is larger than 180. The split geometries are yielded one-by-one as single part.

    Used for splitting large polygons for the h3 lib's `polyfill`, to avoid it inverting the extent.
    """
    for geom in iterator:
        bbox = geom.boundingBox()
        x_diff = abs(bbox.xMaximum() - bbox.xMinimum())
        if x_diff > 180:
            splitter_line = [
                QgsPointXY(bbox.xMinimum() + x_diff / 2, -90),
                QgsPointXY(bbox.xMinimum() + x_diff / 2, 90)
            ]
            op_result, split_geoms_list, topo_list = geom.splitGeometry(splitter_line, False, False)
            for g in split_geoms_list:
                yield g
        else:
            yield geom

def yield_singleparts(feature_iterator: QgsFeatureIterator) -> Iterator[QgsGeometry]:
    """
    Generator function. Takes a QgsFeatureIterator and yields the geometry of each feature as QgsGeometry.
    In case of multipart geometries, yields each part as a separate singlepart geometry.
    """
    for f in feature_iterator:
        geom = f.geometry()
        if geom.isMultipart():
            for part in geom.asGeometryCollection():
                yield part
        else:
            yield geom


def getVersionH3Bindings():
    return h3.versions()
