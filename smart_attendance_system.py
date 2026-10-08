import cv2
import sqlite3
import os
from datetime import datetime

DB = "attendance.db"
FACE_DIR = "faces"
os.makedirs(FACE_DIR, exist_ok=True)

def init_db():
    con = sqlite3.connect(DB)
    cur = con.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS students(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        face_path TEXT NOT NULL
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS attendance(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        date TEXT,
        time TEXT
    )""")
    con.commit()
    con.close()

def register_student():
    name = input("Student name: ").strip()
    if not name:
        print("Name required.")
        return

    cam = cv2.VideoCapture(0)
    detector = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )

    print("Look at the camera. Press SPACE to capture, ESC to cancel.")
    while True:
        ok, frame = cam.read()
        if not ok:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = detector.detectMultiScale(gray, 1.3, 5)

        for x, y, w, h in faces:
            cv2.rectangle(frame, (x,y), (x+w,y+h), (0,255,0), 2)

        cv2.imshow("Register", frame)
        key = cv2.waitKey(1) & 0xFF

        if key == 32 and len(faces) > 0:
            x,y,w,h = faces[0]
            path = os.path.join(FACE_DIR, f"{name.replace(' ','_')}.jpg")
            cv2.imwrite(path, gray[y:y+h, x:x+w])

            con = sqlite3.connect(DB)
            cur = con.cursor()
            cur.execute("INSERT INTO students(name, face_path) VALUES(?,?)",
                        (name, path))
            con.commit()
            con.close()
            print("Student registered:", name)
            break

        if key == 27:
            break

    cam.release()
    cv2.destroyAllWindows()

def list_students():
    con = sqlite3.connect(DB)
    cur = con.cursor()
    cur.execute("SELECT id, name FROM students")
    rows = cur.fetchall()
    con.close()
    print("\nRegistered students:")
    for row in rows:
        print(row)

def mark_attendance():
    list_students()
    try:
        student_id = int(input("Enter recognized student ID: "))
    except ValueError:
        print("Invalid ID.")
        return

    con = sqlite3.connect(DB)
    cur = con.cursor()
    cur.execute("SELECT name FROM students WHERE id=?", (student_id,))
    row = cur.fetchone()

    if not row:
        print("Student not found.")
        con.close()
        return

    now = datetime.now()
    cur.execute("""SELECT 1 FROM attendance
                   WHERE student_id=? AND date=?""",
                (student_id, now.date().isoformat()))

    if cur.fetchone():
        print("Attendance already marked today.")
    else:
        cur.execute("""INSERT INTO attendance(student_id,date,time)
                       VALUES(?,?,?)""",
                    (student_id, now.date().isoformat(),
                     now.strftime("%H:%M:%S")))
        con.commit()
        print("Attendance marked for", row[0])

    con.close()

def main():
    init_db()
    while True:
        print("\n1. Register student")
        print("2. List students")
        print("3. Mark attendance")
        print("4. Exit")
        choice = input("Choice: ")

        if choice == "1":
            register_student()
        elif choice == "2":
            list_students()
        elif choice == "3":
            mark_attendance()
        elif choice == "4":
            break
        else:
            print("Invalid choice.")

if __name__ == "__main__":
    main()
