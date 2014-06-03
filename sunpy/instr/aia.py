# -*- coding: utf-8 -*-
"""
Provides processing routines for data captured with the AIA instrument on SDO.
"""
import numpy as np
from sunpy.image.rotate import affine_transform
from sunpy.map.sources.sdo import AIAMap
from copy import deepcopy

def aiaprep(aiamap):
    """    
    Processes a level 1 AIAMap into a level 1.5 AIAMap

    Parameters
    ----------
    aiamap: AIAMap instance
        A sunpy map from AIA

    Returns
    -------
    A level 1.5 copy of aiamap
    """
    assert isinstance(aiamap, AIAMap)

    scale_ref = 0.6
    scale_factor = aiamap.scale['x'] / scale_ref
    angle = np.radians(-aiamap.rotation_angle['y'])

    c = np.cos(angle)
    s = np.sin(angle)
    rmatrix = np.array([[c, -s], [s, c]])

    map_center = (aiamap.shape[1] - aiamap.reference_pixel['x'],
                  aiamap.shape[0] - aiamap.reference_pixel['y'])

    newmap = deepcopy(aiamap)
    data = newmap.data
    newmap.data = affine_transform(data, rmatrix=rmatrix, recenter=True,
                                   scale=scale_factor, rotation_center=map_center,
                                   missing=aiamap.min())

    # Update header values as needed
    newmap.meta['crpix1'] = newmap.shape[1]/2.0 - 0.5
    newmap.meta['crpix2'] = newmap.shape[0]/2.0 - 0.5
    newmap.meta['cdelt1'] = scale_ref
    newmap.meta['cdelt2'] = scale_ref
    newmap.meta['crota1'] = 0.0
    newmap.meta['crota2'] = 0.0
    newmap.meta['lvl_num'] = 1.5

    return newmap
