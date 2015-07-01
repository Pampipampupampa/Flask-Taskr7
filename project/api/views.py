# -*- coding:Utf8 -*-
# project/api/views.py


from functools import wraps
import datetime

# Api by hands using blueprint.
# from flask import flash, redirect, jsonify, session, url_for, Blueprint, make_response

# Api using flask_restful
from flask import session
from flask_restful import Resource, reqparse, abort, fields, marshal

from project import db, bcrypt
from project.models import Task, User


# Return only defined field inside this dict using marshal and fields modules.
task_fields = {
    'name': fields.String,
    'posted_date': fields.String,
    'due_date': fields.String,
    'priority': fields.Integer,
    'status': fields.Integer
}


# Tools
def login_required(test):
    """
        Used as a decorator. It ensure that user is login before
        let him access to the decorated route.
    """
    @wraps(test)
    def wrapper(*args, **kwargs):
        if 'logged_in' in session:
            return test(*args, **kwargs)
        else:
            abort(401, message="error: You must be logged in before trying to update a task")
    return wrapper


def abort_if_task_doesnt_exist(task_id, task):
    """
        Abort api demand if task_id does not exist.
    """
    if not task or task_id != task.task_id:
        abort(404, message="error: Element does not exist")


def abort_if_user_doesnt_exist(user, password):
    """
        Abort api demand if user name does not exist or if user name and
        password do not match an existing account.
    """
    if user is None or not bcrypt.check_password_hash(user.password, password):
        abort(401, message="error: User does not exist or user name and password do not match.")


def abort_if_wrong_priority(priority):
    """
        Abort api demand if wrong priority number.
    """
    if type(priority) != int or priority > 10 or priority < 1:
        abort(400, message="error: priority must be between 1 and 10 included")


def abort_if_wrong_user(user_id, task_user_id):
    """
        Abort api demand if wrong user ask access.
    """
    if session['role'] != "admin":
        if user_id != task_user_id:
            abort(403, message="error: A user can only update or delete it own tasks.")


# Routes

class ApiTasks(Resource):
    """
        Overload Api base class Resource.
        Support for GET and POST.
    """
    def __init__(self):
        # Parser for add a new task.
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('name', type=str, required=True,
                                 help='A task need a task name.')
        self.parser.add_argument('user_name', type=str, required=True)
        self.parser.add_argument('password', type=str, required=True)
        self.parser.add_argument('due_date', type=str, required=True,
                                 help='Use this format: DD/MM/YYYY')
        self.parser.add_argument('priority', type=int, required=True)
        super(ApiTasks, self).__init__()

    def get(self):
        results = db.session.query(Task).limit(20).offset(0).all()
        json_results = []
        for result in results:
            data = {'task_id': result.task_id,
                    'task name': result.name,
                    'due date': str(result.due_date),
                    'priority': result.priority,
                    'posted date': str(result.posted_date),
                    'status': result.status,
                    'user id': result.user_id
                    }
            json_results.append(data)
        # Call of jsonify() by flask_restful.
        return json_results, 200

    def post(self):
        """
            Add Rest operation: POST.
            Implemented to allow posting whithout have to log in, but need to pass
            password and user_name as arguments.
        """
        # Recup arguments.
        args = self.parser.parse_args()
        # Recup user and password.
        user = db.session.query(User).filter_by(name=args['user_name']).first()
        password = args['password']
        # Test if user and password match.
        abort_if_user_doesnt_exist(user, password)
        # Convert date to correct datetime.date type.
        date = datetime.datetime.strptime(args['due_date'], '%d/%m/%Y')
        # Check priority and avoid priority > 10 or smaller than 1.
        priority = args["priority"]
        abort_if_wrong_priority(priority)

        # Create dict of parameters for Task creator.
        dict_task = {'name': args["name"],
                     'due_date': date,
                     'posted_date': datetime.datetime.utcnow(),
                     'priority': priority,
                     'status': 1,
                     'user_id': user.user_id
                     }
        # Create new task.
        new_task = Task(**dict_task)
        db.session.add(new_task)
        db.session.commit()
        task = {data: dict_task[data] if "date" not in data
                else str(dict_task[data]) for data in dict_task}
        # Display new task.
        return {'Task created': marshal(task, task_fields)}, 201


