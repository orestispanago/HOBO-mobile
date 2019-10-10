import os
import glob
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# make sure to set workdir in QGIS python console
os.chdir("C:\\Users\\user\\Mega\\Drafts\\Hobo-mobile\\QGIS\\Temperature")
print(os.getcwd())

def make_dir(dirname):
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    return f"{dirname}/"


def read_H97(H97_fname):
    hobo = pd.read_csv(H97_fname, skiprows=2, usecols=(1, 2),
                       names=['Time', 'T'],
                       parse_dates={'time': [0]},
                       date_parser=lambda x: pd.to_datetime(x).strftime('%m/%d/%y %H:%M:%S'),
                       index_col='time')
    hobo = hobo[np.isfinite(hobo["T"])]  # dumps rows with NaNs
    return hobo


def read_gps(fname):
    '''Creates timeseries dataframe from 'AntiMap Log' .csv file'''
    # converts filename to Timestamp
    start_time = pd.to_datetime(os.path.basename(fname)[:-4], format='%d%m%y_%H%M_%S')
    utc_time = start_time - pd.Timedelta(hours=3)
    gps = pd.read_csv(fname, names=['lat', 'lon', 'time'], usecols=[0, 1,5],
                      index_col='time')
    
    log_time = pd.to_timedelta(gps.index, unit='ms')  # ms to timedelta
    gps.index = utc_time + log_time  # adds timedeltas to Timestamp//
    gps = gps.resample('1s').mean()
    gps = gps[~gps.index.duplicated(keep='first')]  # dumps duplicates
    return gps    

def read_mobile(day, direction=""):
    ''' Reads HOBO values and lat lon and concatetates to timeseries dataframe'''
    h97 = glob.glob(day+'H97*.csv')[0]
    hobo = read_H97(h97)
#    lapup = read_lapup('Meteo_1min_2019_raw.zip')
    gpslist = glob.glob(day+f'GPS/{direction}/*.csv')
    gps_dflist = [read_gps(i) for i in gpslist]
    
    gps = pd.concat(gps_dflist, axis=0)
    gps = gps[~gps.index.duplicated(keep='first')]
#    lapup = lapup[~lapup.index.duplicated(keep='first')]
    
    first = gps.iloc[0].name
    last = gps.iloc[-1].name
    dr = pd.date_range(first, last, freq='1s', name='Time')
    
    hobo = hobo.reindex(dr)
#    lapup = lapup.reindex(dr)
    gps = gps.reindex(dr)
    
    large_df = pd.concat([gps, hobo], axis=1)
    #df['uhii'] = df['T']-df['LT']
    return large_df


def plot_temp_map(df,z=None,cbar_label=None, folder = None):
    '''Plots temperature colorscale on Basemap'''
    x = df['lat']
    y = df['lon']
    plot_label = df.index[0].strftime("%d %b %Y, %H:%M")+" to "+df.index[-1].strftime("%H:%M ")+"UTC"
    plt.figure(figsize=(14, 8))
#    earth.bluemarble(alpha=0.42)
#    earth.drawcoastlines(color='#555566', linewidth=1)
    plt.scatter(y, x,c=z,alpha=1, zorder=10)
    cbar = plt.colorbar()
    cbar.set_label(cbar_label)
    plt.xlabel(plot_label)
    if folder:
        filedate = df.index[0].strftime("%Y%m%d_%H%M")
        plt.savefig(make_dir(folder)+filedate+'.png',pad_inches='tight')
    plt.show()

def write_merged():
    ''' Writes dataframes to csv files in Merged folder'''
    days = glob.glob('Days/*/')
    for day in days:
        mobile = read_mobile(day)
        #plot_temp_map(mobile, z=mobile['T'],cbar_label='Temperature ($\degree$C)')
        fpath = f"{make_dir('Merged')}{mobile.index[0].date()}.csv"
        mobile.to_csv(fpath)
        

""" QGIS specific functions"""

def csv_to_layers(load_layers=False,shapefiles_expdir=None):
    ''' Creates layers from csv files'''
    csvfiles = glob.glob(os.getcwd()+'/Merged/*.csv')
    for fpath in csvfiles:
        fname = os.path.basename(fpath).split('.')[0]
        vlayer = QgsVectorLayer(f"file:///{fpath}?type=csv&detectTypes=yes&xField=lon&yField=lat&crs=EPSG:4326&spatialIndex=no&subsetIndex=no&watchFile=no", fname, "delimitedtext")
        if load_layers:
            QgsProject.instance().addMapLayer(vlayer)
        if shapefiles_expdir:
            expdir = os.getcwd()+'/'+make_dir(shapefiles_expdir)
            writer = QgsVectorFileWriter.writeAsVectorFormat(vlayer,f"{expdir}{fname}.shp", "utf-8",driverName='ESRI Shapefile')

def load_shapefiles(folder=None):
    ''' Loads vector layers in QGIS '''
    shpfiles = glob.glob(os.getcwd()+f'/Shapefiles/{folder}*.shp')
    for shp in shpfiles:
        fname = os.path.basename(shp).split('.')[0]
        layer = QgsVectorLayer(shp, fname, "ogr")
        QgsProject.instance().addMapLayer(layer)
        
#write_merged()
# WARNING: export_shapefales will write on top of existing shapefiles        
csv_to_layers(shapefiles_expdir="Shapefiles/raw")

    
load_shapefiles(folder='raw/')
#load_shapefiles(folder='processed/')
