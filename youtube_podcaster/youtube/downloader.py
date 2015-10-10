#!/usr/bin/env python3

import youtube_dl
import os


class Downloader:
    instance = None

    def get_instance(file_format, location, base_url):
        if Downloader.instance:
            return Downloader.instance
        else:
            Downloader.instance = Downloader(file_format, location, base_url)
            return Downloader.instance

    def __init__(self, file_format, location, base_url):
        self.file_format = file_format
        self.location = location
        self.base_url = base_url

    def download(self, video, video_id, feed_id):
        output = "%s/%s/%s.ogg" % (self.location, feed_id, video_id)
        options = {"format": "bestaudio/best",
                   "outtmpl": output,
                   "postprocessors": [{
                       "key": "FFmpegExtractAudio",
                       "preferredcodec": self.file_format
                   }],
                   "nooverwrites": True
        }

        video_url = "https://www.youtube.com/watch?v=%s" % (video["snippet"]["resourceId"]["videoId"])
        youtube_dl.YoutubeDL(options).download([video_url])

        url = "%s/%s/%s.ogg" % (self.base_url, feed_id, video_id)
        size = str(os.path.getsize(output))
        mime = "audio/ogg"

        return (url, size, mime)

#  vim: set ts=8 sw=4 tw=0 et :
