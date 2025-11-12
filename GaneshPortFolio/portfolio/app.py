from email.mime.text import MIMEText

from flask import Flask, render_template, request, redirect, url_for, session,flash, get_flashed_messages,abort
import sqlite3, os
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import os
import smtplib
from email.message import EmailMessage
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

conn = sqlite3.connect('portfolio.db')
c = conn.cursor()

load_dotenv()
EMAIL_ADDRESS ="email_address"
EMAIL_PASSWORD ="password"

print(repr(EMAIL_ADDRESS))   
print(repr(EMAIL_PASSWORD)) 

def send_email(to, subject, body):
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = to
    msg.set_content(body)

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)





BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
# app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

app = Flask(__name__)
app.secret_key = 'adminkey'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)






def time_ago(timestamp_str):
    now = datetime.now()
    created = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
    delta = now - created

    seconds = delta.total_seconds()
    if seconds < 60:
        return "just now"
    elif seconds < 3600:
        return f"{int(seconds // 60)} minutes ago"
    elif seconds < 86400:
        return f"{int(seconds // 3600)} hours ago"
    elif seconds < 604800:
        return f"{int(seconds // 86400)} days ago"
    elif seconds < 2592000:
        return f"{int(seconds // 604800)} weeks ago"
    elif seconds < 31536000:
        return f"{int(seconds // 2592000)} months ago"
    else:
        return f"{int(seconds // 31536000)} years ago"

app.jinja_env.filters['timeago'] = time_ago


# 🏠 Home Route
@app.route('/')
def index():
    conn = sqlite3.connect('portfolio.db')
    c = conn.cursor()
    c.execute('SELECT * FROM projects')
    projects = c.fetchall()
    c.execute('SELECT * FROM blogs')
    blogs = c.fetchall()
    c.execute('SELECT * FROM certificates')
    certs = c.fetchall()

    # ✅ Fetch profile
    c.execute('SELECT * FROM profile LIMIT 1')
    profile = c.fetchone()

    conn.close()

    return render_template('index.html', projects=projects, blogs=blogs, certs=certs, profile=profile)

# user send message admin
@app.route("/contact", methods=["POST"])
def contact():
    try:
        name = request.form["name"]
        email = request.form["email"]
        subject = request.form["subject"]
        message = request.form["message"]
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn = sqlite3.connect("portfolio.db")
        conn.execute("INSERT INTO messages (name, email, subject, message, created_at) VALUES (?, ?, ?, ?, ?)",
                    (name, email, subject, message, created_at))
        conn.commit()
        conn.close()

        send_email(EMAIL_ADDRESS, f"New Message from {name}", f"Email: {email}\nSubject: {subject}\n{message}")
        flash("Message sent successfully!", "success")

    except Exception as e:
        print("Error:", e)
        flash("Failed to send message. Please try again.", "danger")

    # return redirect('/')
    return redirect("/")

@app.route('/chat')
def chat():
    return render_template('chat.html')

#  Admin Login
@app.route('/ganeshAdmin', methods=['GET', 'POST'])
def admin():

    if request.method == 'POST':
        try:

            if request.form['username'] == 'admin@123' and request.form['password'] == 'pass@123':
                session['admin'] = True
                flash("Login successful!", "success")
                return redirect('/dashboard')

            else:
                flash("Login failed! Please try again.", "danger")
        except Exception as e:
            pass


    return render_template('login.html')


# Admin Dashboard
@app.route("/dashboard")
def dashboard():
    if 'admin' not in session:
        return render_template("404.html")

    conn = sqlite3.connect("portfolio.db")
    c = conn.cursor()
    projects = c.execute("SELECT * FROM projects").fetchall()
    blogs = c.execute("SELECT * FROM blogs").fetchall()
    certs = c.execute("SELECT * FROM certificates").fetchall()
    messages = c.execute("SELECT * FROM messages ORDER BY created_at DESC").fetchall()

    profile = c.execute("SELECT * FROM profile LIMIT 1").fetchone()
    conn.close()
    active_section = request.args.get("active_section", "projects")

    return render_template("admin.html", projects=projects, blogs=blogs, certs=certs, messages=messages, profile=profile, active_section=active_section)



