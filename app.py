from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mydatabase.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)

class Visit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    count = db.Column(db.Integer, default=0)

@app.route('/')
def home():
    visit = Visit.query.first()
    visit.count += 1
    db.session.commit()
    return render_template('index.html', count=visit.count)

@app.route('/my_ai')
def ai():
    return render_template('my_ai.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
