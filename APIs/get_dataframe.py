import requests
import json
import pandas as pd
import time
from datetime import datetime, timedelta
import dateutil.parser
import fnmatch
from IPython.core.display import clear_output

def build_df(sensor_id, cache="/"):
    """Attempts to open the relevant .csv cache for the sensor as a dataframe 
    and finds and concatenates new records. If the cache doesn't exist, the 
    dataframe is built and output to csv.

    Parameters
    ----------
    sensor_id : int
        ID for sensor of interest, can be found at 
        https://forecast-dot-airqo-250220.appspot.com/api/v1/forecast/channels
    cache : str , optional
        Path for sensor cache files, default is current folder      
    """
    
    try:
        # Open feed from csv
        feeds = pd.read_csv(cache + str(sensor_id) + ".csv", 
                            index_col="created_at", low_memory=False)
        # Get last date
        last_entry = feeds.index[-1][:-1].replace("T", "%20")
        #try:
        # Get feed data from last date until end
        new_feeds = feed_data(sensor_id, last_entry)
        # Concatenate and save df
        feeds = pd.concat([feeds, new_feeds[1:]])
        feeds.to_csv(cache + str(sensor_id) + ".csv")
    except FileNotFoundError:
        # If there is no existing feed, get data and save
        feeds = feed_data(sensor_id)
        feeds.to_csv(cache + str(sensor_id) + ".csv")

def get_df(sensor_id, cache):
    """Returns cached dataframe for given sensor id
    
    Parameters
    ----------    
    sensor_id : int
        ID for sensor of interest, can be found at 
        https://forecast-dot-airqo-250220.appspot.com/api/v1/forecast/channels
    cache : str , optional
        Path for sensor cache files, default is current folder
    
    Returns
    -------
    feeds : DataFrame
        DataFrame of all responses for a given sensor from ThingSpeak API   
    """ 
        
    feeds = pd.read_csv(cache + str(sensor_id) + ".csv", 
                            index_col="created_at", low_memory=False)
    return feeds

def get_responses(sensor_id, start_date = "", end_date = ""):
    """Returns requested responses from the ThingSpeak API
    
    Parameters
    ----------    
    sensor_id : int
        ID for sensor of interest, can be found at 
        https://forecast-dot-airqo-250220.appspot.com/api/v1/forecast/channels
    start_date : str , optional
        If updating the cache, passing a start date will search for all entries
        from the given date until the end of the dataset  
    end_date : str , optional
        
    Returns
    -------
    responses : list
        List of response objects returned from API calls    
    """ 
    
    page_no = 1  # Page no. to keep count
    responses = []
    url = "https://api.thingspeak.com/channels/{}/feeds.json?results={}&start={}&end={}"
    
    while True:
        # Outputs page number and then clears output
        print("Requesting page {}".format(page_no))
        clear_output(wait=True)
        page_no += 1
        
        # Requests 8000 responses (max results from Thingspeak) between given dates
        r = requests.get(url.format(sensor_id, "8000", start_date, end_date))
        responses.append(r)

        # Return error code if API request fails
        if r.status_code != 200:
            print(r.text)
            break

        # If less than 8000 observations are returned, all data points
        # are downloaded and loop ends with message to user
        #if len(r.json()["feeds"]) > 1:                     
        if len(r.json()["feeds"]) < 8000:
            print("All items returned")
            return responses
        # Else if a start date is passed, calculate a new start date and continue
        elif bool(start_date) == True:
            start_date = get_date(r, "start")
            continue
        # Else calculate a new end date and continue
        else:
            end_date = get_date(r, "end")
            continue

def get_headers(feeds, responses):
    """Gets feed headers from the responses and renames DataFrame columns to match
    
    Parameters
    ----------    
    responses : list
        List of response objects returned from API calls
    feeds : DataFrame
        DataFrame of all responses for a given sensor from ThingSpeak API
        
    Returns
    -------
    feeds : DataFrame
        DataFrame of all responses for a given sensor from ThingSpeak API    
    """ 

    # Find field column headers
    matching = fnmatch.filter(feeds.columns, "field*")
    headers = {}  # Initiate headers dict

    # Compare header names with channel keys, which describes
    # the returned field names. Populates headers with field
    # headings descriptions from channel response
    for i in matching:
        if i in responses[0].json()["channel"].keys():
            headers[str(i)] = responses[0].json()["channel"][str(i)]

    # Rename columns
    feeds = feeds.rename(headers, axis="columns")

    return(feeds)

