# Not-So-QT-DEM

An unofficial processing provider plugin for Terrain Analysis Using Digital Elevation Models (TauDEM) version 5.3.x for QGIS (Windows only)

Using this plugin requires manual download and installation of TauDEM tools
https://hydrology.usu.edu/taudem/taudem5/ 

Currently, installing this plugin requires manually copying the directory "nsq_taudem" to your QGIS plugins directory (default is %APPDATA%\QGIS\QGIS3\profiles\default\python\plugins), then enable the plugin from QGIS's plugin manager (QGIS menu bar -> Plugins -> Manage and install plugins -> Installed -> Tick the box next to "Not-So-QT-DEM")
Or you can zip the nsq_taudem directory and use QGIS "Install from Zip" dialogue in the plugin manager.

Make sure to set paths to your TauDEM, GDAL and Microsoft MPI installations in the providers settings (QGIS menu bar -> Settings menu -> Options -> Processing -> Providers -> TauDEM)

This implementation tries to mimic the official ArcGIS toolbox as much as possible. All of the algorithms in the ArcGIS toolbox are available in nsqDEM except for the two SINMAP tools.

This code is licensed under GNU Affero General Public License v3.0. 
