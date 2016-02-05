"use strict";

// Pure-modules
var fs = require("fs");
var log = require("npmlog");
var google = require("googleapis");
var ytdl = require("ytdl-core");
var mkdirp = require("mkdirp");
var async = require("async");

// Class-modules
var Podcast = require("podcast");

// Sub-modules
var youtube = google.youtube("v3");

log.heading = "youtube-podcaster";

var options = {};
var playlists = [];
var indexed_playlists = {};

module.exports = {
    set: function(opts) {
        for (var opt in opts) {
            log.verbose("Setting option '" + opt + "' to: " + opts[opt]);
            if (opt == "log_level")
                log.level = opts[opt];

            options[opt] = opts[opt];
        }
    },

    get: function(key) {
        if (key != undefined)
            return options[key];
        else
            return options;
    },

    addPlaylistsToIndex: function(playlist_ids, callback) {
        log.info("Adding new playlists to the index...");
        youtube.playlists.list({
            auth: options.api_key,
            part: "snippet",
            id: playlist_ids.join(','),
        }, function(err, res) {
            handleYoutubeApiResponse({
                err: err,
                res: res,
                action: addPlaylistsToIndex,
            }, callback);
        });
    },

    updateFeeds: function(callback) {
        log.info("Updating feeds...");

        for (var channel_id in indexed_playlists) {
            for (var playlist_id in indexed_playlists[channel_id].playlists) {
                youtube.playlistItems.list({
                    auth: options.api_key,
                    part: "snippet",
                    playlistId: playlist_id,
                    maxResults: options.max_items_in_feed,
                    fields: "items("
                        + "snippet/channelId,"
                        + "snippet/playlistId,"
                        + "snippet/resourceId/videoId"
                        + ")",
                }, function(err, res) {
                    handleYoutubeApiResponse({
                        err: err,
                        res: res,
                        action: updateFeed,
                    }, callback);
                });
            }
        }
    },

    hasPlaylist: function(channel, playlist) {
        var channel_id = getChannelIdByName(channel);
        if (!channel_id)
            return false;

        var playlist_id = getPlaylistIdByName(channel_id, playlist);
        if (!playlist_id)
            return false;

        return true;
    },

    getRssFeed: function(channel, playlist) {
        var channel_id = getChannelIdByName(channel);
        if (!channel_id)
            return undefined;

        var playlist_id = getPlaylistIdByName(channel_id, playlist);
        if (!playlist_id)
            return undefined;;

        return indexed_playlists[channel_id].playlists[playlist_id].feed.xml("\t");
    },

    getPodcastUrls: function(base_url, extension) {
        var urls = [];

        for (var channel_id in indexed_playlists) {
            for (var playlist_id in indexed_playlists[channel_id].playlists) {
                var channel = indexed_playlists[channel_id].channel;
                var playlist = indexed_playlists[channel_id].playlists[playlist_id].title;
                urls.push([base_url, channel, playlist + extension].join("/"));
            };
        };

        return urls;
    },
};

function searchArray(array, key, value) {
    for (var i = 0; i < array.length; i++) {
        var object = array[i];
        if (key != null && object[key] == value)
            return i;
        else if (key == null && object == value)
            return i;
    }
    return undefined;
};

function handleYoutubeApiResponse(params, callback) {
    var err = params.err;
    var res = params.res;
    var action = params.action;

    if (err) {
        if (err.errors != undefined) {
            err.errors.forEach(function(error) {
                log.error("Youtube Api v3 Error[" + error.reason + "]: " + error.message);
            });
            process.exit(-1);
        };
        return;
    };

    action(res.items, callback);
};

function addPlaylistsToIndex(playlists, callback) {
    for (var playlist of playlists) {
        var channel_id = playlist.snippet.channelId;
        var channel_title = playlist.snippet.channelTitle.toLowerCase().replace(/\s/g, "_");
        if (!(channel_id in indexed_playlists)) {
            log.verbose("Adding channel \"" + channel_title + "\" to index...");
            indexed_playlists[channel_id] = {
                channel: channel_title,
                playlists: {},
            };
        }

        var playlist_id = playlist.id;
        var playlist_title = playlist.snippet.title.toLowerCase().replace(/\s/g, "_");
        if (!(playlist_id in indexed_playlists[channel_id].playlists)) {
            log.verbose("Adding \"" + playlist_title + "\" to \"" + channel_title + "\"...");
            indexed_playlists[channel_id].playlists[playlist_id] = {
                title: playlist_title,
                feed: new Podcast({
                    title: playlist.snippet.title,
                    description: playlist.snippet.description,
                    site_url: "https://www.youtube.com/playlist?list=" + playlist_id,
                    image_url: playlist.snippet.thumbnails.standard.url,
                    author: playlist.snippet.channelTitle,
                    copyright: (new Date).getFullYear() + " " + playlist.snippet.channelTitle,
                    language: "en",
                    pubDate: playlist.snippet.publishedAt,
                    ttl: '60',
                }),
            };
        };
    };

    if (callback != undefined)
        callback();
};

