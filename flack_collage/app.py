from flask import Flask, render_template, request, redirect, url_for, session, flash
from database import connect, create_tables
from datetime import date
from functools import wraps

app = Flask(__name__)
app.secret_key = "college_mgmt_secret_2024"

create_tables()

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "admin" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

def get_grade(marks, max_marks):
    pct = (marks / max_marks * 100) if max_marks else 0
    if pct >= 90: return "O – Outstanding"
    if pct >= 75: return "A – Excellent"
    if pct >= 60: return "B – Good"
    if pct >= 50: return "C – Average"
    if pct >= 40: return "D – Pass"
    return "F – Fail"

@app.route("/", methods=["GET","POST"])
@app.route("/login", methods=["GET","POST"])
def login():
    if "admin" in session:
        return redirect(url_for("dashboard"))
    error = None
    if request.method == "POST":
        username = request.form.get("username","").strip()
        password = request.form.get("password","").strip()
        conn = connect(); cur = conn.cursor()
        cur.execute("SELECT * FROM admin WHERE username=? AND password=?", (username, password))
        user = cur.fetchone(); conn.close()
        if user:
            session["admin"] = username
            return redirect(url_for("dashboard"))
        else:
            error = "Invalid username or password."
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.pop("admin", None)
    flash("Logged out successfully.", "info")
    return redirect(url_for("login"))

@app.route("/dashboard")
@login_required
def dashboard():
    conn = connect(); cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM students"); students = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM faculty");  faculty  = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM courses");  courses  = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM attendance WHERE date=?", (str(date.today()),))
    today_att = cur.fetchone()[0]
    cur.execute("SELECT name,roll_no,department,year FROM students ORDER BY id DESC LIMIT 5")
    recent_students = cur.fetchall()
    conn.close()
    return render_template("dashboard.html",
        students=students, faculty=faculty,
        courses=courses, today_att=today_att,
        recent_students=recent_students)

# ── Students ───────────────────────────────────────────────────────────────────
@app.route("/students")
@login_required
def students():
    q = request.args.get("q","").strip()
    conn = connect(); cur = conn.cursor()
    if q:
        cur.execute("""SELECT * FROM students
                       WHERE name LIKE ? OR roll_no LIKE ? OR enrollment_no LIKE ?
                       ORDER BY id""",
                    (f"%{q}%", f"%{q}%", f"%{q}%"))
    else:
        cur.execute("SELECT * FROM students ORDER BY id")
    rows = cur.fetchall(); conn.close()
    return render_template("students.html", students=rows, q=q)

@app.route("/students/add", methods=["POST"])
@login_required
def add_student():
    name          = request.form.get("name","").strip()
    dept          = request.form.get("department","").strip()
    year          = request.form.get("year","").strip()
    roll_no       = request.form.get("roll_no","").strip()
    enrollment_no = request.form.get("enrollment_no","").strip()

    if not all([name, dept, year, roll_no, enrollment_no]):
        flash("All fields are required.", "danger")
        return redirect(url_for("students"))

    conn = connect(); cur = conn.cursor()
    try:
        cur.execute("SELECT id FROM students WHERE roll_no=?", (roll_no,))
        if cur.fetchone():
            flash("Error: Roll number already exists.", "danger")
            conn.close()
            return redirect(url_for("students"))

        cur.execute("SELECT id FROM students WHERE enrollment_no=?", (enrollment_no,))
        if cur.fetchone():
            flash("Error: Enrollment number already exists.", "danger")
            conn.close()
            return redirect(url_for("students"))

        cur.execute("""INSERT INTO students(name, department, year, roll_no, enrollment_no)
                       VALUES(?, ?, ?, ?, ?)""",
                    (name, dept, int(year), roll_no, enrollment_no))
        conn.commit()
        flash(f"Student '{name}' added successfully.", "success")
    except Exception as e:
        flash(f"Error: {str(e)}", "danger")
    finally:
        conn.close()
    return redirect(url_for("students"))

