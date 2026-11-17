from flask import Flask, render_template, request, redirect, session, url_for, Response
import sqlite3
import csv
import io
from datetime import date
from werkzeug.security import check_password_hash

app = Flask(__name__)
app.secret_key = 'change_this_secret_key_123'


def get_db():
    conn = sqlite3.connect('school.db')
    conn.row_factory = sqlite3.Row
    return conn


def login_required(role=None):
    if 'user_id' not in session:
        return False
    if role and session.get('role') != role:
        return False
    return True


# ---------- LOGIN / LOGOUT ----------

@app.route('/')
def login_page():
    return render_template('login.html')


@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    conn.close()
    if user and check_password_hash(user['password'], password):
        session['user_id'] = user['id']
        session['role'] = user['role']
        session['name'] = user['name']
        if user['role'] == 'admin':
            return redirect(url_for('admin_dashboard'))
        elif user['role'] == 'teacher':
            return redirect(url_for('teacher_dashboard'))
        else:
            return redirect(url_for('student_dashboard'))
    return render_template('login.html', error='Invalid email or password')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))


# ---------- ADMIN ----------

@app.route('/admin/dashboard')
def admin_dashboard():
    if not login_required('admin'):
        return redirect(url_for('login_page'))
    conn = get_db()
    total_students = conn.execute('SELECT COUNT(*) FROM students').fetchone()[0]
    total_teachers = conn.execute('SELECT COUNT(*) FROM teachers').fetchone()[0]
    total_notices = conn.execute('SELECT COUNT(*) FROM notices').fetchone()[0]
    conn.close()
    return render_template('admin_dashboard.html', total_students=total_students,
                            total_teachers=total_teachers, total_notices=total_notices)


@app.route('/admin/students')
def admin_students():
    if not login_required('admin'):
        return redirect(url_for('login_page'))
    conn = get_db()
    all_students = conn.execute('SELECT * FROM students ORDER BY class_name').fetchall()
    conn.close()
    return render_template('students.html', students=all_students)


@app.route('/admin/students/add', methods=['GET', 'POST'])
def add_student():
    if not login_required('admin'):
        return redirect(url_for('login_page'))
    if request.method == 'POST':
        from werkzeug.security import generate_password_hash
        conn = get_db()
        pw_hash = generate_password_hash(request.form['password'] or 'student123')
        cur = conn.execute('INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)',
                            (request.form['name'], request.form['email'], pw_hash, 'student'))
        user_id = cur.lastrowid
        conn.execute('INSERT INTO students (user_id, name, roll_no, class_name, email) VALUES (?, ?, ?, ?, ?)',
                      (user_id, request.form['name'], request.form['roll_no'],
                       request.form['class_name'], request.form['email']))
        conn.commit()
        conn.close()
        return redirect(url_for('admin_students'))
    return render_template('add_student.html')


@app.route('/admin/students/edit/<int:id>', methods=['GET', 'POST'])
def edit_student(id):
    if not login_required('admin'):
        return redirect(url_for('login_page'))
    conn = get_db()
    if request.method == 'POST':
        conn.execute('UPDATE students SET name=?, roll_no=?, class_name=?, email=? WHERE id=?',
                     (request.form['name'], request.form['roll_no'],
                      request.form['class_name'], request.form['email'], id))
        conn.commit()
        conn.close()
        return redirect(url_for('admin_students'))
    student = conn.execute('SELECT * FROM students WHERE id=?', (id,)).fetchone()
    conn.close()
    return render_template('edit_student.html', student=student)


@app.route('/admin/students/delete/<int:id>')
def delete_student(id):
    if not login_required('admin'):
        return redirect(url_for('login_page'))
    conn = get_db()
    student = conn.execute('SELECT * FROM students WHERE id=?', (id,)).fetchone()
    if student:
        conn.execute('DELETE FROM users WHERE id=?', (student['user_id'],))
    conn.execute('DELETE FROM students WHERE id=?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_students'))


@app.route('/admin/teachers')
def admin_teachers():
    if not login_required('admin'):
        return redirect(url_for('login_page'))
    conn = get_db()
    all_teachers = conn.execute('SELECT * FROM teachers').fetchall()
    conn.close()
    return render_template('teachers.html', teachers=all_teachers)