class ApiTaskId(Resource):
    """
        Overload Api base class Resource.
        Api on direct task id.
        Support for GET, PUT, and DELETE.
    """

    def __init__(self):
        # Parser for update a task.
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('name', type=str)
        self.parser.add_argument('due_date', type=str)
        self.parser.add_argument('priority', type=int)
        self.parser.add_argument('status', type=int)
        super(ApiTaskId, self).__init__()

    def get(self, task_id):
        task = db.session.query(Task).filter_by(task_id=task_id).first()
        abort_if_task_doesnt_exist(task_id, task)
        json_result = {'task_id': task.task_id,
                       'name': task.name,
                       'due_date': str(task.due_date),
                       'priority': task.priority,
                       'posted_date': str(task.posted_date),
                       'status': task.status,
                       'user_id': task.user_id
                       }
        # Call of jsonify by flask_restful.
        return {'Corresponding Task': marshal(json_result, task_fields)}, 200

    @login_required
    def put(self, task_id):
        # Recup arguments.
        args = self.parser.parse_args()
        # Check if task exists.
        task = db.session.query(Task).filter_by(task_id=task_id)
        abort_if_task_doesnt_exist(task_id, task.first())
        # Check if user logged_in is the task owner (or admin)
        abort_if_wrong_user(session['user_id'], task.first().user_id)
        # Test priority field value.
        abort_if_wrong_priority(args['priority'])
        # Update task with new fields.
        for key, value in args.items():
            if value is not None:
                # Convert date to correct datetime.date type.
                if key == 'due_date':
                    value = datetime.datetime.strptime(value, '%d/%m/%Y')
                task.update({key: value})
        db.session.commit()
        # Display task updated.
        return {'Task updated': marshal(task.first(), task_fields)}, 200

    @login_required
    def delete(self, task_id):
        # Check if task exists.
        task = db.session.query(Task).filter_by(task_id=task_id)
        abort_if_task_doesnt_exist(task_id, task.first())
        # Check if user logged_in is the task owner (or admin)
        abort_if_wrong_user(session['user_id'], task.first().user_id)
        # Delete task.
        task.delete()
        db.session.commit()
        # Display task deleted.
        return {'Task deleted': marshal(task.first(), task_fields)}, 200


################################################################################
# # Equivalent by hands

# # Config
# api_blueprint = Blueprint("api", __name__)

# @api_blueprint.route("/api/v1/tasks/")
# def api_tasks():
#     results = db.session.query(Task).limit(10).offset(0).all()
#     json_results = []
#     for result in results:
#         data = {'task_id': result.task_id,
#                 'task name': result.name,
#                 'due date': str(result.due_date),
#                 'priority': result.priority,
#                 'posted date': str(result.posted_date),
#                 'status': result.status,
#                 'user id': result.user_id
#                 }
#         json_results.append(data)
#     # jsonify allows beautiful code. Avoid code below.
#     # return json.dumps(json_results), 200, { "Content-Type" :"application/json"}
#     return jsonify(items=json_results)


# @api_blueprint.route("/api/v1/tasks/<int:task_id>")
# def task(task_id):
#     result = db.session.query(Task).filter_by(task_id=task_id).first()
#     if result:
#         json_result = {'task_id': result.task_id,
#                        'task name': result.name,
#                        'due date': str(result.due_date),
#                        'priority': result.priority,
#                        'posted date': str(result.posted_date),
#                        'status': result.status,
#                        'user id': result.user_id
#                        }
#         code = 200
#     else:
#         json_result = {"error": "Element does not exist"}
#         code = 404
#     return make_response(jsonify(json_result), code)
