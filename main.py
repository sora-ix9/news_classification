from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from joblib import load
# import pandas as pd
import os
from random import choices
from math import floor
import http.client, urllib.parse
import json
import time

# Initial set-up for FastAPI
app = FastAPI()
app.mount('/', StaticFiles(directory='static', html=True), name='static')

# Initial set-up for the get_news() function
# pd.set_option('display.max_colwidth', 1000)
API_KEY = os.environ.get('MEDIASTACK_API_KEY')

def get_randNews(news_num, debug=False):
    news_cats = ['business', 'entertainment', 'health', 'science', 'sports', 'technology']
    '''
    nRand_news_cats = choices(news_cats, k=news_num)
    nRand_news_cats.sort() # Ascendingly sort the 'nRand_news_cats' in-place
    '''
    nRand_news_cats = ['business', 'entertainment', 'health']
    unique_cats = list(set(nRand_news_cats))
    unique_cat_num = len(unique_cats)
    parity_4_newsNumPerCat = news_num % unique_cat_num # 0 if parity_4_newsNumPerCat is even (otherwise, ie., odd case, an interger >= 1)
    
    if parity_4_newsNumPerCat == 0: # parity_4_newsNumPerCat is even
        newsNum_per_cat = news_num / unique_cat_num
    
    else: # parity_4_newsNumPerCat is odd
        cats_2_newsNum = {}

        for unique_cat in unique_cats:
            newsNum_per_cat = round(news_num / unique_cat_num)
            cats_2_newsNum[unique_cat] = newsNum_per_cat # Add new pair of the key and value to the dictionary (in this case, add unique category and its news number)

            # The below 'if' case would happend on the last unique category 
            if sum(cats_2_newsNum.values()) > news_num:
                newsNum_per_cat = floor(news_num / unique_cat_num)
                cats_2_newsNum[unique_cat] = newsNum_per_cat

    if debug:
        print('parity_4_newsNumPerCat =', parity_4_newsNumPerCat)

        if parity_4_newsNumPerCat == 0:
            print('newsNum_per_cat =', newsNum_per_cat)
        else:
            print('cats_2_newsNum =', cats_2_newsNum)

    '''
    for unique_cat in set(nRand_news_cats):

        url_params = urllib.parse.urlencode({
            'access_key': API_KEY,
            'limit': news_num,  # Maximum allowed limit value is 100 (See more on https://mediastack.com/documentation)
            'languages': 'en',
            'country': us,
        })

    return
    ''' 

'''
def classify_news():
    model = load('best_logit_clf2.joblib')

    return 
'''
    
'''
@app.get('/')
def index():
    return FileResponse('static\index.html')
'''
    
'''
@app.post('/searched_news'):
def searched_news():
    request_news()


    return
'''