# Add Admin Profile
@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'admin' not in session:
            return render_template("404.html")
    try:



        conn = sqlite3.connect('portfolio.db')
        c = conn.cursor()

        if request.method == 'POST':
            name = request.form['name']
            photo = request.files['photo']
            resume = request.files['resume']

            photo_filename = ''
            resume_filename = ''

            if photo and photo.filename:
                photo_filename = secure_filename(photo.filename)
                photo.save(os.path.join(app.config['UPLOAD_FOLDER'], photo_filename))

            if resume and resume.filename:
                resume_filename = secure_filename(resume.filename)
                resume.save(os.path.join(app.config['UPLOAD_FOLDER'], resume_filename))

            # Check if profile already exists
            existing = c.execute('SELECT id FROM profile').fetchone()
            if existing:
                if photo_filename and resume_filename:
                    c.execute('UPDATE profile SET name=?, photo=?, resume=? WHERE id=1', (name, photo_filename, resume_filename))
                elif photo_filename:
                    c.execute('UPDATE profile SET name=?, photo=? WHERE id=1', (name, photo_filename))
                elif resume_filename:
                    c.execute('UPDATE profile SET name=?, resume=? WHERE id=1', (name, resume_filename))
                else:
                    c.execute('UPDATE profile SET name=? WHERE id=1', (name,))
            else:
                c.execute('INSERT INTO profile (name, photo, resume) VALUES (?, ?, ?)', (name, photo_filename, resume_filename))

            conn.commit()
            conn.close()
            return redirect(url_for("dashboard", active_section="profile"))

        profile = c.execute('SELECT * FROM profile LIMIT 1').fetchone()
        conn.close()
        flash("Profile loaded successfully!", "success")
        # return redirect(url_for("dashboard", active_section="profile"))
    except Exception as e:
        # print("Error:", e)
        flash("Failed to load profile. Please try again.", "danger")
        # profile = None
    return render_template('profile_form.html', profile=profile)

# edit profile
@app.route('/update_profile', methods=['POST'])
def update_profile():
    try:
        if 'admin' not in session:
            return render_template("404.html")

        name = request.form['name']
        photo_file = request.files.get('photo')
        resume_file = request.files.get('resume')

        photo_filename = ''
        resume_filename = ''
        if photo_file and photo_file.filename:
            photo_filename = secure_filename(photo_file.filename)
            photo_file.save(os.path.join(app.config['UPLOAD_FOLDER'], photo_filename))

        if resume_file and resume_file.filename:
            resume_filename = secure_filename(resume_file.filename)
            resume_file.save(os.path.join(app.config['UPLOAD_FOLDER'], resume_filename))

        conn = sqlite3.connect('portfolio.db')
        c = conn.cursor()
        if photo_filename:
            c.execute("UPDATE admin_profile SET photo=? WHERE id=1", (photo_filename,))
        if resume_filename:
            c.execute("UPDATE admin_profile SET resume=? WHERE id=1", (resume_filename,))
        c.execute("UPDATE admin_profile SET name=? WHERE id=1", (name,))
        conn.commit()
        conn.close()
        flash("Profile updated successfully!", "success")
    except Exception as e:
        # print("Error updating profile:", e)
        flash("Failed to update profile. Please try again.", "danger")

    return redirect('/dashboard')


    

# delete profile

@app.route('/delete_profile')
def delete_profile():
    try:
        if 'admin' not in session:
            return render_template("404.html")

        # Delete profile from database
        conn = sqlite3.connect('portfolio.db')
        c = conn.cursor()
        c.execute('DELETE FROM profile')
        conn.commit()
        conn.close()
        flash("Profile deleted successfully!", "success")
    except Exception as e:
        print("Error:", e)
        flash("Failed to delete profile. Please try again.", "danger")
    return redirect(url_for("dashboard", active_section="profile"))




