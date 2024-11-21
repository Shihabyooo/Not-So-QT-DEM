from processing.core.ProcessingConfig import ProcessingConfig, Setting
from qgis.core import QgsProcessingProvider, QgsApplication, QgsMessageLog, Qgis
from .helpers import Utilities
#from .Tools.AlgorithmGenerator import Algorithm
from .Tools import *
import sys, os

class TauDEMProvider(QgsProcessingProvider):

    def __init__(self):
        QgsProcessingProvider.__init__(self)

    
    def load(self):
        ProcessingConfig.settingIcons["TauDEM"] = self.icon() 

        ProcessingConfig.addSetting(Setting("TauDEM", #group
                                             "TAUDEM_PATH", #variable name
                                             "TauDEM directory", #display string
                                             Utilities.DEFAULT_TAUDEM_PATH, #default value
                                             valuetype=Setting.FOLDER)) #value type
        
        ProcessingConfig.addSetting(Setting("TauDEM",
                                            "USE_MPI",
                                            "Use Microsoft MPI",
                                            True))
        
        ProcessingConfig.addSetting(Setting("TauDEM",
                                             "MPI_PATH",
                                             "Microsoft MPI directory",
                                             Utilities.DEFAULT_MPI_PATH,
                                             valuetype=Setting.FOLDER))
         
        ProcessingConfig.readSettings()
        self.refreshAlgorithms() #TODO does this imply loadAlgorithms()? What else?
        Utilities.SetPATH()
        return True

    def unload(self):
        ProcessingConfig.removeSetting("TAUDEM_PATH")        

    def loadAlgorithms(self):
        for tool in Utilities.ParseToolsDesc():
            if (tool.type == 0):
                self.addAlgorithm(AlgorithmGenerator.Algorithm(tool))
            else:
                moduleName = f"{os.path.basename(os.path.normpath(os.path.dirname(__file__)))}.Tools.{tool.exec[0:-3]}"
                
                if moduleName in sys.modules:
                    module = sys.modules[moduleName]
                    self.addAlgorithm(module.StagedAlgorithm(tool))

    def id(self):
        return 'TauDEM'

    def name(self):
        return self.tr('TauDEM')

    def icon(self):
        return Utilities.GetIcon()
    
    def svgIconPath(self):
        return Utilities.GetIconSVGPath()

    def longName(self):
        return self.name()
