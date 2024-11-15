# -*- coding: utf-8 -*-
__author__ = 'Shihab E.'
__date__ = '2024-11-12'
__copyright__ = '(C) 2024 by Shihab E.'


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """
    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .TauDEMPlugin import TauDEMPlugin
    return TauDEMPlugin()
