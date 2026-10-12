from flask import Flask, render_template, request, jsonify
import cv2
import numpy as np
import os
import base64
from database import init_db, create_user, get_db
from face_engine import create_embedding, compare_faces


app = Flask(__name__)


# ==========================================
# DATABASE INITIALIZE
# ==========================================

init_db()


# ==========================================
# DASHBOARD
# ==========================================

@app.route("/")
def dashboard():

    conn = get_db()

    total_users = conn.execute(
        "SELECT COUNT(*) FROM users"
    ).fetchone()[0]

    recent_attendance = conn.execute("""
        SELECT
            users.name,
            users.employee_id,
            users.department,
            attendance.attendance_time,
            attendance.status
        FROM attendance
        INNER JOIN users
            ON attendance.user_id = users.id
        ORDER BY
            attendance.attendance_date DESC,
            attendance.attendance_time DESC
        LIMIT 5
    """).fetchall()

    conn.close()

    return render_template(
        "dashboard.html",
        total_users=total_users,
        recent_attendance=recent_attendance
    )


# ==========================================
# REGISTER PAGE
# ==========================================

@app.route("/register")
def register():

    return render_template("register.html")


# ==========================================
# FACE DETECTION API
# ==========================================

@app.route("/api/detect-face", methods=["POST"])
def detect_face():

    try:

        data = request.json

        image_data = data.get("image")

        if not image_data:

            return jsonify({
                "success": False,
                "message": "Image nahi mili."
            })


        image_data = image_data.split(",")[1]

        image_bytes = base64.b64decode(
            image_data
        )

        np_array = np.frombuffer(
            image_bytes,
            np.uint8
        )

        frame = cv2.imdecode(
            np_array,
            cv2.IMREAD_COLOR
        )


        if frame is None:

            return jsonify({
                "success": False,
                "message": "Image read nahi ho paayi."
            })


        model_path = os.path.join(
            os.path.dirname(
                os.path.abspath(__file__)
            ),
            "face_detection_yunet_2026may.onnx"
        )


        if not os.path.exists(model_path):

            return jsonify({
                "success": False,
                "message": "YuNet model nahi mili."
            })


        detector = cv2.FaceDetectorYN.create(
            model_path,
            "",
            (320, 320),
            0.9,
            0.3,
            5000
        )


        height, width = frame.shape[:2]

        detector.setInputSize(
            (width, height)
        )


        _, faces = detector.detect(frame)


        if faces is None or len(faces) == 0:

            return jsonify({
                "success": False,
                "message": "Face detect nahi hua."
            })


        if len(faces) > 1:

            return jsonify({
                "success": False,
                "message": "Ek time par sirf ek person hona chahiye."
            })


        return jsonify({
            "success": True,
            "message": "Face successfully detect ho gaya."
        })


    except Exception as e:

        print("Face Detection Error:", e)

        return jsonify({
            "success": False,
            "message": "Server error: " + str(e)
        })


# ==========================================
# REGISTER USER API
# ==========================================

