from typing import Annotated
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from joblib import load
import sklearn
import os
from random import choice, choices
from ordered_set import OrderedSet
import http.client, urllib.parse
import json
import time

# Initial set-up for rest api using FastAPI
app = FastAPI()
app.mount('/static', StaticFiles(directory='static', html=True), name='static')
templates = Jinja2Templates(directory='templates')

# Initial set-up for the get_news() function
API_KEY = os.environ.get('MEDIASTACK_API_KEY')

def get_cats_2_NewsNums(news_num, unique_cats, debug=False):
    '''Determine equal number used to get news for every unique category'''
    
    cats_2_NewsNums = {unique_cat: 0 for unique_cat in unique_cats}
    unique_cat_num = len(unique_cats)
    parity_4_newsNumPerCat = news_num % unique_cat_num # 0 if parity_4_newsNumPerCat is even (otherwise, ie., odd case, an interger >= 1)  
    
    if parity_4_newsNumPerCat == 0: # parity_4_newsNumPerCat is even
        
        for cat_key in cats_2_NewsNums:
            cats_2_NewsNums[cat_key] = news_num / unique_cat_num

    else: # parity_4_newsNumPerCat is odd

        for cat_key in cats_2_NewsNums:
            newsNum_per_cat = round(news_num / unique_cat_num)
            cats_2_NewsNums[cat_key] = newsNum_per_cat # Add new pair of the key and value to the dictionary (in this case, add unique category and its news number)

            # The below 'if' case would happend on the last unique category 
            if (cat_key == unique_cats[-1]) and (sum(cats_2_NewsNums.values()) != news_num):
                
                lastExclude_newsNum_sum = sum(list(cats_2_NewsNums.values())[0: -1]) # 'lastExclude_newsNum_sum' is sum of all news numbers excluding the last one.
                newsNum_per_cat = news_num - lastExclude_newsNum_sum
                
                # Swap between the tail (the last number of the last unique category) and the value of the random key  for more natural order of all news number
                swap_target_key = choice(list(cats_2_NewsNums))

                if debug:
                    print('swap_target_key =', swap_target_key)
                    print('cats_2_NewsNums (before swapping) =', cats_2_NewsNums)
                
                cats_2_NewsNums[cat_key] = cats_2_NewsNums[swap_target_key] # At this line, unique_cat stores the last unique category, so this line expression equals moving the swapped-target value to the last location.
                cats_2_NewsNums[swap_target_key] = newsNum_per_cat

    return cats_2_NewsNums
            

