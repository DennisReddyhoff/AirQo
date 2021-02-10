from bokeh.models import (Circle, ColumnDataSource, Plot, HoverTool, Legend, LegendItem, 
                          CustomJS, TextInput, Button, Dropdown, Div)
from bokeh.plotting import figure, show
from bokeh.tile_providers import Vendors, get_provider
from bokeh.layouts import column, row
import pyproj
from pyproj import Transformer
from datetime import datetime, timezone, timedelta
import requests

def merc(lon,lat):

    epsg3857 = pyproj.CRS('EPSG:3857')
    wgs84 = pyproj.CRS('EPSG:4326')
    
    transformer = Transformer.from_crs(wgs84, epsg3857)
    
    x, y = transformer.transform(lat,lon)
    
    return x,y

def datetime_callback(source, value):
    
    if value == 'boda_id':
        datetime_callback = CustomJS(args=dict(source=source), code="""
        source.data['{}'] = cb_obj.item;
        
        console.log(source.data['boda_id'])
        """.format(value, value))
        
    else:   
        datetime_callback = CustomJS(args=dict(source=source), code="""
        source.data['{}'] = cb_obj.value;
        console.log(source.data[['{}']])
        """.format(value, value))
    
    return datetime_callback

def get_defaults():
    
    start_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    end_date = datetime.now().strftime("%Y-%m-%d")
    time = datetime.now().strftime("%H:%M:%S")
    
    user_tz = datetime.now().astimezone().tzinfo
    offset = datetime.now().replace(tzinfo = user_tz).isoformat(timespec='seconds')[-6:]
    
    return [start_date, end_date, time, offset]

def get_map():
    x0, y0, xend, yend = [32.4], [0.01], [32.8], [0.5]
    mercx0, mercy0 = merc(x0, y0)
    mercxend, mercyend = merc(xend, yend)
    boda_id = ["930428"]
    
    defaults = get_defaults()
    
    url = "https://europe-west3-airqo-250220.cloudfunctions.net/get_locations"

    locations = requests.get(url).json()

    locations["boda"]["x"], locations["boda"]["y"] = merc(locations["boda"]["longitude"], locations["boda"]["latitude"])
    locations["static"]["x"], locations["static"]["y"] = merc(locations["static"]["longitude"], locations["static"]["latitude"])

    # Get map tiles
    tile_provider = get_provider(Vendors.CARTODBPOSITRON)

    # Create ColumnDataSource from coordinates, sizes and predicted means
    boda_source = ColumnDataSource(dict(boda_id = locations["boda"]["id"],
                               boda_x = locations["boda"]["x"],
                               boda_y = locations["boda"]["y"],
                               boda_lon = locations["boda"]["longitude"],
                               boda_lat = locations["boda"]["latitude"]
                               ))

    static_source = ColumnDataSource(dict(static_id = locations["static"]["id"],
                               static_x = locations["static"]["x"],
                               static_y = locations["static"]["y"],
                               static_lon = locations["static"]["longitude"],
                               static_lat = locations["static"]["latitude"]))
    
    datetime_source = ColumnDataSource(dict(boda_id = [0],
                                            start_date = [defaults[0]],
                                            start_time = [defaults[2]],
                                            end_date = [defaults[1]],
                                            end_time = [defaults[2]],
                                            offset = [defaults[3]]))

    '''# Hover tools
    boda_hover = HoverTool(names=["boda"],
                           tooltips = [("Type", "Mobile"),
                                       ("Sensor ID", "@boda_id"),
                                       ("Lat/long", "@boda_lat, @boda_lon")])

    static_hover = HoverTool(names=["static"],
                             tooltips = [("Type", "Static"),
                                         ("Sensor ID", "@static_id"),
                                         ("Lat/long", "@static_lat, @static_lon")])
    '''
    # Plot figure and add tiles 
    scaled_map = figure(title=None, 
                        x_range=(mercx0[0], mercxend[0]), 
                        y_range=(mercy0[0], mercyend[0]),
                        x_axis_type="mercator", 
                        y_axis_type="mercator", 
                        #tools = ["pan,wheel_zoom,box_zoom,reset", boda_hover, static_hover])
                        tools = ["pan,wheel_zoom,box_zoom,reset"],
                        sizing_mode = "scale_width")
    scaled_map.add_tile(tile_provider)


    # Create and plot glyphs for sensors
    boda_glyph = Circle(x="boda_x", y="boda_y", size= 10, line_color="white", fill_color="green", fill_alpha=0.8, line_width=1, 
                    line_alpha=1)
    static_glyph = Circle(x="static_x", y="static_y", size= 10, line_color="white", fill_color="red", fill_alpha=0.8, line_width=1, 
                    line_alpha=1)
    r_boda = scaled_map.add_glyph(boda_source, boda_glyph, name="boda")
    r_static = scaled_map.add_glyph(static_source, static_glyph, name="static")
    
    menu = boda_id
    dropdown = Dropdown(label="Select Boda ID", button_type="primary", menu=menu, sizing_mode="stretch_width")
    
    
    start_date = TextInput(value=defaults[0], title="Start Date")
    start_time = TextInput(value=defaults[2], title="Start Time")
    end_date = TextInput(value=defaults[1], title="End Date")
    end_time = TextInput(value=defaults[2], title="End Time")
    
    button = Button(label="Go", button_type="success", sizing_mode="stretch_width")
    div = Div(text="""""", width=300, height=10)
    
    # Create legend items and add to plot

    li = []
    li += [LegendItem(label='Mobile', renderers=[r_boda])]
    li += [LegendItem(label='Static', renderers=[r_static])]
    _legend = Legend(items = li)
    scaled_map.add_layout(_legend)
    scaled_map.legend.click_policy="hide"
    
    callback = CustomJS(args=dict(source=datetime_source, boda_source=boda_source), code="""
    var id = source.data['boda_id'];
    var start_date = source.data['start_date'];
    var start_time = source.data['start_time'];
    var end_date = source.data['end_date'];
    var end_time = source.data['end_time'];
    var offset = source.data['offset']
    
    console.log(source.data)
    
    var endpoint = "http://34.78.78.202:31011/"    
    const start = "'" + start_date + "T" + start_time + offset + "'"
    const end = "'" + end_date + "T" + end_time + offset + "'"
        
    var url = endpoint + 
              "?id="+id+
              "&start="+start+
              "&end="+end;
              
    console.log(url)
    
    fetch(url)        
            .then(
                function(response) {
                  response.json().then(function(data) {
                    boda_source.data = data;
                    });
                }
          )
                
    """)
    
    dropdown.js_on_click(datetime_callback(datetime_source, 'boda_id'))
    start_date.js_on_change("value", datetime_callback(datetime_source, 'start_date'))
    start_time.js_on_change("value", datetime_callback(datetime_source, 'start_time'))
    end_date.js_on_change("value", datetime_callback(datetime_source, 'end_date'))
    end_time.js_on_change("value", datetime_callback(datetime_source, 'end_time'))
    button.js_on_click(callback)
    
    text_boxes = column(row(start_date, start_time), row(end_date, end_time), sizing_mode="stretch_width")
    tools = column(dropdown, text_boxes, div, button, sizing_mode="fixed", height=250, width=300)
    layout = row(tools, scaled_map, sizing_mode="scale_width")
    
    return layout