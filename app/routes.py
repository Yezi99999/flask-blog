# flask-blog-complete/app/routes.py

from flask import render_template, url_for, flash, redirect, request, Blueprint, make_response, abort, jsonify
from flask_login import login_user, current_user, logout_user, login_required
from app import db
from app.models import User, Post, Category, Comment, PostLike
from app.forms import (RegistrationForm, LoginForm, PostForm, CommentForm,
                       CommentEditForm, SearchForm)
from datetime import datetime
import secrets
import os
from sqlalchemy import or_

# 定义蓝图
main = Blueprint('main', __name__)
auth = Blueprint('auth', __name__)
posts = Blueprint('posts', __name__)
comments = Blueprint('comments', __name__)
admin = Blueprint('admin', __name__)
likes = Blueprint('likes', __name__)

# 主页路由
@main.route("/", methods=['GET', 'POST'])
@main.route("/home", methods=['GET', 'POST'])
def home():
    form = SearchForm()
    like_form = SearchForm()
    if form.validate_on_submit():
        return redirect(url_for('main.search', query=form.query.data))

    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.created_at.desc()).paginate(page=page, per_page=5)
    return render_template('index.html', posts=posts, form=form, like_form=like_form)

# 搜索功能
@main.route("/search/<query>")
def search(query):
    page = request.args.get('page', 1, type=int)
    posts = Post.query.filter(Post.title.ilike(f'%{query}%') |
                              Post.content.ilike(f'%{query}%')).order_by(
        Post.created_at.desc()).paginate(page=page, per_page=5)
    return render_template('index.html', posts=posts, title=f"搜索结果: {query}")

# 文章详情
@main.route("/post/<int:post_id>", methods=['GET', 'POST'])
def post(post_id):
    post = Post.query.get_or_404(post_id)
    form = CommentForm()
    like_form = SearchForm()

    # 计算用户是否已经点赞
    user_has_liked = False
    if current_user.is_authenticated:
        user_has_liked = PostLike.query.filter_by(
            user_id=current_user.id,
            post_id=post.id
        ).first() is not None

    if form.validate_on_submit() and current_user.is_authenticated:
        comment = Comment(content=form.content.data,
                          author=current_user,
                          post=post)
        db.session.add(comment)
        db.session.commit()
        flash('评论已发表！', 'success')
        return redirect(url_for('main.post', post_id=post.id))

    return render_template('post.html',
                           post=post,
                           form=form,
                           like_form=like_form,
                           user_has_liked=user_has_liked)

# 按分类查看文章
@main.route("/category/<int:category_id>")
def category_posts(category_id):
    category = Category.query.get_or_404(category_id)
    page = request.args.get('page', 1, type=int)
    posts = Post.query.filter_by(category=category).order_by(
        Post.created_at.desc()).paginate(page=page, per_page=5)
    return render_template('index.html', posts=posts, title=category.name)

# 认证路由
@auth.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)

        # 检查是否已有用户，没有则设为管理员
        if User.query.count() == 0:
            user.is_admin = True

        db.session.add(user)
        db.session.commit()
        flash('账户创建成功！你现在可以登录了。', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', form=form)

@auth.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = LoginForm()
    if form.validate_on_submit():
        identity = form.identity.data
        try:
            user = User.query.filter(or_(User.username == identity, User.email == identity)).first()
        except Exception as e:
            # 打印异常到控制台，便于调试
            print("登录查询异常:", e)
            flash('服务器内部错误，请联系管理员。', 'danger')
            return render_template('auth/login.html', form=form)
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            resp = redirect(next_page) if next_page else redirect(url_for('main.home'))
            resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            resp.headers["Pragma"] = "no-cache"
            resp.headers["Expires"] = "0"
            return resp
        else:
            flash('登录失败，请检查邮箱/用户名和密码。', 'danger')
    return render_template('auth/login.html', form=form)

@auth.route("/logout")
def logout():
    logout_user()
    resp = redirect(url_for('main.home'))
    # 强制刷新，防止导航栏缓存
    resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    resp.headers["Pragma"] = "no-cache"
    resp.headers["Expires"] = "0"
    return resp

# 文章管理路由
@posts.route("/post/new", methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data,
                    content=form.content.data,
                    author=current_user,
                    category_id=form.category.data)
        db.session.add(post)
        db.session.commit()

        # 处理文件上传
        if form.file.data:
            file = form.file.data
            # 生成唯一的文件名
            filename = secrets.token_hex(8) + os.path.splitext(file.filename)[1]
            # 确保上传目录存在
            upload_dir = 'uploads'
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir)
            file_path = os.path.join(upload_dir, filename)
            file.save(file_path)
            # 可以将文件路径存储到数据库中，这里假设 Post 模型有一个 file_path 字段
            post.file_path = file_path
            db.session.commit()

        flash('文章发布成功！', 'success')
        return redirect(url_for('main.post', post_id=post.id))
    return render_template('create_post.html', form=form, title='新建文章')

