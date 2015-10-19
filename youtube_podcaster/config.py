import sys
import os
import json


class ConfigException(Exception):
    def __init__(self, msg):
        super(ConfigException, self).__init__("Config exception: %s" % (msg))


class Config:
    instance = None

    def parse_config(config_file=None):
        if not Config.instance:
            Config.instance = Config(config_file)

        return Config.instance

    def __init__(self, args):
        if args.config:
            config = args.config
        else:
            config_file = "youtube-podcaster.json"

            if sys.platform == "linux" and not hasattr(sys, "real_prefix"):
                config = "/etc/%s" % (config_file)
            else:
                config = "%s/etc/%s" % (sys.prefix, config_file)

        if not os.path.isfile(config):
            raise ConfigException("%s not found" % (config))

        try:
            config = json.load(open(config))
        except json.decoder.JSONDecodeError as e:
            raise ConfigException("%s is not valid json: %s" % (
                                  config, str(e)))

        try:
            self.server = config["server"]
            self.youtube = config["youtube"]
            self.podcasts = config["podcasts"]
        except KeyError as e:
            raise ConfigException("Missing %s-section in %s" % (
                                  str(e), config))

        for arg, value in vars(args).items():
            if not value:
                continue

            if arg == "interface":
                self.server["interface"] = value
            elif arg == "port":
                self.server["port"] = value
            elif arg == "apikey":
                self.youtube["api-key"] = value

    def get_server_address(self):
        interface = str(self.server["interface"])
        port = int(self.server["port"])
        return interface, port

#  vim: set ts=8 sw=4 tw=0 et :
