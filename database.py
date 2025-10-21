import os
import psycopg2
from datetime import datetime
import logging

# Получаем строку подключения из переменных окружения
def get_connection():
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        logging.error("DATABASE_URL not found in environment variables")
        return None
    return psycopg2.connect(database_url)

def escape_markdown_v2(text):
    characters = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    return ''.join(f'\\{char}' if char in characters else char for char in str(text))

def create_tables():
    conn = get_connection()
    if not conn:
        return
    try:
        cursor = conn.cursor()
        
        # Таблица упражнений
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS exercises (
                id SERIAL PRIMARY KEY,
                category TEXT NOT NULL,
                exercise TEXT NOT NULL,
                weights TEXT NOT NULL
            )
        ''')
        
        # Таблица тренировок
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS workouts (
                id SERIAL PRIMARY KEY,
                user_id BIGINT,
                exercise_name TEXT,
                reps INTEGER,
                weight REAL,
                date DATE,
                category TEXT
            )
        ''')
        
        conn.commit()
        logging.info("Tables created successfully")
    except Exception as e:
        logging.error(f"Error creating tables: {e}")
    finally:
        conn.close()

def get_exercises_by_category(category):
    conn = get_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT id, exercise, weights FROM exercises WHERE category = %s', (category,))
        data = cursor.fetchall()
        return data
    except Exception as e:
        logging.error(f"Error getting exercises: {e}")
        return []
    finally:
        conn.close()

def add_exercise(category, exercise, weights):
    conn = get_connection()
    if not conn:
        return
    try:
        cursor = conn.cursor()
        cursor.execute('INSERT INTO exercises (category, exercise, weights) VALUES (%s, %s, %s)', 
                      (category, exercise, weights))
        conn.commit()
    except Exception as e:
        logging.error(f"Error adding exercise: {e}")
    finally:
        conn.close()

def delete_exercise(exercise_id):
    conn = get_connection()
    if not conn:
        return
    try:
        cursor = conn.cursor()
        # Сначала получим название упражнения
        cursor.execute('SELECT exercise FROM exercises WHERE id = %s', (exercise_id,))
        result = cursor.fetchone()
        if result:
            exercise_name = result[0]
            # Удаляем упражнение
            cursor.execute('DELETE FROM exercises WHERE id = %s', (exercise_id,))
            # Удаляем связанные тренировки
            cursor.execute('DELETE FROM workouts WHERE exercise_name = %s', (exercise_name,))
        conn.commit()
    except Exception as e:
        logging.error(f"Error deleting exercise: {e}")
    finally:
        conn.close()

def modify_exercise(exercise_id, new_weights):
    conn = get_connection()
    if not conn:
        return
    try:
        cursor = conn.cursor()
        cursor.execute('UPDATE exercises SET weights = %s WHERE id = %s', (new_weights, exercise_id))
        conn.commit()
    except Exception as e:
        logging.error(f"Error modifying exercise: {e}")
    finally:
        conn.close()

def add_workout(user_id, exercise_name, reps, weight, category):
    conn = get_connection()
    if not conn:
        return
    try:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO workouts (user_id, exercise_name, reps, weight, date, category)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (user_id, exercise_name, reps, weight, datetime.now().date(), category))
        conn.commit()
    except Exception as e:
        logging.error(f"Error adding workout: {e}")
    finally:
        conn.close()

def get_user_stats(user_id, start_date, end_date, category=None):
    conn = get_connection()
    if not conn:
        return escape_markdown_v2("⛔ Database connection error.")
    try:
        cursor = conn.cursor()
        query = '''
            SELECT exercise_name, COUNT(*), AVG(weight), SUM(reps)
            FROM workouts 
            WHERE user_id = %s AND date BETWEEN %s AND %s
        '''
        params = [user_id, start_date, end_date]
        
        if category and category != 'general':
            query += ' AND category = %s'
            params.append(category)
            
        query += ' GROUP BY exercise_name'
        cursor.execute(query, params)
        data = cursor.fetchall()
        
        if not data:
            return escape_markdown_v2(f"⛔ Нет данных за период для категории {category}." if category != 'general' else "⛔ Нет данных за период.")
        
        text = escape_markdown_v2(f"📊 Статистика ({category}):") + "\n\n"
        for row in data:
            text += (f"🏋 *{escape_markdown_v2(row[0])}*\n"
                     f"   🔁 {escape_markdown_v2('Подходов:')} {row[1]}\n"
                     f"   ⚖ {escape_markdown_v2('Средний вес:')} {escape_markdown_v2(round(row[2], 1)) if row[2] else 0} {escape_markdown_v2('кг')}\n"
                     f"   🔄 {escape_markdown_v2('Повторений:')} {row[3]}\n\n")
        return text
    except Exception as e:
        logging.error(f"Error getting stats: {e}")
        return escape_markdown_v2("⛔ Ошибка при получении статистики.")
    finally:
        conn.close()

def get_workout_logs(user_id, exercise_name, start_date, end_date, category=None):
    conn = get_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor()
        query = '''
            SELECT date, weight, reps 
            FROM workouts 
            WHERE user_id = %s AND exercise_name = %s AND date BETWEEN %s AND %s
        '''
        params = [user_id, exercise_name, start_date, end_date]
        
        if category and category != 'general':
            query += ' AND category = %s'
            params.append(category)
            
        cursor.execute(query, params)
        logs = cursor.fetchall()
        return logs
    except Exception as e:
        logging.error(f"Error getting workout logs: {e}")
        return []
    finally:
        conn.close()

def get_workouts_by_user(user_id, start_date, end_date, category=None):
    conn = get_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor()
        query = '''
            SELECT id, exercise_name, weight, reps, date
            FROM workouts 
            WHERE user_id = %s AND date BETWEEN %s AND %s
        '''
        params = [user_id, start_date, end_date]
        
        if category and category != 'general':
            query += ' AND category = %s'
            params.append(category)
            
        query += ' ORDER BY date DESC'
        cursor.execute(query, params)
        workouts = cursor.fetchall()
        return workouts
    except Exception as e:
        logging.error(f"Error getting workouts: {e}")
        return []
    finally:
        conn.close()

def delete_workout(workout_id):
    conn = get_connection()
    if not conn:
        return
    try:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM workouts WHERE id = %s', (workout_id,))
        conn.commit()
    except Exception as e:
        logging.error(f"Error deleting workout: {e}")
    finally:
        conn.close()