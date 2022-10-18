from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from flask_login import current_user
from wtforms import StringField, PasswordField, SubmitField, BooleanField, IntegerField, SelectField, TimeField, EmailField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, NumberRange, Regexp
from flaskblog.models import DocumentType, User


class RegistrationForm(FlaskForm):
    regexp = "^[A-Za-z]+\d+.*$"
    username = StringField('Usuário',
                           validators=[DataRequired(), Length(min=2, max=120)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Senha', validators=[DataRequired(), Regexp(regexp, message='A senha precisa ter letras e caracteres')])
    confirm_password = PasswordField('Confirmar Senha',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Este usuário já existe. Por favor escolha um diferente.')            

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Este email já existe. Por favor escolha um diferente.')


class LoginForm(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Senha', validators=[DataRequired()])
    remember = BooleanField('Lembrar')
    submit = SubmitField('Login')


class UpdateAccountForm(FlaskForm):
    username = StringField('Usuário',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    picture = FileField('Atualizar foto de perfil', validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Atualizar')

    def validate_username(self, username):
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('Este usuário já existe. Por favor escolha um diferente.')

    def validate_email(self, email):
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('Este email já existe. Por favor escolha um diferente.')


class SearchForm(FlaskForm):
    document_type = SelectField('Tipo de Documento', choices=DocumentType.query.all())
    number = IntegerField('Número')
    content = StringField('Conteúdo')
    receiver = EmailField('Destinatário',
                    validators=[DataRequired(), Email()])
    time = TimeField('Horário',
                    validators=[DataRequired()])
    frequency = IntegerField('Periodicidade (dias)',
                            validators=[DataRequired(), NumberRange(min=1)])
    submit = SubmitField('Cadastrar Pesquisa')


class RequestResetForm(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    submit = SubmitField('Redefinir Senha')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is None:
            raise ValidationError('Email não cadastrado. Você deve se registrar primeiro.')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('Senha', validators=[DataRequired()])
    confirm_password = PasswordField('Confirmar Senha',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Redefinir Senha')
