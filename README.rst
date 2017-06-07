===================
gnocchixyz-ci-tools
===================

.. image:: https://travis-ci.org/jd/git-pull-request.png?branch=master
    :target: https://travis-ci.org/jd/git-pull-request
    :alt: Build Status

gnocchixyz-ci-tools are tooling used by gnocchixyz CI to configur
travis and github.

Github branches protections
---------------------------

Github projects branches configuration can be done with::

  $ gnocchixyz-branches-config gnocchixyz/python-gnocchiclient

It sets up master and stable/* branches permissions

Or only one branch with::

  gnocchixyz-branches-config gnocchixyz/python-gnocchiclient --branch stable/3.1

When a new branch is created this script must be re-run to update the
permissions to the new branch.

Travis-ci docker image
----------------------

The docker travis image is hosted here:

* https://hub.docker.com/r/gnocchixyz/ci-tools

The image is automatically rebuild on each change to this repository by
dockerhub itself.

If needed a manually rebuild can be done via the dockerhub gnocchixyz account.
