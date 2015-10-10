#!/usr/bin/env python3

from urllib import parse, request
import json


class Youtube:

    def __init__(self, api_key):
        self.api_key = api_key

    def _api_call(self, section, parameters):
        parameters["key"] = self.api_key
        data = parse.urlencode(parameters)
        api_base = "https://www.googleapis.com/youtube/v3"
        response = request.urlopen("%s/%s?%s" % (api_base, section, data))
        return json.loads(response.read().decode("UTF-8"))["items"]

    def search(self, query):
        return self._api_call("search", {"part": "snippet",
                                         "q": query})

    def get_channel(self, username):
        return self._api_call("channels", {"part": "snippet",
                                           "forUsername": username})

    def get_uploads(self, channel):
        content_details = self._api_call("channels", {"part": "contentDetails",
                                                      "id": channel["id"]})
        uploads_id = content_details[0]["contentDetails"]["relatedPlaylists"]["uploads"]
        return self._api_call("playlists", {"part": "snippet",
                                            "id": uploads_id})

    def get_playlists(self, channel, max_results=5):
        return self._api_call("playlists", {"part": "snippet",
                                            "channelId": channel["id"],
                                            "maxResults": max_results})

    def get_playlist_items(self, playlist, max_results=5):
        return self._api_call("playlistItems", {"part": "snippet",
                                                "playlistId": playlist["id"],
                                                "maxResults": max_results})

#  vim: set ts=8 sw=4 tw=0 et :
