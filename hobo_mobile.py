import os
import glob
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
#from mpl_toolkits.basemap import Basemap
import matplotlib.dates as mdates
from windrose import WindroseAxes
from matplotlib.ticker import FormatStrFormatter
from matplotlib.ticker import StrMethodFormatter

from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()

def read_H97(H97_fname):
    hobo = pd.read_csv(H97_fname, skiprows=2, usecols=(1, 2, 3, 4),
                       names=['Time', 'T', 'rh', 'Dpt'],
                       parse_dates={'time': [0]},
                       date_parser=lambda x: pd.to_datetime(x).strftime('%m/%d/%y %H:%M:%S'),
                       index_col='time')
    hobo = hobo[np.isfinite(hobo["T"])]  # dumps rows with NaNs
    return hobo

def read_lapup(lapup_fname):
    headers = ['time', 'LT', 'phi', 'ws','wd', 'wg']
    lapup = pd.read_csv(lapup_fname,usecols = [0,4,5,6,7,8], skiprows=1,
                     names = headers, parse_dates = True, index_col = 'time')
    return lapup

def read_gps(fname):
    '''Creates timeseries dataframe from 'AntiMap Log' .csv file'''
    # converts filename to Timestamp
    start_time = pd.to_datetime(os.path.basename(fname)[:-4], format='%d%m%y_%H%M_%S')
    utc_time = start_time - pd.Timedelta(hours=3)
    gps = pd.read_csv(fname, names=['lat', 'lon', 'time'], usecols=[0, 1, 5],
                      index_col='time')
    
    log_time = pd.to_timedelta(gps.index, unit='ms')  # ms to timedelta
    gps.index = utc_time + log_time  # adds timedeltas to Timestamp//
    gps = gps.resample('10s').mean()
    gps = gps[~gps.index.duplicated(keep='first')]  # dumps duplicates
    return gps    

def read_all(day):
    
    h97 = glob.glob(day+'H97*.csv')[0]
    hobo = read_H97(h97)
    #lapup = read_lapup('Meteo_1min_JUL2018_raw.zip')
    gpslist = glob.glob(day+'GPS/*.csv')
    gps_dflist = [read_gps(i) for i in gpslist]
    
    gps = pd.concat(gps_dflist, axis=0)
    gps = gps[~gps.index.duplicated(keep='first')]
    
    first = gps.iloc[0].name
    last = gps.iloc[-1].name
    dr = pd.date_range(first, last, freq='1s', name='Time')
    
    hobo = hobo.reindex(dr)
    #lapup = lapup.reindex(dr)
    gps = gps.reindex(dr)
    
    large_df = pd.concat([gps, hobo], axis=1)
    #df['uhii'] = df['T']-df['LT']
    return large_df

def make_dir(dirname):
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    return f"{dirname}/"


def plot_temp_map(df,z=None,cbar_label=None, folder = None):
    '''Plots temperature colorscale on Basemap'''
    x = df['lat']
    y = df['lon']
    plot_label = df.index[0].strftime("%d %b %Y, %H:%M")+" to "+df.index[0].strftime("%H:%M ")+"UTC"
    plt.figure(figsize=(14, 8))
    earth = Basemap(projection='cyl',llcrnrlat=38.18,urcrnrlat=38.30,
                    llcrnrlon=21.68, urcrnrlon=21.8, resolution='l', 
                    area_thresh=50, lat_0=38, lon_0=21)
    earth.arcgisimage(server='http://server.arcgisonline.com/ArcGIS', 
                service='ESRI_Imagery_World_2D', xpixels=720, ypixels=None, 
                dpi=300, verbose=False, )
#    earth.bluemarble(alpha=0.42)
#    earth.drawcoastlines(color='#555566', linewidth=1)
    plt.scatter(y, x,c=z,alpha=1, zorder=10)
    cbar = plt.colorbar()
    cbar.set_label(cbar_label)
    plt.xlabel(plot_label)
    if folder:
        filedate = df.index[0].strftime("%Y%m%d_%H%M")
        plt.savefig(make_dir(folder)+filedate+'.png',pad_inches='tight')


params = {'figure.figsize': (12, 4),
          'axes.titlesize': 18,
          'axes.titleweight': 'bold',
          'axes.labelsize': 18,
          'axes.labelweight': 'bold',
          'xtick.labelsize': 18,
          'ytick.labelsize': 18,
          'font.weight' : 'bold',
          'font.size': 18,}
plt.rcParams.update(params)

def plot_temp_rh(df,temp='LT',rh='phi',letter=None, title=False):
    '''Plots temperature and RH from LapUp timeseries sharing x axis'''
    date = str(df.index[0].date())
    fig, ax1 = plt.subplots()
    fig.text(0.01, 1, letter,fontsize=24, style='italic')
    if title:
        ax1.set_title(date,loc='left')
    ax1.plot(df[temp],color='C0')
    ax1.set_ylabel('Air Temperature (°C)')
#    ax1.yaxis.label.set_color('C0')
    ax1.tick_params(axis='y', colors='C0')
    ax1.yaxis.set_major_formatter(FormatStrFormatter('%.1f'))
    
    ymin = ax1.get_ylim()[0]
    ymax = ax1.get_ylim()[1]
    ax1.vlines(large.index[0],ymin,ymax, linestyles='dashed') # * unpacks tuple
    ax1.vlines(large.index[-1],ymin,ymax, linestyles='dashed')
    
    ax2 = ax1.twinx() 
    ax2.plot(df[rh],color='C1')
#    ax2.yaxis.label.set_color('C1')
    ax2.tick_params(axis='y', colors='C1')
    ax2.yaxis.set_major_formatter(FormatStrFormatter('%.0f'))
    ax2.set_ylabel('Relative Humidity (%)')#,fontsize=20, fontweight='bold'
    myFmt = mdates.DateFormatter('%H:%M')
    ax1.xaxis.set_major_formatter(myFmt)
    plt.savefig(f"{make_dir('Results/Plots/Lapup/')}{date}{letter[0]}.png",bbox_inches="tight")



def plot_windrose(df,letter=None, title=False):
    date = str(df.index[0].date())
    windf = df.drop(df[(df.ws == 0) & (df.wd == 0)].index)
    # Necessary to plot pies instead of triangles
    # see: https://github.com/python-windrose/windrose/issues/43
    plt.hist([0, 1])
    plt.close()
    fig = plt.figure(figsize=(14,9))
    fig.text(0.2, 0.95, letter,fontsize=24, style='italic')
    ax = WindroseAxes.from_ax(fig=fig)
    if title:
        ax.set_title(date)
    ax.bar(windf['wd'], windf['ws'], normed=True, opening=0.8, 
           edgecolor='black', bins=np.arange(0, 8, 1))
    ax.set_yticks(np.arange(10, 60, step=10))
    ax.set_yticklabels(np.arange(10, 60, step=10))
    ax.yaxis.set_major_formatter(StrMethodFormatter(u"{x:.0f}%"))
    ax.legend(loc='center left', bbox_to_anchor=(1.05, 0.5), title='Wind speed (m/s)')
    plt.savefig(f"{make_dir('Results/Plots/Lapup/')}{date}{letter[0]}.png")


days = glob.glob('Days/*/')
lapup = read_lapup('Meteo_1min_2019_raw.zip')
for day in days:
    large = read_all(day)
    lapup_day = lapup[str(large.index[0].date())]
    lapup_exp = lapup[str(large.index[0]):str(large.index[-1])]
    plot_temp_rh(lapup_day,letter='a)',title=True)
    plot_temp_rh(lapup_exp,letter='b)')
    plot_windrose(lapup_day,letter='c)')


