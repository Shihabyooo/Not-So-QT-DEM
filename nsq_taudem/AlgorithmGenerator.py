from .helpers import Utilities, Tool

from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsApplication,
                       QgsMessageLog, #for testing only, TODO remove
                       QgsFeatureSink,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterRasterLayer,
                       QgsProcessingParameterRasterDestination,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterVectorDestination,
                       QgsProcessingParameterBoolean,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterFileDestination,
                       QgsProcessingParameterEnum)
from qgis import processing

class Algorithm(QgsProcessingAlgorithm):
    def __init__(self, tool : Tool):
        super().__init__()
        self.tool = tool

    def tr(self, string): #TODO implement this? Keeping it as useless pass-over because QGIS threw a fit when the method wasn't defined
        return string 

    def createInstance(self):
        return type(self)(self.tool) 

    def name(self):
        return self.tool.name
    
    def displayName(self):
        return self.tr(self.tool.displayName)
    
    def group(self):
        return self.tr(self.tool.groupDisplayName)
    
    def groupId(self):
        return self.tool.group
    
    def tags(self):
        return ["taudem"]
    
    def shortHelpString(self):
        return self.tool.helpText
    
    def helpURL(self):
        return self.tool.helpURL
    
    def icon(self):
        return Utilities.GetIcon()

    def QGISParameter(self, param, isOuput : bool):
        #{"desc" : str = description of the input
            # "option" : str  = cli option
            # "type" : str =
            # "isOptional" : bool =
            # "type" : str =
            # "default" : int/float/bool =
            #}

        pType = param["type"].lower()
        pDispName = self.tr(param["desc"])
        #pIdName = pDispName.replace(" ","")
        #param["option"] is unique for each input/output for each tool. We can strip the leading hyphen and use it as ID.
        pIdName = param["option"][1:]

        defVal = None if "default" not in param else param["default"]

        #TODO consider switching this to match case statement
        if (pType == "r"): #return a new raster parameter
            if isOuput:
                return QgsProcessingParameterRasterDestination(name = pIdName, description = pDispName)
            else:
                return QgsProcessingParameterRasterLayer(name = pIdName, description = pDispName, optional = param["isOptional"], defaultValue = [QgsProcessing.TypeRaster])
        elif (pType in ["v0", "v1", "v2"]): #point, line or poly vec
            vecType = int(param["type"][1]) #0 = point, 1 = line, 2 = poly
            if isOuput:
                return QgsProcessingParameterVectorDestination(name = pIdName, description = pDispName)
            else:
                return QgsProcessingParameterFeatureSource(name = pIdName, description = pDispName, optional = param["isOptional"], types = [vecType])
        elif (pType == "i"): #int, only input
            return QgsProcessingParameterNumber(name = pIdName, description = pDispName, optional = param["isOptional"], defaultValue = defVal, type = QgsProcessingParameterNumber.Integer) 
        elif (pType == "f"): #float, only input
            return QgsProcessingParameterNumber(name = pIdName, description = pDispName, optional = param["isOptional"], defaultValue = defVal, type = QgsProcessingParameterNumber.Double)
        elif (pType == "b"): #bool, only input
            return QgsProcessingParameterBoolean(name = pIdName, description = pDispName, optional = param["isOptional"], defaultValue = defVal) 
        elif (pType == "t"): #text file, only output
            return QgsProcessingParameterFileDestination(name = pIdName, description = pDispName)
        elif(pType == "l"): #list, only input
            #TODO consider setting default to first entry
            return QgsProcessingParameterEnum(name = pIdName, description = pDispName, optional = param["isOptional"], allowMultiple = False, usesStaticStrings = True, options = param["list"].keys())

    def EvaluateQGISInputParameter(self, param, paramList, context) -> list:
        pType = param["type"].lower()
        args = {"parameters" : paramList, "name" : param["option"][1:] , "context" : context}

        evaluatedParam= ""

        if (pType in ["r", "v0", "v1", "v2"]):
            evaluatedParam = self.parameterAsLayer(**args)
            if (evaluatedParam is not None):
                evaluatedParam = Utilities.WrapInQuotes(Utilities.GetLayerAbsolutePath(self.parameterAsLayer(**args)))
        elif (pType == "i"):
            evaluatedParam = self.parameterAsInt(**args)
            if (evaluatedParam is not None):
                evaluatedParam = str(evaluatedParam)
        elif (pType == "f"):
            evaluatedParam = self.parameterAsDouble(**args)
            if (evaluatedParam is not None):
                evaluatedParam = str(evaluatedParam)
        elif (pType == "b"): #bools are special case, they don't have value to input, but they indicate whether the option is included in the command or not
            evaluatedParam = self.parameterAsBool(**args)
            if (evaluatedParam):
                return [param["option"]]
            else:
                return []
        elif (pType == "l"): #The display name is typically different than command value. Former is key to the latter in dict in "default" entry of tool.inputParams.
            evaluatedParam = self.parameterAsEnumString(**args)
            if (evaluatedParam is not None):
                evaluatedParam = param["list"][evaluatedParam]
        
        if (evaluatedParam is None):
            return None

        return [param["option"], evaluatedParam]

    def initAlgorithm(self, config=None):
        for input in self.tool.inputParams:
            self.addParameter(self.QGISParameter(input, False))

        #thread count is universal for all algorithms, not included int he descriptions
        self.addParameter(QgsProcessingParameterNumber(name = "PROCESS_COUNT", description = "Number of processes to use (Requires MPI enabled)", optional = False, defaultValue = 4, type = QgsProcessingParameterNumber.Integer) )

        for output in self.tool.outputParams:
            self.addParameter(self.QGISParameter(output, True))

    def processAlgorithm(self, parameters, context, feedback):
        results = {}
        
        if (self.tool.type > 0):
            feedback.pushInfo(f"Staged tools are not implemented yet")
            return results
        
        command = []
        command.append(Utilities.WrapInQuotes(Utilities.TauDEMPath() + self.tool.exec))

        #loop over inputs and evluate them
        for input in self.tool.inputParams:
            evaluatedParam = self.EvaluateQGISInputParameter(input, parameters, context)
            #if (evaluatedParam is None):
            if (input["type"] != "b" and evaluatedParam is None):
                if (input["isOptional"]): #optional input can be none if the user elects not to use them. in this case just skip to next input
                    continue
                else: #this is an error. required input can't be none unless something is wrong with fetching it.
                    feedback.pushInfo(f"Error evluating parameters for {input["desc"]}")#test
                    raise QgsProcessingException(self.invalidSourceError(parameters, input["option"][1:]))
            
            command += evaluatedParam

            # if (input["type"] in ["r", "v0", "v1", "v2", "t"]):
            #     command += [input["option"], Utilities.WrapInQuotes(Utilities.GetLayerAbsolutePath(evaluatedParam))]
            # elif (input["type"] in ["i", "f"]):
            #     command += [input["option"], str(evaluatedParam)]
            # elif (input["type"] == "b" and evaluatedParam):
            #     command.append(input["option"])

        #loop over outputs. These all evaluate to paths (strings), so no need for special method to handle them
        for output in self.tool.outputParams:
            evaluatedParam = self.parameterAsOutputLayer(parameters,  output["option"][1:], context)
            if (evaluatedParam is None):
                raise QgsProcessingException(self.invalidSinkError(parameters, output["option"][1:]))
            
            command += [output["option"], Utilities.WrapInQuotes(evaluatedParam)]
            
            if(output["type"] != "t"): #we only add rasters and vectors to qgis as a layer, not text
                results[output["option"][1:]] = evaluatedParam
            
        #handle processes count
        processCount = self.parameterAsInt(
            parameters,
            "PROCESS_COUNT",
            context
        )

        #ExecuteTauDemTool expects a single string with command and all args, not a list of strings.
        command = " ".join(command)
        feedback.pushInfo(f"Executing {command}")
        Utilities.ExecuteTauDEMTool(command, processCount, feedback)        
        return results