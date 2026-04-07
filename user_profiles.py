import sqlite3
import json
import random
from datetime import datetime

def init_user_profiles_db():
    """Инициализация базы данных для профилей пользователей"""
    conn = sqlite3.connect('user_profiles.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_profiles (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            chat_id INTEGER,
            fitness_level TEXT DEFAULT 'beginner',
            preferred_categories TEXT DEFAULT '[]',
            motivation_messages TEXT DEFAULT '[]',
            next_workout_date TEXT,
            reminder_hours_before INTEGER DEFAULT 2,
            last_active TEXT,
            created_at TEXT
        )
    ''')
    conn.commit()
    conn.close()

def get_user_profile(user_id):
    """Получает профиль пользователя"""
    conn = sqlite3.connect('user_profiles.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM user_profiles WHERE user_id = ?', (user_id,))
    profile = cursor.fetchone()
    conn.close()
    
    if profile:
        return {
            'user_id': profile[0],
            'username': profile[1],
            'first_name': profile[2],
            'chat_id': profile[3],
            'fitness_level': profile[4],
            'preferred_categories': json.loads(profile[5]),
            'motivation_messages': json.loads(profile[6]),
            'next_workout_date': profile[7],
            'reminder_hours_before': profile[8],
            'last_active': profile[9],
            'created_at': profile[10]
        }
    return None

def create_or_update_user_profile(user_id, username, first_name, chat_id):
    """Создает или обновляет профиль пользователя"""
    conn = sqlite3.connect('user_profiles.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT OR REPLACE INTO user_profiles 
        (user_id, username, first_name, chat_id, last_active, created_at)
        VALUES (?, ?, ?, ?, datetime('now'), COALESCE((SELECT created_at FROM user_profiles WHERE user_id = ?), datetime('now')))
    ''', (user_id, username, first_name, chat_id, user_id))
    
    conn.commit()
    conn.close()

def update_user_fitness_level(user_id, level):
    """Обновляет уровень подготовки пользователя"""
    conn = sqlite3.connect('user_profiles.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE user_profiles SET fitness_level = ? WHERE user_id = ?', (level, user_id))
    conn.commit()
    conn.close()

def set_next_workout_date(user_id, workout_date, reminder_hours=2):
    """Устанавливает дату следующей тренировки"""
    conn = sqlite3.connect('user_profiles.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE user_profiles SET next_workout_date = ?, reminder_hours_before = ? WHERE user_id = ?', 
                   (workout_date, reminder_hours, user_id))
    conn.commit()
    conn.close()

def get_upcoming_workouts():
    """Получает список предстоящих тренировок"""
    conn = sqlite3.connect('user_profiles.db')
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, first_name, chat_id, next_workout_date, reminder_hours_before FROM user_profiles WHERE next_workout_date IS NOT NULL')
    workouts = cursor.fetchall()
    conn.close()
    
    return [{
        'user_id': workout[0],
        'first_name': workout[1],
        'chat_id': workout[2],
        'next_workout_date': workout[3],
        'reminder_hours_before': workout[4]
    } for workout in workouts]

def add_user_motivation_message(user_id, message):
    """Добавляет персонализированное мотивационное сообщение для пользователя"""
    conn = sqlite3.connect('user_profiles.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT motivation_messages FROM user_profiles WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    
    if result:
        messages = json.loads(result[0])
    else:
        messages = []
    
    messages.append(message)
    
    cursor.execute('UPDATE user_profiles SET motivation_messages = ? WHERE user_id = ?', 
                   (json.dumps(messages), user_id))
    conn.commit()
    conn.close()

def get_all_users():
    """Получает всех пользователей"""
    conn = sqlite3.connect('user_profiles.db')
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, first_name, username, chat_id FROM user_profiles')
    users = cursor.fetchall()
    conn.close()
    
    return [{
        'user_id': user[0],
        'first_name': user[1],
        'username': user[2],
        'chat_id': user[3]
    } for user in users]

def get_users_by_chat(chat_id):
    """Получает всех пользователей в конкретном чате"""
    conn = sqlite3.connect('user_profiles.db')
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, first_name, username FROM user_profiles WHERE chat_id = ?', (chat_id,))
    users = cursor.fetchall()
    conn.close()
    
    return [{
        'user_id': user[0],
        'first_name': user[1],
        'username': user[2]
    } for user in users]

# Инициализация базы при импорте
init_user_profiles_db()