function updateFeed(playlistItems, callback) {
    var videos = preparePlaylistItems(playlistItems);

    getInfoOfVideos(Object.keys(videos), function(video_info) {
        downloadVideo(videos[video_info.id], function(video) {
            video.feed.item({
                title:  video_info.snippet.title,
                description: video_info.snippet.description,
                url: video.video_url,
                guid: video_info.id,
                categories: video_info.snippet.tags,
                author: video_info.snippet.channelTitle,
                date: video_info.snippet.publishedAt,
                enclosure : {
                    url: video.file_url,
                    file: video.output_file,
                },
            });


            video.feed.items.sort(compareFeedItems);
            log.verbose("Added item to feed: " + video.output_file);

            removeOldItemsInFeed(video.feed);
        });
    });

    if (callback != undefined)
        callback();
};

function preparePlaylistItems(playlistItems) {
    var videos = {};

    for (var playlistItem of playlistItems) {
        var video_id = playlistItem.snippet.resourceId.videoId;
        var playlist_id = playlistItem.snippet.playlistId;
        var channel_id = playlistItem.snippet.channelId;

        var file = video_id + ".ogg"
        var output_dir = [options.downloads_folder, channel_id, playlist_id].join("/");
        var output_file = [output_dir, file].join("/");
        var file_url = [options.downloads_base_url, channel_id, playlist_id, file].join("/");

        var video_url = "https://youtu.be/" + video_id;

        var feed = indexed_playlists[channel_id].playlists[playlist_id].feed;
        var index_in_feed = searchArray(feed.items, "guid", video_id);
        if (index_in_feed == undefined) {
            videos[video_id] = {
                video_id: video_id,
                playlist_id: playlist_id,
                channel_id: channel_id,
                output_dir: output_dir,
                output_file: output_file,
                file_url: file_url,
                video_url: video_url,
                feed: feed,
            };
        };
    };

    return videos;
};

function getInfoOfVideos(video_ids, callback) {
    if (video_ids.length == 0)
        return;

    youtube.videos.list({
        auth: options.api_key,
        part: "snippet",
        id: video_ids.join(","),
    }, function(err, res) {
        handleYoutubeApiResponse({
            err: err,
            res: res,
            action: function(videos) {
                videos.forEach(callback);
            },
        })
    });
};

function downloadVideo(video, callback) {
    mkdirp.sync(video.output_dir);

    try {
        fs.statSync(video.output_file).isFile();
        callback(video);
    } catch (error) {
        ytdl(video.video_url, { filter: "audioonly" })
            .pipe(fs.createWriteStream(video.output_file))
            .on("finish", function() {
                callback(video);
            });
    };
};

function compareFeedItems(item1, item2) {
    var timestamp1 = new Date(item1.date).getTime();
    var timestamp2 = new Date(item2.date).getTime();

    if (timestamp1 < timestamp2)
        return 1;
    if (timestamp1 > timestamp2)
        return -1;
    return 0;
};

function removeOldItemsInFeed(feed) {
    while (options.max_items_in_feed != undefined
        && feed.items.length > options.max_items_in_feed) {
        var old_item = items.pop();
        var file = old_item.enclosure.file;
        fs.unlinkSync(file);
        log.verbose("Removed item from feed: " + file);
    };
};

function getChannelIdByName(name) {
    for (var channel_id in indexed_playlists) {
        if (indexed_playlists[channel_id].channel == name)
            return channel_id;
    }

    return null;
};

function getPlaylistIdByName(channel_id, name) {
    for (var playlist_id in indexed_playlists[channel_id].playlists) {
        if (indexed_playlists[channel_id].playlists[playlist_id].title == name)
            return playlist_id;
    }

    return null;
};

// vim: set ts=8 sw=4 tw=0 ft=javascript et :