@app.route("/api/register-user", methods=["POST"])
def register_user():

    try:

        data = request.json


        name = data.get("name", "").strip()
        employee_id = data.get("employee_id", "").strip()
        email = data.get("email", "").strip()
        phone = data.get("phone", "").strip()
        department = data.get("department", "").strip()
        image_data = data.get("image")


        # ==================================
        # VALIDATION
        # ==================================

        if not name:

            return jsonify({
                "success": False,
                "message": "Name required hai."
            })


        if not employee_id:

            return jsonify({
                "success": False,
                "message": "Employee ID required hai."
            })


        if not image_data:

            return jsonify({
                "success": False,
                "message": "Face capture karo."
            })


        # ==================================
        # CHECK DUPLICATE EMPLOYEE ID
        # ==================================

        conn = get_db()

        existing_user = conn.execute(
            """
            SELECT id
            FROM users
            WHERE employee_id = ?
            """,
            (employee_id,)
        ).fetchone()

        conn.close()


        if existing_user:

            return jsonify({
                "success": False,
                "message": "Ye Employee ID already registered hai."
            })


        # ==================================
        # IMAGE CONVERT
        # ==================================

        image_base64 = image_data.split(",")[1]

        image_bytes = base64.b64decode(
            image_base64
        )


        # ==================================
        # FACE DATA FOLDER
        # ==================================

        face_folder = os.path.join(
            os.path.dirname(
                os.path.abspath(__file__)
            ),
            "face_data"
        )

        os.makedirs(
            face_folder,
            exist_ok=True
        )


        # ==================================
        # SAFE FILE NAME
        # ==================================

        safe_employee_id = "".join(
            c for c in employee_id
            if c.isalnum() or c in ("-", "_")
        )


        filename = (
            safe_employee_id
            + "_face.jpg"
        )


        image_path = os.path.join(
            face_folder,
            filename
        )


        # ==================================
        # SAVE FACE IMAGE
        # ==================================

        with open(
            image_path,
            "wb"
        ) as file:

            file.write(image_bytes)

        # ==================================
        # CREATE FACE EMBEDDING
        # ==================================

        image = cv2.imdecode(
            np.frombuffer(
                image_bytes,
                np.uint8
            ),
            cv2.IMREAD_COLOR
        )


        if image is None:

            return jsonify({
                "success": False,
                "message": "Face image process nahi ho paayi."
            })


        embedding = create_embedding(
            image
        )


        if embedding is None:

            return jsonify({
                "success": False,
                "message": "Face embedding create nahi ho paayi."
            })


        embedding_bytes = embedding.tobytes()


        # ==================================
        # CHECK DUPLICATE FACE
        # ==================================

        conn = get_db()

        existing_users = conn.execute("""
            SELECT
                id,
                employee_id,
                face_embedding
            FROM users
            WHERE face_embedding IS NOT NULL
        """).fetchall()

        FACE_MATCH_THRESHOLD = 0.363

        duplicate_face_user = None
        duplicate_face_score = -1.0

        for user in existing_users:
            try:
                stored_embedding = np.frombuffer(
                    user["face_embedding"],
                    dtype=np.float32
                )

                stored_embedding = stored_embedding.reshape(
                    embedding.shape
                )

                score = compare_faces(
                    embedding,
                    stored_embedding
                )

                if score > duplicate_face_score:
                    duplicate_face_score = score
                    duplicate_face_user = user

            except Exception as e:
                print("Duplicate face check error:", user["employee_id"], e)

        conn.close()

        if duplicate_face_user is not None and duplicate_face_score >= FACE_MATCH_THRESHOLD:
            return jsonify({
                "success": False,
                "message": f"Ye face already registered hai with Employee ID {duplicate_face_user['employee_id']}."
            })


        # ==================================
        # SAVE USER DATABASE
        # ==================================

        user_id = create_user(
            name,
            employee_id,
            email,
            phone,
            department,
            filename,
            embedding_bytes
        )


        return jsonify({

            "success": True,

            "message":
                "User successfully registered.",

            "user_id":
                user_id

        })


    except Exception as e:

        print("Registration Error:", e)

        return jsonify({

            "success": False,

            "message":
                "Registration error: " + str(e)

        })


# ==========================================
# USERS LIST
# ==========================================

@app.route("/users")
def users():

    conn = get_db()

    users = conn.execute("""
        SELECT
            id,
            name,
            employee_id,
            email,
            phone,
            department,
            created_at
        FROM users
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return render_template(
        "users.html",
        users=users
    )

# ==========================================
# MARK ATTENDANCE PAGE
# ==========================================

@app.route("/attendance")
def attendance():

    return render_template("attendance.html")

# ==========================================
# CHECK ATTENDANCE API
# ==========================================

@app.route("/api/check-attendance", methods=["POST"])
def check_attendance():

    try:

        data = request.json

        if not data:
            return jsonify({
                "success": False,
                "message": "Request data nahi mili."
            })

        image_data = data.get("image")

        if not image_data:
            return jsonify({
                "success": False,
                "message": "Image nahi mili."
            })


        # ======================================
        # BASE64 IMAGE
        # ======================================

        try:

            image_data = image_data.split(",")[1]

        except IndexError:

            return jsonify({
                "success": False,
                "message": "Invalid image format."
            })


        image_bytes = base64.b64decode(
            image_data
        )

        np_array = np.frombuffer(
            image_bytes,
            np.uint8
        )

        frame = cv2.imdecode(
            np_array,
            cv2.IMREAD_COLOR
        )


        if frame is None:

            return jsonify({
                "success": False,
                "message": "Image read nahi ho paayi."
            })


        # ======================================
        # CREATE LIVE FACE EMBEDDING
        # ======================================

        try:

            live_embedding = create_embedding(
                frame
            )

        except ValueError as e:

            return jsonify({
                "success": False,
                "message": str(e)
            })


        if live_embedding is None:

            return jsonify({
                "success": False,
                "message": "Face detect nahi hua."
            })


        # ======================================
        # GET REGISTERED USERS
        # ======================================

        conn = get_db()

        users = conn.execute("""
            SELECT
                id,
                name,
                employee_id,
                department,
                face_embedding
            FROM users
            WHERE face_embedding IS NOT NULL
        """).fetchall()


        if not users:

            conn.close()

            return jsonify({
                "success": False,
                "message": "Koi registered face embedding nahi mila."
            })


        # ======================================
        # FACE MATCHING
        # ======================================

        matched_user = None
        best_score = -1.0

        for user in users:

            try:

                stored_embedding = np.frombuffer(
                    user["face_embedding"],
                    dtype=np.float32
                )

                stored_embedding = stored_embedding.reshape(
                    live_embedding.shape
                )


                score = compare_faces(
                    live_embedding,
                    stored_embedding
                )


                print(
                    "Face Match:",
                    user["employee_id"],
                    score
                )


                if score > best_score:

                    best_score = score
                    matched_user = user


            except Exception as e:

                print(
                    "Matching error:",
                    user["employee_id"],
                    e
                )


        # ======================================
        # MATCH THRESHOLD
        # ======================================

        MATCH_THRESHOLD = 0.363


        if matched_user is None:

            conn.close()

            return jsonify({
                "success": False,
                "message": "Face match nahi hua."
            })


        if best_score < MATCH_THRESHOLD:

            conn.close()

            return jsonify({
                "success": False,
                "message": "Face recognize nahi hua.",
                "score": round(best_score, 4)
            })


        # ======================================
        # MARK ATTENDANCE
        # ======================================

        from datetime import datetime

        now = datetime.now()

        attendance_date = now.strftime(
            "%Y-%m-%d"
        )

        attendance_time = now.strftime(
            "%H:%M:%S"
        )


        # Check today's attendance

        existing_attendance = conn.execute("""
            SELECT id
            FROM attendance
            WHERE user_id = ?
            AND attendance_date = ?
        """, (
            matched_user["id"],
            attendance_date
        )).fetchone()


        # ======================================
        # ALREADY MARKED
        # ======================================

        if existing_attendance:

            conn.close()

            return jsonify({

                "success": True,

                "already_marked": True,

                "message":
                    "Aaj ki attendance already marked hai.",

                "user": {

                    "id":
                        matched_user["id"],

                    "name":
                        matched_user["name"],

                    "employee_id":
                        matched_user["employee_id"],

                    "department":
                        matched_user["department"]

                },

                "score":
                    round(best_score, 4),

                "date":
                    attendance_date

            })


        # ======================================
        # INSERT ATTENDANCE
        # ======================================

        conn.execute("""
            INSERT INTO attendance
            (
                user_id,
                attendance_date,
                attendance_time,
                status
            )
            VALUES (?, ?, ?, ?)
        """, (
            matched_user["id"],
            attendance_date,
            attendance_time,
            "Present"
        ))


        conn.commit()
        conn.close()


        # ======================================
        # SUCCESS RESPONSE
        # ======================================

        return jsonify({

            "success": True,

            "already_marked": False,

            "message":
                "Attendance successfully marked.",

            "user": {

                "id":
                    matched_user["id"],

                "name":
                    matched_user["name"],

                "employee_id":
                    matched_user["employee_id"],

                "department":
                    matched_user["department"]

            },

            "score":
                round(best_score, 4),

            "date":
                attendance_date,

            "time":
                attendance_time

        })


    except Exception as e:

        print(
            "Attendance Error:",
            e
        )

        return jsonify({

            "success": False,

            "message":
                "Server error: " + str(e)

        })

@app.route("/attendance-records")
def attendance_records():
    conn = get_db()

    records = conn.execute("""
        SELECT
            attendance.id,
            users.name,
            users.employee_id,
            users.department,
            attendance.attendance_date,
            attendance.attendance_time,
            attendance.status
        FROM attendance
        INNER JOIN users
            ON attendance.user_id = users.id
        ORDER BY
            attendance.attendance_date DESC,
            attendance.attendance_time DESC
    """).fetchall()

    conn.close()

    return render_template(
        "attendance_records.html",
        records=records
    )
    
@app.route("/api/generate-existing-embeddings")
def generate_existing_embeddings():

    conn = get_db()

    users = conn.execute("""
        SELECT id, name, employee_id, face_image
        FROM users
        WHERE face_embedding IS NULL
    """).fetchall()

    updated = 0

    for user in users:

        image_path = os.path.join(
            os.path.dirname(
                os.path.abspath(__file__)
            ),
            "face_data",
            user["face_image"]
        )

        if not os.path.exists(image_path):
            continue

        image = cv2.imread(
            image_path
        )

        if image is None:
            continue

        try:

            embedding = create_embedding(
                image
            )

            if embedding is None:
                continue

            embedding_bytes = embedding.tobytes()

            conn.execute("""
                UPDATE users
                SET face_embedding = ?
                WHERE id = ?
            """, (
                embedding_bytes,
                user["id"]
            ))

            updated += 1

        except Exception as e:

            print(
                "Embedding error:",
                user["employee_id"],
                e
            )

    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "message":
            f"{updated} user embeddings generated."
    })

# ==========================================
# RUN APP
# ==========================================

if __name__ == "__main__":

    app.run(
        debug=True
    )
