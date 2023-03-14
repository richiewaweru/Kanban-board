import unittest
from app import app, db
from app import User, Task
from werkzeug.security import generate_password_hash
from flask import Flask
import requests

class FlaskTest(unittest.TestCase):
    
    # executed prior to each test
    def setUp(self):
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        with app.app_context():
            db.create_all()
            self.app = app.test_client()
            self.client = app.test_client()
        
       
            self.user = User(username='test', password=generate_password_hash('test', method='sha256'))
            db.session.add(self.user)
            db.session.commit()
            # create test tasks
            self.task1 = Task(title='Test Task 1', complete=False, started=False, user_id=self.user.id)
            db.session.add(self.task1)
            self.task2 = Task(title='Test Task 2', complete=False, started=True, user_id=self.user.id)
            db.session.add(self.task2)
            self.task3 = Task(title='Test Task 3', complete=True, started=True, user_id=self.user.id)
            db.session.add(self.task3)
            db.session.commit()
   
    def tearDown(self):
        with app.app_context():
            self.user = User.query.filter_by(username='test').first()
            #User.query.filter_by(id=self.user.id).delete()
            self.task=Task.query.filter_by(user_id=self.user.id).all()
            Task.query.filter_by(user_id =self.user.id).delete()
            User.query.filter_by(id =self.user.id).delete()
            db.session.commit()
    
            
    # helper method to log in as test user
    def login(self):
        return self.client.post('/login', data=dict(username='test', password='test'), follow_redirects=True)
    
    # helper method to log out
    def logout(self):
        return self.client.get('/logout', follow_redirects=True)
    
    # test home page
    def test_home(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    # test signup
    def test_signup(self):
        # test GET request
        response = self.client.get('/signup')
        self.assertEqual(response.status_code, 200)
        
        # test POST request with valid data
        response = self.client.post('/signup', data=dict(username='newuser', password='password'),follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        
       
        
        
    
    
    # test login and logout
    def test_login_logout(self):
        # test login with valid credentials
        response = self.login()
        self.assertEqual(response.status_code, 200)

    # test kanban page
    def test_kanban(self):
        # test access without login
        response = self.client.get('/kanban')
        self.assertEqual(response.status_code, 302)
        
        # test access with login
        self.login()
        response = self.client.get('/kanban')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test Task 1', response.data)
        self.assertIn(b'Test Task 2', response.data)
        self.assertIn(b'Test Task 3', response.data)

        self.logout()

    def test_add_task(self):
        # log in as test user
        self.login()
        # add new task
        response = self.client.post('/add', data=dict(title='New Test Task'), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        # log out
        self.logout()

     # test add task
    def test_add_task(self):
        # log in as test user
        self.login()
        # add new task
        response = self.client.post('/add', data=dict(title='New Test Task'), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        # check that task was added
        with app.app_context():
            task = Task.query.filter_by(title='New Test Task').first()
            self.assertIsNotNone(task)
            self.assertEqual(task.title, 'New Test Task')
            self.assertFalse(task.started)
            self.assertFalse(task.complete)
        self.logout()

    #test update function
    def test_update_todo_item(self):
        self.login()
        # Test updating an existing todo item
        with app.app_context():
            todo = Task.query.filter_by(title='Test Task 1').first()
            response = self.client.get('/update/{}'.format(todo.id))
            self.assertEqual(response.status_code, 302)
            todo = Task.query.filter_by(title='Test Task 1').first()
            self.assertTrue(not todo.started)
        self.logout()

    #test complete function
    def test_complete_todo_item(self):
        self.login()
        # Test completing an existing todo item
        with app.app_context():
            todo = Task.query.filter_by(title='Test Task 1').first()
            response = self.app.get('/complete/{}'.format(todo.id))
            self.assertEqual(response.status_code, 302)
            todo = Task.query.filter_by(title='Test Task 1').first()
            self.assertTrue(not todo.complete)
        self.logout()
        

    def test_delete_todo_item(self):
        # Test deleting an existing todo item
        self.login()
        with app.app_context():
            todo = Task.query.filter_by(title='Test Task 1').first()
            response = self.app.get('/delete/{}'.format(todo.id), follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            todo = Task.query.filter_by(title='Test Task 1').first()
            self.assertIsNone(todo)
        self.logout()

    def test_edit_page(self):
        # Test editing an existing todo item
        with app.app_context():
            # Get a todo item to edit
            todo = Task.query.filter_by(title='Test Task 1').first()

            # Test GET request to edit page
            response = self.app.get(f'/edit/{todo.id}')
            self.assertEqual(response.status_code, 200)

            # Test POST request to edit page
            response = self.app.post(f'/edit/{todo.id}', data={
                'title': 'Updated Title'}, follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(todo.title,'Updated Title')               
if __name__ == '__main__':
    unittest.main()
