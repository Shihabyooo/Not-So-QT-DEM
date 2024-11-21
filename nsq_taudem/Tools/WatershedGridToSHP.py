#Probably a waste to have this tool, as it simply just calls QGIS/GDAL's Polygonize.
#Implies 8 connectedness and name of field = ("value")

from .AlgorithmGenerator import Algorithm

class StagedAlgorithm(Algorithm):
#class StagedAlgorithm():
    def initAlgorithm(self, config=None):
        self.AddProcessCountInputParam()

    def processAlgorithm(self, parameters, context, feedback):
        return {}