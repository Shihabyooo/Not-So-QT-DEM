#Probably a waste to have this tool, as it simply just calls QGIS/GDAL's Polygonize.
#Implies 8 connectedness and name of field = ("value")

from .AlgorithmGenerator import Algorithm
from qgis.core import QgsProcessing, QgsProcessingException, QgsProcessingParameterRasterLayer, QgsProcessingParameterVectorDestination
import processing

class StagedAlgorithm(Algorithm):
    WATERHSED_GRID = "grid"
    WATERSHED_SHP = "shp"

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterRasterLayer(name = self.WATERHSED_GRID,
                                                            description = "Watershed grid",
                                                            optional = False,
                                                            defaultValue = [QgsProcessing.TypeRaster]))

        self.addParameter(QgsProcessingParameterVectorDestination(name = self.WATERSHED_SHP,
                                                                  description = "Watershed shapefile"))

    def processAlgorithm(self, parameters, context, feedback):
        #TODO handle input error exceptions.
        watershedGrid = self.parameterAsRasterLayer(parameters, self.WATERHSED_GRID, context)
        watershedSHP = self.parameterAsOutputLayer(parameters, self.WATERSHED_SHP, context)

        polygonizeInputDict = {"INPUT" : watershedGrid,
                               "BAND" : 1,
                               "FIELD" : "value",
                               "EIGHT_CONNECTEDNESS": True,
                               "OUTPUT" : watershedSHP}
        processing.run("gdal:polygonize", polygonizeInputDict)
        
        return {"Watershed shape" : watershedSHP}