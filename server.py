import eventlet

eventlet.monkey_patch()

import os
from eventlet.wsgi import server
from flask import Flask, render_template, redirect, abort
from pyexpat.errors import messages
from sqlalchemy.dialects.oracle.dictionary import all_users
from sqlalchemy.testing.suite.test_reflection import users
from ai import test_answer, open_file_to_research_origin, decode_text
from paths import BOOKS_DIR, TEMP_DIR, DB_PATH, ensure_dirs, resolve_book_path, clean_filename
from data import db_session
from data.books import Book
from data.queries import Query
from data.users import User
from forms.add_book import AddBookForm
from forms.login import LoginForm
from forms.register import RegisterForm
from flask_login import current_user, LoginManager, login_user, login_required, logout_user
from flask import request
from flask_socketio import SocketIO, emit
import time

ensure_dirs()

app = Flask(__name__)
app.config['SECRET_KEY'] = '1234'
socketio = SocketIO(app, async_mode='eventlet')

login_manager = LoginManager()
login_manager.init_app(app)


def get_all_books():
    db_sess = db_session.create_session()
    all_books = db_sess.query(Book).all()
    return all_books


def get_all_queries(id):
    db_sess = db_session.create_session()
    queries = db_sess.query(Query).filter(Query.user_id == id).all()
    return queries


def get_all_titles():
    db_sess = db_session.create_session()
    books = db_sess.query(Book).all()
    res = [i.title for i in books]
    return res


def get_all_book_filepathes():
    db_sess = db_session.create_session()
    books = db_sess.query(Book).all()
    res = [i.filepath for i in books]
    return res


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@socketio.on('connect')
def test_connect():
    print('Client connected:', request.sid)


@socketio.on('disconnect')
def test_disconnect():
    print('Client disconnected:', request.sid)


@socketio.on('message')
def handle_message(data):
    print('received message: ' + str(data))
    user = data.get('user', 'Anonymous')
    msg = data.get('msg', '')

    if msg:
        user_message_data = {'user': current_user.username, 'msg': msg, 'type': 'user'}

        emit('message', user_message_data, broadcast=True)

        titles_list = get_all_titles()
        server_answer = test_answer(msg, titles_list)

        server_reply_data = {'user': 'Server', 'msg': server_answer, 'type': 'server'}
        time.sleep(0.1)

        emit('message', server_reply_data, room=request.sid)

        db_sess = db_session.create_session()
        query = Query(question=user_message_data['msg'],
                      answer=server_reply_data['msg'],
                      user_id=current_user.id)
        db_sess.add(query)
        db_sess.commit()


@app.route('/')
def index_with_chat():
    initial_messages = []
    initial_messages.append({'user': 'Server', 'msg': 'Привет! Добро пожаловать в чат.', 'type': 'server'})

    if current_user.is_authenticated:
        messages = get_all_queries(current_user.id)
        for msg in messages:
            initial_messages.append({'user': current_user.username, 'msg': msg.question, 'type': 'user'})
            initial_messages.append({'user': 'Server', 'msg': msg.answer, 'type': 'server'})

    return render_template('index_with_chat.html', messages=initial_messages)


@app.route('/index')
def index():
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        user = User(
            username=form.username.data,
            email=form.email.data
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route('/library')
def library():
    db_sess = db_session.create_session()
    books = db_sess.query(Book).all()
    books.sort(key=lambda x: x.title)
    return render_template('library.html', books=books)


@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    form = AddBookForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        file = form.file.data
        original_name = os.path.basename(file.filename.replace('\\', '/'))

        if not original_name.lower().endswith('.txt'):
            return render_template(
                'add_book.html',
                form=form,
                message='Можно загружать только файлы формата txt'
            )

        text = decode_text(file.read())

        temp_path = os.path.join(TEMP_DIR, original_name)
        with open(temp_path, 'w', encoding='utf-8') as f:
            f.write(text)

        new_title = original_name

        if form.auto_name.data:
            new_title = open_file_to_research_origin(temp_path)[:-1] + ".txt"
            if new_title.startswith('Информации о'):
                new_title = original_name

        new_title = clean_filename(new_title) or original_name

        if db_sess.query(Book).filter(Book.title == new_title).first():
            return render_template(
                'add_book.html',
                form=form,
                message='Книга с таким названием уже есть'
            )

        final_path = os.path.join(BOOKS_DIR, new_title)
        with open(final_path, 'w', encoding='utf-8') as f:
            f.write(text)

        os.remove(temp_path)

        book = Book(
            title=new_title,
            filepath='files/' + new_title
        )
        db_sess.add(book)
        db_sess.commit()

        return redirect('/library')

    return render_template('add_book.html', form=form)


def search_or_create_admin():
    db_sess = db_session.create_session()
    users = db_sess.query(User).all()
    if not users:
        user = User(
            username='admin',
            email='admin@admin'
        )
        user.set_password('admin')
        db_sess.add(user)
        db_sess.commit()


@app.route('/book_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def book_delete(id):
    db_sess = db_session.create_session()
    book = db_sess.query(Book).filter(Book.id == id).first()
    if book:
        db_sess.delete(book)
        db_sess.commit()
    else:
        abort(404)
    return redirect('/')


@app.route('/watch_book/<int:id>')
def watch_book(id):
    db_sess = db_session.create_session()
    book = db_sess.query(Book).filter(Book.id == id).first()
    if book:
        book_path = resolve_book_path(book.filepath)
        if not os.path.exists(book_path):
            abort(404)
        with open(book_path, 'rb') as f:
            text = decode_text(f.read())
        return render_template('watch_book.html', book=book, text=text)


if __name__ == '__main__':
    db_session.global_init(DB_PATH)
    search_or_create_admin()
    socketio.run(app, host='0.0.0.0', port=8085, debug=True)