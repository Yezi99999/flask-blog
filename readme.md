# Flask Blog 完整项目说明

## 项目简介

本项目是一个基于 Flask 框架的博客系统，支持用户注册、登录、发帖、评论、点赞、分类浏览、后台管理等常见博客功能。适合学习 Flask Web 开发和小型博客系统搭建。

---

## 主要功能

- 用户注册与登录（支持邮箱或用户名登录）
- 文章发布、编辑、删除
- 文章分类管理
- 文章评论与评论管理
- 文章点赞（防止重复点赞）
- 用户个人中心
- 管理员后台（用户管理、文章管理等）
- 支持分页、搜索、富文本编辑
- 基于 SQLite3 数据库

---

## 目录结构

```
flask-blog-complete/
│
├── app/
│   ├── __init__.py
│   ├── models.py
│   ├── forms.py
│   ├── routes.py
│   └── templates/
│       ├── base.html
│       ├── index.html
│       ├── post.html
│       ├── create_post.html
│       ├── auth/
│       │   ├── login.html
│       │   └── register.html
│       └── admin/
│           └── users.html
│        
│        
├── config.py
├── run.py
├── requirements.txt
└── readme.md
```

---

## 环境依赖

- Python 3.7+
- Flask
- Flask-Login
- Flask-WTF
- Flask-SQLAlchemy
- email_validator
- 其它依赖见 `requirements.txt`

安装依赖：
```bash
pip install -r requirements.txt
```

---

## 快速启动

1. **初始化数据库**
   ```bash
   python
   >>> from app import db, create_app
   >>> app = create_app()
   >>> with app.app_context():
   ...     db.create_all()
   ... 
   >>> exit()
   ```

2. **运行项目**
   ```bash
   set FLASK_APP=run.py
   set FLASK_ENV=development
   flask run
   ```
   或直接运行
   ```bash
   python run.py
   ```

3. **访问博客**
   打开浏览器访问 [http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## 常见问题

- **登录报错缺少 email_validator**  
  解决：`pip install email_validator`
- **Jinja2 模板不支持 Python 列表推导式**  
  解决：用 Jinja2 的 selectattr 过滤器判断，如  
  ```jinja2
  {% set liked = (post.likes | selectattr('user_id', 'equalto', current_user.id) | list | length > 0) %}
  ```
- **数据库相关问题**  
  确保已初始化数据库，或删除 `blog.db` 重新 `db.create_all()`。

---

## 其它说明

- 默认账户admin 密码admin
- 如需自定义页面风格，可修改 `app/templates/` 下的 html 文件和 `app/static/` 下的静态资源。
- 管理员权限可在数据库中手动设置用户的 `is_admin` 字段为 `True`。

---

