import os
import io
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.getenv("DATABASE_URL") or "sqlite:///exercises.db"

def get_db():
    """Получить подключение к БД"""
    if DATABASE_URL.startswith("postgres"):
        conn = psycopg2.connect(DATABASE_URL)
    else:
        import sqlite3
        conn = sqlite3.connect(DATABASE_URL.replace("sqlite:///", ""))
    return conn

def create_tables():
    """Создаёт таблицы в БД"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS exercises (
                id SERIAL PRIMARY KEY,
                category TEXT NOT NULL,
                exercise_name TEXT NOT NULL,
                min_weight TEXT NOT NULL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS weights_history (
                id SERIAL PRIMARY KEY,
                exercise_id INTEGER NOT NULL REFERENCES exercises(id) ON DELETE CASCADE,
                weights TEXT NOT NULL,
                changed_date TEXT NOT NULL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_stats (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                last_visit TEXT NOT NULL,
                created_at TEXT NOT NULL,
                total_visits INTEGER DEFAULT 1,
                favorite_category TEXT
            )
        ''')
        
        conn.commit()
    except Exception as e:
        print(f"Error creating tables: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def add_exercise(category, exercise, weights):
    """Добавить упражнение"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            'INSERT INTO exercises (category, exercise_name, min_weight) VALUES (%s, %s, %s) RETURNING id',
            (category, exercise, weights)
        )
        exercise_id = cursor.fetchone()[0]
        
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute(
            'INSERT INTO weights_history (exercise_id, weights, changed_date) VALUES (%s, %s, %s)',
            (exercise_id, weights, today)
        )
        
        conn.commit()
        return exercise_id
    finally:
        cursor.close()
        conn.close()

def get_exercises_by_category(category):
    """Получить все упражнения категории"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT id, exercise_name, min_weight FROM exercises WHERE category = %s', (category,))
        results = cursor.fetchall()
        return results
    finally:
        cursor.close()
        conn.close()

def get_exercise_by_id(exercise_id):
    """Получить упражнение по ID"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT id, exercise_name, min_weight FROM exercises WHERE id = %s', (exercise_id,))
        result = cursor.fetchone()
        return result
    finally:
        cursor.close()
        conn.close()

def delete_exercise(exercise_id):
    """Удалить упражнение"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute('DELETE FROM exercises WHERE id = %s', (exercise_id,))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

def get_all_categories():
    """Получить все категории"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT DISTINCT category FROM exercises ORDER BY category')
        categories = [row[0] for row in cursor.fetchall()]
        return categories
    finally:
        cursor.close()
        conn.close()

def modify_exercise(exercise_id, new_weight):
    """Изменить вес упражнения"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute('UPDATE exercises SET min_weight = %s WHERE id = %s', (new_weight, exercise_id))
        
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute(
            'INSERT INTO weights_history (exercise_id, weights, changed_date) VALUES (%s, %s, %s)',
            (exercise_id, new_weight, today)
        )
        
        conn.commit()
    finally:
        cursor.close()
        conn.close()

def get_weight_history(exercise_id):
    """Получить историю весов"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            'SELECT changed_date, weights FROM weights_history WHERE exercise_id = %s ORDER BY changed_date',
            (exercise_id,)
        )
        results = cursor.fetchall()
        return results
    finally:
        cursor.close()
        conn.close()

def generate_weight_chart(exercise_id, exercise_name, category):
    """Создать график весов"""
    history = get_weight_history(exercise_id)
    
    if not history or len(history) < 2:
        return None
    
    dates = []
    weights = []
    
    for date_str, weight in history:
        dates.append(datetime.strptime(date_str, '%Y-%m-%d'))
        weights.append(float(weight))
    
    fig, ax = plt.subplots(figsize=(10, 6))
    fig.patch.set_facecolor('#2d2d2d')
    ax.set_facecolor('#3d3d3d')
    
    ax.plot(dates, weights, marker='o', linewidth=2.5, markersize=8, 
            color='#00ff41', markerfacecolor='#00ff41', markeredgewidth=2, markeredgecolor='#00ff41')
    
    ax.grid(True, alpha=0.2, color='white')
    ax.set_xlabel('Date', fontsize=12, color='white', weight='bold')
    ax.set_ylabel('Weight (kg)', fontsize=12, color='white', weight='bold')
    ax.set_title(f'{exercise_name} ({category})', fontsize=14, color='white', weight='bold', pad=20)
    
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    plt.xticks(rotation=45, color='white')
    plt.yticks(color='white')
    
    for spine in ax.spines.values():
        spine.set_color('white')
        spine.set_linewidth(2)
    
    ax.tick_params(colors='white')
    
    plt.tight_layout()
    
    image_buffer = io.BytesIO()
    plt.savefig(image_buffer, format='png', facecolor='#2d2d2d', bbox_inches='tight')
    image_buffer.seek(0)
    plt.close()
    
    return image_buffer

