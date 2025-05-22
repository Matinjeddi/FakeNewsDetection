from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class News(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False, default=datetime.now)
    url = db.Column(db.String(255), nullable=False)
    prediction = db.Column(db.String(12), nullable=False)
    confidence = db.Column(db.String(12), nullable=False)
    title = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return f"News(id={self.id}, date={self.date}, url={self.url}, prediction={self.prediction}, confidence={self.confidence}, title={self.title})"
    
    @staticmethod
    def get_news():
        return News.query.all()
    
    @staticmethod
    def set_news(url, prediction, confidence, title):
        news = News(url=url, prediction=prediction, confidence=confidence, title=title)
        db.session.add(news)
        db.session.commit()
        print(f"News item added: {news}")
    

