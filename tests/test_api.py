# -*- coding:Utf8 -*-
# tests/test_api.py

import unittest

from datetime import date

from project import app, db, bcrypt
from project.models import Task, User


class APITests(unittest.TestCase):

    """
        API unit test.
    """

# USEFUL FUNCTIONS

    def setUp(self):
        """
            Executing prior to each tasks.
            Create environnement where tests will be executing.
            Start server without the debug mode.
        """
        app.config.from_object('project._config.TestConfig')
        self.app = app.test_client()
        db.create_all()

        self.assertEquals(app.debug, False)

    def tearDown(self):
        """
            Executing after each task.
            Clean environnement.
        """
        db.session.remove()
        db.drop_all()

# HELPER METHODS

    def add_tasks(self, user_id=1):
        """
            Foreign key constraint active by default on my sqlite3 build.
            Need to add first a user before adding a task.
        """
        db.session.add(Task("Run around in circles", date(2015, 10, 22), 10,
                            date(2015, 10, 5), 1, user_id))
        db.session.commit()

        db.session.add(Task("Purchase Real Python", date(2016, 2, 23), 10,
                            date(2016, 2, 7), 1, user_id))
        db.session.commit()

    def create_user(self):
        db.session.add(User("Tester", "mail@mail.fr",
                            bcrypt.generate_password_hash("python")))
        db.session.commit()

    def create_admin_user(self, name='Superman', email='admin@monMail.com',
                          password='allpowerful'):
        new_user = User(name=name, email=email,
                        password=bcrypt.generate_password_hash(password),
                        role='admin')
        db.session.add(new_user)
        db.session.commit()

    def logout(self):
        return self.app.get('logout/', follow_redirects=True)

    def login(self, name='Tester', password="python"):
        return self.app.post('/', data=dict(name=name, password=password),
                             follow_redirects=True)

    def register(self, name='Tester', email='mail@monMail.com',
                 password="python",
                 confirm="python"):
        return self.app.post('register/', data=dict(name=name, password=password,
                                                    email=email, confirm=confirm),
                             follow_redirects=True)


# TEST GET

    def test_collection_endpoint_returns_correct_data(self):
        self.create_user()
        self.add_tasks()
        response = self.app.get("api/v1/tasks/", follow_redirects=True)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.mimetype, 'application/json')
        self.assertIn(b'Run around in circles', response.data)
        self.assertIn(b'Purchase Real Python', response.data)

    def test_resource_endpoint_returns_correct_data(self):
        self.create_user()
        self.add_tasks()
        response = self.app.get('api/v1/tasks/2', follow_redirects=True)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.mimetype, 'application/json')
        self.assertIn(b'Purchase Real Python', response.data)
        self.assertNotIn(b'Run around in circles', response.data)

    def test_invalid_resource_endpoint_returns_error(self):
        self.create_user()
        self.add_tasks()
        # A task id which not yet exist.
        response = self.app.get('api/v1/tasks/209', follow_redirects=True)
        self.assertEquals(response.status_code, 404)
        self.assertEquals(response.mimetype, 'application/json')
        self.assertIn(b'Element does not exist', response.data)


