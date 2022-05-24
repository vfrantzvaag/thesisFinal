import streamlit as st
# Custom imports 
from multipage import MultiPage
from pages import tweetAnalyser, trendAnalyser # import your pages here


# Create an instance of the app 
app = MultiPage()

# Title of the main page
# col1, col2 = st.columns(2)
new_title = f'<p style="font-family:Raleway, sans-serif; color:White; font-size: 50px;">Social Media Dashboard</p>'
st.markdown(new_title,unsafe_allow_html=True)


# Add all your application here
app.add_page("Tweet Analyser", tweetAnalyser.app)
app.add_page("Trend Analyser",trendAnalyser.app)


# The main app
app.run()
