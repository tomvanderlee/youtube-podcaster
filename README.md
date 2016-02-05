# YouTube Podcaster

Lets you covert YouTube-playlists to RSS podcast feeds and serve them.

## How to use

YouTube Podcaster can be both used as a module or a standalone server.

### Server

    $ npm start

### Module

    // my_app.js

    var ytp = require("youtube-podcaster");

    ytp.set({
        api_key: "MY_YOUTUBE_V3_API_KEY",
	downloads_folder: "/path/to/folder",
	downloads_base_url: "example.com/item/",
    });

    ytp.addPlaylistsToIndex(["PLAYLIST_ID", "ANOTHER_ONE"], function() {
	ytp.updateFeeds();
	setInterval(ytp.updateFeeds, 3600000); // Check every hour for new episodes
    });

## Library Documentation

TODO

## To Do

- Comments and documentation
- Test Cases
- Cleaning up the mess

## LICENCE

YouTube Podcaster is licensed under the MIT License, see the LICENSE file for more info.
