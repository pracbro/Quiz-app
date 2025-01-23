from flask import Flask, render_template, request, url_for, g, redirect, session
from database import get_db
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__, static_folder='static')
app.config['SECRET_KEY'] = os.urandom(24)

@app.teardown_appcontext
def close_db(error):

    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()

def get_current_user():

    user_result = None

    if 'user' in session:
        user = session['user']
        user_name = user['name']

        db = get_db()
        user_cur = db.execute('select id, name, password, admin from users where name = ?', [user_name])
        user_result = user_cur.fetchone()

    return user_result

@app.route('/', methods=['GET', 'POST'])
def index(): 
    if 'user' not in session:
        return redirect(url_for('login'))
    
    user = get_current_user()
    cats = fetch_categories()
    leaderboard_d = []
    sel_cat = request.args.get('category_name')
    
    if sel_cat:
        leaderboard_d = get_top_medians(sel_cat)
    
    return render_template('home.html', user=user, leaderboard_d=leaderboard_d, sel_cat=sel_cat, categories=cats)

@app.route('/register', methods=['GET', 'POST'])
def register():

    user = get_current_user()
    if request.method == 'POST':
        db = get_db()
        #same usersname already exists or not 
        existing_user_cur = db.execute('select id from users where name = ?', [request.form['name']])
        existing_user = existing_user_cur.fetchone()
        if existing_user:
            return render_template('register.html', user = user, error = 'Username already taken, Try different username.')

        hashed_password = generate_password_hash(request.form['password'], method='pbkdf2:sha256')
        db.execute('insert into users (name, password, admin) values (?, ?, ?)', [request.form['name'], hashed_password, '0'])
        db.commit()
        session['user']['name'] = request.form['name']
        return redirect(url_for('index'))
    return render_template('register.html', user=user)

@app.route('/login', methods=['GET', 'POST'])
def login():

    user = get_current_user()
    error = None
    if request.method == 'POST':
        db = get_db()
        name = request.form['name']
        password = request.form['password']
        user_cur = db.execute('select id, name, password from users where name = ?', [name])
        user_result = user_cur.fetchone()

        if user_result:
            if check_password_hash(user_result['password'], password):
                session['user'] = {'id': user_result['id'], 'name': user_result['name']}
                return redirect(url_for('index'))
            else:
                error = 'Username or password did not match. Try again.'
    # else:
    #     pass
    #     # error = 'Username or password did not match. Try again.'
    return render_template('login.html', user=user , error = error)

@app.route('/logout')
def logout():

    session.pop('user', None)
    return redirect(url_for('index'))

from quiz import fetch_categories, fetch_quiz_data

@app.route('/categories')
def categories():

    #call the api to fetch categories from quiz py
    categories = fetch_categories()
    return render_template('categories.html', categories=categories)

@app.route('/quiz/<category_name>')
def quiz_by_category(category_name):
    quiz_data = fetch_quiz_data(category_name)
    session['category'] = {'name': category_name, 'quiz_d': quiz_data}
    print("Quiz Data Stored in Session:", quiz_data)
    return render_template('quiz.html', questions=quiz_data)

#REMAINING: FOR MULTIPLE CORRECT ANSWER WRITE LOGIC 

@app.route('/submit', methods=['POST'])
def submit():

    score = 0
    category = session.get('category', [])
    quiz_data = category['quiz_d'] #if it doesnt exist, returns a [] nstead of error
    total_q = len(quiz_data)
    for q in quiz_data:
        user_answer = request.form.get(str(q['id']))
        print(f'Question ID: {q["id"]}, User Answer: {user_answer}, Correct Answer: {q["correct_answer"]}')
        if user_answer == q['correct_answer']:
            score += 1

    user = session.get('user')
    category = session.get('category')
    db = get_db()
    if user:
        db.execute('insert into leaderboard (user_id, score, total_questions, category) VALUES (?, ?, ?, ?)', (user['id'], score, total_q, category['name']))
        #date defualt value is current timestamp so no need to pass
        db.commit()

    session.pop('category', None)
    return f'Your score: {score}/{total_q}'

def get_top_medians(category, top_n=3):
    db = get_db()

    scores_d = db.execute(
        'select user_id, score, total_questions from leaderboard where category = ? order by user_id, score',(category,)).fetchall()

    from statistics import median

    percent_d = {}
    for row in scores_d:
        user_id = row['user_id']
        percent_score = (row['score'] / row['total_questions']) * 100
        if user_id not in percent_d:
            percent_d[user_id] = []
        percent_d[user_id].append(percent_score)

    avg_percent_score = {
        user_id: sum(scores) / len(scores) for user_id, scores in percent_d.items()
    }

    top_users = sorted(avg_percent_score.items(), key=lambda x: x[1], reverse=True)[:top_n]
    print(top_users)
    return top_users

# @app.route('/leaderboard', methods=['GET'])
# def leaderboard():
#     cats = fetch_categories()
#     leaderboard_d = []
#     sel_cat = request.args.get('category_name')
    
#     if sel_cat:
#         leaderboard_d = get_top_medians(sel_cat)


# ... existing code ...

@app.route('/leaderboard')
def leaderboard():
    return render_template('leaderboard.html')

# ... rest of your code ...

if __name__ == '__main__':
    app.run(debug=True)