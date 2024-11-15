import os
import csv
from itertools import islice
import subprocess

from processing.core.ProcessingConfig import ProcessingConfig
#from processing.tools.system import isWindows, isMac, userFolder
#from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (Qgis,
                       QgsApplication,
                       QgsMessageLog,
                       QgsProcessingFeedback)

#TODO create a utility that converts non-supported vector formats to shp
#TauDEM docs state they accept all raster formats supported by GDAL, so we don't need to manipulte them(?)

class Tool():
    def __init__(self):
        self.type = 0 #0 for non-staged (calls a single TauDEM exec), 1 for complicated tools
        self.name = "" #ascii alphanumeric only, no special characters nor spaces.
        self.displayName = "" #displayed ing QGIS toolbox
        self.group = "" #ascii alphanumeric only, no special characters nor spaces.
        self.groupDisplayName = "" #displayed ing QGIS toolbox
        self.exec = "" #either the name of the TauDEM executable, or the python script handling the staging
        self.inputParams = [] #list of dictionaries with detail of inputs for this tool. Keys expected: "desc", "option", "type", "isOptional", "default". See TauDEMToolsDesc.csv for details.
        self.outputParams = [] #ditto for outputs. Only expects "desc", "option", and "type"

class Utilities():
    DEFAULT_TAUDEM_PATH = "C:\\Program Files\\TauDEM\\TauDEM5Exe\\" #default for TauDEM 5.3 installer
    DEFAULT_MPI_PATH = "C:\\Program Files\\Microsoft MPI\\Bin\\" 
    
    @staticmethod
    def IsValidDir(path):
        return os.path.isdir(path)

    @staticmethod
    def FetchPath(settingName, default = ""): #for directories set in settings.
        path = ProcessingConfig.getSetting(settingName)
        
        if path is None or not Utilities.IsValidDir(path):
            QgsMessageLog.logMessage(f"{settingName} is not set to a valid path in provider settings. Currently set path: \"{path}\". Will attempt to use default: \"{default}\"", "Processing", Qgis.Warning)
            return default
        
        #add a trailing slash here
        if not (path.endswith("/") or path.endswith("\\")):
            path += "/"

        return path

    @staticmethod
    def TauDEMPath():
        return Utilities.FetchPath("TAUDEM_PATH", Utilities.DEFAULT_TAUDEM_PATH)
    
    @staticmethod
    def MPIPath():
       return Utilities.FetchPath("MPI_PATH", Utilities.DEFAULT_MPI_PATH)
    
    def GDALPath(): #TODO figure out how to point to the GDAL libs QGIS ships with/uses (although it's probably better to use what TauDEM uses). Alternatively,\
        #implement similar to TauDEMPath() and MPIPath() with a DEFAULT_GDAL_PATH const, and expose setting in QGIS config menu.
        return "C:\\Program Files\\GDAL"

    @staticmethod
    def DescriptionFilePath():
        return os.path.dirname(__file__)+"/TauDEMToolsDesc.csv"

        
    @staticmethod
    def SetPATH():
        #add only what we need. Shouldn't be serious requirment for actual use, but multiple reloading and unloading of this plugin (like what happens in \
        #testing or enabling/disabling via plugins dialogue) with the "naive" implementation will end up with duplicates in PATH var for the QGIS session. 
        #Native implementation:
        #os.environ["PATH"] += ";".join([Utilities.TauDEMPath(), Utilities.MPIPath(), Utilities.GDALPath()])
        
        if (not os.environ["PATH"].endswith(";")): #not guaranteed. We could just force adding the ";" before requirePaths bellow, but i'd rather avoid having double ;; 
            os.environ["PATH"] += ";"

        pathVars = os.environ["PATH"].split(";")
        for requiredPath in [Utilities.TauDEMPath(), Utilities.MPIPath(), Utilities.GDALPath()]:
            if requiredPath not in pathVars:
                os.environ["PATH"] += requiredPath + ";"
        

    @staticmethod
    def ParseToolsDesc():
        tools = []
        
        QgsMessageLog.logMessage(f"Parsing tools description file at \"{Utilities.DescriptionFilePath()}\"", level=Qgis.Info)

        with open (Utilities.DescriptionFilePath(), mode="r", newline="") as descFile:
            descFileParser = csv.reader(descFile, delimiter= ",", quotechar = "\"")
        
            next(islice(descFileParser, 4, None)) #skip to start of first tool desc
            
            for row in descFileParser:
                if(row[0] in ["END", "End", "end"]): #end flag set to end parsing before eof. Mainly for testing
                    QgsMessageLog.logMessage(f"Found a manual end flag while parsing the description file.", level=Qgis.Warning)
                    break

                tool = Tool()
                
                tool.type = int(row[0])
                inputCount = int(row[1])
                outputCount = int(row[2])
                
                tool.displayName, tool.groupDisplayName, tool.exec = next(descFileParser)[0:3]
                tool.name = tool.displayName.replace(" ", "").lower()
                tool.group = tool.groupDisplayName.replace(" ", "").lower()
                
                QgsMessageLog.logMessage(f"Parsed \"{tool.group}/{tool.name}\"", level=Qgis.Info)

                if (tool.type != 0): #we only need to process the next for non-staged tools
                    tools.append(tool)
                    continue

                for input in range(0, inputCount):
                    row = next(descFileParser)
                    params = {  "desc" : row[0],
                                "option" : row[1],
                                "type" : row[2],
                                "isOptional" : int(row[3])}
                    
                    if row[4] != "": #we have a default value for this input
                        if params["type"] in ["b", "i"]:
                            params["default"] = int(row[4])
                        elif params["type"] == "f":
                            params["default"] = float(row[4])

                    tool.inputParams.append(params)

                for output in range (0, outputCount):
                    row = next(descFileParser)
                    params = {  "desc" : row[0],
                                "option" : row[1],
                                "type" : row[2]}
                    tool.outputParams.append(params)

                tools.append(tool)
                
            QgsMessageLog.logMessage(f"Parsed {len(tools)} tools", level=Qgis.Success)
            return tools
        
        QgsMessageLog.logMessage("Failed to parse TauDEM tools file (Error opening file)", Qgis.Warning)
        return []

    @staticmethod
    def GetToolExplanationText(toolName : str): #TODO implement
        return ""

    def GetToolHelpURL(toolName : str): #TODO implement
        return ""

    #Supposedly, results for layer.source() may contain stuff other than the path (i.e. layer name, username, password, etc) This method 
    #sanitizes it and returns only the path. 
    #This trick is copied from ArrNorm plugin. The QGIS docs state that other info may be included with path, but it doesn't state
    #the format. 
    #TODO research this further.
    @staticmethod
    def GetLayerAbsolutePath(layer):
        return layer.source().split("|layername")[0]
    
    @staticmethod
    def WrapInQuotes(path):
        return "\""+path+"\""

    @staticmethod
    def ExecuteTauDEMTool(command, threads, feedback : QgsProcessingFeedback): #command is string that starts with exec name WITHOUT absolute path to TauDEM instllation.
        #Ensure useful thread value
        if (threads < 1):
            feedback.pushInfo(f"Warning: Invalid thread count value {threads}. Setting to 1")
            threads = max(1, threads)
        
        if (ProcessingConfig.getSetting("USE_MPI")):
            feedback.pushInfo(f"Microsoft MPI use enabled. Using {threads} thread(s)")
            command = "mpiexec -n " + str(threads) + " " + command
        else:
            feedback.pushInfo(f"Microsoft MPI use disabled")

        command = "cmd.exe /C " + Utilities.WrapInQuotes(command)

        feedback.pushInfo(f"Executing shell command: {command}")

        #TODO implement process cancelling
        with subprocess.Popen(  command,
                                shell=True,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,
                                universal_newlines=True) as process:
            try:
                for output in iter(process.stdout.readline, ''):
                    feedback.pushInfo(output)
            except Exception as exception:  # noqa  # pylint:disable=bare-except
                feedback.pushInfo(f"caught exception: {exception}") 