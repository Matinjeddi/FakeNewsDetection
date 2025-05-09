from flask import Flask, request, render_template
import newsapi
from transformers import RobertaTokenizer, RobertaForSequenceClassification
import torch
import re

app = Flask(__name__)

news_api = newsapi.NewsApiClient(api_key=os.getenv('NEWS_API_KEY'))

model_path = 'models/fake-news-roberta'
tokenizer = RobertaTokenizer.from_pretrained(model_path)
model = RobertaForSequenceClassification.from_pretrained(model_path)

def get_news(query):
    all_articles = news_api.get_everything(q=query, language='en', sort_by='relevancy')
    articles = all_articles['articles']
    return articles

def predict_news(news):
    inputs = tokenizer(news, return_tensors='pt', padding=True, truncation=True)
    outputs = model(**inputs)
    predictions = torch.argmax(outputs.logits, dim=1)
    if predictions == 0:
        return 'Real News'
    elif predictions == 1:       
        return 'Fake News'
    
def preprocess_text(text):
    # Convert to lowercase
    text = text.lower()
    # Remove URLs
    text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
    # Remove special characters and digits
    text = re.sub(r'\W', ' ', text)
    text = re.sub(r'\d', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\n', ' ', text)
    # Remove extra whitespace
    text = ' '.join(text.split())
    return text

""" news_articles = get_news('usa')

first_article = news_articles[0]

news_description = first_article['description']

news_title = first_article['title']

full_news = news_title + ' ' + news_description + ' ' + first_article['content']

full_news = preprocess_text(full_news) """

news_example = """UK to announce fresh sanctions on Putin's 'shadow fleet'

Havariekommando A black and white oil tanker, suspected of being part of Russia's 'shadow fleet', sails on the ocean. Havariekommando
Germany seized and confiscated the Eventin tanker it believed to be part of Russia's 'shadow fleet'
A fleet of Russian oil tankers which have been used to avoid existing sanctions on oil and gas exports are set to be hit with new restrictions.

Downing Street has said action will be taken against up to 100 vessels which have carried more than £18 billion worth of cargo since the start of 2024.

Sir Keir Starmer is due to make the announcement at a summit of north European leaders known as the Joint Expeditionary Force (JEF) in Oslo, Norway.

The PM has vowed the UK will do everything in its power to "destroy" Russian President Vladimir Putin's "shadow fleet operation, starve his war machine of oil revenues and protect the subsea infrastructure".

Following Russia's invasion of Ukraine in 2022, many western countries imposed sanctions on Russian energy, by limiting imports and capping the price of its oil.

To get round these penalties, Moscow built up what has been referred to as a "shadow fleet" of tankers whose ownership and movements could be obscured.

Downing Street has accused the operation of "bankrolling the Kremlin's illegal war in Ukraine".

The government has referred to the ships as being "decrepit and dangerous" as well as being responsible for "reckless seafaring". It follows reports of damage to a major undersea cable in the Baltic Sea.

Under the measures, the sanctioned tankers will be banned from British ports and risk being detained in UK waters.

Starmer said every step that increases pressure on Moscow and works towards peace for Ukraine "is another step towards security and prosperity in the UK".

The JEF consists of ten nations including Denmark, Norway and the Netherlands.

Members of the JEF are also expected to announce further support for Ukraine's war efforts.

The UK previously imposed sanctions against 133 "shadow" vessels during a meeting of the JEF in December 2024."""
""" 
news_example = preprocess_text(news_example)

prediction = predict_news(news_example) """
""" 
print(news_example)
print(prediction) """

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/news')
def news():
    news_articles = get_news('usa')
    return render_template('news.html', news_articles=news_articles)

@app.route('/predict', methods=['GET', 'POST'])
def predict():
    if request.method == 'POST':
        news = request.form['news']
        news = preprocess_text(news)
        prediction = predict_news(news)
        return render_template('predict.html', prediction=prediction)
    return render_template('predict.html')

@app.route('/statistics')
def statistics():
    return render_template('statistics.html')

if __name__ == '__main__':
    app.run(debug=True)




















