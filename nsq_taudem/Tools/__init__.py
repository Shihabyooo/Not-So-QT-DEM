from os import listdir, path

__all__ = []
excluded = ["CreateParameterRegionGrid.py", "StabilityIndex.py"] #Don't want these tools to be exposed in QGIS yet (till I figure out whether to finish them or nix them)

for file in listdir(path.dirname(__file__)):
    if file.endswith(".py") and file not in excluded:
        __all__.append(file[0:-3])