def generate_category_chart(category):
    """Создать сравнительный график категории"""
    exercises = get_exercises_by_category(category)
    
    if not exercises:
        return None
    
    fig, ax = plt.subplots(figsize=(12, 6))
    fig.patch.set_facecolor('#2d2d2d')
    ax.set_facecolor('#3d3d3d')
    
    exercise_names = []
    current_weights = []
    colors = ['#00ff41', '#ff6b6b', '#4ecdc4', '#ffe66d', '#95e1d3', '#c7ceea']
    
    for idx, (ex_id, ex_name, current_weight) in enumerate(exercises):
        exercise_names.append(ex_name)
        current_weights.append(float(current_weight))
    
    bars = ax.bar(range(len(exercise_names)), current_weights, 
                 color=colors[:len(exercise_names)], edgecolor='white', linewidth=2)
    
    ax.set_xlabel('Exercise', fontsize=12, color='white', weight='bold')
    ax.set_ylabel('Weight (kg)', fontsize=12, color='white', weight='bold')
    ax.set_title(f'{category}', fontsize=14, color='white', weight='bold', pad=20)
    
    ax.set_xticks(range(len(exercise_names)))
    ax.set_xticklabels(exercise_names, rotation=45, ha='right', color='white')
    plt.yticks(color='white')
    
    ax.grid(True, alpha=0.2, axis='y', color='white')
    
    for spine in ax.spines.values():
        spine.set_color('white')
        spine.set_linewidth(2)
    
    for i, (bar, weight) in enumerate(zip(bars, current_weights)):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
               f'{weight:.1f}', ha='center', va='bottom', color='white', fontweight='bold')
    
    ax.tick_params(colors='white')
    
    plt.tight_layout()
    
    image_buffer = io.BytesIO()
    plt.savefig(image_buffer, format='png', facecolor='#2d2d2d', bbox_inches='tight')
    image_buffer.seek(0)
    plt.close()
    
    return image_buffer

def update_user_visit(user_id, username=''):
    """Обновить последний визит пользователя"""
    conn = get_db()
    cursor = conn.cursor()
    
    now = datetime.now().isoformat()
    
    try:
        cursor.execute('SELECT user_id FROM user_stats WHERE user_id = %s', (user_id,))
        exists = cursor.fetchone() is not None
        
        if exists:
            cursor.execute(
                'UPDATE user_stats SET last_visit = %s, total_visits = total_visits + 1 WHERE user_id = %s',
                (now, user_id)
            )
        else:
            cursor.execute(
                'INSERT INTO user_stats (user_id, username, last_visit, created_at, total_visits) VALUES (%s, %s, %s, %s, 1)',
                (user_id, username, now, now)
            )
        
        conn.commit()
    finally:
        cursor.close()
        conn.close()

def get_user_last_visit(user_id):
    """Получить дату последнего визита пользователя"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT last_visit FROM user_stats WHERE user_id = %s', (user_id,))
        result = cursor.fetchone()
        return result[0] if result else None
    finally:
        cursor.close()
        conn.close()

def days_since_last_visit(user_id):
    """Вычислить сколько дней прошло с последнего визита"""
    last_visit = get_user_last_visit(user_id)
    
    if not last_visit:
        return 0
    
    try:
        last_visit_date = datetime.fromisoformat(last_visit)
        days = (datetime.now() - last_visit_date).days
        return days
    except:
        return 0

def get_inactive_users(days=5):
    """Получить всех пользователей которые не заходили N дней"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        cursor.execute(
            'SELECT user_id, username, last_visit, created_at, total_visits, favorite_category FROM user_stats WHERE last_visit < %s',
            (cutoff_date,)
        )
        
        inactive_users = cursor.fetchall()
        return inactive_users
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    create_tables()
    print("Tables created!")
