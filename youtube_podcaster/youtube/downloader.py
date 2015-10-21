#!/usr/bin/env python3

import os
import sys
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
        elif file_format == "opus":
            self.extension = "opus"

    def download(self, video, video_id, feed_id):

        # Real output
        filename = "%s.%s" % (video_id, self.extension)
        output_dir = "%s/%s" % (self.location, feed_id)
        output = "%s/%s" % (output_dir, filename)

        # Tmp output
        tmp_filename = "%s.webm" % (video_id)
        tmp_dir = "%s/tmp" % output_dir
        tmp_output = "%s/%s" % (tmp_dir, tmp_filename)

        options = {"format": "bestaudio/best",
                   "outtmpl": tmp_output,
                   "postprocessors": [{
                       "key": "FFmpegExtractAudio",
                       "preferredcodec": self.file_format
                   }]}

        video_url = "https://www.youtube.com/watch?v=%s" % (video["snippet"]["resourceId"]["videoId"])
        youtube_dl.YoutubeDL(options).download([video_url])

        tmp_output = "%s/%s" % (tmp_dir, filename)

        url = "%s/%s/%s" % (self.base_url, feed_id, filename)
        size = str(os.path.getsize(tmp_output))
        mime = mimetypes.guess_type(tmp_output)[0]

        os.makedirs(output_dir, 0o755, True)
        os.rename(tmp_output, output)

        return (url, size, mime)

#  vim: set ts=8 sw=4 tw=0 et :
