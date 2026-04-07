import sqlite3
import io
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

DB_PATH = 'exercises.db'

def create_tables():
    """Создаёт таблицы в БД"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Таблица упражнений
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS exercises (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            exercise_name TEXT NOT NULL,
            min_weight TEXT NOT NULL
        )
    ''')
    
    # Таблица истории весов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS weights_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            exercise_id INTEGER NOT NULL,
            weights TEXT NOT NULL,
            changed_date TEXT NOT NULL,
            FOREIGN KEY(exercise_id) REFERENCES exercises(id) ON DELETE CASCADE
        )
    ''')
    
    # 🆕 НОВАЯ ТАБЛИЦА - отслеживание пользователей
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
    conn.close()

# ============================================================================
# УПРАЖНЕНИЯ
# ============================================================================

def add_exercise(category, exercise, weights):
    """Добавить упражнение"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute(
        'INSERT INTO exercises (category, exercise_name, min_weight) VALUES (?, ?, ?)',
        (category, exercise, weights)
    )
    
    exercise_id = cursor.lastrowid
    
    # Автоматически добавляем в историю
    today = datetime.now().strftime('%Y-%m-%d')
    cursor.execute(
        'INSERT INTO weights_history (exercise_id, weights, changed_date) VALUES (?, ?, ?)',
        (exercise_id, weights, today)
    )
    
    conn.commit()
    conn.close()
    
    return exercise_id

def get_exercise_by_id(exercise_id):
    """Получить упражнение по ID"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, exercise_name, min_weight FROM exercises WHERE id = ?', (exercise_id,))
    result = cursor.fetchone()
    conn.close()
    
    return result

def get_exercises_by_category(category):
    """Получить все упражнения категории"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, exercise_name, min_weight FROM exercises WHERE category = ?', (category,))
    results = cursor.fetchall()
    conn.close()
    
    return results

def delete_exercise(exercise_id):
    """Удалить упражнение"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM exercises WHERE id = ?', (exercise_id,))
    conn.commit()
    conn.close()

def get_all_categories():
    """Получить все категории"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT DISTINCT category FROM exercises ORDER BY category')
    categories = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    return categories

# ============================================================================
# ВЕСЫ И ИСТОРИЯ
# ============================================================================

def modify_exercise(exercise_id, new_weight):
    """Изменить вес упражнения"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Обновляем текущий вес
    cursor.execute('UPDATE exercises SET min_weight = ? WHERE id = ?', (new_weight, exercise_id))
    
    # Записываем в историю
    today = datetime.now().strftime('%Y-%m-%d')
    cursor.execute(
        'INSERT INTO weights_history (exercise_id, weights, changed_date) VALUES (?, ?, ?)',
        (exercise_id, new_weight, today)
    )
    
    conn.commit()
    conn.close()

def get_weight_history(exercise_id, start_date=None, end_date=None):
    """Получить историю весов за период"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if start_date is None and end_date is None:
        # За всю историю
        cursor.execute(
            'SELECT changed_date, weights FROM weights_history WHERE exercise_id = ? ORDER BY changed_date',
            (exercise_id,)
        )
    else:
        # За период
        cursor.execute('''
            SELECT changed_date, weights FROM weights_history 
            WHERE exercise_id = ? AND changed_date BETWEEN ? AND ?
            ORDER BY changed_date
        ''', (exercise_id, start_date, end_date))
    
    results = cursor.fetchall()
    conn.close()
    
    return results

def record_weight_change(exercise_id, new_weight):
    """Записать изменение веса"""
    today = datetime.now().strftime('%Y-%m-%d')
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute(
        'INSERT INTO weights_history (exercise_id, weights, changed_date) VALUES (?, ?, ?)',
        (exercise_id, new_weight, today)
    )
    
    conn.commit()
    conn.close()

# ============================================================================
# СТАТИСТИКА
# ============================================================================

def get_exercise_progress(exercise_id):
    """Получить прогресс упражнения"""
    history = get_weight_history(exercise_id)
    
    if not history:
        return None
    
    start_weight = float(history[0][1])
    end_weight = float(history[-1][1])
    progress = end_weight - start_weight
    
    return {
        'start': start_weight,
        'end': end_weight,
        'progress': progress,
        'percent': (progress / start_weight * 100) if start_weight > 0 else 0,
        'records': len(history)
    }

