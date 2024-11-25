#This tool stages the following tools: PeukerDouglas -> AreaD8 -> (Optional)DropAnalysis -> Threshold

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
    #TODO use the name that is used for each called TauDEM tool, or the typical name in the docs. See SlopeAreaStreamDef.py
    DEM = "dem"
    FDR = "fdr"
    D8_CONTRIB = "d8contrib"
    WCENTER = "wcenter"
    WSIDE = "wside" 
    WDIAG = "wdiag"
    ACC_THRESH = "accthresh"
    CHECK_EDGE = "checkedge"
    OUTLETS = "outlets"
    MASK = "mask"
    USE_THRESH = "usethresh"
    MIN_THRESH = "minthres"
    MAX_THRESH = "maxthresh"
    NUM_THRESH = "numthresh"
    USE_LOG = "uselog"
    STR_SRC = "strsrc"
    FAC = "fac"
    STR_GRD = "strgrd"
    DRP_FILE = "drpfile"

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
                                                            defaultValue = 50.0,
                                                            type = QgsProcessingParameterNumber.Double))
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
        # D8 conributing area (optional) = r
        self.addParameter(QgsProcessingParameterRasterLayer(name = self.D8_CONTRIB,
                                                            description = "D8 contributing area for drop analysis",
                                                            optional = True,
                                                            defaultValue = [QgsProcessing.TypeRaster]))
        # Use the range below to automatically select threshold by drop analysis = False
        self.addParameter(QgsProcessingParameterBoolean(name = self.USE_THRESH,
                                                        description = "Use the range below to automatically select threshold by drop analysis",
                                                        optional = False,
                                                        defaultValue = False))
        # Minimum threshold = 5
        self.addParameter(QgsProcessingParameterNumber(name = self.MIN_THRESH,
                                                            description = "Minimum threshold value (Drop analysis)",
                                                            optional = False,
                                                            defaultValue = 5.0,
                                                            type = QgsProcessingParameterNumber.Double))
        # Maximum threshold = 500
        self.addParameter(QgsProcessingParameterNumber(name = self.MAX_THRESH,
                                                            description = "Maximum threshold value (Drop analysis)",
                                                            optional = False,
                                                            defaultValue = 500.0,
                                                            type = QgsProcessingParameterNumber.Double))
        # Number of threshold values = 10
        self.addParameter(QgsProcessingParameterNumber(name = self.NUM_THRESH,
                                                            description = "Number of threshold values (Drop analysis)",
                                                            optional = False,
                                                            defaultValue = 10,
                                                            type = QgsProcessingParameterNumber.Integer))
        # Logarithmic spacing = True
        self.addParameter(QgsProcessingParameterBoolean(name = self.USE_LOG,
                                                        description = "Logarithmic spacing (Drop analysis)",
                                                        optional = False,
                                                        defaultValue = True))
        #This tool does call other TauDEM tools, so add processes count option
        self.AddProcessCountInputParam()

        #outputs:
        # Stream source grid
        self.addParameter(QgsProcessingParameterRasterDestination(name = self.STR_SRC, description = "Stream source grid"))
        # Accumulated stream source grid
        self.addParameter(QgsProcessingParameterRasterDestination(name = self.FAC, description = "Accumulated stream source grid"))
        # Stream Raster Gird
        self.addParameter(QgsProcessingParameterRasterDestination(name = self.STR_GRD, description = "Stream raster grid"))
        # Drop analysis text file
        self.addParameter(QgsProcessingParameterFileDestination(name = self.DRP_FILE, description = "Drop analysis table"))

    def processAlgorithm(self, parameters, context, feedback):
        inputs = {}
        outputs = {}
    
        #Note optional params are going to be empty strings "" not None if unset by user
        #TODO reduce these lines similar to SlopeAreaStreamDef.py. Perhaps they can be refactored into their own method in parent AlgorithmGenerator.py?
        inputs[self.DEM] = Utilities.GetLayerAbsolutePath(self.parameterAsLayer(parameters = parameters, name = self.DEM, context = context))
        inputs[self.FDR] = Utilities.GetLayerAbsolutePath(self.parameterAsLayer(parameters = parameters, name = self.FDR, context = context))
        inputs[self.WCENTER] = self.parameterAsDouble(parameters = parameters, name = self.WCENTER, context = context)
        inputs[self.WSIDE] = self.parameterAsDouble(parameters = parameters, name = self.WSIDE, context = context)
        inputs[self.WDIAG] = self.parameterAsDouble(parameters = parameters, name = self.WDIAG, context = context)
        inputs[self.ACC_THRESH] = self.parameterAsDouble(parameters = parameters, name = self.ACC_THRESH, context = context)
        inputs[self.CHECK_EDGE] = self.parameterAsBool(parameters = parameters, name = self.CHECK_EDGE, context = context)
        inputs[self.OUTLETS] = Utilities.GetLayerAbsolutePath(self.parameterAsLayer(parameters = parameters, name = self.OUTLETS, context = context))
        inputs[self.MASK] = Utilities.GetLayerAbsolutePath(self.parameterAsLayer(parameters = parameters, name = self.MASK, context = context))
        inputs[self.D8_CONTRIB] = Utilities.GetLayerAbsolutePath(self.parameterAsLayer(parameters = parameters, name = self.D8_CONTRIB, context = context))
        inputs[self.USE_THRESH] = self.parameterAsBool(parameters = parameters, name = self.USE_THRESH, context = context)
        inputs[self.MIN_THRESH] = self.parameterAsDouble(parameters = parameters, name = self.MIN_THRESH, context = context)
        inputs[self.MAX_THRESH] = self.parameterAsDouble(parameters = parameters, name = self.MAX_THRESH, context = context)
        inputs[self.NUM_THRESH] = self.parameterAsInt(parameters = parameters, name = self.NUM_THRESH, context = context)
        inputs[self.USE_LOG] = self.parameterAsBool(parameters = parameters, name = self.USE_LOG, context = context)

        outputs[self.STR_SRC] = self.parameterAsOutputLayer(parameters, self.STR_SRC, context)
        outputs[self.FAC] = self.parameterAsOutputLayer(parameters, self.FAC, context)
        outputs[self.STR_GRD] = self.parameterAsOutputLayer(parameters, self.STR_GRD, context)
        outputs[self.DRP_FILE] = self.parameterAsFile(parameters, self.DRP_FILE, context)

        processCount = self.parameterAsInt(parameters, self.PROC_COUNT, context)
        
        #validate inputs (TODO is this necessary? QGIS should not allow us to reach this point if the mandatory parameters aren't set)
        # for key in inputs.keys():
        #     if key not in [self.OUTLETS, self.MASK, self.D8_CONTRIB] and inputs[key] is None:
        #         feedback.pushInfo(f"Error! Could not evaulate inputs {key}")
        #         raise QgsProcessingException(self.invalidSourceError(parameters, key))
        
        #TODO validate output path generation 

        #TODO the ArcPy implementation rquires both USE_THRESH to be set and outlet file to be provded to use drop analysis. Validate that outlet file is supplied
        #when USE_THRESH is set to true.

        feedback.pushInfo(f"Executing Peuker Douglas algorithm") #test

        inputSet = {"fel" : inputs[self.DEM],
                    "par" : inputs[self.WCENTER], "sidesmoothingweight" : inputs[self.WSIDE], "diagonalsmoothingweight" : inputs[self.WDIAG], 
                    self.PROC_COUNT : processCount,
                    "ss" : outputs[self.STR_SRC]}
        processing.run("TauDEM:peukerdouglas", inputSet)
            
        #run AreaD8 (in FDR, in Oulets, in strsrc (as weight grid), in CheckEdge, out FAC)
        feedback.pushInfo(f"Executing D8 Contributing Area algorithm") #test
        inputSet = {"p": inputs[self.FDR],
                    "o": inputs[self.OUTLETS] if inputs[self.OUTLETS] != "" else None,
                    "wg": outputs[self.STR_SRC],
                    "nc": inputs[self.CHECK_EDGE],
                    self.PROC_COUNT : processCount,
                    "ad8": outputs[self.FAC]}
        processing.run("TauDEM:d8contributingarea", inputSet)
        
        threshold = inputs[self.ACC_THRESH] #will be overridden if user supplied an outlet file and set USE_THRESH to true.

        #if USETHRESH is set AND Outlets are provided:
            #run DropAnalaysis (in DEM, in FDR, in D8Contrib in FAC, in outlets, in minthresh, in maxthresh, in numthres, in UseLog, out dropfile)
            
        if (inputs[self.USE_THRESH] and inputs[self.OUTLETS] != ""):
            feedback.pushInfo(f"Executing Drop Analysis algorithm") #test
            inputSet = {"fel" : inputs[self.DEM],
                        "p" : inputs[self.FDR],
                        "ad8": inputs[self.D8_CONTRIB],
                        "ssa": outputs[self.FAC], #TODO double check assignment of ad8 and ssa here.
                        "o" : inputs[self.OUTLETS],
                        "par":inputs[self.MIN_THRESH],
                        "maximumthresholdvalue": inputs[self.MAX_THRESH],
                        "numberofthresholdvalues": inputs[self.NUM_THRESH],
                        "typeofthresholdsteptobeusedindropanalysis": int(not inputs[self.USE_LOG]), #The called function has Logarithmic as 0, arithmatic as 1. 
                        self.PROC_COUNT : processCount,
                        "drp": outputs[self.DRP_FILE]}
            processing.run("TauDEM:streamdropanalysis", inputSet)

            #process drop file
            #Drop file has many entires, what we need is the value at the last line, which reads:
            #Optimium Threshold Value: (Threshold as floating number)
            #The arcpy implementation simply opens the file, grabs all content, then splits (using
            #rsplit) once with space as delimited (i.e. dropFileContent.rsplot(" ", 1)) and takes the
            #second entry from the resulting list, which the floating number above.
            
            try:
                dropFile = open(outputs[self.DRP_FILE])
                threshold = float(dropFile.read().rsplit(" ", 1)[1])
                feedback.pushInfo(f"Using automatic threshold value of {threshold}")
                dropFile.close()
            except Exception as exception: 
                feedback.pushInfo(f"Error parsing drop file: {Utilities.WrapInQuotes(outputs[self.DRP_FILE])}")
                raise QgsProcessingException(self.invalidSourceError(parameters, outputs[self.DRP_FILE]))

        #run Threshold (in FAC, in threshold, in mask, out strsrc)
        inputSet = {"ssa": outputs[self.FAC],
                    "mask": inputs[self.MASK] if inputs[self.MASK] != "" else None,
                    "thresh": threshold,
                    self.PROC_COUNT:processCount,
                    "src": outputs[self.STR_GRD]}
        processing.run("TauDEM:streamdefinitionbythreshold", inputSet)
        
        #and we're done!
        
        return {self.STR_SRC : outputs[self.STR_SRC], self.FAC : outputs[self.FAC], self.STR_GRD : outputs[self.STR_GRD]}