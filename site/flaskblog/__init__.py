import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from flaskblog import bot
import math

app = Flask(__name__)
app.config['SECRET_KEY'] = '5791628bb0b13ce0c676dfde280ba245'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = "shaiennyfrezende@gmail.com"
app.config['MAIL_PASSWORD'] = "gbfdcwoohpvfkwwh"
mail = Mail(app)

results = db.session.execute("""
    SELECT
        s.id,
        s.document_type,
        IIF(s.number IS NULL, '', s.number) number,
        s.content,
        u.username,
        s.receiver,
        s.time,
        s.frequency,
        IIF(sh.created_at IS NULL, s.created_at, (SELECT created_at FROM search_history WHERE search_id = s.id ORDER BY id DESC LIMIT 1)) last_search
    FROM
        user u,
        search s
    LEFT JOIN
        search_history sh ON sh.search_id = s.id
    WHERE
        s.user_id = u.id
        AND s.active = 1
	GROUP BY
		s.id""")
scheduler = BackgroundScheduler(timezone="America/Sao_Paulo")
for result in results:
    search_data = {
        'id': result[0],
        'document_type': result[1],
        'number': result[2],
        'content': result[3],
        'frequency': result[7],
        'email': result[5]
    }
    start_date = datetime.combine(datetime.strptime(result[8], "%Y-%m-%d %H:%M:%S.%f").date(), datetime.strptime(result[6], "%H:%M:%S").time())
    scheduler.add_job(bot.search, 'interval', [search_data], days=result[7], start_date=start_date, id=str(result[0]))
scheduler.start()

from flaskblog import routes
