from http.server import BaseHTTPRequestHandler

from .podcastupdater import (
    PodcastUpdater
)


def create_feeder(youtube_config, podcast_config):
    class PodcastFeeder(BaseHTTPRequestHandler):
        def __init__(self, request, client_address, server):
            self.updater = PodcastUpdater(youtube_config, podcast_config)
            super(PodcastFeeder, self).__init__(request, client_address, server)

        def do_GET(self):
            path = self.path.split('/')

            if len(path) == 3:
                channel = path[1]
                playlist = path[2]
            else:
                return self.return_error(404)

            xml = self.updater.get_xml(channel, playlist)

            if not xml:
                return self.return_error(404)
            else:
                self.send_response(200)
                self.send_header("Content-type", "text/xml")
                self.end_headers()
                self.wfile.write(bytes(xml, 'UTF-8'))

        def return_error(self, code):
            self.send_response(code)
            self.send_header("Content-type", "text/html")
            self.end_headers()

            reponse = "<body>Error: %s</body>" % (code)
            self.wfile.write(bytes(reponse, 'UTF-8'))

    return PodcastFeeder

#  vim: set ts=8 sw=4 tw=0 et :