# TEST POST

    def test_existing_user_can_post_task_using_api(self):
        # Add a user.
        self.create_user()
        # Add a task.
        response = self.app.post('api/v1/tasks/',
                                 data={"name": "Add a new task using POST API",
                                       "user_name": "Tester",
                                       "password": "python",
                                       "due_date": "22/09/2055",
                                       "priority": 2},
                                 follow_redirects=True)
        self.assertEquals(response.status_code, 201)
        self.assertEquals(response.mimetype, 'application/json')
        self.assertIn(b'"name": "Add a new task using POST API"', response.data)
        self.assertIn(b'"Task created":', response.data)

    def test_non_existing_user_cannot_post_task_using_api(self):
        # Add a user.
        self.create_user()
        # Add task.
        response = self.app.post('api/v1/tasks/',
                                 data={"name": "Add a new task using POST API",
                                       "user_name": "Cracker",
                                       "password": "crackcrack",
                                       "due_date": "22/09/2055",
                                       "priority": 2},
                                 follow_redirects=True)
        self.assertEquals(response.status_code, 401)
        self.assertEquals(response.mimetype, 'application/json')
        self.assertIn(b'User does not exist', response.data)

    def test_existing_user_cannot_post_task_using_api_with_wrong_data(self):
        # Test password hash and priority range
        # Add a user.
        self.create_user()
        # Password test
        response1 = self.app.post('api/v1/tasks/',
                                  data={"name": "Add a new task using POST API",
                                        "user_name": "Tester",
                                        "password": "crackcrack",
                                        "due_date": "22/09/2055",
                                        "priority": 2},
                                  follow_redirects=True)
        self.assertEquals(response1.status_code, 401)
        self.assertEquals(response1.mimetype, 'application/json')
        self.assertIn(b'User does not exist', response1.data)
        # Priority test
        response2 = self.app.post('api/v1/tasks/',
                                  data={"name": "Add a new task using POST API",
                                        "user_name": "Tester",
                                        "password": "python",
                                        "due_date": "22/09/2055",
                                        "priority": 333},
                                  follow_redirects=True)
        self.assertEquals(response2.status_code, 400)
        self.assertEquals(response2.mimetype, 'application/json')
        self.assertIn(b'error: priority must be between 1 and 10 included', response2.data)

    def test_existing_user_cannot_post_task_using_api_without_required_data(self):
        # Test if all required field are inside the request.
        # Add a user.
        self.create_user()
        response1 = self.app.post('api/v1/tasks/',
                                  data={"name": "Add a new task using POST API",
                                        "user_name": "Tester",
                                        "password": "crackcrack",
                                        "priority": 2},
                                  follow_redirects=True)
        self.assertEquals(response1.status_code, 400)
        self.assertEquals(response1.mimetype, 'application/json')
        self.assertIn(b'Missing required parameter in the JSON body or the post body or the query string', response1.data)


# TEST PUT

    def test_logged_user_can_update_task_using_api_if_owner(self):
        # Register and login to populate session.
        self.register()
        self.login()
        # Add two tasks.
        self.add_tasks()
        # Try to update it own task.
        response = self.app.put('api/v1/tasks/2',
                                data={"name": "Updated",
                                      "priority": 2,
                                      "due_date": "22/01/0888"},
                                follow_redirects=True)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.mimetype, 'application/json')
        self.assertIn(b'"priority": 2', response.data)
        self.assertIn(b'"Task updated":', response.data)
        self.assertIn(b'"due_date": "0888-01-22"', response.data)

    def test_not_logged_user_cannot_update_task_using_api(self):
        # Register.
        self.register()
        # Add two tasks.
        self.add_tasks()
        # Try to update it own task.
        response = self.app.put('api/v1/tasks/2',
                                data={"name": "Updated",
                                      "priority": 2},
                                follow_redirects=True)
        self.assertEquals(response.status_code, 401)
        self.assertEquals(response.mimetype, 'application/json')
        self.assertIn(b'error: You must be logged in before trying to update a task', response.data)

    def test_logged_user_cannot_update_task_using_api_if_wrong_input(self):
        # Register and login to populate session.
        self.register()
        self.login()
        # Add two tasks.
        self.add_tasks()
        # Try to update it own task.
        response = self.app.put('api/v1/tasks/2',
                                data={"priority": 54},
                                follow_redirects=True)
        self.assertEquals(response.status_code, 400)
        self.assertEquals(response.mimetype, 'application/json')
        self.assertIn(b'error: priority must be between 1 and 10 included', response.data)

    def test_logged_user_cannot_update_task_using_api_if_not_owner(self):
        # Register a user and add tasks.
        self.register()
        self.register(name='Jérémy', email='jeremy@monMail.com',
                      password='notOwner', confirm='notOwner')
        # Add task using the second user registered as owner (first == 1).
        self.add_tasks(user_id=2)
        # Log in as first user (user_id == 1)
        self.login()
        # Try to update a task of another user.
        response = self.app.put('api/v1/tasks/2',
                                data={"name": "Updated"},
                                follow_redirects=True)
        self.assertEquals(response.status_code, 403)
        self.assertEquals(response.mimetype, 'application/json')
        self.assertIn(b'A user can only update or delete it own tasks.', response.data)

    def test_logged_admin_can_update_task_using_api_if_not_owner(self):
        # Register a user and add tasks.
        self.register()
        self.add_tasks()
        # Register an admin user and log in him.
        self.create_admin_user()
        self.login(name="Superman", password="allpowerful")
        # Try to update a task of another user as admin.
        response = self.app.put('api/v1/tasks/2',
                                data={"name": "Updated",
                                      "priority": 2},
                                follow_redirects=True)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.mimetype, 'application/json')
        self.assertIn(b'"priority": 2', response.data)
        self.assertIn(b'"Task updated":', response.data)


