from flask import Flask, request, render_template, redirect, url_for, session
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from utils import *
from models import *
from flask_sqlalchemy import SQLAlchemy
from flask_paginate import Pagination, get_page_parameter
from flask_migrate import Migrate
import re
import sys
import atexit
import signal 

app = Flask(__name__)
app.secret_key = 'CaKaBaSa'

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:root@localhost/fake_newsd'
db.init_app(app)  # Initialize db with app

migrate = Migrate(app, db)
migrate.init_app(app, db)
# Create tables
with app.app_context():
    db.create_all()


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/news', methods=['GET', 'POST'])
def news():
    per_page = 10
    page = int(request.args.get('page', 1))
    
    # Get search parameters from either POST or GET
    if request.method == 'POST':
        query = request.form.get('query')
        sort_by = request.form.get('sort_by')
        # Store in session for pagination
        session['news_query'] = query
        session['news_sort_by'] = sort_by
        # redirect to the news page with the new query and sort_by
        return redirect(url_for('news', page=1, query=query, sort_by=sort_by))

    query = session.get('news_query', 'world')
    sort_by = session.get('news_sort_by', 'relevancy')
    
    # Get news articles
    news_articles = get_news(query, sort_by)
    
    # Calculate pagination
    total = len(news_articles)
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    paginated_articles = news_articles[start_idx:end_idx]
    
    # Create pagination object
    pagination = {
        'has_next': end_idx < total,
        'has_prev': page > 1,
        'next_num': page + 1,
        'prev_num': page - 1,
        'pages': (total + per_page - 1) // per_page,
        'current_page': page
    }
    
    return render_template('news.html', 
                         news_articles=paginated_articles,
                         pagination=pagination,
                         page=page,
                         current_query=query,
                         current_sort=sort_by)

@app.route('/fetch_article', methods=['POST'])
def fetch_article():
    url = request.form.get('article_url')
    article_text = ''
    if url:
        try:
            if not is_scraping_allowed(url) or not is_paywall(url):
                article_text = 'Scraping is not allowed for this URL or it is a paywall.'
            else:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                response = requests.get(url, headers=headers, timeout=10)
                response.encoding = 'utf-8'
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Remove unwanted elements including author information
                for element in soup.find_all(['script', 'style', 'nav', 'header', 'footer', 'aside', 'form', 'button', 'input', 'select', 'iframe', 
                                            'meta', 'link', 'author', 'span', 'div'], 
                                           class_=re.compile(r'author|byline|writer|reporter|contributor|credit', re.I)):
                    element.decompose()
                
                # Try to find the main article content
                article = soup.find('article') or soup.find('main') or soup.find('div', class_=re.compile(r'article|content|post|entry', re.I))
                
                if article:
                    # Get only paragraphs from the article
                    paragraphs = article.find_all('p')
                    
                    # Filter and clean paragraphs
                    cleaned_paragraphs = []
                    for p in paragraphs:
                        text = p.get_text(strip=True)
                        # Skip empty paragraphs, very short ones, and author information
                        if len(text) > 20 and not re.search(r'by\s+\w+\s+\w+|\w+\s+\w+\s+reports|\w+\s+\w+\s+writes', text, re.I):
                            # Clean the text
                            text = re.sub(r'\s+', ' ', text)  # Replace multiple spaces with single space
                            text = text.strip()
                            cleaned_paragraphs.append(text)
                    
                    # Join paragraphs with double newlines
                    article_text = '\n\n'.join(cleaned_paragraphs)

                # If no content was found, return a message
                if not article_text:
                    article_text = 'Could not extract article content. The article might be behind a paywall or the content structure is not recognized.'
                
        except Exception as e:
            print(f'Error fetching article: {e}')
            article_text = 'Could not fetch article text. Please check the URL and try again.'
        
        session['prefill_news'] = article_text
        session['prefill_url'] = url
    return redirect(url_for('predict'))

@app.route('/predict', methods=['GET', 'POST'])
def predict():
    prefill_news = session.pop('prefill_news', '')
    prefill_url = session.pop('prefill_url', '')
    if request.method == 'POST':
        news = request.form['news']
        url = request.form.get('news_url', '')
        news_preprocessed = preprocess_text(news)
        prediction = predict_news(news_preprocessed)
        confidence = f"{predict_confidence(news_preprocessed):.2f}%"
        news_item = News(url=url, prediction=prediction, confidence=confidence)
        db.session.add(news_item)
        db.session.commit()
        print(f"News item added: {news_item}")
        return render_template('predict.html', prediction=prediction, confidence=confidence)
    return render_template('predict.html', prefill_news=prefill_news, prefill_url=prefill_url)

@app.route('/statistics')
def statistics():
    per_page = 10
    page = int(request.args.get('page', 1))
    predictions = News.get_news()
    paginationObject = News.query.order_by(News.date.desc()).paginate(page=page, per_page=per_page, error_out=False)
    mean_confidence = calculate_mean_confidence(predictions)
    # Count predictions
    true_count = sum(1 for p in predictions if p.prediction.lower() == 'real news')
    false_count = sum(1 for p in predictions if p.prediction.lower() == 'fake news')
    return render_template(
        'statistics.html',
        predictions=predictions,
        mean_confidence=mean_confidence,
        true_count=true_count,
        false_count=false_count,
        pagination=paginationObject,
        page=page,
        has_next=paginationObject.has_next,
        has_prev=paginationObject.has_prev,
        per_page=per_page
    )

@app.route('/about')
def about():
    return render_template('about.html')


def signal_handler(sig, frame):
    print('Shutting down gracefully...')
    sys.exit(0)


if __name__ == '__main__':
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Register cleanup function
    atexit.register(lambda: print('Cleaning up...'))
    
    app.run(debug=True)