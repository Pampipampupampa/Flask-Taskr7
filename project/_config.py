# -*- coding:Utf8 -*-

import os

########################
#    Main Program :    #
########################

# Grabs the folder where the script runs
basedir = os.path.abspath(os.path.dirname(__file__))

TEST_DB = 'test.db'  # Database used for testing


# Handle all configurations here
class BaseConfig(object):

    DEBUG = False
    SECRET_KEY = 'Trb\x8e&\x06Q\x1eYU\xb1U\xf4_\xfdpEua\x97"\x8d]L'
    WTF_CSRF_ENABLED = True
    SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URI']
    print(SQLALCHEMY_DATABASE_URI)


class TestConfig(BaseConfig):
    DEBUG = False
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, TEST_DB)


class DevelopmentConfig(BaseConfig):
    DEBUG = True


class ProductionConfig(BaseConfig):
    DEBUG = False