@app.route('/resume/<filename>')
def resume(filename):

    return redirect(url_for('static', filename='uploads/' + filename))

# @app.errorhandler(404)
# def page_not_found(e):
#     return "<h1>404 - Page Not Found</h1><p>The page does not exist.</p>", 404


# Add Project
@app.route("/add_project", methods=["GET", "POST"])
def add_project():
    # 👈 This will use your @app.errorhandler(404) view
    if 'admin' not in session:
        return render_template("404.html")
    try:


        if request.method == "POST":
            try:
                title = request.form["title"]
                github = request.form["github"]
                category = request.form["category"]
                description = request.form["description"]
                languages = request.form["languages"]
                created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                image_file = request.files.get("image")
                video_file = request.files.get("video")
                image_name = secure_filename(image_file.filename) if image_file and image_file.filename else None
                video_name = secure_filename(video_file.filename) if video_file and video_file.filename else None

                if image_name:
                    image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], image_name))
                if video_name:
                    video_file.save(os.path.join(app.config['UPLOAD_FOLDER'], video_name))

                conn = sqlite3.connect("portfolio.db")
                conn.execute("INSERT INTO projects (title, github, image, video, category, description, languages) VALUES (?, ?, ?, ?, ?, ?, ?)",
                            (title, github, image_name, video_name, category, description, languages))
                conn.commit()
                conn.close()
                flash("Project added successfully!", "success")
                return redirect(url_for("dashboard", active_section="projects"))
            except Exception as e:
                print("Error:", e)
                flash("Something went wrong while adding the project.", "danger")
            return redirect("/dashboard")
        return render_template("add_project.html")
    except:
        pass

# Edit Project
@app.route("/edit_project/<int:id>", methods=["GET", "POST"])
def edit_project(id):
    if 'admin' not in session:
        return render_template("404.html")

    conn = sqlite3.connect("portfolio.db")
    c = conn.cursor()

    if request.method == "POST":
        title = request.form["title"]
        github = request.form["github"]
        category = request.form["category"]
        description = request.form["description"]
        new_languages = request.form.get("languages")  # could be blank
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # get current image and video and languages
        current = c.execute("SELECT image, video, languages FROM projects WHERE id = ?", (id,)).fetchone()
        current_image, current_video, current_languages = current

        # file handling
        image_file = request.files.get("image")
        video_file = request.files.get("video")
        image_filename = current_image
        video_filename = current_video

        if image_file and image_file.filename:
            image_filename = secure_filename(image_file.filename)
            image_file.save(os.path.join(app.config["UPLOAD_FOLDER"], image_filename))

        if video_file and video_file.filename:
            video_filename = secure_filename(video_file.filename)
            video_file.save(os.path.join(app.config["UPLOAD_FOLDER"], video_filename))

        # if new languages field is left empty, keep old languages
        languages = new_languages.strip() if new_languages.strip() else current_languages

        try:
            c.execute("""UPDATE projects
                         SET title=?, github=?, image=?, video=?, category=?, description=?, languages=?
                         WHERE id=?""",
                      (title, github, image_filename, video_filename, category, description, languages, id))
            conn.commit()
            flash("Project updated successfully!", "success")
            return redirect(url_for("dashboard", active_section="projects"))
        except Exception as e:
            print("Update error:", e)
            flash("Failed to update project.", "danger")

        conn.close()
        return redirect("/dashboard")

    # GET request to show form
    data = c.execute("SELECT * FROM projects WHERE id=?", (id,)).fetchone()
    conn.close()
    return render_template("edit_project.html", data=data)

# Delete Project
@app.route('/delete_project/<int:id>')
def delete_project(id):
    try:
        if 'admin' not in session:
            return render_template("404.html")

        conn = sqlite3.connect('portfolio.db')
        c = conn.cursor()
        c.execute("DELETE FROM projects WHERE id = ?", (id,))
        conn.commit()
        conn.close()
        flash("Project deleted successfully!", "success")
        return redirect(url_for("dashboard", active_section="projects"))
    except Exception as e:
        print("Error:", e)
        flash("Something went wrong while deleting the project.", "danger")

    return redirect('/dashboard')



