import pandas as pd                        
from pytrends.request import TrendReq
pytrend = TrendReq()
import regex as re
from collections import Counter
from bs4 import BeautifulSoup
from lxml import etree
import requests
import tweepy as tp
from datetime import datetime, timedelta
import streamlit as st
from warnings import filterwarnings
filterwarnings("ignore")

bearerToken = "AAAAAAAAAAAAAAAAAAAAAOUBZwEAAAAAuSI9Lk9VJF5p8oZ60%2Ffnb25FSXo%3DsH2SwTWEqpQOe0acAUZeAiPdazuwZYetImYMSn9Wzk7dmXR1VV"

client = tp.Client(bearer_token=bearerToken, wait_on_rate_limit=True)

def convertDate(tweetObject):
    tweetDate = tweetObject['created_at']
    tweetDate = tweetDate.replace("T", " ")
    tweetDate = str(tweetDate.split(".")[0])
    tweetDate = datetime.strptime(tweetDate, '%Y-%m-%d %H:%M:%S')
    return(tweetDate)



def convertTime(inputDate):

    inputDateSplit = inputDate.split("-")

    year = int(inputDateSplit[0])
    month = int(inputDateSplit[1])
    day = int(inputDateSplit[2])

    if month < 10 and day < 10:
        timeString = f"{year}-0{month}-0{day}T00:00:00Z"
        return timeString
    elif month < 10 and day >= 10:
        timeString = f"{year}-0{month}-{day}T00:00:00Z"
        return timeString
    elif month >= 10 and day < 10:
        timeString = f"{year}-{month}-0{day}T00:00:00Z"
        return timeString
    else:
        timeString = f"{year}-{month}-{day}T00:00:00Z"
        return timeString

def generateTweets(date, df, brand):

    tweets = client.search_recent_tweets(query=f"{brand} -is:retweet lang:EN", tweet_fields=['context_annotations', 'created_at', 'text', 'author_id', 'source', 'public_metrics'], max_results=100, end_time=date)
        
    for tweet in tweets.data:
        tweet_ID = tweet.id
        tweet_content = tweet.text
        tweet_date = tweet.created_at
        tweet_retweets = tweet.public_metrics['retweet_count']
        tweet_replies = tweet.public_metrics['reply_count']
        tweet_likes = tweet.public_metrics['like_count']
        tweet_quotes = tweet.public_metrics['quote_count']

        df = df.append({'id': str(tweet_ID), 'full_text':str(tweet_content), 'created_at':tweet_date,  \
                'rt_count':tweet_retweets, 're_count':tweet_replies, 'like_count':tweet_likes, 'quotes':tweet_quotes}, ignore_index=True)


    return df

def filterItems(topTenList):
    filteredItems = []
    for item in topTenList:
    # itemToTest = topTenList[1]
        pytrend.build_payload([item], timeframe='today 1-m')
        relatedTopics = pytrend.related_topics()
        try:
            relatedTopicList = list(relatedTopics[item]['top']['topic_type'][:5])
            relatedTopicList = [x.lower() for x in relatedTopicList]
            if "food" in relatedTopicList or "drink" in relatedTopicList or "beverage" in relatedTopicList:
                filteredItems.append(item)
        except Exception as e:
            # print(e, item)
            None

    return filteredItems


