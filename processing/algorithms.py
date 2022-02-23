import json

import h3  # TODO: review any benefits of h3.api.memview_int

from qgis.PyQt.QtCore import QCoreApplication, QVariant
from qgis.core import (
    QgsFeatureSink,
    QgsProcessing,
    QgsProcessingException,
    QgsProcessingAlgorithm,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterNumber,
    QgsProcessingParameterExtent,
    QgsPointXY,
    QgsGeometry,
    QgsFeature,
    QgsField,
    QgsFields,
    QgsCoordinateReferenceSystem,
    QgsWkbTypes,
    QgsFeatureRequest,
    QgsCoordinateTransformContext,
    QgsVectorLayer
)
from qgis import processing

from .utilities import singlepartGeometries


class CreateH3GridWithinPolygonProcessingAlgorithm(QgsProcessingAlgorithm):
    """
    #TODO: docstring
    """

    INPUT = 'INPUT'
    RESOLUTION = 'RESOLUTION'
    OUTPUT = 'OUTPUT'

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return CreateH3GridWithinPolygonProcessingAlgorithm()

    def name(self):
        return 'createh3gridwithinpolygon'

    def displayName(self):
        return self.tr('Create H3 grid within polygon')

    def shortHelpString(self):
        return self.tr('Creates a H3 grid at specific resolution, within Polygon layer')

    # TODO set up help button url
    # def helpUrl(self):
    #    return

    def initAlgorithm(self, config=None):

        inputParam = QgsProcessingParameterFeatureSource(
            self.INPUT,
            self.tr('Input layer'),
            [QgsProcessing.TypeVectorPolygon]
        )

        resolutionParam = QgsProcessingParameterNumber(
                self.RESOLUTION,
                self.tr('Resolution'),
                type=QgsProcessingParameterNumber.Integer,
                minValue=0,
                maxValue=15
            )

        resolutionParam.setHelp(
            '''
            The resolution of the grid, as defined in the H3 standard.
            <br><br>
            Average hexagon edge length at each H3 resolution: 
            <br><br>
            0: 1,107.71259100 km<br>
            1: 418.676005500 km<br>
            2: 158.244655800 km<br>
            3: 59.810857940 km<br>
            4: 22.606379400 km<br>
            5: 8.544408276 km<br>
            6: 3.229482772 km<br>
            7: 1.220629759 km<br>
            8: 0.461354684 km<br>
            9: 0.174375668 km<br>
            10: 0.065907807 km<br>
            11: 0.024910561 km<br>
            12: 0.009415526 km<br>
            13: 0.003559893 km<br>
            14: 0.001348575 km<br>
            15: 0.000509713 km<br>
            '''
        )
        outputParam = QgsProcessingParameterFeatureSink(self.OUTPUT, self.tr('Output layer'))

        self.addParameter(inputParam)
        self.addParameter(resolutionParam)
        self.addParameter(outputParam)

    def processAlgorithm(self, parameters, context, feedback):

        ####################
        # Input Parameters #
        ####################
        source = self.parameterAsSource(
            parameters,
            self.INPUT,
            context
        )

        resolution = self.parameterAsInt(
            parameters,
            self.RESOLUTION,
            context
        )

        # validate source parameter
        if source is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT))

        # validate resolution parameter
        if resolution < 0 or resolution > 15:
            raise QgsProcessingException('Invalid input resolution')

        #############################
        # Output parameters (sinks) #
        #############################

        # Set up output layer fields
        indexField = QgsField(
            name='index',
            type=QVariant.String,
            len=30,
            comment='H3 index')
        fields = QgsFields()
        fields.append(indexField)

        # create sink
        (sink, dest_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            fields,
            QgsWkbTypes.Polygon,
            QgsCoordinateReferenceSystem('EPSG:4326')
        )
        # Raise error if sink not created
        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT))

        ##############
        # Processing #
        ##############

        # If source is not in WGS84, set up the feature request filter to reproject source features on the fly
        featureRequestFilter = QgsFeatureRequest().setDestinationCrs(
            QgsCoordinateReferenceSystem('EPSG:4326'),
            QgsCoordinateTransformContext()
        )

        # warn user if reprojection is necessary
        if source.sourceCrs() != featureRequestFilter.destinationCrs():
            feedback.pushWarning('Input source is not in WGS84 projection. On the fly reprojection will be used.')

        # -------------------------------------------------------------
        # STEP 1: Find indexes of hexagons cells within source features
        # -------------------------------------------------------------
        feedback.pushInfo('Looking up grid cell indexes...')

        hexIndexSet = set()
        for geom in singlepartGeometries(source.getFeatures(request=featureRequestFilter)):
            geoJsonDict = json.loads(geom.asJson())
            newSet = h3.polyfill(geoJsonDict, resolution, geo_json_conformant=True)
            hexIndexSet.update(newSet)

            # Stop if cancel button has been clicked
            if feedback.isCanceled():
                feedback.pushInfo('Processing canceled.')
                break
        else:
            feedback.pushInfo(f'{len(hexIndexSet)} grid cells to create.')

        # -----------------------------------------
        # STEP 2. Generate the grid cell geometries
        # -----------------------------------------
        feedback.pushInfo('Generating grid cells...')

        # For the progress bar
        progressPerHex = 100.0 / len(hexIndexSet) if len(hexIndexSet) > 0 else 0
        currentProgress = 0
        lastProgress = 0

        # Set up template feature
        feature = QgsFeature(fields)

        for i, index in enumerate(hexIndexSet):
            # create hex geometry
            hexVertexCoords = h3.h3_to_geo_boundary(index)
            hexGeometry = QgsGeometry.fromPolygonXY([[QgsPointXY(lon, lat) for lat, lon in hexVertexCoords], ])

            # create hex feature, add to sink
            feature.setGeometry(hexGeometry)
            feature.setAttribute('index', index)
            sink.addFeature(feature, QgsFeatureSink.FastInsert)

            # check and report progress
            currentProgress = int(i * progressPerHex)
            if currentProgress != lastProgress:
                lastProgress = currentProgress
                feedback.setProgress(lastProgress)

            # Stop if cancel button has been clicked
            if feedback.isCanceled():
                feedback.pushInfo('Processing canceled.')
                break
        else:
            feedback.pushInfo('Done.')

        return {self.OUTPUT: dest_id}