#  Add Blog

@app.route("/add_blog", methods=["GET", "POST"])
def add_blog():
    if 'admin' not in session:
        return render_template("404.html")
    if request.method == "POST":
        try:
            title = request.form["title"]
            summary = request.form["summary"]
            category = request.form["category"]
            created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            image_file = request.files["image"]
            image_name = secure_filename(image_file.filename) if image_file and image_file.filename else None
            if image_name:
                image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], image_name))

            conn = sqlite3.connect("portfolio.db")
            conn.execute("INSERT INTO blogs (title, summary, category, image, created_at) VALUES (?, ?, ?, ?, ?)",
                        (title, summary, category, image_name, created_at))
            conn.commit()
            conn.close()
            flash("Blog added successfully!", "success")
            return redirect(url_for("dashboard", active_section="blogs"))
        except Exception as e:
            print("Error:", e)
            flash("Something went wrong while adding the blog.", "danger")
    return render_template("add_blog.html")

#  Edit Blog
@app.route("/edit_blog/<int:id>", methods=["GET", "POST"])
def edit_blog(id):
    if 'admin' not in session:
        return render_template("404.html")

    conn = sqlite3.connect("portfolio.db")
    c = conn.cursor()

    if request.method == "POST":
        try:
            title = request.form["title"]
            summary = request.form["summary"]
            category = request.form["category"]
            image_file = request.files["image"]
            image_name = secure_filename(image_file.filename) if image_file and image_file.filename else None

            if image_name:
                image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], image_name))
                c.execute("UPDATE blogs SET title=?, summary=?, category=?, image=? WHERE id=?",
                        (title, summary, category, image_name, id))
            else:
                c.execute("UPDATE blogs SET title=?, summary=?, category=? WHERE id=?",
                        (title, summary, category, id))

            conn.commit()
            conn.close()
            flash("Blog updated successfully!", "success")
            return redirect(url_for("dashboard", active_section="blogs"))
        except Exception as e:
            print("Error:", e)
            flash("Something went wrong while updating the blog.", "danger")

    data = c.execute("SELECT * FROM blogs WHERE id=?", (id,)).fetchone()
    conn.close()
    return render_template("edit_blog.html", data=data)

# Delete Blog
@app.route('/delete_blog/<int:id>')
def delete_blog(id):
    try:
        if 'admin' not in session:
            return render_template("404.html")

        conn = sqlite3.connect('portfolio.db')
        c = conn.cursor()
        c.execute("DELETE FROM blogs WHERE id = ?", (id,))
        conn.commit()
        conn.close()
        flash("Blog deleted successfully!", "success")
        return redirect(url_for("dashboard", active_section="blogs"))
    except Exception as e:
        print("Error:", e)
        flash("Something went wrong while deleting the blog.", "danger")
    return redirect('/dashboard')


#  Add Certificate
@app.route("/add_certificate", methods=["GET", "POST"])
def add_certificate():
    if 'admin' not in session:
        return render_template("404.html")
    if request.method == "POST":
        try:
            title = request.form["title"]
            organization = request.form["organization"]
            issued_date = request.form["issued_date"]

            image_file = request.files["image"]
            image_name = secure_filename(image_file.filename) if image_file and image_file.filename else None
            if image_name:
                image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], image_name))

            conn = sqlite3.connect("portfolio.db")
            conn.execute("INSERT INTO certificates (title, organization, issued_date, image) VALUES (?, ?, ?, ?)",
                        (title, organization, issued_date, image_name))
            conn.commit()
            conn.close()
            flash("Certificate added successfully!", "success")
            return redirect(url_for("dashboard", active_section="certificates"))
        except Exception as e:
            print("Error:", e)
            flash("Something went wrong while adding the certificate.", "danger")
    return render_template("add_certificate.html")