def generateDF(phrase):
    df = pd.DataFrame(columns=['id', 'full_text', 'created_at', 'rt_count', 're_count', 'like_count', 'quotes'])

    
    for i in range(6):
        date = convertTime((datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d"))
        
        df = generateTweets(date, df, phrase)

    df.drop_duplicates(subset="id", inplace=True)

    regexStart = str(phrase.split(" ")[-1])
    regexStart = regexStart.replace('"', '')

    df["trending_product"] = "null"
    for a, tweet in enumerate(df.full_text):
        regex = re.search(fr'{regexStart}(..*)', tweet)
        try:
            df["trending_product"][a] = regex.group(1)
        except AttributeError:
            df["trending_product"][a] = regex

    
    df['trending_product'] = df['trending_product'].apply(lambda x: " ".join(str(x).split(" ")[1:3]))
    df = df[df.trending_product.str.len() > 3]
    df['trending_product'] = df['trending_product'].apply(lambda x: str(x).lower())
    df['trending_product'] = df['trending_product'].apply(lambda x: str(x).replace("@", ""))

    return df

def generateTopTen(productList):

    topTen = Counter(productList).most_common(20)

    topTenList = []
    for item in topTen:
        if item != "null":
            topTenList.append(item[0])

    return(topTenList)

def googleTrendTopics(topList):
    filteredItems = []
    for item in topList:
    # itemToTest = topTenList[1]
        pytrend.build_payload([item], timeframe='today 1-m')
        relatedTopics = pytrend.related_topics()
        try:
            relatedTopicList = list(relatedTopics[item]['top']['topic_type'][:5])
            relatedTopicListLower = [x.lower() for x in relatedTopicList]
            relatedTopicListLower = list(relatedTopicListLower)
            if "food" in relatedTopicListLower or "drink" in relatedTopicListLower or "beverage" in relatedTopicListLower:
                filteredItems.append(item)
        except Exception as e:
            # print(e, item)
            None

    return(filteredItems)


def generateNews(brandName):
    urlBrandName = "+".join(brandName.split(" "))

    URL = f"https://news.google.com/search?q={urlBrandName}&hl=en-US&gl=US&ceid=US:en"
    
    HEADERS = ({'User-Agent':
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 \
                (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36',\
                'Accept-Language': 'en-US, en;q=0.5'})
    
    webpage = requests.get(URL, headers=HEADERS)
    soup = BeautifulSoup(webpage.content, "html.parser")
    news = soup.find_all("a", class_="DY5T1d")

    for article in news:
        regex = r"href=\".(..*)\""

        articleText = article.text.lower()
        articleText = articleText.replace("'s", "")
        if brandName in articleText or "-".join(brandName.split(" ")) in articleText:
            # print(article.text.lower())
            url = re.findall(regex, str(article), re.MULTILINE)[0]
            return(articleText, url)


def generateTrendingProducts(useCustomDF=False, df1=None, df2=None):

    productList = []
    phrases = ['"tried the new"', '"has anyone tried"']

    if useCustomDF == False:
        for phrase in phrases:

            df_phrase = generateDF(phrase)
            productList = productList + list(df_phrase.trending_product)

    else:
        productList = list(df1.trending_product) + list(df2.trending_product)


    topTenList = generateTopTen(productList)

    filteredList = googleTrendTopics(topTenList)
    trendingArticleNames = []
    trendingURLNames = []
    for item in filteredList:
        try:
            trendingText, trendingURL = generateNews(item)
            trendingArticleNames.append(trendingText)

            newsUrl = f"https://news.google.com{trendingURL}"
            r = requests.get(newsUrl, allow_redirects=False)
            urlFix = r.headers['Location']
            r2 = requests.get(urlFix, allow_redirects=False)

            trendingURLNames.append(r2.headers['Location'])
        except:
            None

    return(trendingArticleNames, trendingURLNames)


    
# @st.cache
def app():
    page_title = f'<p style="font-family:Muro; color:White; font-size: 35px; text-decoration:underline;text-decoration-color:Orange;">Trend analyzer</p>'
    st.markdown(page_title,unsafe_allow_html=True)

    DF1 = pd.read_excel("data/tried_new_20.05.xlsx", engine="openpyxl", index_col=[0])
    DF2 = pd.read_excel("data/tried_anyone_20.05.xlsx", engine="openpyxl", index_col=[0])


    text_description = """On this page the exploratory nature of the thesis is presented. Press the button below, and our backend will
    scrape for tweets with the goal of locating upcoming trends."""
    page_description = f'<p style="font-family:Raleway, sans-serif; color:White; font-size: 15px;">{text_description}</p>'
    st.markdown(page_description,unsafe_allow_html=True)
    st.write("Clicking the button below will scrape the most recent tweets. Keep in mind the results may vary, as volume is low based on the limitations. ")
    fresh_tweets = st.checkbox("Use fresh tweets'")
    if st.button("Generate Trends"):

        with st.spinner('Gathering data... This may take between 1-2 minutes.'):

            if fresh_tweets:
                articleList, urlList = generateTrendingProducts()
            else:
                articleList, urlList = generateTrendingProducts(True, DF1, DF2)

            
            st.success(f'Query completed! Your search returned {len(articleList)} trends.') 

            for i, articleName in enumerate(articleList):
                st.markdown(f'<p style="color:Orange; font-family:Muro; font-size:25px">#{i+1}:</p>', unsafe_allow_html=True)
                st.markdown(f'''<div style="background-color:rgba(110, 255, 84, 0.019); padding-top:20px; padding-bottom: 20px;">
                <p style="text-align:center; font-family:Raleway, sans-serif; font-size:20px;">{str(articleName).capitalize()}<br></p>
                <p style="text-align:center; font-family:Raleway, sans-serif; font-size:20px;">Check out the article: <a href="{urlList[i]}">[Link]</a></p></div>''', unsafe_allow_html=True)

            
            # df = pd.DataFrame(columns=['id', 'full_text', 'created_at', 'rt_count', 're_count', 'like_count', 'quotes'])
            # for i in range(6):
            #     date = convertTime((datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d"))
                
            #     df = generateTweets(date, df, brand)

            # #Setting up the dataset for further analysis, and one for exploration without manipulating the main
            # df_tweets, df_new = dataset_manipulation(df)


	