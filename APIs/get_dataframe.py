#!/usr/bin/env python
# coding: utf-8

# In[23]:


import requests
import json
import pandas as pd
import time
from datetime import datetime, timedelta
import dateutil.parser
import fnmatch
from IPython.core.display import clear_output


# In[4]:


def build_df(sensor_id, cache="/"):

    try:
        feeds = pd.read_csv(cache + str(sensor_id) + ".csv", 
                            index_col="created_at")
        last_entry = feeds.index[-1][:-1].replace("T", "%20")
        try:
            new_feeds = feed_data(sensor_id, last_entry)
            feeds = pd.concat([feeds, new_feeds[1:]])
            feeds.to_csv(cache + str(sensor_id) + ".csv")
        except AssertionError:
            print("No new records.")         
    except FileNotFoundError:
        feeds = feed_data(sensor_id)
        feeds.to_csv(cache + str(sensor_id) + ".csv")


def get_df(sensor_id, cache):
    
    feeds = pd.read_csv(cache + str(sensor_id) + ".csv", 
                            index_col="created_at")
    return feeds


def get_responses(sensor_id, start_date = "", end_date = ""):
    
    page_no = 1  # Page no. to keep count
    responses = []
    url = "https://api.thingspeak.com/channels/{}/feeds.json?results={}&start={}&end={}"
    
    while True:
        # Outputs page number and then clears output
        print("Requesting page {}".format(page_no))
        clear_output(wait=True)
        page_no += 1

        r = requests.get(url.format(sensor_id, "8000", start_date, end_date))
        responses.append(r)

        # Return error code if API request fails
        if r.status_code != 200:
            print(r.text)
            break

        # If less than 8000 observations are returned, all data points
        # are downloaded and loop ends with message to user
        if len(r.json()["feeds"]) > 1:                     
            if len(r.json()["feeds"]) < 8000:
                print("All items returned")
                return responses
            elif bool(start_date) == True:
                start_date = get_date(r, "start")
                continue
            else:
                end_date = get_date(r, "end")
                continue
        else:
            raise AssertionError
        


# In[6]:


def get_headers(feeds, responses):

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


# In[22]:


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


# In[8]:


def get_date(response, pos):
    
    if pos == "start":
        idx = -1
        delta = 1
    elif pos == "end":
        idx = 0
        delta = -1
        
    date = response.json()["feeds"][idx]["created_at"]
    date = dateutil.parser.parse(date) + timedelta(seconds=delta)
    
    return date.strftime("%Y-%m-%d%%20%H:%M:%S")


# In[ ]:




