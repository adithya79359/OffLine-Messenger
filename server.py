from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    send_from_directory
)

import sqlite3
import os
import uuid

from datetime import datetime
from werkzeug.utils import secure_filename


app = Flask(__name__)

DATABASE = "messages.db"
UPLOAD_FOLDER = "uploads"

# Maximum upload size = 100 MB
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# Create uploads folder automatically
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# -------------------------------------------------
# DATABASE CONNECTION
# -------------------------------------------------

def get_db():

    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row

    return conn


# -------------------------------------------------
# CREATE DATABASE
# -------------------------------------------------

def create_database():

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            username TEXT NOT NULL,

            message TEXT,

            time TEXT NOT NULL,

            type TEXT DEFAULT 'text',

            filename TEXT,

            stored_filename TEXT,

            file_size INTEGER

        )
    """)

    # Upgrade an older messages.db automatically
    existing_columns = {
        row["name"]
        for row in cursor.execute(
            "PRAGMA table_info(messages)"
        ).fetchall()
    }

    new_columns = {

        "type":
            "TEXT DEFAULT 'text'",

        "filename":
            "TEXT",

        "stored_filename":
            "TEXT",

        "file_size":
            "INTEGER"
    }

    for column, definition in new_columns.items():

        if column not in existing_columns:

            cursor.execute(
                f"ALTER TABLE messages "
                f"ADD COLUMN {column} {definition}"
            )

    conn.commit()
    conn.close()


# -------------------------------------------------
# HOME
# -------------------------------------------------

@app.route("/")
def home():

    return render_template("index.html")


# -------------------------------------------------
# GET MESSAGES
# -------------------------------------------------

@app.route("/messages")
def get_messages():

    conn = get_db()

    rows = conn.execute("""
        SELECT
            id,
            username,
            message,
            time,
            type,
            filename,
            stored_filename,
            file_size

        FROM messages

        ORDER BY id ASC
    """).fetchall()

    conn.close()

    messages = []

    for row in rows:

        messages.append({

            "id": row["id"],

            "username": row["username"],

            "message": row["message"],

            "time": row["time"],

            "type": row["type"] or "text",

            "filename": row["filename"],

            "file_size": row["file_size"]

        })

    return jsonify(messages)


# -------------------------------------------------
# SEND TEXT MESSAGE
# -------------------------------------------------

@app.route("/send", methods=["POST"])
def send_message():

    data = request.get_json(silent=True) or {}

    username = data.get(
        "username",
        ""
    ).strip()

    message = data.get(
        "message",
        ""
    ).strip()


    if not username or not message:

        return jsonify({

            "success": False,

            "error":
                "Username and message are required"

        }), 400


    username = username[:30]
    message = message[:2000]

    current_time = datetime.now().strftime(
        "%I:%M %p"
    )


    conn = get_db()

    conn.execute("""

        INSERT INTO messages
        (
            username,
            message,
            time,
            type
        )

        VALUES (?, ?, ?, ?)

    """, (

        username,
        message,
        current_time,
        "text"

    ))

    conn.commit()
    conn.close()


    return jsonify({
        "success": True
    })


# -------------------------------------------------
# UPLOAD FILE
# -------------------------------------------------

@app.route("/upload", methods=["POST"])
def upload_file():

    username = request.form.get(
        "username",
        ""
    ).strip()


    if not username:

        return jsonify({

            "success": False,
            "error": "Please enter your name"

        }), 400


    if "file" not in request.files:

        return jsonify({

            "success": False,
            "error": "No file selected"

        }), 400


    file = request.files["file"]


    if file.filename == "":

        return jsonify({

            "success": False,
            "error": "No file selected"

        }), 400


    original_filename = secure_filename(
        file.filename
    )


    if not original_filename:

        return jsonify({

            "success": False,
            "error": "Invalid filename"

        }), 400


    # Unique stored filename prevents overwriting
    extension = os.path.splitext(
        original_filename
    )[1]


    stored_filename = (
        str(uuid.uuid4()) + extension
    )


    file_path = os.path.join(
        app.config["UPLOAD_FOLDER"],
        stored_filename
    )


    file.save(file_path)


    file_size = os.path.getsize(
        file_path
    )


    current_time = datetime.now().strftime(
        "%I:%M %p"
    )


    conn = get_db()

    conn.execute("""

        INSERT INTO messages
        (
            username,
            message,
            time,
            type,
            filename,
            stored_filename,
            file_size
        )

        VALUES (?, ?, ?, ?, ?, ?, ?)

    """, (

        username[:30],
        "",
        current_time,
        "file",
        original_filename,
        stored_filename,
        file_size

    ))

    conn.commit()
    conn.close()


    return jsonify({

        "success": True,

        "filename": original_filename

    })


# -------------------------------------------------
# DOWNLOAD FILE
# -------------------------------------------------

@app.route("/download/<int:message_id>")
def download_file(message_id):

    conn = get_db()

    row = conn.execute("""

        SELECT
            filename,
            stored_filename

        FROM messages

        WHERE id = ?
        AND type = 'file'

    """, (message_id,)).fetchone()

    conn.close()


    if row is None:

        return "File not found", 404


    stored_filename = row[
        "stored_filename"
    ]

    original_filename = row[
        "filename"
    ]


    if not stored_filename:

        return "File not found", 404


    return send_from_directory(

        app.config["UPLOAD_FOLDER"],

        stored_filename,

        as_attachment=True,

        download_name=original_filename

    )


# -------------------------------------------------
# FILE TOO LARGE
# -------------------------------------------------

@app.errorhandler(413)
def file_too_large(error):

    return jsonify({

        "success": False,

        "error":
            "File is too large. Maximum size is 100 MB."

    }), 413


# -------------------------------------------------
# START SERVER
# -------------------------------------------------

if __name__ == "__main__":

    create_database()

    print()
    print("---------------------------------------")
    print("       OFFGRID MESSENGER")
    print("---------------------------------------")
    print("Messaging      : Enabled")
    print("File Sharing   : Enabled")
    print("Internet       : Not Required")
    print("---------------------------------------")
    print()
    print("Open on laptop:")
    print("http://127.0.0.1:5000")
    print()
    print("Open on other devices using:")
    print("http://YOUR-LAPTOP-IP:5000")
    print("---------------------------------------")
    print()

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )