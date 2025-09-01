import types

from qgis.core import QgsGeometry, QgsFeature, QgsFeatureIterator, QgsAbstractFeatureIterator, QgsFeatureRequest

from h3_toolkit.processing.utilities import (
    yield_singleparts,
    yield_small_polygons,
    yield_singleparts,
    getVersionH3Bindings
)

def test_yield_small_singleparts():
    pass #TODO

def test_yield_small_polygons():

    input_wkts = [
        'Polygon ((0 0, 179 10, 179 0, 0 0))',
        'Polygon ((0 0, 200 10, 200 0, 0 0))',  # length exceeds 180 along y, we expect result to be split
        'Polygon ((0 0, 10 -100, 10 100, 0 0))'
    ]

    input_qgsgeoms = map(QgsGeometry.fromWkt, input_wkts)
    result = yield_small_polygons(input_qgsgeoms)

    assert isinstance(result, types.GeneratorType)

    expected_wkts = [
        'Polygon ((0 0, 179 10, 179 0, 0 0))',
        'Polygon ((100 0, 100 5, 200 10, 200 0, 100 0))',
        'Polygon ((100 5, 100 0, 0 0, 100 5))',
        'Polygon ((0 0, 10 -100, 10 100, 0 0))'
    ]
    result_wkts = list(map(QgsGeometry.asWkt, result))

    assert expected_wkts == result_wkts


def test_yield_singleparts():
    input_wkts = [
        'Polygon ((0 0, 10 10, 10 0, 0 0))',
        'MultiPolygon (((0 0, 10 10, 10 0, 0 0)), ((0 0, -10 -10, -10 0, 0 0)))'
    ]

    features = []
    for geom in map(QgsGeometry.fromWkt, input_wkts):
        feat = QgsFeature()
        feat.setGeometry(geom)
        features.append(feat)

    class FeatIter(QgsAbstractFeatureIterator):
        """A basic feature iterator, for creating a suitable QgsFeatureIterator as input"""

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.iterator = iter(features)

        def nextFeature(self, f):
            feat = next(self.iterator, False)
            if feat:
                f.setGeometry(feat.geometry())
                return True
            else:
                return False

    input_iterator = QgsFeatureIterator(FeatIter(QgsFeatureRequest()))
    result = yield_singleparts(input_iterator)

    assert isinstance(result, types.GeneratorType)

    expected_wkts = [
        'Polygon ((0 0, 10 10, 10 0, 0 0))',
        'Polygon ((0 0, 10 10, 10 0, 0 0))',
        'Polygon ((0 0, -10 -10, -10 0, 0 0))'
    ]
    result_wkts = list(map(QgsGeometry.asWkt, result))

    assert expected_wkts == result_wkts


