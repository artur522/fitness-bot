import sqlite3
import datetime

def escape_markdown_v2(text):
    characters = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    return ''.join(f'\\{char}' if char in characters else char for char in str(text))

def create_tables():
    conn = sqlite3.connect('exercises.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS exercises (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            exercise TEXT NOT NULL,
            weights TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()
    
    conn = sqlite3.connect('workouts.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS workouts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            exercise_name TEXT,
            reps INTEGER,
            weight REAL,
            date TEXT,
            category TEXT
        )
    ''')
    conn.commit()
    conn.close()

def get_exercises_by_category(category):
    conn = sqlite3.connect('exercises.db')
    cursor = conn.cursor()
    if category:
        cursor.execute('SELECT id, exercise, weights FROM exercises WHERE category = ?', (category,))
    else:
        cursor.execute('SELECT id, exercise, weights FROM exercises')
    data = cursor.fetchall()
    conn.close()
    return data

def add_exercise(category, exercise, weights):
    conn = sqlite3.connect('exercises.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO exercises (category, exercise, weights) VALUES (?, ?, ?)', (category, exercise, weights))
    conn.commit()
    conn.close()

def delete_exercise(exercise_id):
    conn = sqlite3.connect('exercises.db')
    cursor = conn.cursor()
    cursor.execute('SELECT exercise FROM exercises WHERE id = ?', (exercise_id,))
    exercise_name = cursor.fetchone()[0]
    cursor.execute('DELETE FROM exercises WHERE id = ?', (exercise_id,))
    conn.commit()
    conn.close()
    conn = sqlite3.connect('workouts.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM workouts WHERE exercise_name = ?', (exercise_name,))
    conn.commit()
    conn.close()

def modify_exercise(exercise_id, new_weights):
    conn = sqlite3.connect('exercises.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE exercises SET weights = ? WHERE id = ?', (new_weights, exercise_id))
    conn.commit()
    conn.close()

def add_workout(user_id, exercise_name, reps, weight, category):
    conn = sqlite3.connect('workouts.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO workouts (user_id, exercise_name, reps, weight, date, category)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_id, exercise_name, reps, weight, datetime.date.today().isoformat(), category))
    conn.commit()
    conn.close()

def get_user_stats(user_id, start_date, end_date, category=None):
    conn = sqlite3.connect('workouts.db')
    cursor = conn.cursor()
    query = '''
        SELECT exercise_name, COUNT(*), AVG(weight), SUM(reps)
        FROM workouts 
        WHERE date BETWEEN ? AND ? AND user_id = ?
    '''
    params = (start_date, end_date, user_id)
    if category and category != 'general':
        query += ' AND category = ?'
        params = (start_date, end_date, user_id, category)
    query += ' GROUP BY exercise_name'
    cursor.execute(query, params)
    data = cursor.fetchall()
    conn.close()
    if not data:
        return escape_markdown_v2(f"⛔ Нет данных за период для категории {category}." if category != 'general' else "⛔ Нет данных за период.")
    text = escape_markdown_v2(f"📊 Статистика ({category}):") + "\n\n"
    for row in data:
        text += (f"🏋 *{escape_markdown_v2(row[0])}*\n"
                 f"   🔁 {escape_markdown_v2('Подходов:')} {row[1]}\n"
                 f"   ⚖ {escape_markdown_v2('Средний вес:')} {escape_markdown_v2(round(row[2], 1))} {escape_markdown_v2('кг')}\n"
                 f"   🔄 {escape_markdown_v2('Повторений:')} {row[3]}\n\n")
    return text

def get_workout_logs(user_id, exercise_name, start_date, end_date, category=None):
    conn = sqlite3.connect('workouts.db')
    cursor = conn.cursor()
    query = '''
        SELECT date, weight, reps 
        FROM workouts 
        WHERE exercise_name = ? AND date BETWEEN ? AND ? AND user_id = ?
    '''
    params = (exercise_name, start_date, end_date, user_id)
    if category and category != 'general':
        query += ' AND category = ?'
        params = (exercise_name, start_date, end_date, user_id, category)
    cursor.execute(query, params)
    logs = cursor.fetchall()
    conn.close()
    return logs

def get_workouts_by_user(user_id, start_date, end_date, category=None):
    conn = sqlite3.connect('workouts.db')
    cursor = conn.cursor()
    query = '''
        SELECT id, exercise_name, weight, reps, date
        FROM workouts 
        WHERE date BETWEEN ? AND ? AND user_id = ?
    '''
    params = (start_date, end_date, user_id)
    if category and category != 'general':
        query += ' AND category = ?'
        params = (start_date, end_date, user_id, category)
    query += ' ORDER BY date DESC'
    cursor.execute(query, params)
    workouts = cursor.fetchall()
    conn.close()
    return workouts

def delete_workout(workout_id):
    conn = sqlite3.connect('workouts.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM workouts WHERE id = ?', (workout_id,))
    conn.commit()
    conn.close()
    
def delete_all_workouts():
    """Удаляет все записи тренировок"""
    conn = sqlite3.connect('workouts.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM workouts')
    conn.commit()
    conn.close()