# TEST DELETE

    def test_logged_user_can_delete_task_using_api_if_owner(self):
        # Register and login to populate session.
        self.register()
        self.login()
        # Add two tasks.
        self.add_tasks()
        # Test if a user can see all tasks before deleted one.
        response1 = self.app.get("api/v1/tasks/", follow_redirects=True)
        self.assertIn(b'Run around in circles', response1.data)
        self.assertIn(b'Purchase Real Python', response1.data)
        # Try to delete a task.
        response2 = self.app.delete('api/v1/tasks/2', follow_redirects=True)
        self.assertEquals(response2.status_code, 200)
        self.assertEquals(response2.mimetype, 'application/json')
        self.assertIn(b'"Task deleted":', response2.data)
        # Check that the deleted task does not appear.
        response3 = self.app.get("api/v1/tasks/", follow_redirects=True)
        self.assertIn(b'Run around in circles', response3.data)
        self.assertNotIn(b'Purchase Real Python', response3.data)

    def test_not_logged_user_cannot_delete_task_using_api(self):
        # Register.
        self.register()
        # Add two tasks.
        self.add_tasks()
        # Try to delete a task.
        response1 = self.app.delete('api/v1/tasks/2', follow_redirects=True)
        self.assertEquals(response1.status_code, 401)
        self.assertEquals(response1.mimetype, 'application/json')
        self.assertIn(b'error: You must be logged in before trying to update a task', response1.data)
        # Test if all tasks still inside the database.
        response2 = self.app.get("api/v1/tasks/", follow_redirects=True)
        self.assertIn(b'Run around in circles', response2.data)
        self.assertIn(b'Purchase Real Python', response2.data)

    def test_logged_user_cannot_delete_task_using_api_if_not_owner(self):
        # Register a user and add tasks.
        self.register()
        self.register(name='Jérémy', email='jeremy@monMail.com',
                      password='notOwner', confirm='notOwner')
        # Add task using the second user registered as owner (first=1).
        self.add_tasks(user_id=2)
        # Log in as first user (user_id == 1)
        self.login()
        # Try to update a task of another user.
        response1 = self.app.delete('api/v1/tasks/2', follow_redirects=True)
        self.assertEquals(response1.status_code, 403)
        self.assertEquals(response1.mimetype, 'application/json')
        self.assertIn(b'A user can only update or delete it own tasks.', response1.data)
        # Test if all tasks still inside the database.
        response2 = self.app.get("api/v1/tasks/", follow_redirects=True)
        self.assertIn(b'Run around in circles', response2.data)
        self.assertIn(b'Purchase Real Python', response2.data)

    def test_logged_admin_can_delete_task_using_api_if_not_owner(self):
        # Register a user and add tasks.
        self.register()
        self.add_tasks()
        # Register an admin user and log in him.
        self.create_admin_user()
        self.login(name="Superman", password="allpowerful")
        # Try to update a task of another user as admin.
        response1 = self.app.delete('api/v1/tasks/2', follow_redirects=True)
        self.assertEquals(response1.status_code, 200)
        self.assertEquals(response1.mimetype, 'application/json')
        self.assertIn(b'"Task deleted":', response1.data)
        # Check that the deleted task does not appear.
        response2 = self.app.get("api/v1/tasks/", follow_redirects=True)
        self.assertIn(b'Run around in circles', response2.data)
        self.assertNotIn(b'Purchase Real Python', response2.data)


if __name__ == '__main__':
    unittest.main()