@app.route("/students/edit/<int:sid>", methods=["GET","POST"])
@login_required
def edit_student(sid):
    conn = connect(); cur = conn.cursor()
    if request.method == "POST":
        name          = request.form.get("name","").strip()
        dept          = request.form.get("department","").strip()
        year          = request.form.get("year","").strip()
        roll_no       = request.form.get("roll_no","").strip()
        enrollment_no = request.form.get("enrollment_no","").strip()
        try:
            cur.execute("SELECT id FROM students WHERE enrollment_no=? AND id!=?", (enrollment_no, sid))
            if cur.fetchone():
                flash("Error: Enrollment number already exists.", "danger")
                conn.close()
                return redirect(url_for("edit_student", sid=sid))

            cur.execute("""UPDATE students
                           SET name=?, department=?, year=?, roll_no=?, enrollment_no=?
                           WHERE id=?""",
                        (name, dept, int(year), roll_no, enrollment_no, sid))
            conn.commit()
            flash("Student updated.", "success")
        except Exception as e:
            flash(f"Error: {str(e)}", "danger")
        conn.close()
        return redirect(url_for("students"))

    cur.execute("SELECT * FROM students WHERE id=?", (sid,))
    student = cur.fetchone(); conn.close()
    if not student:
        flash("Student not found.", "danger")
        return redirect(url_for("students"))
    return render_template("edit_student.html", student=student)

@app.route("/students/delete/<int:sid>")
@login_required
def delete_student(sid):
    conn = connect(); cur = conn.cursor()
    cur.execute("SELECT name FROM students WHERE id=?", (sid,))
    row = cur.fetchone()
    if row:
        cur.execute("DELETE FROM students WHERE id=?", (sid,))
        conn.commit()
        flash(f"Student '{row['name']}' deleted.", "warning")
    else:
        flash("Student not found.", "danger")
    conn.close()
    return redirect(url_for("students"))

# ── Faculty ────────────────────────────────────────────────────────────────────
@app.route("/faculty")
@login_required
def faculty():
    q = request.args.get("q","").strip()
    conn = connect(); cur = conn.cursor()
    if q:
        cur.execute("SELECT * FROM faculty WHERE name LIKE ? OR subject LIKE ? ORDER BY id",
                    (f"%{q}%", f"%{q}%"))
    else:
        cur.execute("SELECT * FROM faculty ORDER BY id")
    rows = cur.fetchall(); conn.close()
    return render_template("faculty.html", faculty=rows, q=q)

@app.route("/faculty/add", methods=["POST"])
@login_required
def add_faculty():
    name    = request.form.get("name","").strip()
    subject = request.form.get("subject","").strip()
    dept    = request.form.get("dept","").strip()
    if not all([name, subject, dept]):
        flash("All fields are required.", "danger")
        return redirect(url_for("faculty"))
    conn = connect(); cur = conn.cursor()
    cur.execute("INSERT INTO faculty(name,subject,dept) VALUES(?,?,?)", (name, subject, dept))
    conn.commit(); conn.close()
    flash(f"Faculty '{name}' added.", "success")
    return redirect(url_for("faculty"))

@app.route("/faculty/edit/<int:fid>", methods=["GET","POST"])
@login_required
def edit_faculty(fid):
    conn = connect(); cur = conn.cursor()
    if request.method == "POST":
        name    = request.form.get("name","").strip()
        subject = request.form.get("subject","").strip()
        dept    = request.form.get("dept","").strip()
        cur.execute("UPDATE faculty SET name=?,subject=?,dept=? WHERE id=?",
                    (name, subject, dept, fid))
        conn.commit(); conn.close()
        flash("Faculty updated.", "success")
        return redirect(url_for("faculty"))
    cur.execute("SELECT * FROM faculty WHERE id=?", (fid,))
    f = cur.fetchone(); conn.close()
    if not f:
        flash("Faculty not found.", "danger")
        return redirect(url_for("faculty"))
    return render_template("edit_faculty.html", faculty=f)

@app.route("/faculty/delete/<int:fid>")
@login_required
def delete_faculty(fid):
    conn = connect(); cur = conn.cursor()
    cur.execute("SELECT name FROM faculty WHERE id=?", (fid,))
    row = cur.fetchone()
    if row:
        cur.execute("DELETE FROM faculty WHERE id=?", (fid,))
        conn.commit()
        flash(f"Faculty '{row['name']}' deleted.", "warning")
    conn.close()
    return redirect(url_for("faculty"))