@posts.route("/post/<int:post_id>/edit", methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user and not current_user.is_admin:
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        post.category_id = form.category.data
        post.updated_at = datetime.utcnow()
        db.session.commit()
        flash('文章已更新！', 'success')
        return redirect(url_for('main.post', post_id=post.id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
        form.category.data = post.category_id
    return render_template('create_post.html', form=form, title='编辑文章')

@posts.route("/post/<int:post_id>/delete", methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user and not current_user.is_admin:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('文章已删除！', 'success')
    return redirect(url_for('main.home'))

# 评论管理路由
@comments.route("/comment/<int:comment_id>/edit", methods=['GET', 'POST'])
@login_required
def edit_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    if comment.author != current_user and not current_user.is_admin:
        abort(403)
    form = CommentEditForm()
    if form.validate_on_submit():
        comment.content = form.content.data
        comment.updated_at = datetime.utcnow()
        db.session.commit()
        flash('评论已更新！', 'success')
        return redirect(url_for('main.post', post_id=comment.post_id))
    elif request.method == 'GET':
        form.content.data = comment.content
    return render_template('edit_comment.html', form=form, comment=comment)

@comments.route("/comment/<int:comment_id>/delete", methods=['POST'])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    if comment.author != current_user and not current_user.is_admin:
        abort(403)
    post_id = comment.post_id
    db.session.delete(comment)
    db.session.commit()
    flash('评论已删除！', 'success')
    return redirect(url_for('main.post', post_id=post_id))

# 点赞功能路由
@likes.route("/post/<int:post_id>/like", methods=['POST'])
@login_required
def like_post(post_id):
    post = Post.query.get_or_404(post_id)
    like = PostLike.query.filter_by(user_id=current_user.id, post_id=post_id).first()

    if like:
        db.session.delete(like)
        db.session.commit()
        liked = False
    else:
        like = PostLike(user_id=current_user.id, post_id=post_id)
        db.session.add(like)
        db.session.commit()
        liked = True

    like_count = post.like_count()
    return jsonify({'like_count': like_count, 'liked': liked})

# 管理员仪表盘路由
@admin.route('/dashboard')
@login_required
def admin_dashboard():
    # 验证用户是否为管理员
    if not current_user.is_admin:
        abort(403)  # 非管理员用户返回403错误

    # 获取统计数据
    post_count = Post.query.count()
    user_count = User.query.count()
    comment_count = Comment.query.count()
    recent_posts = Post.query.order_by(Post.created_at.desc()).limit(5).all()
    recent_comments = Comment.query.order_by(Comment.created_at.desc()).limit(5).all()

    return render_template('admin/dashboard.html',
                           post_count=post_count,
                           user_count=user_count,
                           comment_count=comment_count,
                           recent_posts=recent_posts,
                           recent_comments=recent_comments)

# 管理员文章管理路由
@admin.route('/posts')
@login_required
def admin_posts():
    # 验证用户是否为管理员
    if not current_user.is_admin:
        abort(403)  # 非管理员用户返回403错误

    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.created_at.desc()).paginate(page=page, per_page=10)
    return render_template('admin/posts.html', posts=posts)

# 新增管理员用户列表视图
@admin.route('/users')
@login_required
def admin_users():
    if not current_user.is_admin:
        abort(403)
    page = request.args.get('page', 1, type=int)
    users = User.query.order_by(User.registered_at.desc()).paginate(page=page, per_page=10)
    return render_template('admin/users.html', users=users)

# 新增管理员评论管理视图
@admin.route('/comments')
@login_required
def admin_comments():
    if not current_user.is_admin:
        abort(403)
    page = request.args.get('page', 1, type=int)
    comments = Comment.query.order_by(Comment.created_at.desc()).paginate(page=page, per_page=10)
    return render_template('admin/comments.html', comments=comments)