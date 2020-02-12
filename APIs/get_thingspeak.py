import requests
import requests_cache
import json
import pandas as pd
import time
from datetime import datetime
import fnmatch
from IPython.core.display import clear_output
requests_cache.install_cache()

def feed_data(sensor_id):
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

    # Get list of responses from API
    responses = get_feeds(sensor_id)
    # Create data frame excluding last feed to avoid overlap
    # List is created backwards from responses to be chronologically correct
    frames = [pd.DataFrame(response.json()['feeds'][:-1])
              for response in responses[::-1]]
    feeds = pd.concat(frames)
    # Set row names as date of creation
    feeds = feeds.set_index('created_at')
    # Get headers from "channel" response
    feeds = get_headers(feeds, responses)

    return feeds

def get_feeds(sensor_id):
    
    # Set end date to current time
    new_end = datetime.now().strftime("%Y-%m-%d %H:%M:%SZ")  
    responses = []  # Initialise list of responses
    page_no = 1  # Page no. to keep count

    while True:
        # Outputs page number and then clears output
        print("Requesting page {}".format(page_no))
        #clear_output(wait=True)
        page_no += 1
        # Pull 8000 requests from thingspeak API and append to responses
        r = requests.get(
            "https://api.thingspeak.com/channels/{}/feeds.json?results={}&end={}".format(sensor_id, "8000", new_end))
        print(r.from_cache)
        responses.append(r)
        # Return error code if API request fails
        if r.status_code != 200:
            print(r.text)
            break
        # If less than 8000 observations are returned, all data points
        # are downloaded and loop ends with message to user
        if len(r.json()["feeds"]) < 8000:
            print("All items returned")
            return responses
        # Otherwise, define new_end as first date in response
        else:
            # Returns first date in response, stripped of "T" and "Z" chars
            new_end = r.json()['feeds'][0]['created_at'][:-
                                                         1].replace("T", "%20")
            # If response is got from cache, sleep to prevent API overload
            if getattr(responses, 'from_cache', False):
                time.sleep(0.25)
            print(new_end)
               
                
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

