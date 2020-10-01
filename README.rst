===================
gnocchixyz-ci-tools
===================

.. image:: https://travis-ci.org/gnocchixyz/ci-tools.png?branch=stable/4.3
    :target: https://travis-ci.org/gnocchixyz/ci-tools
    :alt: Build Status

gnocchixyz-ci-tools is a set of tools used by the gnocchixyz CI to configure
Travis and GitHub.

GitHub branches protections
---------------------------

GitHub projects branches configuration can be done with::

  $ gnocchixyz-branches-config gnocchixyz/python-gnocchiclient

It sets up `master` and `stable/*` branches permissions so that they are
protected and cannot be pushed directly and requires Travis-CI to be pass
before merge anything.

You can protect only one branch by passing the `--branch` option::

  gnocchixyz-branches-config gnocchixyz/python-gnocchiclient --branch stable/3.1

When a new branch is created this script must be run again to set the right
permissions for the new branch.

Travis CI docker image
----------------------

The docker image used by Travis CI is hosted here:

* https://hub.docker.com/r/gnocchixyz/ci-tools

The image is automatically rebuilt on each change done on this repository by
dockerhub itself.

If needed, a manual rebuild can be done by using the dockerhub gnocchixyz
account.
