from ..helpers import Utilities, Tool

from qgis.core import (QgsProcessing,
                       QgsMessageLog, #for testing only
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

#TODO consider rewriting QGSParmater() method to handle generation for both staged and non-staged tools. Saves LOC on staged tools' scripts.

class Algorithm(QgsProcessingAlgorithm):
    PROC_COUNT = "proccount"

    def __init__(self, tool : Tool):
        super().__init__()
        self.tool = tool
        self.inputs = {} #Currently used only by staged tools
        self.outputs = {} #ditto

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
            return QgsProcessingParameterEnum(name = pIdName, description = pDispName, optional = param["isOptional"], defaultValue = 0, allowMultiple = False, options = param["list"].keys())


    #TODO Unify EvaluateParameters() and EvaluateQGISInputParameter(). Will require to rewrite algorithm generator for non-staged tools and its command generator 
    #EvaluateParameters() currently only used by staged tools
    def EvaluateParameters(self, paramList, context,
                           layerParams : list = None, floatParams : list = None, intParams : list = None, boolParams : list = None,
                           outputLayers : list = None, outputFiles : list = None):
        
        if layerParams is not None:
            for param in layerParams:
                self.inputs[param] = Utilities.GetLayerAbsolutePath(self.parameterAsLayer(parameters = paramList, name = param, context = context))
        
        if boolParams is not None:
            for param in boolParams:
                self.inputs[param] = self.parameterAsBool(parameters = paramList, name = param, context = context)

        if (floatParams is not None):
            for param in floatParams:
                self.inputs[param] = self.parameterAsDouble(parameters = paramList, name = param, context = context)

        if (intParams is not None):
            for param in intParams:
                self.inputs[param] = self.parameterAsInt(parameters = paramList, name = param, context = context)

        processCount = self.parameterAsInt(paramList, self.PROC_COUNT, context)
        if processCount is not None:
            self.inputs[self.PROC_COUNT] = processCount

        if outputLayers is not None:
            for param in outputLayers:
                self.outputs[param] = self.parameterAsOutputLayer(paramList, param, context)

        if outputFiles is not None:
            for param in outputFiles:
                self.outputs[param] = self.parameterAsFile(paramList, param, context)


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
            #evaluatedParam = self.parameterAsEnumString(**args)
            evaluatedParam = self.parameterAsEnum(**args)
            if (evaluatedParam is not None): 
                evaluatedParam = param["list"][list(param["list"].keys())[evaluatedParam]] #TODO Assumption here is that list(param["list"].keys()) will return keys in\
                                                                                           #the same order as enums, and enums always start from 0 incrementing by 1. Does\
                                                                                           #python guarantee that?
        
        if (evaluatedParam is None):
            return None

        return [param["option"], evaluatedParam]

    def AddProcessCountInputParam(self):
        self.addParameter(QgsProcessingParameterNumber(name = self.PROC_COUNT, description = "Number of processes to use (Requires MPI enabled)", optional = False, defaultValue = 4, type = QgsProcessingParameterNumber.Integer))

    def initAlgorithm(self, config=None):
        for input in self.tool.inputParams:
            self.addParameter(self.QGISParameter(input, False))

        #process count is universal for all algorithms, not included int the descriptions
        self.AddProcessCountInputParam()

        for output in self.tool.outputParams:
            self.addParameter(self.QGISParameter(output, True))

    def processAlgorithm(self, parameters, context, feedback):
        feedback.pushInfo(f"Starting processing of tool {self.tool.displayName}") #test
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
            evaluatedParam = self.parameterAsOutputLayer(parameters,  output["option"][1:], context) #TODO should text ouputs (e.g. from drop analysis) be parameterAsFile instead?
            if (evaluatedParam is None):
                raise QgsProcessingException(self.invalidSinkError(parameters, output["option"][1:]))
            
            command += [output["option"], Utilities.WrapInQuotes(evaluatedParam)]
            
            if(output["type"] != "t"): #we only add rasters and vectors to qgis as a layer, not text
                results[output["option"][1:]] = evaluatedParam
            
        #handle processes count
        processCount = self.parameterAsInt(parameters, self.PROC_COUNT, context)

        #ExecuteTauDemTool expects a single string with command and all args, not a list of strings.
        command = " ".join(command)
        feedback.pushInfo(f"Executing {command}")
        Utilities.ExecuteTauDEMTool(command, processCount, feedback)        
        return results