@app.route('/admin/teachers/add', methods=['GET', 'POST'])
def add_teacher():
    if not login_required('admin'):
        return redirect(url_for('login_page'))
    if request.method == 'POST':
        from werkzeug.security import generate_password_hash
        conn = get_db()
        pw_hash = generate_password_hash(request.form['password'] or 'teacher123')
        cur = conn.execute('INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)',
                            (request.form['name'], request.form['email'], pw_hash, 'teacher'))
        user_id = cur.lastrowid
        conn.execute('INSERT INTO teachers (user_id, name, subject, email) VALUES (?, ?, ?, ?)',
                      (user_id, request.form['name'], request.form['subject'], request.form['email']))
        conn.commit()
        conn.close()
        return redirect(url_for('admin_teachers'))
    return render_template('add_teacher.html')


@app.route('/admin/teachers/edit/<int:id>', methods=['GET', 'POST'])
def edit_teacher(id):
    if not login_required('admin'):
        return redirect(url_for('login_page'))
    conn = get_db()
    if request.method == 'POST':
        conn.execute('UPDATE teachers SET name=?, subject=?, email=? WHERE id=?',
                     (request.form['name'], request.form['subject'], request.form['email'], id))
        conn.commit()
        conn.close()
        return redirect(url_for('admin_teachers'))
    teacher = conn.execute('SELECT * FROM teachers WHERE id=?', (id,)).fetchone()
    conn.close()
    return render_template('edit_teacher.html', teacher=teacher)


@app.route('/admin/teachers/delete/<int:id>')
def delete_teacher(id):
    if not login_required('admin'):
        return redirect(url_for('login_page'))
    conn = get_db()
    teacher = conn.execute('SELECT * FROM teachers WHERE id=?', (id,)).fetchone()
    if teacher:
        conn.execute('DELETE FROM users WHERE id=?', (teacher['user_id'],))
    conn.execute('DELETE FROM teachers WHERE id=?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_teachers'))


# ---------- NOTICES (admin posts, everyone views) ----------

