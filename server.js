"use strict";

var config = require("./youtube-podcaster.json");

var express = require("express");
var app = express();

var ytp = require(".")

var downloads_host = config.downloads.url.host;
var downloads_subdir = config.downloads.url.subdir;
var downloads_base = downloads_host + downloads_subdir;

ytp.set({
    log_level: "silly",
    api_key: config.youtube.api_key,
    downloads_folder: config.downloads.path,
    downloads_base_url: downloads_base,
    max_items_in_feed: config.downloads.max_items_in_feed,
});

app.use(downloads_subdir, express.static(config.downloads.path, {
    index: false,
}));

app.get("/feed/", function(req, res) {
    var urls = ytp.getPodcastUrls("/feed", ".rss");
    var response = "<html>"
                 + "<body>";

    for (var url of urls)
        response += "<a href='" + url + "'>" + url + "</a></br>";

    response += "</body>"
                "</html>"

    res.send(response);
});

app.get("/feed/:channel/:playlist\.rss", function(req, res) {
    var channel = req.params.channel;
    var playlist = req.params.playlist;

    if (!ytp.hasPlaylist(channel, playlist))
        return res.status(404).send(playlist + " not a playlist of " + channel);

    res.set("Content-Type", "application/rss+xml");
    return res.send(ytp.getRssFeed(channel, playlist));
});

ytp.addPlaylistsToIndex(config.playlists, function() {
    ytp.updateFeeds();
    setInterval(ytp.updateFeeds, 3600000);
});

app.listen(config.server.port, config.server.interface, function () {
    console.log("Started listening on " + config.server.interface + ":" + config.server.port);
});

// vim: set ts=8 sw=4 tw=0 ft=javascript et :
