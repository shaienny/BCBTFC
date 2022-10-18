from datetime import datetime
from re import search
#from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from authlib.jose import jwt, JoseError
from flaskblog import db, login_manager, app
from flask_login import UserMixin


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    password = db.Column(db.String(60), nullable=False)

    #def get_reset_token(self, expires_sec=1800):
    #def get_reset_token(self, operation, **kwargs):
    def get_reset_token(self, **kwargs):
        #s = Serializer(app.config['SECRET_KEY'], expires_sec)
        #return s.dumps({'user_id': self.id}).decode('utf-8')
        """ Generate for mailbox validation JWT（json web token）"""
        #  Signature algorithm 
        header = {
        'alg': 'HS256'}
        #  The key used for the signature 
        key = app.config['SECRET_KEY']
        #  Data load to be signed 
        #data = {
        #'id': self.id, 'operation': operation}
        data = {
        'id': self.id}
        data.update(**kwargs)

        return jwt.encode(header=header, payload=data, key=key)

    @staticmethod
    #def verify_reset_token(token):
    #def validate_token(user, token, operation):
    def validate_token(token):
        #s = Serializer(app.config['SECRET_KEY'])
        #try:
        #    user_id = s.loads(token)['user_id']
        #except:
        #    return None
        #return User.query.get(user_id)
        """ Used to verify user registration and change password or mailbox token,  And complete the corresponding confirmation operation """
        key = app.config['SECRET_KEY']

        try:
            data = jwt.decode(token, key)
            return data
        except JoseError:
            return False
        ... #  Other fields confirm 
        return True

    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.image_file}')"

class DocumentType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    def __repr__(self):
        return f"{self.name}"

class Search(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    document_type = db.Column(db.String(100))
    number = db.Column(db.Integer)
    content = db.Column(db.String(100))    
    receiver = db.Column(db.String(120))
    time = db.Column(db.String(100))
    frequency = db.Column(db.Integer)
    user_id = db.Column(db.Integer)
    active = db.Column(db.Integer)
    created_at = db.Column(db.String(100))
    #searchs_history = db.relationship('SearchHistory', backref='search_history', lazy='dynamic')
    def __repr__(self):
        return f"{self.id}"

class SearchHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    search_id = db.Column(db.Integer, db.ForeignKey('search.id'), nullable=False)
    created_at = db.Column(db.String(100))
    search = db.relationship('Search')
    def __repr__(self):
        return f"SearchHistory('{self.id}', '{self.search_id}')"
