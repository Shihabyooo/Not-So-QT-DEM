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
    FDR = "pfile"
    DINF_CONTRIB = "scafile"
    SLOPE = "slpfile"
    MASK = "maskfile"
    OUTLETS = "shfl"
    CHECK_EDGE = "nc"
    DEM = "felfile"
    D8_CONTRIB = "ad8file"
    SLP_EXP = "slpexp"
    AREA_EXP = "areaexp"
    THRESH = "thresh"
    USE_THRESH = "usedroprange"
    MIN_THRESH = "minthresh"
    MAX_THRESH = "maxthres"
    NUM_THRESH = "numthresh"
    USE_LOG = "logspace"
    STR_SRC = "srcfile"
    STR_SAREA = "safile"
    MAX_USLP = "ssafile"
    DRP_FILE = "drpfile"

    def initAlgorithm(self, config=None):
        #D8 flow direction grid (p) = r
        self.addParameter(QgsProcessingParameterRasterLayer(name = self.FDR,
                                                            description = "D8 flow direction grid",
                                                            optional = False,
                                                            defaultValue = [QgsProcessing.TypeRaster]))
        #D-infinity contributing area grid (sca) = r
        self.addParameter(QgsProcessingParameterRasterLayer(name = self.DINF_CONTRIB,
                                                            description = "D-infinity contributing area grid",
                                                            optional = False,
                                                            defaultValue = [QgsProcessing.TypeRaster]))
        #Slope grid (slp) = r
        self.addParameter(QgsProcessingParameterRasterLayer(name = self.SLOPE,
                                                            description = "Slope grid",
                                                            optional = False,
                                                            defaultValue = [QgsProcessing.TypeRaster]))
        #Mask grid (mask) (optional) = r
        self.addParameter(QgsProcessingParameterRasterLayer(name = self.MASK,
                                                            description = "Mask grid",
                                                            optional = True,
                                                            defaultValue = [QgsProcessing.TypeRaster]))
        #Outlets (shfl1) (optional) = v0
        self.addParameter(QgsProcessingParameterFeatureSource(name = self.OUTLETS,
                                                              description = "Outlets",
                                                              optional = True,
                                                              types = [0]))
        #Check for edge contamination = True
        self.addParameter(QgsProcessingParameterBoolean(name = self.CHECK_EDGE,
                                                        description = "Check edge contamination",
                                                        optional = False,
                                                        defaultValue = True))
        #Pit-filled eldvation grid for drop analysis (fel) (optional) = r
        self.addParameter(QgsProcessingParameterRasterLayer(name = self.DEM,
                                                            description = "Pit-filled elevation grid for drop analysis",
                                                            optional = True,
                                                            defaultValue = [QgsProcessing.TypeRaster]))
        #D8 contributing area grid for drop analysis (ad8) (optional) = r
        self.addParameter(QgsProcessingParameterRasterLayer(name = self.D8_CONTRIB,
                                                            description = "D8 contributing area grid for drop analysis",
                                                            optional = True,
                                                            defaultValue = [QgsProcessing.TypeRaster]))
        #Slope exponent (slpexp) = 2.0
        self.addParameter(QgsProcessingParameterNumber(name = self.SLP_EXP,
                                                            description = "Slope exponent",
                                                            optional = False,
                                                            defaultValue = 2.0,
                                                            type = QgsProcessingParameterNumber.Double))
        #Area exponent (areaexp) = 1.0
        self.addParameter(QgsProcessingParameterNumber(name = self.AREA_EXP,
                                                            description = "Area exponent",
                                                            optional = False,
                                                            defaultValue = 1.0,
                                                            type = QgsProcessingParameterNumber.Double))
        #Threshold (thresh) = 200
        self.addParameter(QgsProcessingParameterNumber(name = self.THRESH,
                                                            description = "Threshold",
                                                            optional = False,
                                                            defaultValue = 200,
                                                            type = QgsProcessingParameterNumber.Integer))
        
        # Use the range below to automatically select threshold by drop analysis = False
        self.addParameter(QgsProcessingParameterBoolean(name = self.USE_THRESH,
                                                        description = "Use the range below to automatically select threshold by drop analysis",
                                                        optional = False,
                                                        defaultValue = False))
         #Minimum threshold value (Drop analysis) (minthresh) = 5
        self.addParameter(QgsProcessingParameterNumber(name = self.MIN_THRESH,
                                                            description = "Minimum threshold value (Drop analysis)",
                                                            optional = False,
                                                            defaultValue = 5,
                                                            type = QgsProcessingParameterNumber.Integer))
        #Maximum threshold value (Drop analysis) (maxthresh) = 500
        self.addParameter(QgsProcessingParameterNumber(name = self.MAX_THRESH,
                                                            description = "Maximum threshold value (Drop analysis)",
                                                            optional = False,
                                                            defaultValue = 500,
                                                            type = QgsProcessingParameterNumber.Integer))
        #Number of threshold values (Drop analysis) (numthresh)= 10
        self.addParameter(QgsProcessingParameterNumber(name = self.NUM_THRESH,
                                                            description = "Number of threshold values (Drop analysis)",
                                                            optional = False,
                                                            defaultValue = 10,
                                                            type = QgsProcessingParameterNumber.Integer))
        #Logarithmic Spacing (Drop analysis) (logspace) = True
        self.addParameter(QgsProcessingParameterBoolean(name = self.USE_LOG,
                                                        description = "Logarithmic spacing (Drop analysis)",
                                                        optional = False,
                                                        defaultValue = True))
        
        #Process Count
        self.AddProcessCountInputParam()

        #Stream raster grid (src) = r
        self.addParameter(QgsProcessingParameterRasterDestination(name = self.STR_SRC, description = "Stream raster grid"))
        #Source area grid (sa) = r
        self.addParameter(QgsProcessingParameterRasterDestination(name = self.STR_SAREA, description = "Stream area grid"))
        #Maximum upslope grid (ssa) = r
        self.addParameter(QgsProcessingParameterRasterDestination(name = self.MAX_USLP, description = "Max upslope grid"))
        #Drop analysis table (drp) = t
        self.addParameter(QgsProcessingParameterFileDestination(name = self.DRP_FILE, description = "Drop analysis table"))

    def processAlgorithm(self, parameters, context, feedback):
        inputs = {}
        outputs = {}

        for param in [self.FDR, self.DINF_CONTRIB, self.SLOPE, self.MASK, self.OUTLETS, self.DEM, self.D8_CONTRIB]:
            inputs[param] = Utilities.GetLayerAbsolutePath(self.parameterAsLayer(parameters = parameters, name = param, context = context))
        
        for param in [self.CHECK_EDGE, self.USE_THRESH, self.USE_LOG]:
            inputs[param] = self.parameterAsBool(parameters = parameters, name = param, context = context)

        for param in [self.SLP_EXP, self.AREA_EXP, self.THRESH, self.MIN_THRESH, self.MAX_THRESH]:
            inputs[param] = self.parameterAsDouble(parameters = parameters, name = param, context = context)

        inputs[self.NUM_THRESH] = self.parameterAsInt(parameters = parameters, name = self.NUM_THRESH, context = context)
        processCount = self.parameterAsInt(parameters, self.PROC_COUNT, context)

        for param in [self.STR_SRC, self.STR_SAREA, self.MAX_USLP]:
            outputs[param] = self.parameterAsOutputLayer(parameters, param, context)

        outputs[self.DRP_FILE] = self.parameterAsFile(parameters, self.DRP_FILE, context)

        #TODO validate input and output
        #TODO the ArcPy implementation rquires both USE_THRESH to be set and outlet file to be provded to use drop analysis. Validate that outlet file is supplied
        #when USE_THRESH is set to true.

        #run SlopeArea (in slpfile, in scafile, in slpexp, in areaexp, out safile )
        feedback.pushInfo(f"Executing Slope Area Combination algorithm") #test
        inputSet = {"slp" : inputs[self.SLOPE],
                    "sca" : inputs[self.DINF_CONTRIB],
                    "par" : inputs[self.SLP_EXP],
                    "areaexponentn" : inputs[self.AREA_EXP],
                    self.PROC_COUNT : processCount,
                    "sa" : outputs[self.STR_SAREA]}
        
        processing.run("TauDEM:slopeareacombination", inputSet)
        
        #run D8FlowPathExtremeUp (in pfile, in safile, in shfl, in nc, out ssafile)
        feedback.pushInfo(f"Executing D8 Extreme Upslope Value algorithm") #test
        inputSet = {"p" : inputs[self.FDR],
                    "sa" : outputs[self.STR_SAREA],
                    "min" : False, #False is the default, but this plugin requires all boolean flags to be input.
                    "nc" : True, #ditto (but default is true)
                    "o" : inputs[self.OUTLETS] if inputs[self.OUTLETS] != "" else None,
                    self.PROC_COUNT : processCount,
                    "ssa" : outputs[self.MAX_USLP]}
        
        processing.run("TauDEM:d8extremeupslopevalue", inputSet)

        threshold = inputs[self.THRESH] #will be overridden if user supplied an outlet file and set USE_THRESH to true.

        #if use_thresh and outlets is given:
        if inputs[self.USE_THRESH] and inputs[self.OUTLETS] != "":
            #run DropAnalysis (in felfile, in pfile, in ad8file, in ssafile, in shfl, in minthresh, in maxthresh, in numbthresh, in uselog, out drpfile)
            feedback.pushInfo(f"Executing Drop Analysis algorithm") #test
            inputSet = {"fel" : inputs[self.DEM],
                        "p" : inputs[self.FDR],
                        "ad8": inputs[self.D8_CONTRIB],
                        "ssa": outputs[self.MAX_USLP],
                        "o" : inputs[self.OUTLETS],
                        "par":inputs[self.MIN_THRESH],
                        "maximumthresholdvalue": inputs[self.MAX_THRESH],
                        "numberofthresholdvalues": inputs[self.NUM_THRESH],
                        "typeofthresholdsteptobeusedindropanalysis": int(not inputs[self.USE_LOG]), #The called function has Logarithmic as 0, arithmatic as 1. 
                        self.PROC_COUNT : processCount,
                        "drp": outputs[self.DRP_FILE]}
            
            processing.run("TauDEM:streamdropanalysis", inputSet)
            
            #extract threshold from drop file.
            try:
                dropFile = open(outputs[self.DRP_FILE])
                threshold = float(dropFile.read().rsplit(" ", 1)[1])
                feedback.pushInfo(f"Using automatic threshold value of {threshold}")
                dropFile.close()
            except Exception as exception: 
                feedback.pushInfo(f"Error parsing drop file: {Utilities.WrapInQuotes(outputs[self.DRP_FILE])}")
                raise QgsProcessingException(self.invalidSourceError(parameters, outputs[self.DRP_FILE]))
        
        #run Threshold (in ssa, in thresh, in maskfile, out src)
        feedback.pushInfo(f"Executing Stream Definition by Threshold algorithm") #test
        inputSet = {"ssa": outputs[self.MAX_USLP],
                    "mask": inputs[self.MASK] if inputs[self.MASK] != "" else None,
                    "thresh": threshold,
                    self.PROC_COUNT:processCount,
                    "src": outputs[self.STR_SRC]}
        processing.run("TauDEM:streamdefinitionbythreshold", inputSet)
        
        return {self.STR_SRC : outputs[self.STR_SRC], self.STR_SAREA : outputs[self.STR_SAREA], self.MAX_USLP : outputs[self.MAX_USLP]}