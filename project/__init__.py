# -*- coding:Utf8 -*-

from flask import Flask, render_template, request
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.bcrypt import Bcrypt

import datetime

app = Flask(__name__)
app.config.from_pyfile('_config.py')
bcrypt = Bcrypt(app)
db = SQLAlchemy(app)

from project.users.views import users_blueprint
from project.tasks.views import tasks_blueprint


# Register our blueprints
app.register_blueprint(users_blueprint)
app.register_blueprint(tasks_blueprint)

# Api by hands
# from project.api.views import api_blueprint
# app.register_blueprint(api_blueprint)

# Api with library
from flask_restful import Api
from project.api.views import ApiTasks, ApiTaskId

api = Api(app)
api.add_resource(ApiTasks, '/api/v1/tasks/', endpoint='tasks')
api.add_resource(ApiTaskId, '/api/v1/tasks/<int:task_id>', endpoint='task')


# Add error handler
@app.errorhandler(404)
def page_not_found(error):
    if not app.debug:
        now = datetime.datetime.now()
        r = request.url
        with open('error.log', 'a') as f:
            current_timestamp = now.strftime("%d-%m-%Y %H:%M:%S")
            f.write("\n404 error at {}: {}".format(current_timestamp, r))
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    if not app.debug:
        now = datetime.datetime.now()
        r = request.url
        with open('error.log', 'a') as f:
            current_timestamp = now.strftime("%d-%m-%Y %H:%M:%S")
            f.write("\n500 error at {}: {}".format(current_timestamp, r))
    return render_template('500.html'), 500
