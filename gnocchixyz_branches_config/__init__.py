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
        description='Set Gnocchixyz style branches configuration'
    )
    parser.add_argument("--debug",
                        action='store_true',
                        help="Enabled debugging.")
    parser.add_argument("--branch",
                        help="branch to setup (by default all "
                        "branches are setup")
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

    if args.branch:
        protect(args, g_repo, args.branch)
    else:
        for g_branch in g_repo.get_branches():
            protect(args, g_repo, g_branch.name)


def protect(args, g_repo, branch):
    g_repo.protect_branch(branch, enabled=True)

    # NOTE(sileht): Not yet part of the API
    # maybe soon https://github.com/PyGithub/PyGithub/pull/527
    g_repo._requester.requestJsonAndCheck(
        'PUT',
        "{base_url}/branches/{branch}/protection".format(base_url=g_repo.url,
                                                         branch=branch),
        input={
            'required_pull_request_reviews': {
                "dismissal_restrictions": {},
                "dismiss_stale_reviews": True,
            },
            'required_status_checks': {
                'strict': True,
                'contexts': ['continuous-integration/travis-ci'],
            },
            'restrictions': None,
            'enforce_admins': True,
        },
        headers={'Accept': 'application/vnd.github.loki-preview+json'}
    )
    g_branch = g_repo.get_protected_branch(branch)
    print("%s:" % branch)
    print("* protected: %s" % g_branch.protected)
    headers, data = g_repo._requester.requestJsonAndCheck(
            "GET",
            g_repo.url + "/branches/" + branch + '/protection',
            headers={'Accept': 'application/vnd.github.loki-preview+json'}
        )
    print("* required_pull_request_reviews:")
    print("  * dismiss_stale_reviews: %s" %
          data['required_pull_request_reviews']['dismiss_stale_reviews'])
    print("  * dismissal_restrictions: %s" %
          data['required_pull_request_reviews'].get('dismissal_restrictions'))
    print("* required_status_checks:")
    print("  * contexts: %s" %
          data["required_status_checks"]["contexts"])
    print("  * strict: %s" %
          data["required_status_checks"]["strict"])
    print("* restrictions: %s" % data.get("restrictions"))
    print("* enforce_admins: %s" % data["enforce_admins"]["enabled"])

    if args.debug:
        print(json.dumps(data, sort_keys=True,
                         indent=4, separators=(',', ': ')))


if __name__ == '__main__':
    sys.exit(main())
