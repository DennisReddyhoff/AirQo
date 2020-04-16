from gpmodel import gpmodel
from interpolate import interp, lonlat, getgrid
from getresponse import getresponse
from flask import Flask, jsonify, request, render_template
from getmap import getmap
import numpy as np
from bokeh.embed import file_html
from bokeh.resources import CDN
import time
import threading

app = Flask(__name__)

def run_models():
    global mean_interp, var_interp
    
    while True:
        print("* Updating GP model *")
        predmeans, predvars, Xtest = gpmodel()
        temp_interp = interp(predmeans, predvars, Xtest)
        print("* Updating interpolator *")
        mean_interp, var_interp = temp_interp
        print("* Sleeping for 1 hour *")
        time.sleep(3600)
        
threading.Thread(target=run_models, name="interpolator", daemon=True).start()        

@app.route('/api',methods=['GET', 'POST'])
def main():        
    response = getresponse(request, mean_interp, var_interp)        
    return jsonify(response)

@app.route('/')
def showmap():
    map = getmap()
    return file_html(map, CDN, "Kampala")