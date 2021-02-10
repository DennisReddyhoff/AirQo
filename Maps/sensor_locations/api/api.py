from flask import Flask, jsonify, request
from google.cloud import bigquery
import pyproj
from pyproj import Transformer
from datetime import timezone
import dateutil
import dateutil.parser
client = bigquery.Client.from_service_account_json("airqo-250220-c81b55f1dc21.json")

api = Flask(__name__)

def merc(lon,lat):

    epsg3857 = pyproj.CRS('EPSG:3857')
    wgs84 = pyproj.CRS('EPSG:4326')
    
    transformer = Transformer.from_crs(wgs84, epsg3857)
    
    x, y = transformer.transform(lat,lon)
    
    return x,y

def to_utc(datetime):
    datetime = dateutil.parser.parse(datetime)
    datetime = datetime.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    return datetime

def get_locations(request):

    start = to_utc(request.args["start"])
    end = to_utc(request.args["end"])

    sql = """
    SELECT * FROM `airqo-250220.thingspeak.clean_feeds_pms` 
    WHERE channel_id = {} 
    AND created_at > '{}'
    AND  created_at < '{}'  
    """.format(request.args["id"], start,end)
    
    locs = client.query(sql)

    channel_id = []
    lat = []
    lon = []
    
    for row in locs: 
        if row.longitude != 0 and row.longitude != 1000:
            channel_id.append(row.channel_id)
            lat.append(row.latitude)
            lon.append(row.longitude)
    
    x, y = merc(lon,lat)

    #headers = {"Access-Control-Allow-Origin" : "*", "Access-Control-Allow-Credentials": true} 

    response = {"boda_id": channel_id,
                "boda_x": x,
                "boda_y": y,
                "boda_lon": lon,
                "boda_lat": lat} 

    response = jsonify(response)
    response.headers['Access-Control-Allow-Origin'] = '*'      
                    
    return(response)

@api.route('/', methods = ['GET'])
def main():
    response = get_locations(request)
    return response 