import os
import tweepy
import openai
import streamlit as st
from datetime import datetime
from dotenv import load_dotenv
import pandas as pd

# Load environment variables
load_dotenv()

# Twitter API credentials from .env file
TWITTER_API_KEY = os.getenv('TWITTER_API_KEY')
TWITTER_API_SECRET_KEY = os.getenv('TWITTER_API_SECRET_KEY')
TWITTER_ACCESS_TOKEN = os.getenv('TWITTER_ACCESS_TOKEN')
TWITTER_ACCESS_TOKEN_SECRET = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')

summarizer_sys_prompt = """
You are a Newsletter author. 
Your role is to compile a list of tweets into a coherent newsletter that summarises the main topics so readers can have a digest that helps them save time.
""".strip()

# Authenticate with Twitter API
def authenticate_twitter(api_key, api_secret_key, access_token, access_token_secret):
    auth = tweepy.OAuthHandler(api_key, api_secret_key)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth)
    return api

# Fetch tweets from a list within a time frame
def fetch_tweets_from_list(api, list_id, start_time, end_time):
    tweets = []
    for tweet in tweepy.Cursor(api.list_timeline, list_id=list_id).items():
        if start_time <= tweet.created_at <= end_time:
            tweets.append({
                'text': tweet.text,
                'retweet_count': tweet.retweet_count,
                'favorite_count': tweet.favorite_count
            })
    return tweets

# Summarize tweets using OpenAI GPT-4
def summarize_tweets_openai(tweets):
    text = "\n\n---\n\n".join(tweets)
    response = openai.chat.completions.create(
        temperature=0.4,
        model="gpt-4o",
        messages=[{
                "role": "system",
                "content": "Summarize the following tweets",
            },
            {
                "role": "user",
                "content": text
            }]
    )
    return str(response.choices[0].message.content).strip()

# Streamlit app
def main():
    st.title("X.com List Summarizer")
    
    # Input fields
    list_id = st.text_input("Twitter List ID or URL")

    # Date range
    # Start date should be 1 week ago by default
    today = datetime.today()
    start_date = st.date_input("Start Date", value= today - pd.Timedelta(days=7))
    end_date = st.date_input("End Date", value=today)

    if st.button("Generate Summary"):
        if list_id:
            
            # If list URL is provided, extract list ID
            if 'x.com' in list_id:
                list_id = list_id.split('/')[-1]

            # Convert dates to datetime
            start_time = datetime.combine(start_date, datetime.min.time())
            end_time = datetime.combine(end_date, datetime.min.time())

            tweets = fetch_tweets_from_list(api, list_id, start_time, end_time)

            # Convert to DataFrame to select tweets with the highest reach
            df = pd.DataFrame(tweets)
            df['reach'] = df['retweet_count'] + df['favorite_count']
            top_tweets = df.nlargest(100, 'reach')['text'].tolist()

            summary = summarize_tweets_openai(top_tweets)
            
            st.subheader("Summary of the top topics/tweets:")
            st.write(summary)
        else:
            st.error("Please provide all required inputs")

api = authenticate_twitter(TWITTER_API_KEY, TWITTER_API_SECRET_KEY, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET)

if __name__ == "__main__":
    main()