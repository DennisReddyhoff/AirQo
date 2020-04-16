from gpmodel import gpmodel
from interpolate import interp, lonlat, getgrid
from flask import Flask, jsonify, request, render_template
from getmap import getmap
import numpy as np
from bokeh.embed import file_html
from bokeh.resources import CDN
#from scipy import interpolate
app = Flask(__name__)

predmeans, predvars, Xtest = gpmodel()
mean_interp, var_interp = interp(predmeans, predvars, Xtest)

@app.route('/api',methods=['GET', 'POST'])
def main():
        
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
    
    
    return jsonify({"xgrid": xgrid,
                    "ygrid": ygrid,
                    "means": means.reshape(np.square(gridsize)).tolist(),
                    "vars": vars.reshape(np.square(gridsize)).tolist(),
                    "lon": lon,
                    "lat": lat,
                    "sizes": sizes.tolist()})

@app.route('/')
def showmap():
    map = getmap()
    return file_html(map, CDN, "Kampala")