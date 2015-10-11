#!/usr/bin/env python3

import json

from http.server import (
    HTTPServer,
)

from . import (
    youtube,
)

from .podcastfeeder import (
    create_feeder
)


def main():
    config = json.load(open("youtube-podcaster.json"))

    try:
        PodcastFeeder = create_feeder(config["youtube"], config["podcasts"])
        server = HTTPServer(("", 8888), PodcastFeeder)
        server.serve_forever()
    except KeyboardInterrupt:
        server.socket.close()

#  vim: set ts=8 sw=4 tw=0 et :