# ── Courses ────────────────────────────────────────────────────────────────────
@app.route("/courses")
@login_required
def courses():
    conn = connect(); cur = conn.cursor()
    cur.execute("""SELECT c.id, c.course_name, f.name AS faculty_name, f.subject
                   FROM courses c LEFT JOIN faculty f ON c.faculty_id=f.id ORDER BY c.id""")
    rows = cur.fetchall()
    cur.execute("SELECT id, name FROM faculty ORDER BY name")
    faculty_list = cur.fetchall()
    conn.close()
    return render_template("courses.html", courses=rows, faculty_list=faculty_list)

@app.route("/courses/add", methods=["POST"])
@login_required
def add_course():
    name = request.form.get("course_name","").strip()
    fid  = request.form.get("faculty_id","").strip() or None
    if not name:
        flash("Course name required.", "danger")
        return redirect(url_for("courses"))
    conn = connect(); cur = conn.cursor()
    cur.execute("INSERT INTO courses(course_name,faculty_id) VALUES(?,?)", (name, fid))
    conn.commit(); conn.close()
    flash(f"Course '{name}' added.", "success")
    return redirect(url_for("courses"))

@app.route("/courses/delete/<int:cid>")
@login_required
def delete_course(cid):
    conn = connect(); cur = conn.cursor()
    cur.execute("DELETE FROM courses WHERE id=?", (cid,))
    conn.commit(); conn.close()
    flash("Course deleted.", "warning")
    return redirect(url_for("courses"))

# ── Attendance ─────────────────────────────────────────────────────────────────
@app.route("/attendance")
@login_required
def attendance():
    conn = connect(); cur = conn.cursor()
    cur.execute("SELECT id,name,roll_no FROM students ORDER BY id")
    students = cur.fetchall()
    cur.execute("""SELECT s.id,s.name,s.roll_no,
                   COUNT(a.id) AS total,
                   SUM(CASE WHEN a.status='Present' THEN 1 ELSE 0 END) AS present
                   FROM students s LEFT JOIN attendance a ON s.id=a.student_id
                   GROUP BY s.id ORDER BY s.id""")
    summary = cur.fetchall()
    conn.close()
    today = str(date.today())
    return render_template("attendance.html", students=students, summary=summary, today=today)

@app.route("/attendance/mark", methods=["POST"])
@login_required
def mark_attendance():
    att_date = request.form.get("att_date", str(date.today()))
    conn = connect(); cur = conn.cursor()
    cur.execute("SELECT id FROM students")
    students = cur.fetchall()
    records = []
    for s in students:
        status = request.form.get(f"status_{s['id']}", "Absent")
        records.append((s['id'], att_date, status))
    cur.executemany("INSERT INTO attendance(student_id,date,status) VALUES(?,?,?)", records)
    conn.commit(); conn.close()
    flash(f"Attendance marked for {len(records)} students on {att_date}.", "success")
    return redirect(url_for("attendance"))

@app.route("/attendance/student/<int:sid>")
@login_required
def student_attendance(sid):
    conn = connect(); cur = conn.cursor()
    cur.execute("SELECT * FROM students WHERE id=?", (sid,))
    student = cur.fetchone()
    cur.execute("SELECT date,status FROM attendance WHERE student_id=? ORDER BY date", (sid,))
    records = cur.fetchall(); conn.close()
    total   = len(records)
    present = sum(1 for r in records if r['status']=='Present')
    pct     = round(present/total*100, 1) if total else 0
    return render_template("student_attendance.html",
        student=student, records=records, total=total, present=present, pct=pct)

# ── Staff Attendance ──────────────────────────────────────────────────────────
@app.route("/staff-attendance")
@login_required
def staff_attendance():
    conn = connect(); cur = conn.cursor()
    cur.execute("SELECT * FROM faculty ORDER BY name")
    faculty = cur.fetchall()
    cur.execute("""SELECT f.id, f.name, f.dept,
                   COUNT(sa.id) AS total,
                   SUM(CASE WHEN sa.status='Present' THEN 1 ELSE 0 END) AS present
                   FROM faculty f
                   LEFT JOIN staff_attendance sa ON f.id=sa.faculty_id
                   GROUP BY f.id ORDER BY f.name""")
    summary = cur.fetchall()
    conn.close()
    today = str(date.today())
    return render_template("staff_attendance.html", faculty=faculty, summary=summary, today=today)

