import sqlite3

def validate_login(username, password):
    conn = sqlite3.connect("fitness_tracker.db")
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    result = cur.fetchone()
    conn.close()
    return bool(result)

def register_user(username, password):
    try:
        conn = sqlite3.connect("fitness_tracker.db")
        cur = conn.cursor()
        cur.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        conn.close()
        return True
    except:
        return False
def save_workout(username, exercise, weight, reps, sets):
    conn = sqlite3.connect("fitness_tracker.db")
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO workouts (username, date, exercise, weight, reps, sets)
        VALUES (?, DATE('now'), ?, ?, ?, ?)
    ''', (username, exercise, weight, reps, sets))
    conn.commit()
    conn.close()
