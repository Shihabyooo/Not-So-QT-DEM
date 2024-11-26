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
    DEM = "felfile"
    FDR = "pfile"
    D8_CONTRIB = "ad8file"
    FAC = "ssafile"
    OUTLETS = "ofile"
    MASK = "maskfile"
    MIN_THRESH = "minthresh"
    MAX_THRESH = "maxthresh"
    NUM_THRESH = "numthresh"
    USE_LOG = "uselog"
    DRP_FILE = "drpfile"
    STR_SRC = "srcfile"

    def initAlgorithm(self, config=None):
        #Pit-filled elevation grid (fel) = r
        self.addParameter(QgsProcessingParameterRasterLayer(name = self.DEM,
                                                            description = "Pit-filled elevation grid",
                                                            optional = False,
                                                            defaultValue = [QgsProcessing.TypeRaster]))
        #D8 flow direction grid (p) = r
        self.addParameter(QgsProcessingParameterRasterLayer(name = self.FDR,
                                                            description = "D8 flow direction grid",
                                                            optional = False,
                                                            defaultValue = [QgsProcessing.TypeRaster]))
        #D8 contributing area grid (ad8) = r
        self.addParameter(QgsProcessingParameterRasterLayer(name = self.D8_CONTRIB,
                                                            description = "D8 contributing area grid",
                                                            optional = False,
                                                            defaultValue = [QgsProcessing.TypeRaster]))
        #Accumulated stream source grid (ssa) = r
        self.addParameter(QgsProcessingParameterRasterLayer(name = self.FAC,
                                                            description = "Accumulated stream source grid",
                                                            optional = False,
                                                            defaultValue = [QgsProcessing.TypeRaster]))
        #Oulets (shfl1) = v0
        self.addParameter(QgsProcessingParameterFeatureSource(name = self.OUTLETS,
                                                              description = "Outlets",
                                                              optional = False,
                                                              types = [0]))
        #Mask grid (optional) (mask()) = r
        self.addParameter(QgsProcessingParameterRasterLayer(name = self.MASK,
                                                            description = "Mask grid",
                                                            optional = True,
                                                            defaultValue = [QgsProcessing.TypeRaster]))
        #Minimum threshold value (minthresh) = 5.0
        self.addParameter(QgsProcessingParameterNumber(name = self.MIN_THRESH,
                                                            description = "Minimum threshold value",
                                                            optional = False,
                                                            defaultValue = 5.0,
                                                            type = QgsProcessingParameterNumber.Double))
        #Maximum threshold value (maxthresh) = 500.0
        self.addParameter(QgsProcessingParameterNumber(name = self.MAX_THRESH,
                                                            description = "Maximum threshold value",
                                                            optional = False,
                                                            defaultValue = 500.0,
                                                            type = QgsProcessingParameterNumber.Double))
        #Number of threshold values (numthresh) = 10
        self.addParameter(QgsProcessingParameterNumber(name = self.NUM_THRESH,
                                                            description = "Number of threshold values",
                                                            optional = False,
                                                            defaultValue = 10,
                                                            type = QgsProcessingParameterNumber.Integer))
        #Use logarithmic spacing for threshold values (logspace) = True
        self.addParameter(QgsProcessingParameterBoolean(name = self.USE_LOG,
                                                        description = "Use logarithmic spacing for threshold values",
                                                        optional = False,
                                                        defaultValue = True))
        
        #Drop analysis text file (drp) = t
        self.addParameter(QgsProcessingParameterFileDestination(name = self.DRP_FILE, description = "Drop analysis text file"))
        #Stream raster grid (src) = r
        self.addParameter(QgsProcessingParameterRasterDestination(name = self.STR_SRC, description = "Stream raster grid"))
        
    
    def processAlgorithm(self, parameters, context, feedback):
        inputLayers =  [self.DEM, self.FDR, self.D8_CONTRIB, self.FAC, self.OUTLETS, self.MASK]
        inputFloats = [self.MIN_THRESH, self.MAX_THRESH]
        inputInts = [self.NUM_THRESH]
        inputsBools = [self.USE_LOG]
        outputLayers = [self.STR_SRC]
        outputFiles = [self.DRP_FILE]

        self.EvaluateParameters(parameters, context, inputLayers, inputFloats, inputInts, inputsBools, outputLayers, outputFiles)
        
        
        #run DropAnalysis (in felfile, in pfile, in ad8file, in ssafile, in ofile, in minthresh, in maxthresh, in numthresh, in logspace, out drpfile)
        feedback.pushInfo(f"Executing Drop Analysis algorithm") #test
        inputSet = {"fel" : self.inputs[self.DEM],
                        "p" : self.inputs[self.FDR],
                        "ad8": self.inputs[self.D8_CONTRIB],
                        "ssa": self.inputs[self.FAC],
                        "o" : self.inputs[self.OUTLETS],
                        "par" : self.inputs[self.MIN_THRESH],
                        "maximumthresholdvalue": self.inputs[self.MAX_THRESH],
                        "numberofthresholdvalues": self.inputs[self.NUM_THRESH],
                        "typeofthresholdsteptobeusedindropanalysis": int(not self.inputs[self.USE_LOG]), #The called function has Logarithmic as 0, arithmatic as 1. 
                        self.PROC_COUNT : self.inputs[self.PROC_COUNT],
                        "drp": self.outputs[self.DRP_FILE]}
        
        processing.run("TauDEM:streamdropanalysis", inputSet, feedback = feedback)

        #extract threshold from drop file.
        try:
            dropFile = open(self.outputs[self.DRP_FILE])
            threshold = float(dropFile.read().rsplit(" ", 1)[1])
            feedback.pushInfo(f"Using automatic threshold value of {threshold}")
            dropFile.close()
        except Exception as exception: 
            feedback.pushInfo(f"Error parsing drop file: {Utilities.WrapInQuotes(self.outputs[self.DRP_FILE])}")
            raise QgsProcessingException(self.invalidSourceError(parameters, self.outputs[self.DRP_FILE]))

        #run Threshold (in ssafile, in threshold, out srcfile)
        feedback.pushInfo(f"Executing Stread Definition By Threshold algorithm") #test
        inputSet = {"ssa" : self.inputs[self.FAC],
                    "mask" : self.inputs[self.MASK] if self.inputs[self.MASK] != "" else None,
                    "thresh" : threshold,
                    self.PROC_COUNT : self.inputs[self.PROC_COUNT],
                    "src" : self.outputs[self.STR_SRC]}
        
        processing.run("TauDEM:streamdefinitionbythreshold", inputSet, feedback = feedback)

        return {self.STR_SRC : self.outputs[self.STR_SRC]}