@app.route("/staff-attendance/mark", methods=["POST"])
@login_required
def mark_staff_attendance():
    att_date = request.form.get("att_date", str(date.today()))
    conn = connect(); cur = conn.cursor()
    cur.execute("SELECT id FROM faculty")
    faculty = cur.fetchall()
    records = []
    for f in faculty:
        status = request.form.get(f"status_{f['id']}", "Absent")
        records.append((f['id'], att_date, status))
    cur.executemany("INSERT INTO staff_attendance(faculty_id,date,status) VALUES(?,?,?)", records)
    conn.commit(); conn.close()
    flash(f"Staff attendance marked for {len(records)} faculty on {att_date}.", "success")
    return redirect(url_for("staff_attendance"))

@app.route("/staff-attendance/detail/<int:fid>")
@login_required
def staff_attendance_detail(fid):
    conn = connect(); cur = conn.cursor()
    cur.execute("SELECT * FROM faculty WHERE id=?", (fid,))
    faculty = cur.fetchone()
    cur.execute("SELECT * FROM staff_attendance WHERE faculty_id=? ORDER BY date DESC", (fid,))
    records = cur.fetchall()
    conn.close()
    total   = len(records)
    present = sum(1 for r in records if r['status']=='Present')
    pct     = round(present/total*100, 1) if total else 0
    return render_template("staff_attendance_detail.html",
        faculty=faculty, records=records, total=total, present=present, pct=pct)

@app.route("/staff-attendance/delete/<int:rid>/<int:fid>")
@login_required
def delete_staff_attendance(rid, fid):
    conn = connect(); cur = conn.cursor()
    cur.execute("DELETE FROM staff_attendance WHERE id=?", (rid,))
    conn.commit(); conn.close()
    flash("Attendance record deleted.", "warning")
    return redirect(url_for("staff_attendance_detail", fid=fid))

# ── Student Report ────────────────────────────────────────────────────────────
@app.route("/student-report")
@login_required
def student_report():
    q   = request.args.get("q", "").strip()
    sid = request.args.get("sid", "").strip()

    search_results = []
    student        = None
    marks_data     = []
    att_records    = []
    total_marks = total_max = overall_pct = 0
    present = total_att = att_pct = 0

    if q:
        conn = connect(); cur = conn.cursor()
        cur.execute("SELECT * FROM students WHERE name LIKE ? ORDER BY name", (f"%{q}%",))
        search_results = cur.fetchall()
        conn.close()

    if sid:
        conn = connect(); cur = conn.cursor()

        # Student info
        cur.execute("SELECT * FROM students WHERE id=?", (sid,))
        student = cur.fetchone()

        if student:
            # Marks
            cur.execute("""SELECT m.id, m.subject, m.marks, m.max_marks
                           FROM marks m WHERE m.student_id=? ORDER BY m.subject""", (sid,))
            raw_marks = cur.fetchall()
            marks_data = [(r, get_grade(r['marks'], r['max_marks'])) for r in raw_marks]
            total_marks = sum(r['marks'] for r in raw_marks)
            total_max   = sum(r['max_marks'] for r in raw_marks)
            overall_pct = round(total_marks / total_max * 100, 1) if total_max else 0

            # Attendance
            cur.execute("SELECT date, status FROM attendance WHERE student_id=? ORDER BY date DESC", (sid,))
            att_records = cur.fetchall()
            total_att   = len(att_records)
            present     = sum(1 for r in att_records if r['status'] == 'Present')
            att_pct     = round(present / total_att * 100, 1) if total_att else 0

        conn.close()

    return render_template("student_report.html",
        q=q, sid=sid,
        search_results=search_results,
        student=student,
        marks_data=marks_data,
        att_records=att_records,
        total_marks=total_marks,
        total_max=total_max,
        overall_pct=overall_pct,
        present=present,
        total_att=total_att,
        att_pct=att_pct)

