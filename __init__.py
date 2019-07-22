# -*- coding: utf-8 -*-

__author__ = 'Stamen Design LLC'
__date__ = '2019-07-21'
__copyright__ = '(C) 2019 by Stamen Design LLC'


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load Stamen class from file Stamen.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .stamen import StamenPlugin
    return StamenPlugin()
