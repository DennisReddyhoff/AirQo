from scipy import interpolate
import numpy as np

def getgrid(xstart, xend, ystart, yend, gridsize):
    xnew = np.linspace(xstart, xend, gridsize)
    ynew = np.linspace(ystart, yend, gridsize)
    xgrid, ygrid = np.meshgrid(xnew,ynew)
    xgrid = xgrid.reshape(np.square(gridsize)).tolist()
    ygrid = ygrid.reshape(np.square(gridsize)).tolist()
    
    return xnew, ynew, xgrid, ygrid

def merc(lon, lat):
    ''' Get mercator projection co-ordinates from latitude and logitude'''
    x=[]
    y=[]
    r_major = 6378137.000
    for i in range(len(lon)):
        x.append(r_major * np.radians(lon[i])) 
        scale = x[i]/lon[i]
        y.append(180.0/np.pi * np.log(np.tan(np.pi/4.0 + 
         lat[i]* (np.pi/180.0)/2.0)) * scale)
    return x, y

def lonlat(x, y):
    lon = []
    lat = []
    r_major = 6378137.000
    for i in range(len(x)):
        lon.append(np.degrees(x[i]/r_major))
        scale = lon[i]/x[i]
        lat.append(2.0*(np.arctan(np.exp(np.pi*y[i]/180.0*scale))-np.pi/4.0)*180.0/np.pi)
    return lon, lat
    
def interp(predmeans, predvars, Xtest):
    gridx, gridy = merc(Xtest[0][0].tolist(), Xtest[1].T[0])
    mean_interp = interpolate.RectBivariateSpline(gridx, gridy, predmeans.reshape(150,150))
    var_interp = interpolate.RectBivariateSpline(gridx, gridy, predvars.reshape(150,150))
    
    return mean_interp, var_interp
