from .AlgorithmGenerator import Algorithm
from ..helpers import Utilities

from qgis.core import (QgsProcessing,
                       QgsProcessingException,
                       QgsProcessingParameterRasterLayer,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterBoolean,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterRasterDestination,
                       QgsProcessingParameterFileDestination)

import processing

class StagedAlgorithm(Algorithm):

    def initAlgorithm(self, config=None):
        pass

    def processAlgorithm(self, parameters, context, feedback):
        return {}