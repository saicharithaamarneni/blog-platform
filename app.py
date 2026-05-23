from flask import Flask, render_template, request, redirect
from werkzeug.utils import secure_filename
import os
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    UserMixin,
    current_user
)

app = Flask(__name__)

app.config["SECRET_KEY"] = "blogsecret"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///blog.db"

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

login_manager = LoginManager()
login_manager.init_app(app)

login_manager.login_view = "login"


# ------------------
# MODELS
# ------------------

class User(UserMixin, db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    username = db.Column(
        db.String(100),
        nullable=False
    )

    email = db.Column(
        db.String(100),
        unique=True
    )

    password = db.Column(
        db.String(300)
    )

class Post(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    title = db.Column(
        db.String(200)
    )

    content = db.Column(
        db.Text
    )

    image = db.Column(
        db.String(300)
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id")
    )
class Comment(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    text = db.Column(
        db.Text
    )

    post_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "post.id"
        )
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "user.id"
        )
    )
class Like(db.Model):

    id=db.Column(
        db.Integer,
        primary_key=True
    )

    user_id=db.Column(
        db.Integer,
        db.ForeignKey(
            "user.id"
        )
    )

    post_id=db.Column(
        db.Integer,
        db.ForeignKey(
            "post.id"
        )
    )

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(
        int(user_id)
    )


with app.app_context():
    db.create_all()


# ------------------
# HOME
# ------------------
@app.route("/")
def home():

    return render_template(
        "index.html"
    )


# ------------------
# REGISTER
# ------------------

@app.route(
    "/register",
    methods=["GET", "POST"]
)
def register():

    if request.method == "POST":

        username = request.form["username"]

        email = request.form["email"]

        password = request.form["password"]

        existing = User.query.filter_by(
            email=email
        ).first()

        if existing:
            return "Email already exists"

        hashed = bcrypt.generate_password_hash(
            password
        ).decode("utf-8")

        user = User(
            username=username,
            email=email,
            password=hashed
        )

        db.session.add(user)

        db.session.commit()

        return redirect(
            "/login"
        )

    return render_template(
        "register.html"
    )


# ------------------
# LOGIN
# ------------------

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if request.method == "POST":

        email = request.form["email"]

        password = request.form["password"]

        user = User.query.filter_by(
            email=email
        ).first()

        if user and bcrypt.check_password_hash(
                user.password,
                password):

            login_user(user)

            return redirect(
                "/dashboard"
            )

        return "Invalid Login"

    return render_template(
        "login.html"
    )


# ------------------
# DASHBOARD
# ------------------

@app.route(
    "/dashboard"
)

@login_required
def dashboard():

    posts = Post.query.filter_by(
        user_id=current_user.id
    ).all()

    return render_template(
        "dashboard.html",
        posts=posts
    )


# ------------------
# CREATE BLOG
# ------------------

@app.route(
"/create",
methods=["GET","POST"]
)

@login_required
def create():

    if request.method=="POST":

        title=request.form["title"]

        content=request.form["content"]

        file=request.files["image"]

        filename=""

        if file:

            filename=secure_filename(
                file.filename
            )

            os.makedirs(
                "static/uploads",
                exist_ok=True
            )

            file.save(
                "static/uploads/"
                + filename
            )

        post=Post(

            title=title,

            content=content,

            image=filename,

            user_id=current_user.id
        )

        db.session.add(
            post
        )

        db.session.commit()

        return redirect(
            "/dashboard"
        )

    return render_template(
        "create_post.html"
    )
@app.route(
"/edit/<int:id>",
methods=["GET","POST"]
)

@login_required
def edit(id):

    post = Post.query.get_or_404(
        id
    )

    if request.method == "POST":

        post.title = request.form[
            "title"
        ]

        post.content = request.form[
            "content"
        ]

        db.session.commit()

        return redirect(
            "/dashboard"
        )

    return render_template(
        "edit_post.html",
        post=post
    )
@app.route(
"/delete/<int:id>"
)

@login_required
def delete(id):

    post = Post.query.get_or_404(
        id
    )

    db.session.delete(
        post
    )

    db.session.commit()

    return redirect(
        "/dashboard"
    )
@app.route(
"/post/<int:id>"
)

@login_required
def view_post(id):

    post = Post.query.get_or_404(
        id
    )

    comments = Comment.query.filter_by(
        post_id=id
    ).all()

    return render_template(
        "view_post.html",
        post=post,
        comments=comments
    )
@app.route(
"/comment/<int:id>",
methods=["POST"]
)

@login_required
def comment(id):

    text = request.form[
        "comment"
    ]

    new_comment = Comment(

        text=text,

        post_id=id,

        user_id=current_user.id
    )

    db.session.add(
        new_comment
    )

    db.session.commit()

    return redirect(
        f"/post/{id}"
    )
@app.route(
"/like/<int:id>"
)

@login_required
def like(id):

    existing=Like.query.filter_by(
        user_id=current_user.id,
        post_id=id
    ).first()

    if not existing:

        like=Like(
            user_id=current_user.id,
            post_id=id
        )

        db.session.add(
            like
        )

        db.session.commit()

    return redirect(
        "/dashboard"
    )
# ------------------
# LOGOUT
# ------------------

@app.route(
    "/logout"
)

@login_required
def logout():

    logout_user()

    return redirect(
        "/login"
    )

@app.route(
"/profile"
)

@login_required
def profile():

    total_posts = Post.query.filter_by(
        user_id=current_user.id
    ).count()

    total_comments = Comment.query.filter_by(
        user_id=current_user.id
    ).count()

    return render_template(

        "profile.html",

        posts=total_posts,

        comments=total_comments
    )
# ------------------

if __name__ == "__main__":
    app.run(
        debug=True
    )