class CreateH3GridProcessingAlgorithm(QgsProcessingAlgorithm):
    """
    #TODO: docstring
    """

    EXTENT = 'EXTENT'
    RESOLUTION = 'RESOLUTION'
    OUTPUT = 'OUTPUT'

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return CreateH3GridProcessingAlgorithm()

    def name(self):
        return 'createh3grid'

    def displayName(self):
        return self.tr('Create H3 grid')

    #def group(self):
    #    return self.tr('Grid Creation')

    #def groupId(self):
    #    return 'gridcreation'

    def shortHelpString(self):
        return self.tr('Creates a H3 grid at specific resolution')

    # TODO set up help button url
    # def helpUrl(self):
    #    return

    def initAlgorithm(self, config=None):

        extentParam = QgsProcessingParameterExtent(self.EXTENT, self.tr('Extent'))

        resolutionParam = QgsProcessingParameterNumber(
                self.RESOLUTION,
                self.tr('Resolution'),
                type=QgsProcessingParameterNumber.Integer,
                minValue=0,
                maxValue=15
            )

        resolutionParam.setHelp(
            '''
            The resolution of the grid, as defined in the H3 standard.
            <br><br>
            Average hexagon edge length at each H3 resolution: 
            <br><br>
            0: 1,107.71259100 km<br>
            1: 418.676005500 km<br>
            2: 158.244655800 km<br>
            3: 59.810857940 km<br>
            4: 22.606379400 km<br>
            5: 8.544408276 km<br>
            6: 3.229482772 km<br>
            7: 1.220629759 km<br>
            8: 0.461354684 km<br>
            9: 0.174375668 km<br>
            10: 0.065907807 km<br>
            11: 0.024910561 km<br>
            12: 0.009415526 km<br>
            13: 0.003559893 km<br>
            14: 0.001348575 km<br>
            15: 0.000509713 km<br>
            '''
        )
        outputParam = QgsProcessingParameterFeatureSink(self.OUTPUT, self.tr('Output layer'))

        self.addParameter(extentParam)
        self.addParameter(resolutionParam)
        self.addParameter(outputParam)

    def processAlgorithm(self, parameters, context, feedback):

        ####################
        # Input Parameters #
        ####################
        extent = self.parameterAsExtentGeometry(
            parameters,
            self.EXTENT,
            context,
            QgsCoordinateReferenceSystem('EPSG:4326')
        )

        # validate extent parameter
        if extent is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.EXTENT)) #TODO: is this the correct error?
        elif extent.isGeosValid() is False:
            raise QgsProcessingException('Invalid input extent')
        bbox = extent.boundingBox()
        if bbox.xMinimum() < -180 or bbox.xMaximum() > 180 or bbox.yMinimum() < -90 or bbox.yMaximum() > 90:
            raise QgsProcessingException('Invalid input extent: Larger than WGS84 projection bounds')

        ##############
        # Processing #
        ##############

        # Construct temporary vector layer from the input extent
        inputLayer = QgsVectorLayer('polygon?crs=epsg:4326', 'h3plugin_temp', 'memory')
        feature = QgsFeature()
        feature.setGeometry(extent)
        inputLayer.dataProvider().addFeature(feature)

        # Run "Create H3 grid within polygons"  with the temp layer as input
        grid = processing.run(
            'H3:createh3gridwithinpolygon',
            {
                'INPUT': inputLayer,
                'RESOLUTION': parameters['RESOLUTION'],
                'OUTPUT': parameters['OUTPUT'],
            },
            is_child_algorithm=True,
            context=context,
            feedback=feedback,
        )
        return {self.OUTPUT: grid['OUTPUT']}
