#
from .AlgorithmGenerator import Algorithm
from ..helpers import Utilities

from qgis.core import (QgsProcessing,
                       QgsProcessingException,
                       QgsProcessingParameterRasterLayer,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterRasterDestination,
                       QgsProcessingParameterFileDestination)

import processing

class StagedAlgorithm(Algorithm):
    def initAlgorithm(self, config=None):
        #DEM raster (dem) = r
        #Source for parameter regions = l
            #One uniform parameter region
            #Regions from raster
            #Regions from polygon
        
        #Region dataset (parreg-in) (optional?) = r
            #Required for "Region from raster"
        #Region feature class (shp) (optional?) = v2?
            #Region feature class attribute (shp-att-name) = attribute (defaults to ID)
            #required for "regions from polygon"
        #Transmissivity lower bound (m^2/hr) (att-tmin) = 2.708
        #Transmissivity upper bound (m^2/hr) (att-tmax) = 2.708
        #Dimensionless cohesion lower bound (att-cmmin) = 0.0
        #Dimensionless cohesion upper bound (att-cmax) = 0.25
        #Soil friction angle lower bound (att-phimin) = 30.0
        #Soil friction angle upper bound (att-phimax) = 45.0
        #Soil density (kg/m^3) (att-soildens) = 2000.0


        #Parameter region grid (parreg) = r
        #Caliberation table text file (att) = t


        pass

def processAlgorithm(self, parameters, context, feedback):
    inputs = {}
    outputs = {}



    #Get DEM pixel size
    #if shp is input:
        #rasterize shp
    #elif parreg-in is input:
        #resample to same size as dem (TODO coregister?)

    return {}