import json

import h3

from qgis.PyQt.QtCore import QCoreApplication, QVariant
from qgis.core import (
    QgsFeatureSink,
    QgsProcessingException,
    QgsProcessingAlgorithm,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterNumber,
    QgsProcessingParameterExtent,
    QgsPointXY,
    QgsGeometry,
    QgsFeature,
    QgsField,
    QgsFields,
    QgsCoordinateReferenceSystem,
    QgsWkbTypes
)


class CreateH3GridProcessingAlgorithm(QgsProcessingAlgorithm):
    """
    #TODO: docstring
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.
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

        resolution = self.parameterAsInt(
            parameters,
            self.RESOLUTION,
            context
        )

        # validate extent parameter
        if extent is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.EXTENT))
        elif extent.isGeosValid() is False:
            raise QgsProcessingException('Invalid input extent')

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

        # Send some information to the user
        #feedback.pushInfo('CRS is {}'.format(QgsCoordinateReferenceSystem('EPSG:4326')))

        ##############
        # Processing #
        ##############

        #Get indeces H3 hexagons within extent
        feedback.pushInfo('Looking up hexagons within extent...')
        hexIndices = h3.polyfill(
            json.loads(extent.asJson()),
            resolution,
            geo_json_conformant=True
        )

        # Set up template feature
        feature = QgsFeature(fields)

        # For the progress bar
        progressPerHex = 100.0 / len(hexIndices) if len(hexIndices) > 0 else 0
        currentProgress = 0
        lastProgress = 0

        feedback.pushInfo('Generating grid layer...')
        for i, index in enumerate(hexIndices):
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