#  Edit Certificate
@app.route("/edit_certificate/<int:id>", methods=["GET", "POST"])
def edit_certificate(id):
    if 'admin' not in session:
        return render_template("404.html")

    conn = sqlite3.connect("portfolio.db")
    c = conn.cursor()

    if request.method == "POST":
        try:
            title = request.form["title"]
            organization = request.form["organization"]
            issued_date = request.form["issued_date"]
            image_file = request.files["image"]

            image_name = secure_filename(image_file.filename) if image_file and image_file.filename else None
            if image_name:
                image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], image_name))
                c.execute("UPDATE certificates SET title=?, organization=?, issued_date=?, image=? WHERE id=?",
                        (title, organization, issued_date, image_name, id))
            else:
                c.execute("UPDATE certificates SET title=?, organization=?, issued_date=? WHERE id=?",
                        (title, organization, issued_date, id))

            conn.commit()
            flash("Certificate updated successfully!", "success")
            return redirect(url_for("dashboard", active_section="certificates"))
        except Exception as e:
            print("Error:", e)
            flash("Something went wrong while updating the certificate.", "danger")

    data = c.execute("SELECT * FROM certificates WHERE id=?", (id,)).fetchone()
    conn.close()
    return render_template("edit_certificate.html", data=data)

#  Delete Certificate
@app.route("/delete_certificate/<int:id>")
def delete_certificate(id):
    try:
        if 'admin' not in session:
            return render_template("404.html")

        conn = sqlite3.connect("portfolio.db")
        c = conn.cursor()

        # Optional: delete associated image file
        cert = c.execute("SELECT image FROM certificates WHERE id=?", (id,)).fetchone()
        if cert and cert[0]:

            image_path = os.path.join(app.config["UPLOAD_FOLDER"], cert[0])
            if os.path.exists(image_path):
                os.remove(image_path)

        c.execute("DELETE FROM certificates WHERE id=?", (id,))
        conn.commit()
        conn.close()
        flash("Certificate deleted successfully!", "success")
        return redirect(url_for("dashboard", active_section="certificates"))
    except Exception as e:
        print("Error:", e)
        flash("Something went wrong while deleting the certificate.", "danger")
    return redirect("/dashboard")


# delete message
@app.route("/delete_message/<int:id>")
def delete_message(id):
    if 'admin' not in session:
        return render_template("404.html")
    try:
        conn = sqlite3.connect("portfolio.db")
        conn.execute("DELETE FROM messages WHERE id=?", (id,))
        conn.commit()
        conn.close()
        flash("Message deleted successfully.", "success")
        return redirect(url_for("dashboard", active_section="messages"))

    except Exception as e:
        print("Delete error:", e)
        flash("Failed to delete message.", "danger")
    return redirect(url_for("dashboard", active_section="messages"))





# delete selected message
@app.route("/delete_selected_messages", methods=["POST"])
def delete_selected_messages():
    if 'admin' not in session:
        return render_template("404.html")


    ids = request.form.getlist("selected_ids")
    if ids:
        try:
            conn = sqlite3.connect("portfolio.db")
            query = f"DELETE FROM messages WHERE id IN ({','.join(['?']*len(ids))})"
            conn.execute(query, ids)
            conn.commit()
            flash(f"{len(ids)} message(s) deleted.", "success")
            return redirect(url_for("dashboard", active_section="messages"))
        except Exception as e:
            print("Bulk delete error:", e)
            flash("Failed to delete selected messages.", "danger")
        finally:
            conn.close()
    else:
        flash("No messages selected.", "info")
    return redirect(url_for("dashboard", active_section="messages"))

