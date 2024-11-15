from processing.core.ProcessingConfig import ProcessingConfig, Setting
from qgis.core import QgsProcessingProvider
from .helpers import Utilities, Tool
from .AlgorithmGenerator import Algorithm


class TauDEMProvider(QgsProcessingProvider):

    def __init__(self):
        QgsProcessingProvider.__init__(self)

    
    def load(self):
        #TODO set icon.
        #ProcessingConfig.settingIcons["TauDEM"] = self.icon() 

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
            self.addAlgorithm(Algorithm(tool))

    def id(self):
        return 'TauDEM'

    def name(self):
        return self.tr('TauDEM')

    def icon(self):
        return QgsProcessingProvider.icon(self)

    def longName(self):
        return self.name()
