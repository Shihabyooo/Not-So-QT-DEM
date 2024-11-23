from os import listdir, path

__all__ = []

for file in listdir(path.dirname(__file__)):
    if file.endswith(".py"):
        __all__.append(file[0:-3])