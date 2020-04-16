import numpy as np
from flask import request
from interpolate import lonlat

def getresponse(request, mean_interp, var_interp):
    
    xstart = float(request.args["xstart"])
    xend = float(request.args["xend"])
    ystart = float(request.args["ystart"])
    yend = float(request.args["yend"])
    gridsize = int(request.args["gridsize"])
    
    xnew = np.linspace(xstart, xend, gridsize)
    ynew = np.linspace(ystart, yend, gridsize)
    xgrid, ygrid = np.meshgrid(xnew,ynew)
    xgrid = xgrid.reshape(np.square(gridsize)).tolist()
    ygrid = ygrid.reshape(np.square(gridsize)).tolist()
    
    lon, lat = lonlat(xgrid, ygrid)
    means = mean_interp(xnew,ynew)
    vars = var_interp(xnew,ynew)
    sizes = 150*np.log(1 + 300/np.sqrt(vars.reshape(np.square(gridsize)).tolist()))
    
    response = {"xgrid": xgrid,
                "ygrid": ygrid,
                "means": means.reshape(np.square(gridsize)).tolist(),
                "vars": vars.reshape(np.square(gridsize)).tolist(),
                "lon": lon,
                "lat": lat,
                "sizes": sizes.tolist()}
    
    return response