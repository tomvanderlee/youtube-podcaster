#!/usr/bin/env python3

import argparse

from http.server import HTTPServer

from .podcastfeeder import create_feeder
from .config import (
        Config,
        ConfigException
)

"""
Start the program
"""


def main():
    arg_parser = argparse.ArgumentParser(prog="youtube-podcaster",
                                         description="Converts youtube \
                                         playlists to RSS-feeds")
    arg_parser.add_argument("-c", "--config",
                            dest="config",
                            help="Use CONFIG as the config file")
    arg_parser.add_argument("-i", "--interface",
                            dest="interface",
                            help="The interface the http server will listen on")
    arg_parser.add_argument("-p", "--port",
                            dest="port",
                            help="The port the http server will listen on")
    arg_parser.add_argument("--api-key",
                            dest="apikey",
                            help="The YouTube API v3 key")
    args = arg_parser.parse_args()

    try:
        config = Config.parse_config(args)

        PodcastFeeder = create_feeder(config)

        server = HTTPServer(config.get_server_address(), PodcastFeeder)
        server.serve_forever()
    except ConfigException as e:
        print(e)
    except KeyboardInterrupt:
        server.socket.close()

#  vim: set ts=8 sw=4 tw=0 et :