def get_randNews(news_num, debug=False):
    news_cats = ['business', 'entertainment', 'health', 'science', 'sports', 'technology']
    nRand_news_cats = choices(news_cats, k=news_num)
    nRand_news_cats.sort() # Ascendingly sort the 'nRand_news_cats' in-place
    unique_cats = list(OrderedSet(nRand_news_cats))
    randNews_lst = []
    errors = [] # For later logging/debugging
    json_res_lst = [] # For later logging/debugging

    # Determine equal number used to get news for every unique category
    cats_2_newsNums = get_cats_2_NewsNums(news_num, unique_cats)

    # Requesting news
    unique_cat_ind = 0
    unique_cat_num = len(unique_cats)
    last_unique_cat = unique_cats[-1]
    curNewsAPI_sent_num = unique_cat_num
    while unique_cat_ind < unique_cat_num:
        unique_cat = unique_cats[unique_cat_ind]
        request_news_num = cats_2_newsNums[unique_cat]
        url_params = urllib.parse.urlencode({
            'access_key': API_KEY,
            'limit': request_news_num,  # Maximum allowed limit value is 100 (See more on https://mediastack.com/documentation)
            'categories': unique_cat,
            'languages': 'en',
            'country': 'us',
        })

        try:
            conn = http.client.HTTPConnection('api.mediastack.com')
            conn.request('GET', '/v1/news?{}'.format(url_params))
            res = conn.getresponse()
            json_res_bytes = res.read() # The 'json_res_bytes' has rough structure like {'pagination': ..., 'data', [{'author': ..., ..., 'published_at': ...}, ..., {'author': ..., ..., 'published_at': ...}]}.  
            json_res_str = json_res_bytes.decode('utf-8')
            json_res = json.loads(json_res_str)

            json_res_lst.append(json_res)
            if 'data' in json_res:
                json_news = json_res['data']
                # randNews_lst.extend(json_res['data']) # 'randNews_lst' stores all request news and would roughly has structure like [{'author': ..., ..., 'published_at': ...}, ..., {'author': ..., ..., 'published_at': ...}].

                for news in json_news:
                    randNews_lst.append({
                        'news': (news['title'] + '. ' + news['description']).replace('&nbsp;', ' '),
                        'auctual_category': news['category'], 
                        'predicted_category': None,
                        }) # 'randNews_lst' stores dictionaries of all news, where each has structure like this {'news': ..., 'auctual_category': ..., 'predicted_category': None}
            if 'error' in json_res:
                errors.extend(json_res['error'])

        except Exception as e:
            print('Failed on_status,', str(e))
            time.sleep(3)
                    
            continue

        # Section that is responsible for requerying unrecieved news
        if (unique_cat == last_unique_cat) and (len(randNews_lst) != news_num):

            for news in randNews_lst:
                print('news =', news)
                cat_key = news['auctual_category']
                cats_2_newsNums[cat_key] -= 1 # Decrease the number of the already recieved news 1 by 1

                # If any category already recieved all news, then remove the category out from the 'unique_cats' and 'cats_2_newsNums' variables. 
                if cats_2_newsNums[cat_key] == 0:
                    unique_cats.remove(cat_key)
                    cats_2_newsNums.pop(cat_key)
                
            unique_cat_ind = 0
            unique_cat_num = len(unique_cats)
            print('unique_cats =', unique_cats)
            continue

        unique_cat_ind += 1

    if debug:
        print('-------------- Debug --------------------')
        print('cats_2_newsNums =', cats_2_newsNums)

        print('len(randNews_lst) =', len(randNews_lst))
        print('randNews_lst =', randNews_lst)

        if len(randNews_lst) != news_num:
            print('json_res_lst =', json_res_lst)

        if len(errors) != 0:
            print('json_res_lst =', json_res_lst, '\n')
            print('errors =', errors)

        print('----------------------------------------')

    return randNews_lst, curNewsAPI_sent_num # Return 'curNewsAPI_sent_num' for tracking the available count of news API request left for calling in future. 

def classify_news(randNews_lst):
    tfidf_transformer = load('ml_model_building/tfidf_transformer.joblib')
    label_encoder = load('ml_model_building/label_encoder.joblib')
    model = load('ml_model_building/best_logit_clf2.joblib')
    news_lst = [news_dct['news'] for news_dct in randNews_lst]
    
    prep_data = tfidf_transformer.transform(news_lst)
    preds = model.predict(prep_data)

    for ind in range(len(preds)):
        pred_cat = label_encoder.classes_[preds[ind]]
        randNews_lst[ind]['predicted_category'] = pred_cat

    return randNews_lst
    
@app.get('/', response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(request=request, name='index.html')

@app.post('/classified_news', response_class=HTMLResponse)
def classified_news(request: Request, news_num: Annotated[str, Form()]):
    news_num = int(news_num)
    randNews_lst, curNewsAPI_sent_num = get_randNews(news_num) # 'randNews_lst' stores dictionaries of all news, where each has structure like this {'news': ..., 'auctual_category': ..., 'predicted_category': None}
    classified_news_lst = classify_news(randNews_lst) # From this line, each news dictionary in 'classified_news_lst' would finally have the actual value at the 'predicted_category' key which is unequivalent to the None value.

    # Tracking available count for news API request (read and write it)
    with open('logs/newsAPI_req_count.txt', 'r') as newsAPI_reqCount_f1:
        newsAPI_reqCount_str1 = newsAPI_reqCount_f1.read() # E.g., newsAPI_reqCount_str1 looks like 'MEDIASTACK_API_KEY: 044' etc.
        newsAPI_req_count = int(newsAPI_reqCount_str1[20: ]) + curNewsAPI_sent_num 
        newsAPI_reqCount_str2 = newsAPI_reqCount_str1[0: 20] + str(newsAPI_req_count).zfill(3)

        newsAPI_reqCount_f2 = open('logs/newsAPI_req_count.txt', 'w')
        newsAPI_reqCount_f2.write(newsAPI_reqCount_str2)
        print('newsAPI_req_count =', newsAPI_req_count)

    return templates.TemplateResponse(request=request, name='classified_news.html', context={'classified_news': classified_news_lst})