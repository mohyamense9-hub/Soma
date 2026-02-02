from flask import (
    Flask, render_template, request,
    redirect, url_for, send_from_directory, jsonify
)
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin,
    login_user, login_required,
    logout_user, current_user
)
import os
from datetime import datetime
import traceback

# ================== CONFIG ==================
app = Flask(__name__)
app.secret_key = "SELVA_SUPER_SECRET"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = "uploads"

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

# ================== OWNER ==================
OWNER_USERNAME = "mohaymen"
OWNER_PASSWORD = "mohaymenn"

# ================== MODELS ==================
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(100))

class NumberFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    country = db.Column(db.String(50))
    filename = db.Column(db.String(200))

class OTPMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.Text)
    time = db.Column(db.String(50))

# ================== LOGIN ==================
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ================== ERROR HANDLER ==================
@app.errorhandler(Exception)
def handle_exception(e):
    # اطبع الخطأ في اللوج عشان Railway يوريك السبب
    traceback.print_exc()
    return f"⚠️ حدث خطأ: {str(e)}", 500

# ================== ROUTES ==================
@app.route("/", methods=["GET", "POST"])
def login():
    try:
        if request.method == "POST":
            username = request.form.get("username")
            password = request.form.get("password")

            if username == OWNER_USERNAME and password == OWNER_PASSWORD:
                owner = User(id=0, username=OWNER_USERNAME)
                login_user(owner)
                return redirect("/admin")

            user = User.query.filter_by(username=username, password=password).first()
            if user:
                login_user(user)
                return redirect("/dashboard")
        return render_template("login.html")
    except Exception as e:
        traceback.print_exc()
        return f"⚠️ حدث خطأ في صفحة تسجيل الدخول: {str(e)}", 500

@app.route("/admin", methods=["GET", "POST"])
@login_required
def admin():
    if current_user.username != OWNER_USERNAME:
        return "Access Denied"
    try:
        if request.method == "POST":
            if "create_account" in request.form:
                u = request.form.get("new_username")
                p = request.form.get("new_password")
                if u and p:
                    db.session.add(User(username=u, password=p))
                    db.session.commit()

            if "upload_file" in request.form:
                file = request.files.get("file")
                country = request.form.get("country")
                if file and country:
                    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
                    path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
                    file.save(path)
                    db.session.add(NumberFile(country=country, filename=file.filename))
                    db.session.commit()

            if "delete_file" in request.form:
                fid = request.form.get("file_id")
                f = NumberFile.query.get(fid)
                if f:
                    try:
                        os.remove(os.path.join(app.config["UPLOAD_FOLDER"], f.filename))
                    except:
                        pass
                    db.session.delete(f)
                    db.session.commit()

            if "delete_all" in request.form:
                files = NumberFile.query.all()
                for f in files:
                    try:
                        os.remove(os.path.join(app.config["UPLOAD_FOLDER"], f.filename))
                    except:
                        pass
                NumberFile.query.delete()
                db.session.commit()

        files = NumberFile.query.all()
        users = User.query.all()
        return render_template("admin.html", files=files, users=users)
    except Exception as e:
        traceback.print_exc()
        return f"⚠️ حدث خطأ في لوحة الادمن: {str(e)}", 500

@app.route("/dashboard")
@login_required
def dashboard():
    try:
        files = NumberFile.query.all()
        otps = OTPMessage.query.order_by(OTPMessage.id.desc()).limit(50).all()
        return render_template("dashboard.html", files=files, otps=otps)
    except Exception as e:
        traceback.print_exc()
        return f"⚠️ حدث خطأ في Dashboard: {str(e)}", 500

@app.route("/download/<filename>")
@login_required
def download(filename):
    try:
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename, as_attachment=True)
    except Exception as e:
        traceback.print_exc()
        return f"⚠️ حدث خطأ عند تحميل الملف: {str(e)}", 500

@app.route("/otp", methods=["POST"])
def receive_otp():
    try:
        data = request.get_json()
        msg = data.get("msg")
        if msg:
            db.session.add(OTPMessage(message=msg, time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            db.session.commit()
            return jsonify({"status": "ok"})
        return jsonify({"status": "error"})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"status": "error", "msg": str(e)})

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/")

# ================== RUN ==================
if __name__ == "__main__":
    try:
        os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
        db.create_all()
    except Exception as e:
        traceback.print_exc()
        print("⚠️ خطأ أثناء إنشاء المجلدات أو قاعدة البيانات:", e)
    app.run(host="0.0.0.0", port=5000)
