import os
import sys
import inspect

from qgis.core import QgsApplication, QgsMessageLog, Qgis

from .TauDEMProvider import TauDEMProvider
from .helpers import Utilities

cmd_folder = os.path.split(inspect.getfile(inspect.currentframe()))[0]

if cmd_folder not in sys.path:
    sys.path.insert(0, cmd_folder)


class TauDEMPlugin(object):

    def __init__(self):
        self.provider = None

    def initProcessing(self):
        """Init Processing provider for QGIS >= 3.8."""
        platformSupportStatus = Utilities.CheckSupportedPlaform()
        if not platformSupportStatus[0]:
            QgsMessageLog.logMessage(f"Error! This operating system \"{platformSupportStatus[1]}\" is not supported!", level=Qgis.Critical, notifyUser = True)
        self.provider = TauDEMProvider()
        QgsApplication.processingRegistry().addProvider(self.provider)

    def initGui(self):
        self.initProcessing()

    def unload(self):
        QgsApplication.processingRegistry().removeProvider(self.provider)