def feed_data(sensor_id, last_entry=""):
    """Gets all data points for a given sensor from ThingSpeak API and returns
    them as a formatted Pandas dataframe. 

    Parameters
    ----------
    sensor_id : int
        ID for sensor of interest, can be found at 
        https://forecast-dot-airqo-250220.appspot.com/api/v1/forecast/channels

    Returns
    -------
    feeds : DataFrame
        DataFrame of all responses for a given sensor from ThingSpeak API      
    """
    
    if last_entry == True:
        step = 1
    else:
        step = -1

    # Get list of responses from API
    responses = get_responses(sensor_id, start_date=last_entry)
    # Create data frame excluding last feed to avoid overlap
    # List is created backwards from responses to be chronologically correct
    frames = [pd.DataFrame(response.json()['feeds'])
              for response in responses[::step]]
    feeds = pd.concat(frames, ignore_index=True)
    # Set row names as date of creation
    feeds = feeds.set_index('created_at')
    # Get headers from "channel" response
    feeds = get_headers(feeds, responses)


    return feeds

def get_date(response, pos):
    """Gets new start or end date depending on passed pos parameter 

    Parameters
    ----------
    response : Response
        HTTPResponse object from API call
    pos : str
        Position to calculate date from, either start or end

    Returns
    -------
    date : str
        Returns new start or end date      
    """
    
    # For start date, get last date entry and add 1 second
    if pos == "start":
        idx = -1
        delta = 1
    # For end date, get first date entry and subtract a second
    elif pos == "end":
        idx = 0
        delta = -1
    
    # Get relevant date from response and add delta
    date = response.json()["feeds"][idx]["created_at"]
    date = dateutil.parser.parse(date) + timedelta(seconds=delta)
    
    return date.strftime("%Y-%m-%d%%20%H:%M:%S")


def get_pollution(id, feeds):
    """Takes a cached dual sensor DataFrame, extracts sensor data and
    returns a tidy DataFrame.

    Parameters
    ----------
    feeds : DataFrame
        DataFrame of all responses for a given sensor from ThingSpeak API
    
    Returns
    -------
    pm_df : DataFrame
        DataFrame indexed by datetime with PM2.5 and PM10 readings for each sensor      
    """
    
    # Drop unnecessary columns
    pm_df = feeds.drop(["entry_id", 
                    "Latitude", 
                    "Longitude", 
                    "Battery Voltage", 
                    "GpsData"], 
                    axis=1)
    # Rename columns to remove spelling errors and make split easier
    pm_df.columns = ["Sensor1 PM2.5",
                     "Sensor1 PM10",
                     "Sensor2 PM2.5",
                     "Sensor2 PM10"]
    # Reset index and convert dates column to datetime
    pm_df = pm_df.reset_index()
    pm_df["created_at"] = pd.to_datetime(pm_df["created_at"])
    
    # Melt columns into rows
    values = [pm_df.columns[i] for i in range(1,len(pm_df.columns))]
    pm_df = pm_df.melt(id_vars="created_at", 
                       value_vars=values, 
                       var_name="sensor")
    
    # Split sensor name from PM2.5 / PM10 and update dataframe
    split = pm_df["sensor"].str.split(" ", 1, expand=True)
    pm_df.insert(1, column="pollutiontype", value=split[1])
    pm_df.insert(1, column="sensortype", value=split[0])
    pm_df.insert(0, column="sensor_id", value=id)
    pm_df = pm_df.drop("sensor", axis=1)
    
    # Reindex DataFrame hierarchically 
    pm_df = pm_df.set_index(["sensor_id",
                             "created_at", 
                             "sensortype", 
                             "pollutiontype"])["value"].unstack()
    pm_df.columns.name = ""
    
    return pm_df




