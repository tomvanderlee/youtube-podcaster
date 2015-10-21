import pickle
import os
import time
import hashlib
import sys

from feedgen.feed import FeedGenerator

from . import (
    youtube,
)

from threading import Thread


class PodcastUpdater:
    def __init__(self, config):
        self.podcasts = config.podcasts
        self.youtube = youtube.Youtube(config.youtube["api-key"])
        self.downloads = config.downloads

        if sys.platform == "linux" and not hasattr(sys, "real_prefix"):
            self.data_dir = "/var/lib/youtube-podcaster"
        else:
            self.data_dir = "%s/var/lib/youtube-podcaster" % (sys.prefix)

        os.makedirs(self.data_dir, 0o755, True)

        self.feeds_file = "%s/feeds.dump" % (self.data_dir)

        if os.path.isfile(self.feeds_file):
            with open(self.feeds_file, "rb") as feeds:
                self.feeds = pickle.load(feeds)
        else:
            self.feeds = {}

    def get_xml(self, channel, playlist):
        channel = channel.replace('_', ' ')
        playlist = playlist.replace('_', ' ')

        for podcast in self.podcasts:
            if podcast["username"] == channel:
                break
        else:
            return None

        if playlist not in podcast["playlists"]:
            return None

        xml = self.update_podcast(channel, playlist)

        if xml:
            return open(xml).read()

    def update_podcast(self, channel, playlist):
        feed_id = hashlib.sha1(bytes("%s %s" % (channel, playlist), "UTF-8")).hexdigest()
        feed_file = "%s/%s.xml" % (self.data_dir, feed_id)

        yt_channel = self.youtube.get_channel(channel)[0]
        yt_playlists = self.youtube.get_playlists(yt_channel, 50)

        for yt_playlist in yt_playlists:
            if yt_playlist["snippet"]["title"] == playlist:
                break
        else:
            return None

        if feed_id in self.feeds:
            feed = self.feeds[feed_id]
        else:
            feed = self.add_feed(feed_id, yt_playlist)

        if feed.last_updated < time.time() - 600:
            self.populate_feed(feed, feed_id, yt_playlist, max_results=1)
            feed.rss_file(feed_file)

            with open(self.feeds_file, "wb") as feeds:
                pickle.dump(self.feeds, feeds)

        return feed_file

    def add_feed(self, feed_id, yt_playlist):
        feed = FeedGenerator()

        feed.load_extension("podcast")
        feed.id(feed_id)
        feed.title(yt_playlist["snippet"]["title"])
        feed.author({"name": yt_playlist["snippet"]["channelTitle"]})
        feed.description(yt_playlist["snippet"]["description"])
        feed.logo(yt_playlist["snippet"]["thumbnails"]["standard"]["url"])
        feed.link(href="https://www.youtube.com/playlist?list=%s" % (yt_playlist["id"]))
        feed.rss_str(pretty=True)
        feed.last_updated = 0

        self.feeds[feed_id] = feed

        return feed

    def populate_feed(self, feed, feed_id, yt_playlist, max_results=5):
        videos = self.youtube.get_playlist_items(yt_playlist, max_results)

        file_format = self.downloads["format"]
        download_path = self.downloads["path"]
        download_url = self.downloads["url"]

        downloader = youtube.Downloader.get_instance(file_format, download_path, download_url)

        threads = []

        entries = feed.entry()
        for video in videos:
            video_id = hashlib.sha1(bytes(video["id"], "UTF-8")).hexdigest()
            for entry in entries:
                if entry.id() == video_id:
                    break
            else:
                t = Thread(target=self.process_video, args=(downloader, video, video_id, feed_id))
                threads.append(t)
                t.start()

        for t in threads:
            t.join()

        feed.last_updated = time.time()

    def process_video(self, downloader, video, video_id, feed_id):
            url, size, mime = downloader.download(video, video_id, feed_id)

            feed = self.feeds[feed_id]
            feed_entry = feed.add_entry()

            feed_entry.id(video_id)
            feed_entry.guid(video_id)
            feed_entry.title(video["snippet"]["title"])
            feed_entry.description(video["snippet"]["description"])
            feed_entry.published(video["snippet"]["publishedAt"])
            feed_entry.enclosure(url, size, mime)


#  vim: set ts=8 sw=4 tw=0 et :
