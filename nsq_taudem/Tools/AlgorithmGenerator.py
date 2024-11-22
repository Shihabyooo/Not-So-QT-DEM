from ..helpers import Utilities, Tool

from qgis.core import (QgsProcessing,
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

#TODO consider refactoring the QGISParameters() method to call individual Parameter generation methods. Bonus: saves lines in the\
#staged tools' scripts (wouldn't need to import the types for each one)

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
    
    def helpUrl(self):
        return self.tool.helpURL
    
    def icon(self):
        return Utilities.GetIcon()
    
    def svgIconPath(self):
        return Utilities.GetIconSVGPath()

    def ParameterName(self, param):
        #param["option"] is unique for each input/output for each tool. We can strip the leading hyphen and use it as ID.
        #rationale: QGIS tool tip when hovering on input shows its ID.
        #Some input don't have their own options. Multiple ones may use one option, which is defined for the first input in the description file. Handle them here
        if ("option" in param.keys() and param["option"] != ""):
            return param["option"][1:]
        else:
            return Utilities.SanitizeString(param["desc"])

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
        pIdName = self.ParameterName(param)
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
        args = {"parameters" : paramList, "name" : self.ParameterName(param) , "context" : context}
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

    def AddProcessCountInputParam(self):
        self.addParameter(QgsProcessingParameterNumber(name = "PROCESS_COUNT", description = "Number of processes to use (Requires MPI enabled)", optional = False, defaultValue = 4, type = QgsProcessingParameterNumber.Integer))

    def initAlgorithm(self, config=None):
        for input in self.tool.inputParams:
            self.addParameter(self.QGISParameter(input, False))

        #process count is universal for all algorithms, not included int the descriptions
        self.AddProcessCountInputParam()

        for output in self.tool.outputParams:
            self.addParameter(self.QGISParameter(output, True))

    def processAlgorithm(self, parameters, context, feedback):
        results = {}
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

        #loop over outputs. These all evaluate to paths (strings), so no need for special method to handle them
        for output in self.tool.outputParams:
            evaluatedParam = self.parameterAsOutputLayer(parameters,  output["option"][1:], context)
            if (evaluatedParam is None):
                raise QgsProcessingException(self.invalidSinkError(parameters, output["option"][1:]))
            
            command += [output["option"], Utilities.WrapInQuotes(evaluatedParam)]
            
            if(output["type"] != "t"): #we only add rasters and vectors to qgis as a layer, not text
                results[output["option"][1:]] = evaluatedParam
            
        #handle processes count
        processCount = self.parameterAsInt(parameters, "PROCESS_COUNT", context)

        #ExecuteTauDemTool expects a single string with command and all args, not a list of strings.
        command = " ".join(command)
        feedback.pushInfo(f"Executing {command}")
        Utilities.ExecuteTauDEMTool(command, processCount, feedback)        
        return results