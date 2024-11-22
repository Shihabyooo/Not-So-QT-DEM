#Probably a waste to have this tool, as it simply just calls QGIS/GDAL's Polygonize.
#Implies 8 connectedness and name of field = ("value")

from .AlgorithmGenerator import Algorithm
from ..helpers import Utilities
from qgis.core import (QgsProcessing,
                       QgsProcessingException,
                       QgsProcessingParameterRasterLayer,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterBoolean,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterRasterDestination)
import processing

class StagedAlgorithm(Algorithm):
    #TODO use the name that is used for each called TauDEM tool.
    DEM = "dem"
    FDR = "fdr"
    WCENTER = "wcenter"
    WSIDE = "wside" 
    WDIAG = "wdiag"
    ACC_THRESH = "accthresh"
    CHECK_EDGE = "checkedge"
    OUTLETS = "outlets"
    MASK = "mask"
    USE_THRESH = "usethresh"
    STR_SRC = "strsrc"
    FAC = "fac"
    STR_GRD = "strgrd"

    def initAlgorithm(self, config=None):
        #Elevation Grid =r
        self.addParameter(QgsProcessingParameterRasterLayer(name = self.DEM,
                                                            description = "Elevation grid",
                                                            optional = False,
                                                            defaultValue = [QgsProcessing.TypeRaster]))
        #D8 FLow Direction Grid = r
        self.addParameter(QgsProcessingParameterRasterLayer(name = self.FDR,
                                                            description = "D8 flow direction grid",
                                                            optional = False,
                                                            defaultValue = [QgsProcessing.TypeRaster]))
        #Weight Center = 0.4f (default)
        self.addParameter(QgsProcessingParameterNumber(name = self.WCENTER,
                                                            description = "Weight center",
                                                            optional = False,
                                                            defaultValue = 0.4,
                                                            type = QgsProcessingParameterNumber.Double))
        
        #Weight Side = 0.1f
        self.addParameter(QgsProcessingParameterNumber(name = self.WSIDE,
                                                            description = "Weight side",
                                                            optional = False,
                                                            defaultValue = 0.1,
                                                            type = QgsProcessingParameterNumber.Double))
        #Weight Diagonal = 0.05f
        self.addParameter(QgsProcessingParameterNumber(name = self.WDIAG,
                                                            description = "Weight diagonal",
                                                            optional = False,
                                                            defaultValue = 0.05,
                                                            type = QgsProcessingParameterNumber.Double))
        # Accumulation Threshold = 50
        self.addParameter(QgsProcessingParameterNumber(name = self.ACC_THRESH,
                                                            description = "Accumulation threshold",
                                                            optional = False,
                                                            defaultValue = 50,
                                                            type = QgsProcessingParameterNumber.Integer))
        # Check Edge contamination = True
        self.addParameter(QgsProcessingParameterBoolean(name = self.CHECK_EDGE,
                                                        description = "Check edge contamination",
                                                        optional = False,
                                                        defaultValue = True))
        # Outlets (optional) = v0
        self.addParameter(QgsProcessingParameterFeatureSource(name = self.OUTLETS,
                                                              description = "Outlets",
                                                              optional = True,
                                                              types = [0]))
        # Mask Grid = (optional) = r 
        self.addParameter(QgsProcessingParameterRasterLayer(name = self.MASK,
                                                            description = "Mask grid",
                                                            optional = True,
                                                            defaultValue = [QgsProcessing.TypeRaster]))
        # Use the range below to automatically select threshold by drop analysis = False
        self.addParameter(QgsProcessingParameterBoolean(name = self.USE_THRESH,
                                                        description = "Use the range below to automatically select threshold by drop analysis",
                                                        optional = False,
                                                        defaultValue = False))
        #This tool does call other TauDEM tools, so add processes count option
        self.AddProcessCountInputParam()

        #outputs:
        # Stream source grid
        self.addParameter(QgsProcessingParameterRasterDestination(name = self.STR_SRC, description = "Stream source grid"))
        # Accumulated stream source grid
        self.addParameter(QgsProcessingParameterRasterDestination(name = self.FAC, description = "Accumulated stream source grid"))
        # Stream Raster Gird
        self.addParameter(QgsProcessingParameterRasterDestination(name = self.STR_GRD, description = "Stream raster grid"))


    def processAlgorithm(self, parameters, context, feedback):
         #{"desc" : str = description of the input
            # "option" : str  = cli option
            # "type" : str =
            # "isOptional" : bool =
            # "type" : str =
            # "default" : int/float/bool =
            #}
        #def EvaluateQGISInputParameter(self, param, paramList, context) -> list:
        #pType = param["type"].lower()
        #args = {"parameters" : paramList, "name" : self.ParameterName(param) , "context" : context}
        inputs = {}
        outputs = {}
        
        inputs[self.DEM] = self.EvaluateQGISInputParameter({"type" : "r", "option" : "", "desc" : self.DEM}, parameters, context)
        inputs[self.FDR] = self.EvaluateQGISInputParameter({"type" : "r", "option" : "", "desc" : self.FDR}, parameters, context)
        inputs[self.WCENTER] = self.EvaluateQGISInputParameter({"type" : "f", "option" : "", "desc" : self.WCENTER}, parameters, context)
        inputs[self.WSIDE] = self.EvaluateQGISInputParameter({"type" : "f", "option" : "", "desc" : self.WSIDE}, parameters, context)
        inputs[self.WDIAG] = self.EvaluateQGISInputParameter({"type" : "f", "option" : "", "desc" : self.WDIAG}, parameters, context)
        inputs[self.ACC_THRESH] = self.EvaluateQGISInputParameter({"type" : "i", "option" : "", "desc" : self.ACC_THRESH}, parameters, context)
        inputs[self.CHECK_EDGE] = len(self.EvaluateQGISInputParameter({"type" : "b", "option" : "", "desc" : self.CHECK_EDGE}, parameters, context)) > 0
        inputs[self.OUTLETS] = self.EvaluateQGISInputParameter({"type" : "v0", "option" : "", "desc" : self.OUTLETS}, parameters, context)
        inputs[self.MASK] = self.EvaluateQGISInputParameter({"type" : "r", "option" : "", "desc" : self.MASK}, parameters, context)
        inputs[self.USE_THRESH] = len(self.EvaluateQGISInputParameter({"type" : "b", "option" : "", "desc" : self.USE_THRESH}, parameters, context)) > 0

        outputs[self.STR_SRC] = self.parameterAsOutputLayer(parameters, self.STR_SRC, context)
        outputs[self.FAC] = self.parameterAsOutputLayer(parameters, self.FAC, context)
        outputs[self.STR_GRD] = self.parameterAsOutputLayer(parameters, self.STR_GRD, context)

        processCount = self.parameterAsInt(parameters, "PROCESS_COUNT", context)
        
        #validate inputs
        for key in inputs.keys():
            if key not in [self.OUTLETS, self.MASK] and inputs[key] is None:
                feedback.pushInfo(f"Error! Could not evaulate inputs {key}")
                raise QgsProcessingException(self.invalidSourceError(parameters, key))
        
        #TODO validate output path generation 
         
                
        return {self.STR_SRC : outputs[self.STR_SRC], self.FAC : outputs[self.FAC], self.STR_GRD : outputs[self.STR_GRD]}