# flask-blog-complete/app/__init__.py
from flask import Flask
from app.extensions import db, login_manager, csrf
import os
from app.forms import SearchForm  # 导入 SearchForm

# 导入蓝图
from app.routes import main, auth, posts, comments, admin, likes

def create_app(config_class=None):
    app = Flask(__name__)

    # 配置应用
    if config_class:
        app.config.from_object(config_class)
    else:
        # 默认使用开发配置
        from config import DevelopmentConfig
        app.config.from_object(DevelopmentConfig)

    # 初始化扩展
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    # 用户加载函数
    from app.models import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # 注册蓝图
    app.register_blueprint(main)
    app.register_blueprint(auth)
    app.register_blueprint(posts)
    app.register_blueprint(comments)
    app.register_blueprint(admin)  # 注册 admin 蓝图
    app.register_blueprint(likes)

    # 上下文处理器，使分类在所有模板中可用
    @app.context_processor
    def inject_categories():
        from app.models import Category
        categories = Category.query.all()
        return dict(categories=categories)

    # 新增上下文处理器，使 search_form 在所有模板中可用
    @app.context_processor
    def inject_search_form():
        search_form = SearchForm()
        return dict(search_form=search_form)

    # 确保数据库表存在
    with app.app_context():
        from app.models import User, Category
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        if db_path and not os.path.exists(db_path):
            open(db_path, 'a').close()
        db.create_all()

        # 创建默认分类（如果不存在）
        if Category.query.count() == 0:
            default_categories = ['文章', '技术', '生活', '随笔']
            for cat_name in default_categories:
                category = Category(name=cat_name)
                db.session.add(category)
            db.session.commit()

    return app