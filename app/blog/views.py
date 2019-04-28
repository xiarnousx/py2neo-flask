from flask import Flask, request, session, redirect, url_for, render_template, flash
from .models import User, Post

app = Flask(__name__)


@app.route("/")
def index():
    postObj = Post()
    posts = postObj.recent_post(5)

    return render_template("index.html", posts=posts)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User(username)

        if not user.register(password):
            flash("User Already exists")
        else:
            flash("Successfully registered")
            return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User(username)

        if not user.verify_password(password):
            flash("Invalid login in")
        else:
            flash("Successfully logged in")
            session['username'] = user.username
            return redirect(url_for("index"))

    return render_template("login.html")


@app.route("/add_post", methods=["POST"])
def add_post():
    title = request.form["title"]
    tags = request.form["tags"]
    text = request.form["text"]

    user = User(session["username"])

    if not title or not tags or not text:
        flash("All fields are required")
    else:
        user.add_post(title,tags, text)


    return redirect(url_for("index"))


@app.route("/like_post/<post_id>")
def like_post(post_id):

    username = session.get("username")

    if not username:
        flash("You need to login to like posts")
        return redirect(url_for("login"))

    user = User(username)
    user.like_post(post_id)
    flash("You Liked The Post")
    return redirect(request.referrer)


@app.route("/profile/<username>")
def profile(username):
    postObj = Post()
    posts = postObj.recent_post_by_username(username, 10)
    user = User(session['username'])
    similar = []
    common = {}

    if username == session['username']:
        similar = user.similar_users(5)
    else:
        common = user.commonality_of_user(User(username))

    return render_template("profile.html", username=username, posts=posts, similar=similar, common=common)


@app.route("/logout")
def logout():
    session.pop("username")
    flash("Logged Out")
    return redirect(url_for("index"))


