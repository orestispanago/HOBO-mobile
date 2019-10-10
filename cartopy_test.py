import matplotlib.pyplot as plt

import cartopy.crs as ccrs
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER

def make_map(projection=ccrs.PlateCarree()):
    fig, ax = plt.subplots(figsize=(9, 13),
                           subplot_kw=dict(projection=projection))
    gl = ax.gridlines(draw_labels=True)
    gl.xlabels_top = gl.ylabels_right = False
    gl.xformatter = LONGITUDE_FORMATTER
    gl.yformatter = LATITUDE_FORMATTER
    return fig, ax

import cartopy.io.img_tiles as cimgt

extent = [21.65, 21.85, 38.18, 38.32]

request = cimgt.GoogleTiles(style='satellite')

fig, ax = make_map(projection=request.crs)
ax.set_extent(extent)

ax.add_image(request, 8)
#ax.add_image(request, 10, interpolation='spline36') # for better resolution, see https://stackoverflow.com/questions/49155110/why-do-my-google-tiles-look-poor-in-a-cartopy-map
#
#import numpy as np 
#import matplotlib as mpl        
#import matplotlib.pyplot as plt 
#import cartopy.crs as ccrs
#import cartopy.io.img_tiles as cimgt
#import six
#
#
#import numpy as np 
#import matplotlib as mpl        
#import matplotlib.pyplot as plt 
#import cartopy.crs as ccrs
#import cartopy.io.img_tiles as cimgt
#
#fig, ax = plt.subplots(figsize=(9, 13), subplot_kw=dict(projection=ccrs.PlateCarree()))
#request = cimgt.GoogleTiles(style='satellite')
#extent = [21.65, 21.85, 38.18, 38.32]
#ax = plt.axes(projection=request.crs)
#ax.set_extent(extent)
#
#ax.add_image(request, 14,interpolation='spline36')
#plt.show()
