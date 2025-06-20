import json

import h3
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
    QgsCoordinateTransform,
    QgsWkbTypes,
    QgsFeatureRequest,
    QgsCoordinateTransformContext,
    QgsVectorLayer,
    QgsProject,
)
from qgis import processing

from .utilities import yield_small_singleparts


class CreateH3GridInsidePolygonsProcessingAlgorithm(QgsProcessingAlgorithm):
    """
    Processing algorithm to create an H3 grid inside polygons.
    Takes vector layer and resolution as inputs.
    Evaluates H3 grid cells at given resolutions inside polygons of input layer.
    Cells are considered to be 'inside' if their centroid is contained by a polygon.
    Generates the grid cells as polygons with their H3 index in the attribute table.
    Outputs result as a polygon vector layer.
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
        return CreateH3GridInsidePolygonsProcessingAlgorithm()

    def name(self):
        return 'createh3gridinsidepolygons'

    def displayName(self):
        return self.tr('Create H3 grid inside polygons')

    #def group(self):
    #    return self.tr('Grid Creation')

    #def groupId(self):
    #    return 'gridcreation'

    def shortHelpString(self):
        helpString = (
            'Creates H3 grid cells that fit within the input polygons at a specified resolution.<br><br>'
            '<b>Input:</b> Polygon layer (automatically transformed to WGS84 if needed)<br>'
            '<b>Resolution:</b> H3 grid density level (0=largest, 15=smallest)<br>'
            '<b>Output:</b> Polygon layer with H3 indexes as attributes<br><br>'
            'Grid cells are considered <i>inside</i> a polygon if their centroid falls within it.<br><br>'
            '<b>Resolution Reference Table:</b><br>'
            '<table>'
            '  <tr><th>Level</th><th>Avg Edge Length</th></tr>'
            '  <tr><td>0</td><td>1107 km</td></tr>'
            '  <tr><td>1</td><td>418 km</td></tr>'
            '  <tr><td>2</td><td>158 km</td></tr>'
            '  <tr><td>3</td><td>59.8 km</td></tr>'
            '  <tr><td>4</td><td>22.6 km</td></tr>'
            '  <tr><td>5</td><td>8.54 km</td></tr>'
            '  <tr><td>6</td><td>3.23 km</td></tr>'
            '  <tr><td>7</td><td>1.22 km</td></tr>'
            '  <tr><td>8</td><td>461 m</td></tr>'
            '  <tr><td>9</td><td>174 m</td></tr>'
            '  <tr><td>10</td><td>65.9 m</td></tr>'
            '  <tr><td>11</td><td>24.9 m</td></tr>'
            '  <tr><td>12</td><td>9.42 m</td></tr>'
            '  <tr><td>13</td><td>3.56 m</td></tr>'
            '  <tr><td>14</td><td>1.35 m</td></tr>'
            '  <tr><td>15</td><td>0.51 m</td></tr>'
            '</table><br>'
            '<b>Note:</b> Input layers are automatically transformed to WGS84 (EPSG:4326). '
            'Results may be inaccurate for features crossing CRS boundaries (e.g., polar regions or 180th meridian).'
        )
        return self.tr(helpString)

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
            The resolution level of the grid, as defined in the H3 standard.
            <br>
            <table>
              <tr>
                <th>Resolution<br>Level</th>
                <th>Avg. Hexagon<br>Edge Length</th>
              </tr>
              <tr>
                <td style="text-align: center">0</td>
                <td style="text-align: center">1107.71 km</td>
              </tr>
              <tr>
                <td style="text-align: center">1</td>
                <td style="text-align: center">418.68 km</td>
              </tr>
              <tr>
                <td style="text-align: center">2</td>
                <td style="text-align: center">158.24 km</td>
              </tr>
              <tr>
                <td style="text-align: center">3</td>
                <td style="text-align: center">59.81 km</td>
              </tr>
              <tr>
                <td style="text-align: center">4</td>
                <td style="text-align: center">22.61 km</td>
              </tr>
              <tr>
                <td style="text-align: center">5</td>
                <td style="text-align: center">8.54 km</td>
              </tr>
              <tr>
                <td style="text-align: center">6</td>
                <td style="text-align: center">3.23 km</td>
              </tr>
              <tr>
                <td style="text-align: center">7</td>
                <td style="text-align: center">1.22 km</td>
              </tr>
              <tr>
                <td style="text-align: center">8</td>
                <td style="text-align: center">461.35 m</td>
              </tr>
              <tr>
                <td style="text-align: center">9</td>
                <td style="text-align: center">174.38 m</td>
              </tr>
              <tr>
                <td style="text-align: center">10</td>
                <td style="text-align: center">65.91 m</td>
              </tr>
              <tr>
                <td style="text-align: center">11</td>
                <td style="text-align: center">24.91 m</td>
              </tr>
              <tr>
                <td style="text-align: center">12</td>
                <td style="text-align: center">9.42 m</td>
              </tr>
              <tr>
                <td style="text-align: center">13</td>
                <td style="text-align: center">3.56 m</td>
              </tr>
              <tr>
                <td style="text-align: center">14</td>
                <td style="text-align: center">1.35 m</td>
              </tr>
              <tr>
                <td style="text-align: center">15</td>
                <td style="text-align: center">0.51 m</td>
              </tr>
            </table>
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
        # looping on geometries, yielding them as single-part, with any overly-large geoms split into two.
        # The latter is to avoid h3.polyfill() inverting geom's domain along lon,
        # when geom's length along lon > 180  (WGS84)
        for geom in yield_small_singleparts(source.getFeatures(request=featureRequestFilter)):
            """
            polys = []
            if geom.isMultipart():
                for part in geom.asMultiPolygon():
                    polypart = []
                    for ring in part:
                        polypart.append([(p.y(), p.x()) for p in ring])
                    polys.append(h3.LatLngPoly(*polypart))
                poly_obj = h3.LatLngMultiPoly(*polys)
            else:
                for ring in geom.asPolygon():
                    polys.append([(p.y(), p.x()) for p in ring])
                poly_obj = h3.LatLngPoly(*polys)

            newSet = h3.h3shape_to_cells(poly_obj, resolution)
            """
            polys = []
            for ring in geom.asPolygon():
                polys.append([(p.y(), p.x()) for p in ring])
            poly_obj = h3.LatLngPoly(*polys)
            newSet = h3.h3shape_to_cells(poly_obj, resolution)
            hexIndexSet.update(newSet)

            # Stop if cancel button has been clicked
            if feedback.isCanceled():
                feedback.pushInfo('Processing canceled.')
                break
        else:
            hexIndexSetLenth = len(hexIndexSet)
            if hexIndexSetLenth > 0:
                feedback.pushInfo(f'{hexIndexSetLenth} grid cells to create.')
            else:
                feedback.pushWarning(
                    '0 grid cells to create. '
                    'You may need to enlarge the input area or increase the resolution.'
                )
                feedback.pushWarning('Empty Output.')
                return {self.OUTPUT: dest_id}

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
            hexVertexCoords = h3.cell_to_boundary(index)
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
    Processing algorithm to create an H3 grid inside an extent.
    Takes extent and resolution as inputs. Creates an in-memory polygon vector layer from the extent, then
    calls `CreateH3GridInsidePolygonsProcessingAlgorithm` as child algorithm with the in-memory layer
    and the resolution as inputs.

    Outputs the child algorithm's output.

    Note:
    Child algorithm carries out the actual processing;
    see `CreateH3GridInsidePolygonsProcessingAlgorithm` for details
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
        helpString = (
            'Generates H3 grid cells within a specified geographic extent at a chosen resolution.<br><br>'
            '<b>Input Extent:</b> Geographic area to cover (auto-detected from project or manually specified)<br>'
            '<b>Resolution:</b> H3 grid density level (0=largest, 15=smallest)<br>'
            '<b>Output:</b> Polygon layer with H3 indexes as attributes<br><br>'
            'This tool internally creates a temporary polygon from the input extent and uses the same '
            'processing logic as the <i>Create H3 Grid Inside Polygons</i> tool.<br><br>'
            'See resolution reference table in <i>Create H3 Grid Inside Polygons</i> help for detailed cell sizes.'
        )
        return self.tr(helpString)

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
            The resolution level of the grid, as defined in the H3 standard.
            <br>
            <table>
              <tr>
                <th>Resolution<br>Level</th>
                <th>Avg. Hexagon<br>Edge Length</th>
              </tr>
              <tr>
                <td style="text-align: center">0</td>
                <td style="text-align: center">1107.71 km</td>
              </tr>
              <tr>
                <td style="text-align: center">1</td>
                <td style="text-align: center">418.68 km</td>
              </tr>
              <tr>
                <td style="text-align: center">2</td>
                <td style="text-align: center">158.24 km</td>
              </tr>
              <tr>
                <td style="text-align: center">3</td>
                <td style="text-align: center">59.81 km</td>
              </tr>
              <tr>
                <td style="text-align: center">4</td>
                <td style="text-align: center">22.61 km</td>
              </tr>
              <tr>
                <td style="text-align: center">5</td>
                <td style="text-align: center">8.54 km</td>
              </tr>
              <tr>
                <td style="text-align: center">6</td>
                <td style="text-align: center">3.23 km</td>
              </tr>
              <tr>
                <td style="text-align: center">7</td>
                <td style="text-align: center">1.22 km</td>
              </tr>
              <tr>
                <td style="text-align: center">8</td>
                <td style="text-align: center">461.35 m</td>
              </tr>
              <tr>
                <td style="text-align: center">9</td>
                <td style="text-align: center">174.38 m</td>
              </tr>
              <tr>
                <td style="text-align: center">10</td>
                <td style="text-align: center">65.91 m</td>
              </tr>
              <tr>
                <td style="text-align: center">11</td>
                <td style="text-align: center">24.91 m</td>
              </tr>
              <tr>
                <td style="text-align: center">12</td>
                <td style="text-align: center">9.42 m</td>
              </tr>
              <tr>
                <td style="text-align: center">13</td>
                <td style="text-align: center">3.56 m</td>
              </tr>
              <tr>
                <td style="text-align: center">14</td>
                <td style="text-align: center">1.35 m</td>
              </tr>
              <tr>
                <td style="text-align: center">15</td>
                <td style="text-align: center">0.51 m</td>
              </tr>
            </table>
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
            'h3:createh3gridinsidepolygons',
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


class CountPointsOnH3GridProcessingAlgorithm(QgsProcessingAlgorithm):
    #TODO:
    # - status bar
    # - more feedback info to user
    """
    Count points to H3 grid processing algorithm.

    Takes point vector layer as input.
    Counts points falling within H3 grid cells at given resolution

    Generates the grid cells as polygons with their H3 index and point counts in the attribute table.
    Outputs result as a polygon vector layer.
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
        return CountPointsOnH3GridProcessingAlgorithm()

    def name(self):
        return 'countpointson3Grid'

    def displayName(self):
        return self.tr('Count points on H3 Grid')

    # def group(self):
    #    return self.tr('Grid Creation')

    # def groupId(self):
    #    return 'gridcreation'

    def shortHelpString(self):
        helpString = (
            'Aggregates point features into H3 grid cells and counts points per cell.<br><br>'
            '<b>Input:</b> Point layer (automatically transformed to WGS84 if needed)<br>'
            '<b>Resolution:</b> H3 grid density level (0=largest, 15=smallest)<br>'
            '<b>Output:</b> Polygon layer of H3 index geometry with point counts as attributes<br><br>'
            'Grid cells are generated where points exist. Each cell shows total points within its boundaries.<br><br>'
            'See resolution reference table in <i>Create H3 Grid Inside Polygons</i> help for detailed cell sizes.<br><br>'
            '<b>Note:</b> Input points are transformed to WGS84 (EPSG:4326). '
            'Results may be inaccurate for features crossing CRS boundaries.'
        )
        return self.tr(helpString)

    # TODO set up help button url
    # def helpUrl(self):
    #    return

    def initAlgorithm(self, config=None):
        #extentParam = QgsProcessingParameterExtent(self.EXTENT, self.tr('Extent'))
        pointlayerParam = QgsProcessingParameterFeatureSource(
            self.INPUT,
            self.tr('Input point layer'),
            [QgsProcessing.TypeVectorPoint]
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
            The resolution level of the grid, as defined in the H3 standard.
            <br>
            <table>
              <tr>
                <th>Resolution<br>Level</th>
                <th>Avg. Hexagon<br>Edge Length</th>
              </tr>
              <tr>
                <td style="text-align: center">0</td>
                <td style="text-align: center">1107.71 km</td>
              </tr>
              <tr>
                <td style="text-align: center">1</td>
                <td style="text-align: center">418.68 km</td>
              </tr>
              <tr>
                <td style="text-align: center">2</td>
                <td style="text-align: center">158.24 km</td>
              </tr>
              <tr>
                <td style="text-align: center">3</td>
                <td style="text-align: center">59.81 km</td>
              </tr>
              <tr>
                <td style="text-align: center">4</td>
                <td style="text-align: center">22.61 km</td>
              </tr>
              <tr>
                <td style="text-align: center">5</td>
                <td style="text-align: center">8.54 km</td>
              </tr>
              <tr>
                <td style="text-align: center">6</td>
                <td style="text-align: center">3.23 km</td>
              </tr>
              <tr>
                <td style="text-align: center">7</td>
                <td style="text-align: center">1.22 km</td>
              </tr>
              <tr>
                <td style="text-align: center">8</td>
                <td style="text-align: center">461.35 m</td>
              </tr>
              <tr>
                <td style="text-align: center">9</td>
                <td style="text-align: center">174.38 m</td>
              </tr>
              <tr>
                <td style="text-align: center">10</td>
                <td style="text-align: center">65.91 m</td>
              </tr>
              <tr>
                <td style="text-align: center">11</td>
                <td style="text-align: center">24.91 m</td>
              </tr>
              <tr>
                <td style="text-align: center">12</td>
                <td style="text-align: center">9.42 m</td>
              </tr>
              <tr>
                <td style="text-align: center">13</td>
                <td style="text-align: center">3.56 m</td>
              </tr>
              <tr>
                <td style="text-align: center">14</td>
                <td style="text-align: center">1.35 m</td>
              </tr>
              <tr>
                <td style="text-align: center">15</td>
                <td style="text-align: center">0.51 m</td>
              </tr>
            </table>
            '''
        )
        outputParam = QgsProcessingParameterFeatureSink(self.OUTPUT, self.tr('Output layer'))
        self.addParameter(pointlayerParam)
        self.addParameter(resolutionParam)
        self.addParameter(outputParam)

    def processAlgorithm(self, parameters, context, feedback):
        ####################
        # Input Parameters #
        ####################

        pointSource = self.parameterAsSource(
            parameters,
            self.INPUT,
            context
        )

        resolution = self.parameterAsInt(
            parameters,
            self.RESOLUTION,
            context
        )

        # Set up output layer fields
        indexField = QgsField(
            name='index',
            type=QVariant.String,
            len=30,
            comment='H3 index')
        countField = QgsField(
            name='count',
            type=QVariant.Int,
            comment='Point count'
        )
        fields = QgsFields()
        fields.append(indexField)
        fields.append(countField)

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

        sourceCrs = pointSource.sourceCrs()
        transformer = QgsCoordinateTransform(
            sourceCrs,
            QgsCoordinateReferenceSystem('EPSG:4326'),
            QgsProject.instance()
        )

        # -------------------------------
        # STEP 1. Index points on H3 grid
        # -------------------------------
        h3Indexed = []
        for f in pointSource.getFeatures():
            point = f.geometry().asPoint()
            point_wgs84 = transformer.transform(point)
            idx = h3.latlng_to_cell(point_wgs84.y(), point_wgs84.x(), resolution)
            h3Indexed.append(idx)

        # ----------------------------------
        # Step 2. Count records per H3 index
        # ----------------------------------
        counts = dict()
        for i in h3Indexed:
            counts[i] = counts.get(i, 0) + 1

        # ----------------------------------------------
        # Step 3. Generate h3 cell geometries and output
        # ----------------------------------------------
        # Set up template feature
        feature = QgsFeature(fields)
        for k, v in counts.items():
            hexVertexCoords = h3.cell_to_boundary(k)
            hexGeometry = QgsGeometry.fromPolygonXY([[QgsPointXY(lon, lat) for lat, lon in hexVertexCoords], ])
            # create hex feature, add to sink
            feature.setGeometry(hexGeometry)
            feature.setAttributes([k, v])
            sink.addFeature(feature, QgsFeatureSink.FastInsert)

        return {self.OUTPUT: dest_id}