# search message
@app.route("/search_messages", methods=["POST"])
def search_messages():
    if 'admin' not in session:
        return render_template("404.html")


    filter_type = request.form.get("filter_type")
    search_text = request.form.get("search_text")
    query = ""
    values = []

    if filter_type and search_text:
        if filter_type == "name":
            query = "SELECT * FROM messages WHERE name LIKE ?"
        elif filter_type == "email":
            query = "SELECT * FROM messages WHERE email LIKE ?"
        elif filter_type == "subject":
            query = "SELECT * FROM messages WHERE subject LIKE ?"
        values = [f"%{search_text}%"]
    else:
        flash("Please enter search input.", "info")
        return redirect(url_for("dashboard", active_section="messages"))

    conn = sqlite3.connect("portfolio.db")
    c = conn.cursor()
    messages = c.execute(query, values).fetchall()
    projects = c.execute("SELECT * FROM projects").fetchall()
    blogs = c.execute("SELECT * FROM blogs").fetchall()
    certs = c.execute("SELECT * FROM certificates").fetchall()
    profile = c.execute("SELECT * FROM profile LIMIT 1").fetchone()
    conn.close()
    session["search_results"] = messages

    flash(f"Showing results for {filter_type}: '{search_text}'", "info")
    return render_template(
        "admin.html",
        projects=projects,
        blogs=blogs,
        certs=certs,
        messages=messages,
        profile=profile,
        active_section="messages"
    )

# @app.route("/delete_selected_messages", methods=["POST"])
# def delete_selected_messages():
#     if 'admin' not in session:
#         return redirect("/admin")

#     ids = request.form.getlist("selected_ids")
#     if ids:
#         try:
#             conn = sqlite3.connect("portfolio.db")
#             query = f"DELETE FROM messages WHERE id IN ({','.join(['?']*len(ids))})"
#             conn.execute(query, ids)
#             conn.commit()
#             flash(f"{len(ids)} message(s) deleted.", "success")
#         except Exception as e:
#             print("Bulk delete error:", e)
#             flash("Failed to delete selected messages.", "danger")
#         finally:
#             conn.close()
#     else:
#         flash("No messages selected.", "info")
#     return redirect("/dashboard")

# admin replay message
@app.route("/reply_message/<int:id>", methods=["POST"])
def reply_message(id):
    if 'admin' not in session:
        return render_template("404.html")

    try:
        reply_text = request.form["reply"]
        reply_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn = sqlite3.connect("portfolio.db")
        c = conn.cursor()
        user_data = c.execute("SELECT name, email FROM messages WHERE id=?", (id,)).fetchone()

        name, email = user_data
        status = "Pending"

        # Optional Email Reply
        try:
            smtp_server = "smtp.gmail.com"
            smtp_port = 587
            sender_email = "enter_email"
            sender_pass = "enter_passwod"

            msg = MIMEText(reply_text)
            msg["Subject"] = f"Reply to your message: {name}"
            msg["From"] = sender_email
            msg["To"] = email

            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(sender_email, sender_pass)
                server.sendmail(sender_email, email, msg.as_string())

            status = "Success"
        except Exception as e:
            print("Email failed:", e)
            status = "Failed"

        c.execute("UPDATE messages SET reply=?, reply_time=?, status=? WHERE id=?",
                (reply_text, reply_time, status, id))
        conn.commit()
        conn.close()
        flash("Reply sent successfully!", "success")
        return redirect(url_for("dashboard", active_section="messages"))
    except Exception as e:
        print("Error:", e)
        flash("Something went wrong while sending the reply.", "danger")
    return redirect(url_for("dashboard", active_section="messages"))





# Create Table
def init_db():
    conn = sqlite3.connect('portfolio.db')
    c = conn.cursor()

    # Updated schema
    c.execute('''
        CREATE TABLE IF NOT EXISTS profile (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            photo TEXT,
            resume TEXT
        )''')


    c.execute('''CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        github TEXT,
        image TEXT,
        video TEXT,
        category TEXT,
        description TEXT,
        languages TEXT

    )''')


    c.execute('''CREATE TABLE IF NOT EXISTS blogs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        summary TEXT,
        category TEXT,
        image TEXT,
        created_at TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS certificates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        organization TEXT,
        issued_date TEXT,
        image TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT,
    subject TEXT,
    message TEXT,
    created_at TEXT,
    reply TEXT,
    reply_time TEXT,
    status TEXT
    )''')

    conn.commit()
    conn.close()

# Run App
if __name__ == '__main__':
    init_db()
   

    # debug_mode = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    # app.run(debug=debug_mode)
    app.run(debug=True)