def get_category_stats(category, days=30):
    """Получить статистику категории за период"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    
    cursor.execute('''
        SELECT e.id, e.exercise_name, e.min_weight
        FROM exercises e
        WHERE e.category = ?
    ''', (category,))
    
    exercises = cursor.fetchall()
    conn.close()
    
    stats = []
    for ex_id, ex_name, current_weight in exercises:
        history = get_weight_history(ex_id, start_date)
        
        if history:
            start_weight = float(history[0][1])
            end_weight = float(history[-1][1])
            progress = end_weight - start_weight
            
            stats.append({
                'id': ex_id,
                'name': ex_name,
                'current': end_weight,
                'start': start_weight,
                'progress': progress,
                'changes': len(history)
            })
    
    return stats

def get_all_category_stats():
    """Получить статистику всех категорий"""
    categories = get_all_categories()
    stats = {}
    
    for category in categories:
        exercises = get_exercises_by_category(category)
        
        total_progress = 0
        count = 0
        
        for ex_id, ex_name, weight in exercises:
            progress = get_exercise_progress(ex_id)
            if progress:
                total_progress += progress['progress']
                count += 1
        
        stats[category] = {
            'exercises': len(exercises),
            'total_progress': total_progress,
            'avg_progress': total_progress / count if count > 0 else 0
        }
    
    return stats

# ============================================================================
# ГРАФИКИ
# ============================================================================

def generate_weight_chart(exercise_id, exercise_name, category):
    """Создать график весов для упражнения"""
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
    
    ax.set_xlabel('Дата', fontsize=12, color='white', weight='bold')
    ax.set_ylabel('Вес (кг)', fontsize=12, color='white', weight='bold')
    ax.set_title(f'📈 {exercise_name} ({category})', fontsize=14, color='white', weight='bold', pad=20)
    
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    plt.xticks(rotation=45, color='white')
    plt.yticks(color='white')
    
    # Цвета элементов
    for spine in ax.spines.values():
        spine.set_color('white')
        spine.set_linewidth(2)
    
    ax.tick_params(colors='white')
    
    # Добавляем значения на точки
    for date, weight in zip(dates, weights):
        ax.annotate(f'{weight:.1f}', (date, weight), textcoords="offset points", 
                   xytext=(0,10), ha='center', color='#00ff41', fontweight='bold')
    
    plt.tight_layout()
    
    # Сохраняем в буфер
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
    
    ax.set_xlabel('Упражнение', fontsize=12, color='white', weight='bold')
    ax.set_ylabel('Текущий вес (кг)', fontsize=12, color='white', weight='bold')
    ax.set_title(f'📊 Сравнение: {category}', fontsize=14, color='white', weight='bold', pad=20)
    
    ax.set_xticks(range(len(exercise_names)))
    ax.set_xticklabels(exercise_names, rotation=45, ha='right', color='white')
    plt.yticks(color='white')
    
    ax.grid(True, alpha=0.2, axis='y', color='white')
    
    for spine in ax.spines.values():
        spine.set_color('white')
        spine.set_linewidth(2)
    
    # Значения на барах
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

# ============================================================================
# 🆕 ОТСЛЕЖИВАНИЕ ПОЛЬЗОВАТЕЛЕЙ
# ============================================================================

def update_user_visit(user_id, username=''):
    """Обновить последний визит пользователя"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    now = datetime.now().isoformat()
    
    # Проверяем есть ли уже пользователь
    cursor.execute('SELECT user_id FROM user_stats WHERE user_id = ?', (user_id,))
    exists = cursor.fetchone() is not None
    
    if exists:
        # Обновляем
        cursor.execute('''
            UPDATE user_stats 
            SET last_visit = ?, total_visits = total_visits + 1
            WHERE user_id = ?
        ''', (now, user_id))
    else:
        # Создаём новый рекорд
        cursor.execute('''
            INSERT INTO user_stats (user_id, username, last_visit, created_at, total_visits)
            VALUES (?, ?, ?, ?, 1)
        ''', (user_id, username, now, now))
    
    conn.commit()
    conn.close()

def get_user_last_visit(user_id):
    """Получить дату последнего визита пользователя"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT last_visit FROM user_stats WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return result[0]
    return None

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
    """Получить всех пользователей которые не заходили 5+ дней"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
    
    cursor.execute('''
        SELECT user_id, username, last_visit, created_at, total_visits, favorite_category
        FROM user_stats
        WHERE last_visit < ?
    ''', (cutoff_date,))
    
    inactive_users = cursor.fetchall()
    conn.close()
    
    return inactive_users

# ============================================================================
# ИНИЦИАЛИЗАЦИЯ
# ============================================================================

if __name__ == '__main__':
    create_tables()
    print("✅ Таблицы созданы успешно!")
