# -*- coding:Utf8 -*-

"""
    Fabfile used to automate deploy of the app when add some code.
    Run test first and then add, commit and push to repository.
"""

from fabric.api import local, settings, abort
from fabric.contrib.console import confirm


# Preparation
def test():
    with settings(warn_only=True):
        result = local("nosetests -v", capture=True)
    if result.failed and not confirm("Tests failed. Continue and commit changes ?"):
        abort("Aborted at user request.")


def commit():
    message = raw_input("Enter a git commit message: ")
    local("git add . && git commit -am '{}'".format(message))


def push():
    local("git push origin master")


def prepare():
    test()
    commit()
    push()


# Deploying
def heroku():
    local("git push heroku master")


def heroku_test():
    local("heroku run nosetests -v")


def pull():
    local("git pull origin master")


def deploy():
    # pull()
    test()
    # commit()
    heroku()
    heroku_test()


# Rollback if test does not pass on heroku
def rollback():
    local("heroku rollback")