# ── Marks ──────────────────────────────────────────────────────────────────────
@app.route("/marks")
@login_required
def marks():
    conn = connect(); cur = conn.cursor()
    cur.execute("SELECT id,name,roll_no FROM students ORDER BY name")
    students = cur.fetchall()
    sid = request.args.get("sid","")
    student_marks = []; selected_student = None
    if sid:
        cur.execute("SELECT * FROM students WHERE id=?", (sid,))
        selected_student = cur.fetchone()
        cur.execute("""SELECT m.id, m.subject, m.marks, m.max_marks, s.name, s.roll_no
                       FROM marks m JOIN students s ON m.student_id=s.id
                       WHERE m.student_id=? ORDER BY m.subject""", (sid,))
        student_marks = cur.fetchall()
    conn.close()
    total_m = sum(r['marks'] for r in student_marks)
    total_x = sum(r['max_marks'] for r in student_marks)
    overall_pct = round(total_m/total_x*100,1) if total_x else 0
    marks_with_grade = [(r, get_grade(r['marks'], r['max_marks'])) for r in student_marks]
    return render_template("marks.html",
        students=students, selected_sid=sid,
        selected_student=selected_student,
        marks_with_grade=marks_with_grade,
        total_m=total_m, total_x=total_x,
        overall_pct=overall_pct,
        overall_grade=get_grade(total_m, total_x) if total_x else "")

@app.route("/marks/add", methods=["POST"])
@login_required
def add_marks():
    sid       = request.form.get("student_id","").strip()
    subject   = request.form.get("subject","").strip()
    marks_val = request.form.get("marks","").strip()
    max_marks = request.form.get("max_marks","100").strip() or "100"
    if not all([sid, subject, marks_val]):
        flash("All fields are required.", "danger")
        return redirect(url_for("marks"))
    conn = connect(); cur = conn.cursor()
    try:
        m = float(marks_val); mx = float(max_marks)
        if m > mx:
            flash("Marks cannot exceed max marks.", "danger")
            conn.close()
            return redirect(url_for("marks", sid=sid))
        cur.execute("SELECT id FROM marks WHERE student_id=? AND subject=?", (sid, subject))
        existing = cur.fetchone()
        if existing:
            cur.execute("UPDATE marks SET marks=?,max_marks=? WHERE student_id=? AND subject=?",
                        (m, mx, sid, subject))
            flash(f"Marks updated for '{subject}'.", "success")
        else:
            cur.execute("INSERT INTO marks(student_id,subject,marks,max_marks) VALUES(?,?,?,?)",
                        (sid, subject, m, mx))
            flash(f"Marks added for '{subject}'.", "success")
        conn.commit()
    except ValueError:
        flash("Marks must be numeric.", "danger")
    finally:
        conn.close()
    return redirect(url_for("marks", sid=sid))

@app.route("/marks/delete/<int:mid>/<int:sid>")
@login_required
def delete_marks(mid, sid):
    conn = connect(); cur = conn.cursor()
    cur.execute("DELETE FROM marks WHERE id=?", (mid,))
    conn.commit(); conn.close()
    flash("Marks record deleted.", "warning")
    return redirect(url_for("marks", sid=sid))

@app.route("/marks/report")
@login_required
def marks_report():
    conn = connect(); cur = conn.cursor()
    cur.execute("SELECT DISTINCT subject FROM marks ORDER BY subject")
    subjects = [r['subject'] for r in cur.fetchall()]
    subject = request.args.get("subject", subjects[0] if subjects else "")
    rows = []
    if subject:
        cur.execute("""SELECT s.roll_no,s.name,m.marks,m.max_marks
                       FROM marks m JOIN students s ON m.student_id=s.id
                       WHERE m.subject=? ORDER BY m.marks DESC""", (subject,))
        rows = cur.fetchall()
    conn.close()
    marks_list = [r['marks'] for r in rows]
    avg = round(sum(marks_list)/len(marks_list),2) if marks_list else 0
    rows_with_grade = [(i+1, r, get_grade(r['marks'],r['max_marks'])) for i,r in enumerate(rows)]
    return render_template("marks_report.html",
        subjects=subjects, selected_subject=subject,
        rows=rows_with_grade, avg=avg,
        highest=max(marks_list) if marks_list else 0,
        lowest=min(marks_list) if marks_list else 0)

if __name__ == "__main__":
    app.run(debug=True)