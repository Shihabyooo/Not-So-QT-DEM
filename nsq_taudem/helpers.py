from os import path as osPath, environ as osEnviron
from csv import reader as csvReader
from subprocess import Popen, PIPE, STDOUT
from itertools import islice
from platform import uname
from multiprocessing import cpu_count

from processing.core.ProcessingConfig import ProcessingConfig
from qgis.core import (Qgis,
                       QgsMessageLog,
                       QgsProcessingFeedback)
from qgis.PyQt.QtGui import QIcon

class Tool():
    def __init__(self):
        self.type = 0 #0 for non-staged (calls a single TauDEM exec), 1 for complicated tools
        self.name = "" #ascii alphanumeric only, no special characters nor spaces.
        self.displayName = "" #displayed ing QGIS toolbox
        self.group = "" #ascii alphanumeric only, no special characters nor spaces.
        self.groupDisplayName = "" #displayed ing QGIS toolbox
        self.exec = "" #either the name of the TauDEM executable, or the python script handling the staging
        self.inputParams = [] #list of dictionaries with detail of inputs for this tool. Keys expected: "desc", "option", "type", "isOptional", "default", or "list". See TauDEMToolsDesc.csv for details.
        self.outputParams = [] #ditto for outputs. Only expects "desc", "option", and "type"
        self.helpText = "" #An HTML text to be shown in the tool's dialogue.
        self.helpURL = "" #URL to be opened when user clicks on "help" button on the tool's dialogue.