@app.route('/notices', methods=['GET', 'POST'])
def notices():
    if not login_required():
        return redirect(url_for('login_page'))
    conn = get_db()
    if request.method == 'POST' and session['role'] in ('admin', 'teacher'):
        conn.execute('INSERT INTO notices (title, message, date, posted_by) VALUES (?, ?, ?, ?)',
                     (request.form['title'], request.form['message'], str(date.today()), session['name']))
        conn.commit()
    all_notices = conn.execute('SELECT * FROM notices ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('notices.html', notices=all_notices)


@app.route('/notices/delete/<int:id>')
def delete_notice(id):
    if not login_required('admin'):
        return redirect(url_for('login_page'))
    conn = get_db()
    conn.execute('DELETE FROM notices WHERE id=?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('notices'))


# ---------- TEACHER ----------

@app.route('/teacher/dashboard')
def teacher_dashboard():
    if not login_required('teacher'):
        return redirect(url_for('login_page'))
    conn = get_db()
    total_students = conn.execute('SELECT COUNT(*) FROM students').fetchone()[0]
    total_assignments = conn.execute('SELECT COUNT(*) FROM assignments WHERE posted_by=?',
                                      (session['name'],)).fetchone()[0]
    conn.close()
    return render_template('teacher_dashboard.html', total_students=total_students,
                            total_assignments=total_assignments)


@app.route('/teacher/students')
def teacher_students():
    if not login_required('teacher'):
        return redirect(url_for('login_page'))
    conn = get_db()
    all_students = conn.execute('SELECT * FROM students ORDER BY class_name').fetchall()
    conn.close()
    return render_template('teacher_students.html', students=all_students)


@app.route('/teacher/students/download')
def teacher_download_students():
    if not login_required('teacher'):
        return redirect(url_for('login_page'))
    conn = get_db()
    all_students = conn.execute('SELECT name, roll_no, class_name, email FROM students ORDER BY class_name').fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Name', 'Roll No', 'Class', 'Email'])
    for s in all_students:
        writer.writerow([s['name'], s['roll_no'], s['class_name'], s['email']])

    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=students_data.csv'}
    )


@app.route('/teacher/attendance', methods=['GET', 'POST'])
def teacher_attendance():
    if not login_required('teacher'):
        return redirect(url_for('login_page'))
    conn = get_db()
    classes = [r['class_name'] for r in conn.execute('SELECT DISTINCT class_name FROM students ORDER BY class_name')]
    selected_class = request.values.get('class_name', classes[0] if classes else '')
    today = str(date.today())

    if request.method == 'POST':
        class_students = conn.execute('SELECT id FROM students WHERE class_name=?', (selected_class,)).fetchall()
        conn.execute('DELETE FROM attendance WHERE date=? AND student_id IN (SELECT id FROM students WHERE class_name=?)',
                     (today, selected_class))
        for s in class_students:
            status = request.form.get(f'status_{s["id"]}', 'Absent')
            conn.execute('INSERT INTO attendance (student_id, date, status) VALUES (?, ?, ?)',
                         (s['id'], today, status))
        conn.commit()

    class_students = conn.execute('SELECT * FROM students WHERE class_name=?', (selected_class,)).fetchall()
    conn.close()
    return render_template('teacher_attendance.html', classes=classes, selected_class=selected_class,
                            students=class_students, today=today)


@app.route('/teacher/assignments', methods=['GET', 'POST'])
def teacher_assignments():
    if not login_required('teacher'):
        return redirect(url_for('login_page'))
    conn = get_db()
    classes = [r['class_name'] for r in conn.execute('SELECT DISTINCT class_name FROM students ORDER BY class_name')]
    if request.method == 'POST':
        conn.execute('''INSERT INTO assignments (class_name, subject, title, description, due_date, posted_by)
                         VALUES (?, ?, ?, ?, ?, ?)''',
                     (request.form['class_name'], request.form['subject'], request.form['title'],
                      request.form['description'], request.form['due_date'], session['name']))
        conn.commit()
    all_assignments = conn.execute('SELECT * FROM assignments ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('teacher_assignments.html', assignments=all_assignments, classes=classes)


@app.route('/teacher/assignments/delete/<int:id>')
def delete_assignment(id):
    if not login_required('teacher'):
        return redirect(url_for('login_page'))
    conn = get_db()
    conn.execute('DELETE FROM assignments WHERE id=?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('teacher_assignments'))


# ---------- STUDENT ----------

def get_current_student(conn):
    return conn.execute('SELECT * FROM students WHERE user_id=?', (session['user_id'],)).fetchone()


@app.route('/student/dashboard')
def student_dashboard():
    if not login_required('student'):
        return redirect(url_for('login_page'))
    conn = get_db()
    me = get_current_student(conn)
    total_present = conn.execute('SELECT COUNT(*) FROM attendance WHERE student_id=? AND status="Present"',
                                  (me['id'],)).fetchone()[0]
    total_marked = conn.execute('SELECT COUNT(*) FROM attendance WHERE student_id=?', (me['id'],)).fetchone()[0]
    assignment_count = conn.execute('SELECT COUNT(*) FROM assignments WHERE class_name=?',
                                     (me['class_name'],)).fetchone()[0]
    conn.close()
    percent = round((total_present / total_marked) * 100) if total_marked else 0
    return render_template('student_dashboard.html', me=me, percent=percent, assignment_count=assignment_count)


@app.route('/student/attendance')
def student_attendance():
    if not login_required('student'):
        return redirect(url_for('login_page'))
    conn = get_db()
    me = get_current_student(conn)
    records = conn.execute('SELECT * FROM attendance WHERE student_id=? ORDER BY date DESC', (me['id'],)).fetchall()
    conn.close()
    return render_template('student_attendance.html', records=records)


@app.route('/student/assignments')
def student_assignments():
    if not login_required('student'):
        return redirect(url_for('login_page'))
    conn = get_db()
    me = get_current_student(conn)
    records = conn.execute('SELECT * FROM assignments WHERE class_name=? ORDER BY id DESC',
                            (me['class_name'],)).fetchall()
    conn.close()
    return render_template('student_assignments.html', records=records)


if __name__ == '__main__':
    app.run(debug=True)
