#!/usr/bin/env python3

import os
import mimetypes

import youtube_dl


class Downloader:
    instance = None

    def get_instance(file_format, location, base_url):
        if not Downloader.instance:
            Downloader.instance = Downloader(file_format, location, base_url)
        return Downloader.instance

    def __init__(self, file_format, location, base_url):
        self.file_format = file_format
        self.location = location
        self.base_url = base_url

        if file_format == "vorbis":
            self.extension = "ogg"

    def download(self, video, video_id, feed_id):
        output = "%s/%s/%s.%s" % (self.location, feed_id, video_id, self.extension)
        options = {"format": "bestaudio/best",
                   "outtmpl": output,
                   "postprocessors": [{
                       "key": "FFmpegExtractAudio",
                       "preferredcodec": self.file_format
                   }],
                   "nooverwrites": True}


        video_url = "https://www.youtube.com/watch?v=%s" % (video["snippet"]["resourceId"]["videoId"])
        youtube_dl.YoutubeDL(options).download([video_url])

        url = "%s/%s/%s.%s" % (self.base_url, feed_id, video_id, self.extension)
        size = str(os.path.getsize(output))
        mime = mimetypes.guess_type(output)[0]

        return (url, size, mime)

#  vim: set ts=8 sw=4 tw=0 et :