class Utilities():
    DEFAULT_TAUDEM_PATH = "C:/Program Files/TauDEM/TauDEM5Exe/" #default for TauDEM 5.3 installer
    DEFAULT_MPI_PATH = "C:/Program Files/Microsoft MPI/Bin/" 
    DEFAULT_PROCESSOR_COUNT = 4

    @staticmethod
    def CheckSupportedPlaform() -> []: #[isSupported : boolean, platformName : str]
        platform = uname().system.lower()
        isSupported = False
        if platform == "windows":
            isSupported = True
        return [isSupported, platform]

    @staticmethod
    def IsValidDir(path : str) -> bool:
        return osPath.isdir(path)

    @staticmethod
    def FetchPath(settingName : str, default = "") -> str: #for directories set in settings.
        path = ProcessingConfig.getSetting(settingName)
        
        if path is None or not Utilities.IsValidDir(path):
            QgsMessageLog.logMessage(f"{settingName} is not set to a valid path in provider settings. Currently set path: \"{path}\". Will attempt to use default: \"{default}\"", level=Qgis.Warning, notifyUser = False)
            return default
        
        #add a trailing slash here
        if not (path.endswith("/") or path.endswith("\\")):
            path += "/"

        return path

    @staticmethod
    def TauDEMPath() -> str:
        return Utilities.FetchPath("TAUDEM_PATH", Utilities.DEFAULT_TAUDEM_PATH)
    
    @staticmethod
    def MPIPath() -> str:
       return Utilities.FetchPath("MPI_PATH", Utilities.DEFAULT_MPI_PATH)
    
    def GDALPath() -> str: #TODO figure out how to point to the GDAL libs QGIS ships with/uses (although it's probably better to use what TauDEM uses). Alternatively,\
        #implement similar to TauDEMPath() and MPIPath() with a DEFAULT_GDAL_PATH const, and expose setting in QGIS config menu.
        return "C:/Program Files/GDAL"

    @staticmethod
    def DescriptionFilePath() -> str:
        return osPath.dirname(__file__) + "/TauDEMToolsDesc.csv"
    
    @staticmethod
    def HelpTextFilePath(toolName : str) -> str:
        return osPath.dirname(__file__) + "/HelpTexts/" + toolName + ".txt"
    
    @staticmethod
    def ImageDirPath()->str:
        return osPath.dirname(__file__) + "/img/"

    @staticmethod
    def GetIcon() -> QIcon:
        return QIcon(Utilities.ImageDirPath() + "logo.png")
    
    @staticmethod
    def GetIconSVGPath() -> str:
        return Utilities.ImageDirPath() + "logo.svg"
    
    @staticmethod
    def SetPATH() -> None:
        #add only what's missing. Shouldn't be serious requirment for actual use, but multiple reloading and unloading of this plugin (like what happens in \
        #testing or enabling/disabling via plugins dialogue) with the "naive" implementation will end up with duplicates in PATH var for the QGIS session. 
        #Naive implementation:
        #osEnviron["PATH"] += ";".join([Utilities.TauDEMPath(), Utilities.MPIPath(), Utilities.GDALPath()])
        
        if not osEnviron["PATH"].endswith(";"): #not guaranteed. We could just force adding the ";" before requirePaths bellow, but i'd rather avoid having double ;; 
            osEnviron["PATH"] += ";"

        pathVars = osEnviron["PATH"].split(";")
        for requiredPath in [Utilities.TauDEMPath(), Utilities.MPIPath(), Utilities.GDALPath()]:
            if requiredPath not in pathVars:
                osEnviron["PATH"] += requiredPath + ";"
    
    @staticmethod
    def SetProcessorCount() -> None:
        Utilities.DEFAULT_PROCESSOR_COUNT = cpu_count()

    @staticmethod
    def SanitizeString(string : str) -> str: #returns a string with only lowercase, alphanumeric ASCII characters, no spaces, no special chars (although QGIS didn't object to hyphens)
        legalCharset = "abcdefghijklmnopqrstuvwxyz123456789"
        sanitizedString = ""
        
        loweredString = string.lower()

        for letter in loweredString:
            if letter in legalCharset:
                sanitizedString += letter

        if len(sanitizedString) < 1:
            QgsMessageLog.logMessage(f"Warning: When sanitizeing string {string}, result was an empty string", level=Qgis.Warning, notifyUser = False)

        return sanitizedString

    @staticmethod
    def ParseToolsDesc() -> list[Tool]:
        tools = []
        
        QgsMessageLog.logMessage(f"Parsing tools description file at \"{Utilities.DescriptionFilePath()}\"", level=Qgis.Info, notifyUser = False)

        try:
            descFile = open (Utilities.DescriptionFilePath(), mode="r", newline="")
        except Exception as exception:
            QgsMessageLog.logMessage(f"Failed to parse TauDEM tool descriptions file.", level=Qgis.Critical, notifyUser = True)
            QgsMessageLog.logMessage(f"Failed to open file: \"{Utilities.DescriptionFilePath()}\". Exception thrown: {str(exception)}", level=Qgis.Critical, notifyUser = False)
            return tools
            
        descFileParser = csvReader(descFile, delimiter= ",", quotechar = "\"")
    
        next(islice(descFileParser, 4, None)) #skip to start of first tool desc 
        
        for row in descFileParser:
            if row[0] in ["END", "End", "end"]: #end flag set to end parsing before eof. Mainly for testing
                QgsMessageLog.logMessage(f"Found a manual end flag while parsing the description file.", level=Qgis.Info, notifyUser = False)
                break

            tool = Tool()
            tool.type = int(row[0])
            if tool.type == 0: #input/output count is only useful (at this phase) for non-staged tools. Values may not be set in the desc file for staged tools, which would cause reading them to bug out.
                inputCount = int(row[1])
                outputCount = int(row[2])
            
            tool.displayName, tool.groupDisplayName, tool.exec = next(descFileParser)[0:3]
            tool.name = Utilities.SanitizeString(tool.displayName)
            tool.group = Utilities.SanitizeString(tool.groupDisplayName)
            
            #parse the tool's help text and URL
            helpTextURL = Utilities.ParseToolHelpTextURL(tool.name)
            tool.helpURL = helpTextURL["url"]
            tool.helpText = helpTextURL["text"]

            if tool.type != 0: #we only need to process the next for non-staged tools
                tools.append(tool)
                continue

            for input in range(0, inputCount):
                row = next(descFileParser)
                params = {  "desc" : row[0],
                            "option" : row[1],
                            "type" : row[2],
                            "isOptional" : int(row[3])}
                
                if row[4] != "": #we have a default value (or list elements) for this input
                    if params["type"] in ["b", "i"]:
                        params["default"] = int(row[4])
                    elif params["type"] == "f":
                        params["default"] = float(row[4])
                    elif params["type"] == "l":
                        subList = row[4].split("|")
                        subListDict = {}
                        for entry in subList:
                            pair = entry.split(":")
                            subListDict[pair[0]] = pair[1]
                        params["list"] = subListDict

                tool.inputParams.append(params)

            for output in range (0, outputCount):
                row = next(descFileParser)
                params = {"desc" : row[0], "option" : row[1], "type" : row[2]}
                tool.outputParams.append(params)

            tools.append(tool)
            
        QgsMessageLog.logMessage(f"Parsed {len(tools)} tools", level=Qgis.Success, notifyUser = False)
        descFile.close()
        return tools

    @staticmethod
    def ParseToolHelpTextURL(toolName : str) -> dict[str, str]: 
        result = {"url" : "", "text" : ""}

        try:
            helpTextFile = open (Utilities.HelpTextFilePath(toolName), "r")
        except Exception as exception:
            QgsMessageLog.logMessage(f"Failed to open help text file \"{Utilities.HelpTextFilePath(toolName)}\"", level=Qgis.Critical, notifyUser = False)
            QgsMessageLog.logMessage(f"Exception thrown: {str(exception)}", level=Qgis.Critical, notifyUser = False)
            return result
        
        for line in helpTextFile:
            if line[0] == "#": 
                continue
            sanitzedLine = line.strip().lower()
            if sanitzedLine in ["url", "text"]:
                value = ""
                for line in helpTextFile:
                    if line[0] != "#":
                        if not line.strip().lower() in ["end text", "end url"]:
                            value += line
                        else:
                            break
                result[sanitzedLine] = value.strip("\n")

        result["text"] = result["text"].replace("<imgdir>", Utilities.ImageDirPath())
        helpTextFile.close()
        return result

    #Supposedly, results for layer.source() may contain stuff other than the path (i.e. layer name, username, password, etc) This method 
    #sanitizes it and returns only the path. 
    #This trick is copied from ArrNorm plugin. The QGIS docs state that other info may be included with path, but it doesn't state
    #the format. 
    #TODO research this further.
    @staticmethod
    def GetLayerAbsolutePath(layer : str) -> str:
        if layer is None:
            return ""
        return layer.source().split("|layername")[0]
    
    @staticmethod
    def WrapInQuotes(path : str) -> str:
        return "\""+path+"\""

    #TODO consider disabling MPI if mpiProcessCount is set to 1
    @staticmethod
    def GetPlatformSpecificCommand(command : str, mpiProcessCount : int) -> str:
        
        platformSupportStatus = Utilities.CheckSupportedPlaform()
        if not platformSupportStatus[0]:
            return ""

        useMPI = ProcessingConfig.getSetting("USE_MPI")
        
        if platformSupportStatus[1] == "windows": #use Microsoft's MPI (if enabled) and prepend "cmd.exe /C " to the command
            if useMPI:
                 command = "mpiexec -n " + str(mpiProcessCount) + " " + command
            return "cmd.exe /C " + Utilities.WrapInQuotes(command)
        elif platformSupportStatus[1] == "linux": #TODO implement
            if useMPI:
                pass
            return ""
        elif platformSupportStatus[1] == "darwin": #Anyone willing to shell out $$$ on Apple's overpriced walled garden is welcome to implement and test this...
            if useMPI:
                pass
            return ""
        else: #Shouldn't -practically- happen, but still.
            return ""

    @staticmethod
    def ExecuteTauDEMTool(command : str, mpiProcessCount : int, feedback : QgsProcessingFeedback) -> None: #command is string that starts with exec name WITHOUT absolute path to TauDEM instllation.
        #Ensure useful process count value
        if mpiProcessCount < 1:
            feedback.pushInfo(f"Warning: Invalid process count value {mpiProcessCount}. Setting to 1")
            mpiProcessCount = max(1, mpiProcessCount)

        command = Utilities.GetPlatformSpecificCommand(command, mpiProcessCount)
        if command == "": #should happen only with unsupported system.
            feedback.reportError("Error! This operating system is not supported by this plugin.", True)
            return
        
        feedback.pushInfo(f"Executing shell command: {command}")

        #TODO implement process cancelling
        with Popen(  command,
                                shell=True,
                                stdout=PIPE,
                                stderr=STDOUT,
                                universal_newlines=True) as process:
            try:
                for output in iter(process.stdout.readline, ''):
                    feedback.pushInfo(output)
            except Exception as exception:  # noqa  # pylint:disable=bare-except
                feedback.pushInfo(f"caught exception: {str(exception)}") 