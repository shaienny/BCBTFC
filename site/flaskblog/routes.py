from multiprocessing.dummy import active_children
import os
import secrets
from PIL import Image
from flask import render_template, url_for, flash, redirect, request, abort
from sqlalchemy import true, desc
from sympy import POSform
from flaskblog import app, db, bcrypt, mail, bot, scheduler
from flaskblog.forms import (RegistrationForm, LoginForm, UpdateAccountForm,
                             SearchForm, RequestResetForm, ResetPasswordForm)
from flaskblog.models import SearchHistory, User, Search
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message
import subprocess
from selenium import webdriver
from datetime import date, datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler


@app.route("/")
@app.route("/home")
def home():
    return redirect(url_for('search_history'))


@app.route("/about")
def about():
    return render_template('about.html', title='Sobre')


@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Sua conta foi criada! Agora você pode logar', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Registrar', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login incorreto. Por favor verifique o email e senha', 'danger')
    return render_template('login.html', title='Login', form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)

    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn


@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Sua conta foi atualizada!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('account.html', title='Conta',
                           image_file=image_file, form=form)

def my_job():
    print("text")

@app.route("/search/new", methods=['GET', 'POST'])
@login_required
def new_search():
    form = SearchForm()
    if request.method == 'GET':
        form.receiver.data = current_user.email
    elif request.method == 'POST' and form.submit():
        document_type = form.document_type.data
        number = form.number.data
        content = form.content.data
        receiver = form.receiver.data
        time = str(form.time.data)
        frequency = form.frequency.data
        user_id = current_user.get_id()
        search = Search(document_type=document_type, number=number, content=content, receiver=receiver, time=time, frequency=frequency, user_id=user_id, active=1, created_at=str(datetime.now()))
        db.session.add(search)
        db.session.commit()
        search_data = {
            'id': search.id,
            'document_type': document_type,
            'number': number,
            'content': content,
            'frequency': frequency,
            'email': receiver
        }
        scheduler.add_job(bot.search, 'interval', [search_data], days=frequency, start_date=datetime.combine(datetime.now().date(), form.time.data), id=str(search.id))
        flash('Pesquisa cadastrada!', 'success')
        return redirect(url_for('new_search'))
    return render_template('create_search.html', title='Nova Pesquisa',
                           form=form, legend='Nova Pesquisa')   

@app.route("/search-history", methods=['GET'])
@login_required
def search_history():
    searchs = Search.query.filter_by(user_id=current_user.get_id()).order_by(desc('active')).order_by(desc('id'))
    return render_template('search_history.html', title='Histórico de Pesquisa', legend='Histórico de Pesquisa', searchs=searchs)    


@app.route("/search/<int:search_id>/history", methods=['GET'])
@login_required
def search_history_search_id(search_id):
    searchs_history = SearchHistory.query.filter_by(search_id=search_id).join(SearchHistory.search, aliased=True).filter_by(user_id=current_user.get_id())
    return render_template('search_history_search_id.html', title='Histórico de Pesquisa', legend='Histórico de Pesquisa', searchs_history=searchs_history, datetime=datetime)

@app.route("/search/<int:search_id>/pause-continue/<int:active>", methods=['POST'])
@login_required
def pause_continue_search(search_id, active):
    search = Search.query.get_or_404(search_id)
    search.active = active
    db.session.commit()
    if active == 0:
        scheduler.remove_job(str(search_id))
    else:
        search_data = {
            'id': search.id,
            'document_type': search.document_type,
            'number': search.number,
            'content': search.content,
            'frequency': search.frequency,
            'email': search.receiver
        }
        scheduler.add_job(bot.search, 'interval', [search_data], days=search.frequency, start_date=datetime.combine(datetime.now().date(), datetime.strptime(search.time, "%H:%M:%S").time()), id=str(search.id))
    flash('Pesquisa ' + ('in' if active == 0 else '') + 'ativada', 'success')
    return redirect(url_for('search_history'))

def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Redefinição de Senha',
                  sender='noreply@demo.com',
                  recipients=[user.email])
    msg.body = f'''Para redefinir sua senha, visite o link:
{url_for('reset_token', token=token, _external=True)}

Se você não fez este pedido, então simplesmente ignore este email e nenhuma mudança será feita.
'''
    mail.send(msg)

@app.route("/reset_password", methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('Um email foi enviado com as instruções para redefinir sua senha.', 'info')
        return redirect(url_for('login'))
    return render_template('reset_request.html', title='Redefinir Senha', form=form)


@app.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    user = User.validate_token(token)
    if user is False:
        flash('Token expirado ou inválido', 'warning')
        return redirect(url_for('reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User.query.get(user.get('id'))
        user.password = hashed_password
        db.session.commit()
        flash('Sua senha foi atualizada! Você está apto a logar', 'success')
        return redirect(url_for('login'))
    return render_template('reset_token.html', title='Reset Password', form=form)

