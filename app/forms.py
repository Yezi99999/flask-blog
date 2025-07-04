from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, PasswordField, SubmitField, BooleanField, FileField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from app.extensions import db
from app.models import User, Category

class PostForm(FlaskForm):
    title = StringField('标题', validators=[DataRequired(), Length(max=100)])
    content = TextAreaField('内容', validators=[DataRequired()])
    category = SelectField('分类', coerce=int, validators=[DataRequired()])
    file = FileField('上传文件')  # 添加文件字段
    submit = SubmitField('提交')

    def __init__(self, *args, **kwargs):
        super(PostForm, self).__init__(*args, **kwargs)
        self.category.choices = [(cat.id, cat.name) for cat in Category.query.all()]


class CommentForm(FlaskForm):
    content = TextAreaField('评论内容', validators=[DataRequired(), Length(max=500)])
    submit = SubmitField('发表评论')

class CommentEditForm(FlaskForm):
    content = TextAreaField('编辑评论', validators=[DataRequired(), Length(max=500)])
    submit = SubmitField('保存修改')

class LoginForm(FlaskForm):
    # 支持邮箱或用户名登录
    identity = StringField('邮箱或用户名', validators=[DataRequired()])
    password = PasswordField('密码', validators=[DataRequired()])
    remember = BooleanField('记住我')
    submit = SubmitField('登录')

class RegistrationForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('邮箱', validators=[DataRequired(), Email()])
    password = PasswordField('密码', validators=[DataRequired()])
    confirm_password = PasswordField('确认密码', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('注册')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('该用户名已被使用，请选择其他用户名。')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('该邮箱已被注册，请使用其他邮箱。')

class SearchForm(FlaskForm):
    query = StringField('搜索', validators=[DataRequired()])
    submit = SubmitField('搜索')