# -*- coding: utf-8 -*-
"""Classification-and-Sentiment.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1EmvGxQzBjCnq5FKXCU4CAGMBwf-ARk_5
"""

import pandas as pd
import re
import nltk
import numpy as np
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.multiclass import OneVsRestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.naive_bayes import MultinomialNB

from transformers import AutoModelForSequenceClassification, AutoTokenizer
from scipy.special import softmax
import urllib.request
import csv
import torch

# Download required NLTK resources
nltk.download('stopwords')
nltk.download('wordnet')
nltk.download('punkt')

# Load dataset
dataset = pd.read_csv("labelled.csv")
dataset['CategoryId'] = dataset['Category'].factorize()[0]
category_mapping = dict(zip(dataset['CategoryId'], dataset['Category']))

# Preprocessing function
def preprocess_text(text):
    text = re.sub(r'<[^>]+>', '', text)  # Remove HTML tags
    text = ''.join([x if x.isalnum() else ' ' for x in text])  # Remove special characters
    text = text.lower()  # Convert to lowercase
    stop_words = set(stopwords.words('english'))
    words = word_tokenize(text)
    words = [word for word in words if word not in stop_words]  # Remove stopwords
    lemmatizer = WordNetLemmatizer()
    return " ".join([lemmatizer.lemmatize(word) for word in words])  # Lemmatization

nltk.download('punkt_tab')

# Preprocess the 'Body' column
dataset['Body'] = dataset['Body'].apply(preprocess_text)

# Prepare data for classification model
x = np.array(dataset['Body'])
y = np.array(dataset['CategoryId'])

cv = CountVectorizer(max_features=5000)
x = cv.fit_transform(x).toarray()

x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.3, random_state=0, shuffle=True)

models = {
    'Logistic Regression': LogisticRegression(),
    'Random Forest': RandomForestClassifier(n_estimators=100, criterion='entropy', random_state=0),
    'Multinomial Naive Bayes': MultinomialNB(),
}

trained_models = {}
for model_name, model in models.items():
    oneVsRest = OneVsRestClassifier(model)
    oneVsRest.fit(x_train, y_train)
    trained_models[model_name] = oneVsRest

# Load sentiment analysis model
task = 'sentiment'
MODEL = f"cardiffnlp/twitter-roberta-base-{task}"
tokenizer = AutoTokenizer.from_pretrained(MODEL)
sentiment_model = AutoModelForSequenceClassification.from_pretrained(MODEL)

# Load sentiment labels
labels = []
mapping_link = f"https://raw.githubusercontent.com/cardiffnlp/tweeteval/main/datasets/{task}/mapping.txt"
with urllib.request.urlopen(mapping_link) as f:
    html = f.read().decode('utf-8').split("\n")
    csvreader = csv.reader(html, delimiter='\t')
    labels = [row[1] for row in csvreader if len(row) > 1]

def sentiment_analysis(text):
    text = text[:1500]
    encoded_input = tokenizer(text, return_tensors='pt')
    with torch.no_grad():
        output = sentiment_model(**encoded_input)
    scores = output[0][0].cpu().numpy()
    scores = softmax(scores)
    max_index = np.argmax(scores)
    return labels[max_index]

def predict_category_and_sentiment(user_input):
    # Classification prediction
    processed_input = preprocess_text(user_input)
    input_vector = cv.transform([processed_input]).toarray()
    category_predictions = {
        model_name: category_mapping[model.predict(input_vector)[0]]
        for model_name, model in trained_models.items()
    }

    # Sentiment prediction
    sentiment_result = sentiment_analysis(user_input)

    return category_predictions, sentiment_result

# Main loop
if __name__ == "__main__":
    while True:
        user_input = input("Enter text to classify and analyze sentiment (or type '-1' to quit): ")
        if user_input == '-1':
            print("Exiting program.")
            break

        category_predictions, sentiment_result = predict_category_and_sentiment(user_input)

        print("\nCategory Predictions:")
        for model_name, category in category_predictions.items():
            print(f"{model_name}: {category}")

        print(f"\nSentiment Analysis Result: {sentiment_result}\n")





