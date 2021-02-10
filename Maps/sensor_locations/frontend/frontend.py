from flask import Flask
from bokeh.embed import file_html
from bokeh.resources import CDN
import getmap

frontend = Flask(__name__)

@frontend.route('/')
def main():
    map = getmap.get_map()
    return file_html(map, CDN, "Sensor Locations")
