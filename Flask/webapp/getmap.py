import numpy as np
from bokeh.models import Circle, ColumnDataSource,Plot,ColorBar, HoverTool, CustomJS, AjaxDataSource
from bokeh.plotting import figure, save
from bokeh.transform import linear_cmap
from bokeh.palettes import YlOrBr
from bokeh.tile_providers import Vendors, get_provider
from bokeh.io import show, output_notebook, output_file
from bokeh.events import Event, LODEnd
from bokeh.embed import components, file_html
from bokeh.resources import CDN
import requests
from interpolate import merc

def getmap():

    x0, y0, xend, yend = [32.4], [0.01], [32.8], [0.5]
    mercx0, mercy0 = merc(x0, y0)
    mercxend, mercyend = merc(xend, yend)
    gridsize = 20

    url = "http://127.0.0.1:5000/api?xstart={}&xend={}&ystart={}&yend={}&gridsize={}".format(mercx0[0],
                                                                                          mercxend[0],
                                                                                          mercy0[0],
                                                                                          mercyend[0],
                                                                                          gridsize)
    init_json = requests.get(url).json()

    # Get map tiles
    tile_provider = get_provider(Vendors.CARTODBPOSITRON)

    # Create ColumnDataSource from coordinates, sizes and predicted means
    source = ColumnDataSource(dict(xgrid=init_json["xgrid"], 
                                   ygrid=init_json["ygrid"], 
                                   sizes=init_json["sizes"], 
                                   means=init_json["means"], 
                                   vars=np.sqrt(init_json["vars"]).tolist(), 
                                   lat=init_json["lat"], 
                                   lon=init_json["lon"]))

    # Create linear colour map for pollution data
    mapper = linear_cmap(field_name='means', palette=YlOrBr[9][::-1] ,low=0 ,high=max(init_json["means"]))

    # Tooltips
    tooltips = [("Lat/long", "@lat, @lon"),
                ("Predicted PM2.5", "@means"),
                ("Predicted Variance", "@vars")]

    # Plot figure and add tiles 
    scaled_map = figure(title=None, x_range=(mercx0[0], mercxend[0]), y_range=(mercy0[0], mercyend[0]),
               x_axis_type="mercator", y_axis_type="mercator", tooltips=tooltips, tools = "pan,wheel_zoom,box_zoom,reset,hover")

    scaled_map.add_tile(tile_provider)


    # Create and plot glyphs for predictions
    glyph = Circle(x="xgrid", y="ygrid", size= 10, line_color="white", fill_color=mapper, fill_alpha=0.8, line_width=1, 
                    line_alpha=1)
    scaled_map.add_glyph(source, glyph)

    # Add colour bar 
    color_bar = ColorBar(color_mapper=mapper['transform'], width=8,  location=(0,0))
    scaled_map.add_layout(color_bar, 'right')

    callback = CustomJS(args=dict(source=source, xr=scaled_map.x_range, yr=scaled_map.y_range), code="""

        var xstart = xr.start;
        var xend = xr.end;
        var ystart = yr.start;
        var yend = yr.end;
        var gridsize = 20;
        var url = "http://127.0.0.1:5000/api?xstart="+xstart+"&xend="+xend+"&ystart="+ystart+"&yend="+yend+"&gridsize="+gridsize;

        fetch(url)        
            .then(
                function(response) {
                  response.json().then(function(data) {
                    source.data = data;
                    });
                }
          )


        """)

    scaled_map.js_on_event(LODEnd, callback)

    return scaled_map