import streamlit as st
import pandas as pd
import tweepy as tp
from datetime import datetime, timedelta
from helperFunctions import twitter_functions as tf
import altair as alt
from pytrends.request import TrendReq


pytrend = TrendReq()



#Personal API key
bearerToken = r"AAAAAAAAAAAAAAAAAAAAAOUBZwEAAAAAuSI9Lk9VJF5p8oZ60%2Ffnb25FSXo%3DsH2SwTWEqpQOe0acAUZeAiPdazuwZYetImYMSn9Wzk7dmXR1VV"


#Initate client
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

    brandSplit = brand.split(" ")

    if len(brandSplit) > 1:
        brand = f'"{" ".join(brandSplit)}"'

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


def dataset_manipulation(df):

    df['created_dt'] = df.created_at.dt.date
    df['created_time'] = df.created_at.dt.time
    #New column to do manipulations on
    df['clean_text'] = df.full_text

    df_new = df[["created_dt", "created_time", "full_text", "rt_count"]]
    df_new = df_new.rename(columns = {"created_dt": "Date", 
                                 "created_time": "Time", 
                                  "full_text": "Tweet", 
                                  "rt_count": "Retweets",  
                                  "fav_count": "Favourites"})

    return df, df_new



# @st.cache
def app():
    
    page_title = f'<p style="font-family:Muro; color:White; font-size: 35px; text-decoration:underline;text-decoration-color:Orange;">Brand analyzer</p>'
    st.markdown(page_title,unsafe_allow_html=True)


    text_description = """On this page you can insert any brand in the textbox below, which will provide insight into that brand's 
    current reputation on Twitter. Simply just write any brand name in the box, and press the 'Generate Tweets' button below. """
    page_description = f'<p style="font-family:Raleway, sans-serif; color:White; font-size: 15px;">{text_description}</p>'
    st.markdown(page_description,unsafe_allow_html=True)

    # st.markdown("## Brand analyser")
    brand = st.text_input(label='', placeholder="e.g., 'Carlsberg'").lower()

    if st.button("Analyze Tweets  ▶️"):

        if len(brand) > 2:
            
            df = pd.DataFrame(columns=['id', 'full_text', 'created_at', 'rt_count', 're_count', 'like_count', 'quotes'])
            for i in range(6):
                date = convertTime((datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d"))
                
                df = generateTweets(date, df, brand)

            #Setting up the dataset for further analysis, and one for exploration without manipulating the main
            df_tweets, df_new = dataset_manipulation(df)


            with st.spinner('Getting data from Twitter...'):

                st.success(f'Query completed! Your search returned {len(df_tweets)} tweets containing {brand} ⭐️') 

                # Extracting all relevant features to be used for sentiment analysis
                df_tweets = tf.feature_extract(df_tweets)

                # Cleaning all unecessary chars from the clean_text column
                df_tweets['clean_text'] = df_tweets.clean_text.apply(tf.text_clean_round1)

                ## Third round of cleaning, removing all stopwords that are unecessary for all NLP analsys
                df_tweets.clean_text  = tf.text_clean_round3(df_tweets.clean_text)


                #Total amount of tweets to be used later
                total_tweets = len(df_tweets['full_text'])

                # 4.2: Sentiment Analysis
                #------------------------------------#

                # Subtitle
                st.header('🌼Sentiment Analysis')
                text_description_sentiment = f"""Below you can see the sentiment scores that {brand} currenty have, divided into segments."""
                page_description_sentiment = f'<p style="font-family:Raleway, sans-serif; color:White; font-size: 15px;">{text_description_sentiment}</p>'
                st.markdown(page_description_sentiment,unsafe_allow_html=True)

                # Get sentiment scores on raw tweets
                text_sentiment = tf.get_sentiment_scores(df_tweets, 'full_text')

                # Add sentiment classification
                text_sentiment = tf.sentiment_classifier(df_tweets, 'compound_score')

                # Select columns to output
                df_sentiment = df_tweets[['created_at', 'full_text', 'sentiment', 'positive_score', 'negative_score', 'neutral_score', 'compound_score']]

                # Sentiment group dataframe
                sentiment_group = df_sentiment.groupby('sentiment').agg({'sentiment': 'count'}).transpose()

                ## 4.2.1: Summary Card Metrics
                ##----------------------------------##

                # KPI Cards for sentiment summary
                negCol, neuCol, posCol = st.columns(3)
                st.subheader('Summary')
                negCol.metric("% 😡 Negative Tweets:", "{:.0%}".format(max(sentiment_group.Negative)/total_tweets))
                neuCol.metric("% 😑 Neutral Tweets: ", "{:.0%}".format(max(sentiment_group.Neutral)/total_tweets))
                posCol.metric("% 😃 Positive Tweets: ", "{:.0%}".format(max(sentiment_group.Positive)/total_tweets))


                ## 4.2.2: Sentiment Expander Bar
                ##----------------------------------##
                sentiment_expander = st.expander('Expand to see more sentiment analysis', expanded=False)


                ## 4.2.3: Sentiment by day bar chart
                ##----------------------------------##

                # Altair chart: sentiment bart chart by day
                sentiment_bar = alt.Chart(df_sentiment).mark_bar().encode(
                    x = alt.X('count(id):Q', stack="normalize", axis = alt.Axis(title = 'Percent of Total Tweets', format='%')),
                    y = alt.Y('monthdate(created_at):O', axis = alt.Axis(title = 'Date')),
                    tooltip = [alt.Tooltip('sentiment', title = 'Sentiment Group'), 'count(id):Q', alt.Tooltip('average(compound_score)', title = 'Avg Compound Score'), alt.Tooltip('median(compound_score)', title = 'Median Compound Score')],
                    color=alt.Color('sentiment',
                        scale=alt.Scale(
                        domain=['Positive', 'Neutral', 'Negative'],
                        range=['forestgreen', 'lightgray', 'indianred']))
                ).properties(
                    height = 400
                ).interactive()

                # Write the chart
                sentiment_expander.subheader('Classifying Tweet Sentiment by Day')
                sentiment_expander.altair_chart(sentiment_bar, use_container_width=True)

                # Wordclouds

                st.header('☁️🔝 Wordcloud & Top Tweets')


                ## 4.3.1: Sentiment Expander Bar
                ##----------------------------------##

                # # Setup expander
                # wordcloud_expander = st.expander('Expand to customize wordcloud & top tweets', expanded=False)

                # # Sentiment Wordcloud subheader & note
                # wordcloud_expander.subheader('Advanced Settings')


                ## 4.3.2: Wordcloud expander submit form
                ##----------------------------------##

                # Sentiment expander form submit for the wordcloud & top tweets
                # with wordcloud_expander.form('form_2'):    
                #     score_type = st.selectbox('Select sentiment', ['All', 'Positive', 'Neutral', 'Negative'], key=1)
                #     wordcloud_words = st.number_input('Choose the max number of words for the word cloud', 15, key = 3)
                #     top_n_tweets =  st.number_input('Choose the top number of tweets *', 3, key = 2)
                #     submitted2 = st.form_submit_button('Regenerate Wordcloud', help = 'Re-run the Wordcloud with the current inputs')


                ## 4.3.3: Plot wordcloud
                ##----------------------------------##
                submitted2 = False
                wordcloud_words = 15
                top_n_tweets = 3

                stek = "All"

                tf.plot_wordcloud(submitted2, stek, text_sentiment, wordcloud_words, top_n_tweets, brand)

                
                ## 4.3.4: Plot top tweets
                ##----------------------------------##
                ## TODO: ADD SESSION STATES
                # Scenarios
                # score_type = st.selectbox('Select sentiment', ['All', 'Positive', 'Neutral', 'Negative'], key=1)
                # session_state = sess
                score_type = "Negative"

                # Scenario 1: All
                if score_type == 'All':
                    score_type_nm = 'compound_score'
                    score_nickname = 'All'

                # Scenario 2: Positive
                if score_type == 'Positive':
                    score_type_nm = 'positive_score'
                    score_nickname = 'Positive'

                # Scenario 3: Neutral
                if score_type == 'Neutral':
                    score_type_nm = 'neutral_score'
                    score_nickname = 'Neutral'

                # Scenario 4: Negative
                if score_type == 'Negative':
                    score_type_nm = 'negative_score'
                    score_nickname = 'Negative'

                # Run the top n tweets
                top_tweets_res = tf.print_top_n_tweets(df_sentiment, score_type_nm, top_n_tweets)

                # Conditional title
                str_num_tweets = str(top_n_tweets)
                show_top = str('Showing top ' + 
                                str_num_tweets + 
                                ' ' +
                                score_nickname + 
                                ' tweets ranked by '+ 
                                score_type_nm)

                # Write conditional
                st.write(show_top)

                # Show top n tweets
                for i in range(top_n_tweets):
                    i = i + 1
                    st.info('**Tweet #**' + str(i) + '**:** ' + top_tweets_res['full_text'][i] + '  \n **Score:** ' + str(top_tweets_res[score_type_nm][i]))

                # pytrend.build_payload([brand], timeframe='today 1-m')

                # trendScore = round(sum(list(pytrend.interest_over_time().iloc[:, 0][:7]))/7, 2)
                st.header('📈 Average Google Trend score over time')

                #search interest per region
                #run model for keywords (can also be competitors)
                pytrend.build_payload([brand], timeframe='today 1-m')


                interestOverTime = pytrend.interest_over_time()

                interestOverTime = interestOverTime.loc[interestOverTime['isPartial'] == False]

                # interestOverTime.columns.values[0] = "Google trends score over time"

                st.line_chart(interestOverTime.iloc[:, 0])
                # fig, ax = plt.subplots(figsize=(8,6))
                # ax.plot(interestOverTime.iloc[:, 0])
                # fig.autofmt_xdate()

                #provide your search terms
                kw_list=[f'{brand}']

                #search interest per region
                #run model for keywords (can also be competitors)
                pytrend.build_payload(kw_list, timeframe='today 1-m')

                # Interest by Region
                regiondf = pytrend.interest_by_region()
                #looking at rows where all values are not equal to 0
                regiondf = regiondf[(regiondf != 0).all(1)]

                #drop all rows that have null values in all columns
                regiondf.dropna(how='all',axis=0, inplace=True)

                # #visualise
                # regiondf.plot(figsize=(20, 12), y=kw_list, kind ='bar')
                st.header('📈 Most recent Google Trend score, by country')
                st.bar_chart(regiondf.sort_values(by=regiondf.columns[0], ascending=False)[:12])







            
        
        else:
            st.write("Please insert a valid brand.")


