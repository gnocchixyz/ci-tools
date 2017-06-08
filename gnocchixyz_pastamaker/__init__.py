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
import atexit
import netrc
import os
import re
import sys
import logging

import daiquiri
import github
import requests
import time

LOG = logging.getLogger(__name__)


def get_login_password(site_name="github.com", netrc_file="~/.netrc"):
    """Read a .netrc file and return login/password for LWN."""
    n = netrc.netrc(os.path.expanduser(netrc_file))
    return "sileht-tester", n.hosts[site_name][2]
    return n.hosts[site_name][0], n.hosts[site_name][2]


def web_github_login(user, password):
    s = requests.Session()
    s.headers['User-Agent'] = (
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/58.0.3029.96 Safari/537.36')
    s.trust_env = False  # Don't read netrc
    r = s.get("https://github.com/login")
    r.raise_for_status()
    m = re.search('<input name="authenticity_token" '
                  'type="hidden" value="([^"]*)" />', r.text)
    token = m.group(1)
    r = s.post("https://github.com/session",
               data={"commit": "Sign in",
                     "utf8": "✓",
                     "authenticity_token": token,
                     "login": user,
                     "password": password})
    r.raise_for_status()
    return s


def web_github_logout(s):
    s.get("https://github.com/logout")


def web_github_update_branch(s, pr_url):
    r = s.get(pr_url + "/merge-button",
              headers={'x-requested-with': 'XMLHttpRequest',
                       'accept': 'text/html'})
    r.raise_for_status()
    m = re.search('/update_branch" .*<input name="authenticity_token" '
                  'type="hidden" value="([^"]*)" />', r.text)
    token = m.group(1)
    m = re.search('<input type="hidden" name="expected_head_oid" '
                  'value="([^"]*)">', r.text)
    expected_head_oid = m.group(1)
    r = s.post(pr_url + "/update_branch",
               headers={'X-Requested-With': 'XMLHttpRequest',
                        'Content-Type': 'application/x-www-form-urlencoded; '
                        'charset=UTF-8'},
               data={"utf8": "✓",
                     "expected_head_oid": expected_head_oid,
                     "authenticity_token": token})
    r.raise_for_status()


def main():
    parser = argparse.ArgumentParser(
        description='Automatically update and merge approved pull requests'
    )
    parser.add_argument("--debug",
                        action='store_true',
                        help="Enabled debugging.")
    parser.add_argument("--polling-interval",
                        type=int,
                        default=10*60,
                        help="Interval between each pull requests check")
    parser.add_argument("--required-approvals",
                        type=int,
                        default=2,
                        help="Number of required approval.")
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

    try:
        client_id, client_secret = get_login_password("pastamaker")
    except KeyError:
        LOG.critical(
            "Unable to find the pastamaker app GitHub client id/secret.\n"
            "Make sure you have a line like this in your ~/.netrc file:\n"
            "machine pastamaker login <login> password <pwd>"
        )
        return 35

    LOG.debug("Found GitHub user: `%s' password: <redacted>", user)

    try:
        owner, repo = args.slug.split('/')
    except Exception:
        LOG.critical("Fail to parse slug name")
        return 40

    g_web = web_github_login(user, password)
    atexit.register(web_github_logout, g_web)

    # TODO(sileht): Use application client_id instead of user creds
    # g = github.Github(client_id=client_id, client_secret=client_secret)
    g = github.Github(user, password)

    g_repo = g.get_user(owner).get_repo(repo)

    def is_pr_mergeable(p):
        approved = len(filter(lambda r: r.state == 'APPROVED',
                              p[0].get_reviews()))
        return (approved >= args.required_approvals and
                p[0].mergeable and
                p[1] in ["pending", "success"])

    def add_pull_state(p):
        head = g_repo.get_commit(p.head.sha)
        return (p, head.get_combined_status().state)

    def is_pr_ready(p):
        pr_base_ref = p[0].base.ref
        pr_base_sha = p[0].base.sha
        real_base_sha = g_repo.get_git_ref("heads/" + pr_base_ref).object.sha
        return pr_base_sha == real_base_sha

    # TODO(sileht): allow to merge branches in //, currently only one PR at a
    # time is handled
    while True:

        # FIXME(sileht): We should be able to use mergeable_state attribute
        # instead of doing many requests to get the last commit and the CI
        # state, but this attribute is undocumented and I don't get what
        # each state mean (clean, behind, blocked, ok, unstable...).
        pulls = list(filter(is_pr_mergeable,
                            map(add_pull_state,
                                g_repo.get_pulls(state="open",
                                                 sort="updated_at",
                                                 direction="asc"))))

        LOG.info("Pull requests approved and mergeable:")
        for p, state in pulls:
            LOG.info("* PR%s (%s): %s" % (p.number, state, p.updated_at))

        pulls_ready = list(filter(is_pr_ready, pulls))

        # Do we have a PR up2date and with CI OK ? if yes merge it!
        pulls_ci_success = list(filter(lambda p: p[1] == "success",
                                       pulls_ready))
        if pulls_ci_success:
            p = pulls_ci_success[0][0]
            p.merge()
            LOG.info("PR#%s merged" % p.number)
            time.sleep(args.polling_interval)
            continue

        # Do we have a PR up2date and with CI pending, if yes
        # wait for it
        pulls_ci_pending = list(filter(lambda p: p[1] == "pending",
                                       pulls_ready))
        if pulls_ci_pending:
            p = pulls_ci_pending[0][0]
            LOG.info("PR#%s waiting for CI" % p.number)
            time.sleep(args.polling_interval)
            continue

        # Now the same but for not up2date PR, so we merge "master" into
        pulls_ci_success = list(filter(lambda p: p[1] == "success", pulls))
        if pulls_ci_success:
            p = pulls_ci_success[0][0]
            web_github_update_branch(g_web, p.html_url)
            LOG.info("PR%s base branch updated" % p.number)
            time.sleep(args.polling_interval)
            continue

        pulls_ci_pending = list(filter(lambda p: p[1] == "pending", pulls))
        if pulls_ci_pending:
            p = pulls_ci_pending[0][0]
            web_github_update_branch(g_web, p.html_url)
            LOG.info("PR%s base branch updated" % p.number)
            time.sleep(args.polling_interval)
            continue

        LOG.info("No PR to update or merge")
        time.sleep(args.polling_interval)


if __name__ == '__main__':
    sys.exit(main())
