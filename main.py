from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from datetime import date, timedelta
import random
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'musornyy_kvest_secret_2026'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quest.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ====================== МОДЕЛИ ======================
class Streak(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    last_date = db.Column(db.Date)
    current_streak = db.Column(db.Integer, default=0)

class DailyTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(200), nullable=False)

class UserStats(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    total_score = db.Column(db.Integer, default=0)
    trash_collected = db.Column(db.Integer, default=0)
    upcycled_count = db.Column(db.Integer, default=0)
    games_played = db.Column(db.Integer, default=0)

# ====================== ИНИЦИАЛИЗАЦИЯ ======================
with app.app_context():
    db.create_all()
    
    # Добавляем ежедневные задания
    if not DailyTask.query.first():
        tasks = [
            "Собрать 10 окурков за прогулку",
            "Отказаться от одноразового пластика на весь день",
            "Сортировать весь мусор дома за 5 минут",
            "Собрать мусор на улице 5 минут",
            "Сделать органайзер из старой бутылки (апсайклинг)",
            "Провести матч-3 с мусором в игре"
        ]
        for t in tasks:
            db.session.add(DailyTask(description=t))
        db.session.commit()
    
    # Создаём стрик если нет
    if not Streak.query.first():
        db.session.add(Streak(last_date=date.today() - timedelta(days=1), current_streak=0))
        db.session.commit()
    
    # Создаём статистику пользователя если нет
    if not UserStats.query.first():
        db.session.add(UserStats())
        db.session.commit()

# ====================== МАРШРУТЫ ======================
@app.route('/')
def index():
    return app.send_static_file('index.html')  # раздаём HTML из папки static/

@app.route('/api/streak', methods=['GET', 'POST'])
def api_streak():
    streak = Streak.query.first()
    today = date.today()
    
    if request.method == 'POST':
        if streak.last_date != today:
            if streak.last_date == today - timedelta(days=1):
                streak.current_streak += 1
            else:
                streak.current_streak = 1
            streak.last_date = today
            db.session.commit()
    
    return jsonify({
        'streak': streak.current_streak,
        'last_date': streak.last_date.strftime('%Y-%m-%d')
    })

@app.route('/api/dice')
def api_dice():
    task = random.choice(DailyTask.query.all())
    return jsonify({'task': task.description})

@app.route('/api/stats', methods=['GET'])
def api_stats():
    stats = UserStats.query.first()
    return jsonify({
        'total_score': stats.total_score,
        'trash_collected': stats.trash_collected,
        'upcycled_count': stats.upcycled_count,
        'games_played': stats.games_played
    })

@app.route('/api/game/end', methods=['POST'])
def api_game_end():
    data = request.get_json()
    game_score = data.get('score', 0)
    trash_sorted = data.get('trash_sorted', 0)

    stats = UserStats.query.first()
    stats.total_score += game_score
    stats.trash_collected += trash_sorted
    stats.games_played += 1
    db.session.commit()

    return jsonify({
        'total_score': stats.total_score,
        'trash_collected': stats.trash_collected,
        'games_played': stats.games_played,
        'message': f'Игра завершена! +{game_score} очков'
    })

@app.route('/api/upcycle', methods=['POST'])
def api_upcycle():
    stats = UserStats.query.first()
    stats.upcycled_count += 1
    stats.total_score += 50
    db.session.commit()
    return jsonify({
        'upcycled_count': stats.upcycled_count,
        'total_score': stats.total_score,
        'message': 'Апсайклинг выполнен! +50 очков'
    })

# ====================== ЗАПУСК ======================
if __name__ == '__main__':
    print("🚀 Мусорный Квест запущен на http://127.0.0.1:5000")
    print("   Соревнования, челленджи, стрики, кубик и игра готовы!")
    app.run(debug=True)