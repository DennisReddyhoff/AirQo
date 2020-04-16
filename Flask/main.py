#!/usr/bin/env python
# coding: utf-8

# In[ ]:

import redis
import msgpack
import msgpack_numpy as mnp
pool = redis.ConnectionPool(host='34.69.39.105', port=6379, db=0)
r = redis.Redis(connection_pool=pool)
from flask import Flask, jsonify, request
from flask_cors import CORS
app = Flask(__name__)
CORS(app)


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

predmeans = mnp.unpackb(r.get('predmeans'), raw=True)
predvars = mnp.unpackb(r.get('predvars'), raw=True)
Xtest = mnp.unpackb(r.get('Xtest'), raw=True)

gridx, gridy = merc(Xtest[0][0].tolist(), Xtest[1].T[0])
mean_interp = interpolate.RectBivariateSpline(gridx, gridy, predmeans.reshape(150,150))
var_interp = interpolate.RectBivariateSpline(gridx, gridy, predvars.reshape(150,150))

@app.route('/updateinterp', methods=['POST'])
def updateinterp():
    predmeans = mnp.unpackb(r.get('predmeans'), raw=True)
    predvars = mnp.unpackb(r.get('predvars'), raw=True)
    Xtest = mnp.unpackb(r.get('Xtest'), raw=True)

    gridx, gridy = merc(Xtest[0][0].tolist(), Xtest[1].T[0])
    mean_interp_tmp = interpolate.RectBivariateSpline(gridx, 
                                                      gridy, 
                                                      predmeans.reshape(150,150))
    var_interp_tmp = interpolate.RectBivariateSpline(gridx, 
                                                     gridy, 
                                                     predvars.reshape(150,150))
    global mean_interp 
    mean_interp = mean_interp_tmp
    global var_interp 
    var_interp = var_interp_tmp
    return jsonify("",200)


@app.route('/',methods=['GET', 'POST'])
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

