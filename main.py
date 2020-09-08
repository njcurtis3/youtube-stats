#-----------------------------------------------------------------------------------------
# Copyright (c) Articles of Unity. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for license information.
#-----------------------------------------------------------------------------------------

import os
import googleapiclient.discovery
import googleapiclient.errors
import pandas
from google.cloud import bigquery
from datetime import datetime
import base64

api_service_name = "youtube"
api_version = "v3"

# In the future we may want to be able to make this payload variable
campfire_playlist_id = "PLRPsQ54HdnfpxM6jE4nJZs-MosDBixHe1"

# For whatever reason, Python doesn't add the Z to the end of an ISO8601 formatted string, which violates the spec.
# https://stackoverflow.com/questions/19654578/python-utc-datetime-objects-iso-format-doesnt-include-z-zulu-or-zero-offset
# date_collected = datetime.utcnow().isoformat(timespec="seconds") + "Z"

def get_video_id_from_playlist_item(playlist_item):
    return playlist_item["snippet"]["resourceId"]["videoId"]

def request_playlist_items(client, page_token=None):
    if page_token is not None:
        return client.playlistItems().list(
            part="snippet",
            maxResults=50,
            playlistId=campfire_playlist_id,
            pageToken=page_token
        )
    else:
        return client.playlistItems().list(
            part="snippet",
            maxResults=50,
            playlistId=campfire_playlist_id
        )

def collect_video_ids(client):
    """
    Returns a comma-separated string of video ids contained in a playlist. Needed so that
    the actual video statistic data can be requested in fetch_videos.
    """
    response = request_playlist_items(client).execute()

    playlist_items = response["items"]
    next_page_token = response.get("nextPageToken")

    while next_page_token is not None:
        response = request_playlist_items(client, next_page_token).execute()
        playlist_items.extend(response["items"])
        next_page_token = response.get("nextPageToken")
      
    ids = map(get_video_id_from_playlist_item, playlist_items)
    return ",".join(set(ids))

def fetch_videos(client, video_id_string):
    return client.videos().list(
        part="snippet,statistics",
        id=video_id_string
    ).execute()["items"]

def convert_videos_to_dataframe(videos, collection_time):
    """
    Flattens the videos data into a table-friendly structure (pandas.DataFrame) to be ingested by BigQuery.
    """
    dictionary = {}
    dictionary["id"] = map(lambda x: x["id"], videos)
    dictionary["title"] = map(lambda x: x["snippet"]["title"], videos)
    dictionary["publish_date"] = map(lambda x: pandas.Timestamp(x["snippet"]["publishedAt"]), videos)
    dictionary["channel_title"] = map(lambda x: x["snippet"]["channelTitle"], videos)
    dictionary["channel_id"] = map(lambda x: x["snippet"]["channelId"], videos)
    dictionary["comment_count"] = map(lambda x: int(x["statistics"]["commentCount"]), videos)
    dictionary["dislike_count"] = map(lambda x: int(x["statistics"]["dislikeCount"]), videos)
    dictionary["favorite_count"] = map(lambda x: int(x["statistics"]["favoriteCount"]), videos)
    dictionary["like_count"] = map(lambda x: int(x["statistics"]["likeCount"]), videos)
    dictionary["view_count"] = map(lambda x: int(x["statistics"]["viewCount"]), videos)
    dictionary["date_collected"] = pandas.Timestamp(collection_time)
    return pandas.DataFrame(data=dictionary)

def run(run_time):
    youtube = googleapiclient.discovery.build(
        api_service_name, 
        api_version
    )
    
    video_id_string = collect_video_ids(youtube)
    video_response = fetch_videos(youtube, video_id_string)

    dataframe = convert_videos_to_dataframe(video_response, run_time)

    bg_client = bigquery.Client()
    # We may want this to be variable in the future, however since this is currently the only use of the YouTube
    # data API, this will do for now.
    table_id = "youtube.campfire"

    job = bg_client.load_table_from_dataframe(dataframe, table_id)

    job.result()

def gather_youtube_stats(event, context):
    """
    Entrypoint for the Google Cloud Function. Parses the event payload and kicks off the data collection.
    """
    print("This function was triggered by messageId {} published at {}".format(context.event_id, context.timestamp))

    # TODO: We should implement some sort of logic to notify (maybe via slack) in the event the function fails.
    if "data" in event:
        data = base64.b64decode(event["data"]).decode("utf-8")
        if data == "weekly":
            run(context.timestamp)
            print("Completed data transfer to bigquery")
        else:
            print("Unrecognized event payload")
    else:
        print("Unrecognized event payload")
