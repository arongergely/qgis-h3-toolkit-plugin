import h3
from collections import Counter

from qgis.PyQt.QtCore import QCoreApplication, QMetaType

from qgis.core import (
    QgsFeatureSink,
    QgsProcessing,
    QgsProcessingException,
    QgsProcessingAlgorithm,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterNumber,
    QgsProcessingParameterExtent,
    QgsFeature,
    QgsField,
    QgsFields,
    QgsCoordinateReferenceSystem,
    QgsWkbTypes,
    QgsFeatureRequest,
    QgsVectorLayer,
)
from qgis import processing

from .utilities import yield_small_singleparts, cell_to_qgs_geometry


def _resolution_table_html() -> str:
    """
    Return the H3 resolution reference table as an HTML string.
    Used by setHelp() in every processing algorithm class so the table is defined in exactly one place.
    """
    rows = [
        ('0',  '1107.71 km'),
        ('1',  '418.68 km'),
        ('2',  '158.24 km'),
        ('3',  '59.81 km'),
        ('4',  '22.61 km'),
        ('5',  '8.54 km'),
        ('6',  '3.23 km'),
        ('7',  '1.22 km'),
        ('8',  '461.35 m'),
        ('9',  '174.38 m'),
        ('10', '65.91 m'),
        ('11', '24.91 m'),
        ('12', '9.42 m'),
        ('13', '3.56 m'),
        ('14', '1.35 m'),
        ('15', '0.51 m'),
    ]
    header = (
        '<table>'
        '<tr>'
        '<th>Resolution<br>Level</th>'
        '<th>Avg. Hexagon<br>Edge Length</th>'
        '</tr>'
    )
    body = ''.join(
        f'<tr>'
        f'<td style="text-align: center">{res}</td>'
        f'<td style="text-align: center">{edge}</td>'
        f'</tr>'
        for res, edge in rows
    )
    return f'The resolution level of the grid, as defined in the H3 standard.<br>{header}{body}</table>'


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

    def __init__(self):
      super().__init__()

    def name(self):
      return 'createh3gridinsidepolygons'

    def displayName(self):
      return self.tr('Create H3 grid inside polygons')
    
    def tr(self, string):
      """
      Returns a translatable string with the self.tr() function.
      """
      return QCoreApplication.translate('Processing', string)

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
   
    def helpUrl(self):
      return 'https://github.com/arongergely/qgis-h3-toolkit-plugin'

    def createInstance(self):
      return CreateH3GridInsidePolygonsProcessingAlgorithm()

    def checkParameterValues(self, parameters, context):
      source = self.parameterAsSource(parameters, self.INPUT, context)
      resolution = self.parameterAsInt(parameters, self.RESOLUTION, context)

      # Validate source parameter
      if source is None or not source.hasFeatures():
          return False, self.tr('Invalid input source.')
      
      # Validate resolution parameter
      if resolution < 0 or resolution > 15:
          return False, self.tr('Invalid input resolution')

      return super().checkParameterValues(parameters, context)

    def initAlgorithm(self, config=None):
      inputParam = QgsProcessingParameterFeatureSource(name=self.INPUT, description=self.tr('Input layer'), types=[QgsProcessing.TypeVectorPolygon], optional=False)
      resolutionParam = QgsProcessingParameterNumber(name=self.RESOLUTION, description=self.tr('Resolution'), type=QgsProcessingParameterNumber.Integer, minValue=0, maxValue=15)
      resolutionParam.setHelp(help=_resolution_table_html())
      outputParam = QgsProcessingParameterFeatureSink(name=self.OUTPUT, description=self.tr('Output layer'))

      self.addParameter(inputParam)
      self.addParameter(resolutionParam)
      self.addParameter(outputParam)

    def processAlgorithm(self, parameters, context, feedback):
      ####################
      # Input Parameters #
      ####################
      source = self.parameterAsSource(parameters, self.INPUT, context)
      resolution = self.parameterAsInt(parameters, self.RESOLUTION, context)

      #############################
      # Output parameters (sinks) #
      #############################

      # Set up output layer fields
      indexField = QgsField(name='index', type=QMetaType.Type.QString, len=30, comment='H3 index')
      fields = QgsFields()
      fields.append(indexField)

      # create sink
      (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT, context, fields, QgsWkbTypes.Polygon, QgsCoordinateReferenceSystem('EPSG:4326'))
      # Raise error if sink not created
      if sink is None:
          raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT))

      ##############
      # Processing #
      ##############
      
      # If source is not in WGS84, set up the feature request filter to reproject source features on the fly
      featureRequestFilter = QgsFeatureRequest().setDestinationCrs(QgsCoordinateReferenceSystem('EPSG:4326'), context.transformContext())

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
          polys = [[(p.y(), p.x()) for p in ring] for ring in geom.asPolygon()]
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
      progressPerHex = 100.0 / hexIndexSetLenth if hexIndexSetLenth > 0 else 0
      currentProgress = 0
      lastProgress = 0

      # Set up template feature
      feature = QgsFeature(fields)

      for i, index in enumerate(hexIndexSet):
          # create hex geometry
          hexGeometry = cell_to_qgs_geometry(index)

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
    Note: This is a child algorithm carries out the actual processing;
    See the parent `CreateH3GridInsidePolygonsProcessingAlgorithm` for details
    """

    EXTENT = 'EXTENT'
    RESOLUTION = 'RESOLUTION'
    OUTPUT = 'OUTPUT'

    def __init__(self):
      super().__init__()

    def name(self):
      return 'createh3grid'

    def displayName(self):
      return self.tr('Create H3 grid')

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

    def helpUrl(self):
      return 'https://github.com/arongergely/qgis-h3-toolkit-plugin'

    def tr(self, string):
      """
      Returns a translatable string with the self.tr() function.
      """
      return QCoreApplication.translate('Processing', string)
    
    def createInstance(self):
      return CreateH3GridProcessingAlgorithm()
    
    def checkParameterValues(self, parameters, context):
      extent = self.parameterAsExtentGeometry(parameters, self.EXTENT, context, QgsCoordinateReferenceSystem('EPSG:4326'))

      # validate extent parameter
      if extent is None or extent.isNull():
          return False, self.tr('No extent provided.')
      
      elif not extent.isGeosValid():
          return False, self.tr('Invalid input extent')
              
      bbox = extent.boundingBox()
      if bbox.xMinimum() < -180 or bbox.xMaximum() > 180 or bbox.yMinimum() < -90 or bbox.yMaximum() > 90:
          return False, self.tr('Invalid input extent: Larger than WGS84 projection bounds')

      return super().checkParameterValues(parameters, context)
       
    def initAlgorithm(self, config=None):
      extentParam = QgsProcessingParameterExtent(name=self.EXTENT, description=self.tr('Extent'))
      resolutionParam = QgsProcessingParameterNumber(name=self.RESOLUTION, description=self.tr('Resolution'), type=QgsProcessingParameterNumber.Integer,  minValue=0, maxValue=15)
      resolutionParam.setHelp(help=_resolution_table_html())
      outputParam = QgsProcessingParameterFeatureSink(name=self.OUTPUT, description=self.tr('Output layer'), type=QgsProcessing.TypeVectorPolygon)

      self.addParameter(extentParam)
      self.addParameter(resolutionParam)
      self.addParameter(outputParam)

    def processAlgorithm(self, parameters, context, feedback):
      ####################
      # Input Parameters #
      ####################
      extent = self.parameterAsExtentGeometry(parameters, self.EXTENT, context, QgsCoordinateReferenceSystem('EPSG:4326'))

      ##############
      # Processing #
      ##############

      # Construct temporary vector layer from the input extent
      # Use addFeatures (plural) which is the provider's batch method and returns bool
      inputLayer = QgsVectorLayer('polygon', 'h3plugin_temp', 'memory')
      inputLayer.setCrs(srs=QgsCoordinateReferenceSystem('EPSG:4326'))
      provider = inputLayer.dataProvider()
      feature = QgsFeature()
      feature.setGeometry(extent)
      provider.addFeatures([feature])

      # Run "Create H3 grid within polygons" with the temp layer as input
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

  def __init__(self):
    super().__init__()

  def name(self):
    return 'countpointsonh3grid'

  def displayName(self):
    return self.tr('Count points on H3 Grid')

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
  
  def helpUrl(self):
    return 'https://github.com/arongergely/qgis-h3-toolkit-plugin'

  def tr(self, string):
    """
    Returns a translatable string with the self.tr() function.
    """
    return QCoreApplication.translate('Processing', string)
  
  def createInstance(self):
    return CountPointsOnH3GridProcessingAlgorithm()
  
  def checkParameterValues(self, parameters, context):
    pointSource = self.parameterAsSource(parameters, self.INPUT, context)
    resolution = self.parameterAsInt(parameters, self.RESOLUTION, context)

    # Validate resolution parameter
    if resolution < 0 or resolution > 15:
        return False, self.tr('Invalid input resolution')

    # Validate source parameter
    if pointSource is None or not pointSource.hasFeatures():
        return False, self.tr('Invalid input source.')

    return super().checkParameterValues(parameters, context)
  
  def initAlgorithm(self, config=None):
    pointlayerParam = QgsProcessingParameterFeatureSource(name=self.INPUT, description=self.tr('Input point layer'), types=[QgsProcessing.TypeVectorPoint], optional=False)
    resolutionParam = QgsProcessingParameterNumber(name=self.RESOLUTION, description=self.tr('Resolution'), type=QgsProcessingParameterNumber.Integer, minValue=0, maxValue=15)
    resolutionParam.setHelp(help=_resolution_table_html())
    outputParam = QgsProcessingParameterFeatureSink(name=self.OUTPUT, description=self.tr('Output layer'), type=QgsProcessing.TypeVectorPolygon)

    self.addParameter(pointlayerParam)
    self.addParameter(resolutionParam)
    self.addParameter(outputParam)

  def processAlgorithm(self, parameters, context, feedback):
    ####################
    # Input Parameters #
    ####################
    pointSource = self.parameterAsSource(parameters, self.INPUT, context)
    resolution = self.parameterAsInt(parameters, self.RESOLUTION, context)
    
    # Set up output layer fields
    indexField = QgsField(name='index', type=QMetaType.Type.QString, len=30, comment='H3 index')
    countField = QgsField(name='count', type=QMetaType.Type.Int, comment='Point count')
    fields = QgsFields()
    fields.append(indexField)
    fields.append(countField)

    # create sink
    (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT, context, fields, QgsWkbTypes.Polygon, QgsCoordinateReferenceSystem('EPSG:4326'))
    # Raise error if sink not created
    if sink is None:
        raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT))

    ####################
    #    Processing    #
    ####################

    featureRequestFilter = QgsFeatureRequest().setDestinationCrs(QgsCoordinateReferenceSystem('EPSG:4326'), context.transformContext())

    # warn user if reprojection is necessary
    if pointSource.sourceCrs() != featureRequestFilter.destinationCrs():
        feedback.pushWarning('Input source is not in WGS84 projection. On the fly reprojection will be used.')

    # -----------------------------------------------
    # STEP 1. index each point and count in one pass.
    # -----------------------------------------------

    feature_count = pointSource.featureCount()
    progress_step = 100.0 / feature_count if feature_count > 0 else 0

    counts: Counter = Counter()
    for i, f in enumerate(pointSource.getFeatures(request=featureRequestFilter)):
        point = f.geometry().asPoint()
        idx = h3.latlng_to_cell(point.y(), point.x(), resolution)
        counts[idx] += 1

        feedback.setProgress(int(i * progress_step))
        
        if feedback.isCanceled():
            feedback.pushInfo('Processing canceled.')
            break

    # ----------------------------------------------
    # Step 2. Generate h3 cell geometries and output
    # ----------------------------------------------
    # Set up template feature
    feature = QgsFeature(fields)

    for index, count in counts.items():
        hexGeometry = cell_to_qgs_geometry(index)

        # create hex feature, add to sink
        feature.setGeometry(hexGeometry)
        feature.setAttributes([index, count])
        sink.addFeature(feature, QgsFeatureSink.FastInsert)

        # Stop if cancel button has been clicked
        if feedback.isCanceled():
            feedback.pushInfo('Processing canceled.')
            break
    else:
        feedback.pushInfo('Done.')

    return {self.OUTPUT: dest_id}
