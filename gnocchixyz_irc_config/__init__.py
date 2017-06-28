# -*- encoding: utf-8 -*-
#
# Copyright © 2017 Red Hat, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import argparse
import json
import logging
import netrc
import os
import sys

import daiquiri
import github

LOG = daiquiri.getLogger("git-pull-request")


def get_login_password(site_name="github.com", netrc_file="~/.netrc"):
    """Read a .netrc file and return login/password for LWN."""
    n = netrc.netrc(os.path.expanduser(netrc_file))
    return n.hosts[site_name][0], n.hosts[site_name][2]


def main():
    parser = argparse.ArgumentParser(
        description='Set Gnocchixyz irc configuration'
    )
    parser.add_argument("--debug",
                        action='store_true',
                        help="Enabled debugging.")
    parser.add_argument("slug", help="project slug (ie: gnocchixyz/gnocchi)")

    args = parser.parse_args()
    daiquiri.setup(
        outputs=(
            daiquiri.output.Stream(
                sys.stdout,
                formatter=logging.Formatter(
                    fmt="%(message)s")),),
        level=logging.DEBUG if args.debug else logging.INFO,
    )

    try:
        user, password = get_login_password()
    except KeyError:
        LOG.critical(
            "Unable to find your GitHub credentials.\n"
            "Make sure you have a line like this in your ~/.netrc file:\n"
            "machine github.com login <login> password <pwd>"
        )
        return 35

    LOG.debug("Found GitHub user: `%s' password: <redacted>", user)

    try:
        owner, repo = args.slug.split('/')
    except Exception:
        LOG.critical("Fail to parse slug name")
        return 40

    g = github.Github(user, password)
    g_repo = g.get_user(owner).get_repo(repo)

    config = {
        'notice': '0',
        'room': '#gnocchi',
        'ssl': '0',
        'no_colors': '0',
        'server': 'chat.freenode.net',
        'nick': 'pastamaker',
        'message_without_join': '1',
        'long_url': '1',
        'port': '6667'
    }

    for hook in g_repo.get_hooks():
        if hook.name == "irc":
            hook.edit(hook.name, config)
            break
    else:
        hook = g_repo.create_hook("irc", config)

    # check
    for hook in g_repo.get_hooks():
        if hook.name == "irc":
            print(json.dumps(hook.config, sort_keys=True,
                             indent=4, separators=(',', ': ')))


if __name__ == '__main__':
    sys.exit(main())
