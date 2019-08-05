import traceback,sys
import os, re, pathlib

from wsgiref.handlers import CGIHandler
from werkzeug.contrib.fixers import ProxyFix
from werkzeug.debug import DebuggedApplication 
from flask import Flask
from flask import Response, abort
from flask import session, get_flashed_messages

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy import Boolean, ForeignKey, Integer, String
from pathlib import Path

import json

# A hack to get /web/zXXXXXXX/...
HOME_DIR = Path.home().parts[-1]
FULL_DIR = os.path.dirname(os.path.realpath(__file__))
DB_NAME = "vue_server.db"

# Breaks flask when not set
if 'PATH_INFO' not in os.environ:
    os.environ['PATH_INFO'] = ''

for variable in 'REDIRECT_SCRIPT_URI REQUEST_URI SCRIPT_URI PATH_INFO SCRIPT_URL REDIRECT_URL REDIRECT_SCRIPT_URL'.split():
    if '//' in os.environ.get(variable, ''):
        os.environ[variable] = re.sub(r'(^|[^:])/+', r'\1/', os.environ[variable])

try:
    app = Flask(__name__)
    app.secret_key = "ThisKeyIsNotSecretButThat1sTotallyFineByMe:)"

    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///"+ os.path.join(DB_NAME)
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # don't log on errors
    app.logger.disabled = True

    db = SQLAlchemy(app)
    migrate = Migrate(app, db)


    class Todo(db.Model):
        __tablename__ = 'todo'
        # Here we define columns for the table person
        # Notice that each column is also a normal Python instance attribute.
        id = db.Column(Integer, primary_key=True)
        tags = db.Column(String(250), nullable=False)
        text = db.Column(String(1000), nullable=False)
        status = db.Column(String(250), nullable=False)


    @app.route('/', methods=['GET'])
    def listings():
        files = list(map(str, pathlib.Path(FULL_DIR).glob("*.html")))
        objects = []
        for f in files:
            objects.append({
                'href': "http://web.cse.unsw.edu.au/~z5205060/vue/"+f.split('/')[-1],
                'name': f.split('/')[-1].replace('.html', '')
            })
        return json.dumps(objects)

    @app.route('/todos/new/', methods=['POST'])
    def new_todo():
        new_todo = Todo(tags=request.form['tags'], text=request.form['text'], status=request.form['status'])
        db.session.add(new_todo)
        db.session.commit()
        return json.dumps({'id': new_todo.id})

    def todo_to_dict(todo):
        return {
            'id': todo.id,
            'tags': todo.tags,
            'text': todo.text,
            'status': todo.status,
        }

    @app.route('/todos/', methods=['GET'])
    def list_todos():
        todos = []
        for todo in Todo.query.all():
            todos.append(todo_to_dict(todo))
        return json.dumps(todos)

    @app.route('/todos/<int:todo_id>/', methods=['GET', 'PATCH'])
    def check_todos(todo_id):
        todo = Todo.query.get(todo_id)
        if todo is None:
            abort(404)
        if request.method == "PATCH":
            if request.form.get('id'):
                abort(400)
            if request.form.get('tags'):
                todo.tags = request.form['tags']
            if request.form.get('text'):
                todo.text = request.form['text']
            if request.form.get('status'):
                todo.status = request.form['status']
            db.session.add(new_todo)
            db.session.commit()
        return json.dumps({'id': new_todo.id})


except BaseException:
    print("Content-type: text/html\n")
    print('<pre>' + traceback.format_exc() + '</pre>')
    sys.exit(1)

# This is a backup error handler for when flask is loaded
@app.errorhandler(500)
def error(func):
    debug_info = [
        traceback.format_exc(),
    ]
    return Response('<pre>'+'\n\n'.join(debug_info)+'</pre>', status=500)

if __name__ == '__main__':
    app.wsgi_app = ProxyFix(app.wsgi_app)
    # app = DebuggedApplication(app)
    CGIHandler().run(app)

