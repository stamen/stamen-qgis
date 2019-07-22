# -*- coding: utf-8 -*-

__author__ = 'Stamen Design LLC'
__date__ = '2019-07-21'
__copyright__ = '(C) 2019 by Stamen Design LLC'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

from qgis.PyQt.QtCore import (QCoreApplication, QVariant)
from qgis.core import (QgsFeature,
                       QgsFeatureRequest,
                       QgsField,
                       QgsFields,
                       QgsGeometry,
                       QgsProcessing,
                       QgsFeatureSink,
                       QgsPointXY,
                       QgsProcessingAlgorithm,
                       QgsProcessingOutputLayerDefinition,
                       QgsProcessingParameterBand,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterField,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterRasterLayer,
                       QgsProcessingParameterString,
                       QgsProcessingParameterVectorLayer,
                       QgsTriangle,
                       QgsVectorLayer,
                       QgsWkbTypes)
import processing


class HullsFromPoints(QgsProcessingAlgorithm):
    """
    This is an example algorithm that takes a vector layer and
    creates a new identical one.

    It is meant to be used as an example of how to create your own
    algorithms and explain methods and variables used to do it. An
    algorithm like this will be available in all elements, and there
    is not need for additional work.

    All Processing algorithms should extend the QgsProcessingAlgorithm
    class.
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    OUTPUT = 'OUTPUT'
    INPUT = 'INPUT'
    FIELD_NAME = 'FIELD_NAME'
    ALPHA = 'ALPHA'

    def initAlgorithm(self, config):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        # We add the input vector features source. It can have any kind of
        # geometry.
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.INPUT,
                self.tr('Input point layer')
            )
        )

        self.addParameter(
            QgsProcessingParameterField(
                self.FIELD_NAME,
                self.tr('Key field'),
                optional=True,
                parentLayerParameterName=self.INPUT
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.ALPHA,
                self.tr('Threshold (0-1, where 1 is equivalent with convex hull)'),
                defaultValue=0.3,
                optional=False,
                maxValue=1.0,
                minValue=0.0,
                type=QgsProcessingParameterNumber.Double
            )
        )

        # We add a feature sink in which to store our processed features (this
        # usually takes the form of a newly created vector layer when the
        # algorithm is run in QGIS).
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Output layer'),
                QgsProcessing.TypeVector
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """

        source = self.parameterAsVectorLayer(parameters, self.INPUT, context)
        key_field_name = self.parameterAsString(parameters, self.FIELD_NAME, context)
        if key_field_name:
            field = source.fields().field(key_field_name)
            key_field_type = field.type()
            key_field_type_name = field.typeName()
        alpha = self.parameterAsDouble(parameters, self.ALPHA, context)
        sink_fields = QgsFields()
        if key_field_name:
            sink_fields.append(QgsField(key_field_name, key_field_type))
        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT, context,
                fields = sink_fields,
                geometryType = QgsWkbTypes.Polygon,
                crs = source.crs())
        points_groups = {}

        # Create a temporary layer for the Delaunay triangles that will form our hulls
        if key_field_name:
            if key_field_type_name == 'int':
                hull_triangles = QgsVectorLayer(f'polygon?field={key_field_name}:integer', 'α-shapes triangles', 'memory')
            elif key_field_type_name == 'double' or key_field_type_name == 'float':
                hull_triangles = QgsVectorLayer(f'polygon?field={key_field_name}:double', 'α-shapes triangles', 'memory')
            else:
                hull_triangles = QgsVectorLayer(f'polygon?field={key_field_name}:string', 'α-shapes triangles', 'memory')
        else:
            hull_triangles = QgsVectorLayer(f'polygon', 'α-shapes triangles', 'memory')
        hull_triangles.startEditing()

        # Extract points from layer, grouped by key
        if key_field_name:
            feedback.pushConsoleInfo(f'Extracting points and grouping by {key_field_name}...')
        else:
            feedback.pushConsoleInfo('Extracting points...')
        for f in source.getFeatures():
            if key_field_name:
                group_key = f.attribute(key_field_name)
            else:
                group_key = None
            points_groups.setdefault(group_key, [])
            points_groups[group_key].append(f.geometry().asPoint())

            if feedback.isCanceled():
                    return {self.OUTPUT: None}

        # Go through each cluster of points and generate Delaunay triangulations.
        # Use these triangulations to generate triangle polygons that will form the
        # α-shapes.
        if key_field_name:
            feedback.pushConsoleInfo(f'Creating Delaunay triangulations, keyed by f{key_field_name}...')
        else:
            feedback.pushConsoleInfo('Creating Delaunay triangulation...')
        for group_key, points_group in points_groups.items():
            tri_polys = QgsGeometry.fromMultiPointXY(points_group).delaunayTriangulation()

            # Go through each triangle in the cluster triangulation.
            # If the circumscribed radius < alpha, we include it in the concave hull.
            #
            # NB: Alpha is expressed as a proportion of the max circumscribed radius length:
            #
            # alpha = 1 means that every triangle will be included in the hull
            # alpha = 0.5 means that only triangles with circumscribed radii that are 50%
            #   as long or shorter than the longest circumscribed radius will be included
            #   in the hull
            # alpha = 0 means that no triangles will be included in the hull
            triangle_vertices = [list(tri_poly.vertices()) for tri_poly in tri_polys.parts()]
            circumscribed_radii = [QgsTriangle(*vertices[0:-1]).circumscribedRadius() for vertices in triangle_vertices]
            max_circumscribed_radius = max(circumscribed_radii)
            sorted_radii = circumscribed_radii.copy()
            sorted_radii.sort()
            expanded_alpha = sorted_radii[round(alpha * len(sorted_radii))]

            for i, vertices in enumerate(triangle_vertices):
                if circumscribed_radii[i] <= expanded_alpha:
                    feature = QgsFeature(sink_fields)
                    feature.setGeometry(QgsGeometry.fromPolygonXY(
                        [[QgsPointXY(vertex) for vertex in vertices]]
                    ))
                    if key_field_name:
                        feature.setAttribute(key_field_name, group_key)
                    hull_triangles.addFeature(feature)

                if feedback.isCanceled():
                    return {self.OUTPUT: None}

        feedback.pushConsoleInfo(f'Committing {hull_triangles.featureCount()} triangles...')
        hull_triangles.commitChanges()

        # Dissolve triangles into hulls
        feedback.pushConsoleInfo('Dissolving triangles into hulls...')
        hulls = processing.run(
            'native:dissolve',
            {
                'INPUT': hull_triangles,
                'FIELD': key_field_name,
                'OUTPUT': 'memory:'
            },
            context = context,
            feedback = feedback
        )['OUTPUT']

        sink.addFeatures(hulls.getFeatures())

        sink.flushBuffer()
        feedback.setProgress(100)

        # Return the results of the algorithm. In this case our only result is
        # the feature sink which contains the processed features, but some
        # algorithms may return multiple feature sinks, calculated numeric
        # statistics, etc. These should all be included in the returned
        # dictionary, with keys matching the feature corresponding parameter
        # or output names.
        return {self.OUTPUT: dest_id}

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'hullsfrompoints'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Create hulls from points')

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr(self.groupId())

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'Vector geometry'

    def shortDescription(self):
        return """\
            This algorithm computes the concave or convex hull of the features\
            in an input layer. If a key field is optionally specified, the\
            algorithm will compute multiple hulls, one for each set of features\
            in the input layer grouped by the field value. For example, if the\
            key field is set to CLUSTER_ID, a new hull will be computed for each\
            set of features that shares the same CLUSTER_ID.\n\n

            The threshold is a ratio that determines the concavity of the computed\
            hulls. 1 is equivalent to the features' convex hull.
        """

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return HullsFromPoints()
