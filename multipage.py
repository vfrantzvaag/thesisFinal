"""
This file is the framework for generating multiple Streamlit applications 
through an object oriented framework. 
"""

# Import necessary libraries 
import streamlit as st

# Define the multipage class to manage the multiple apps in our program 
class MultiPage: 
    """Framework for combining multiple streamlit applications."""

    def __init__(self) -> None:
        """Constructor class to generate a list which will store all our applications as an instance variable."""
        self.pages = []
    
    def add_page(self, title, func) -> None: 
        """Class Method to Add pages to the project

        Args:
            title ([str]): The title of page which we are adding to the list of apps 
            
            func: Python function to render this page in Streamlit
        """

        self.pages.append(
            {
                "title": title, 
                "function": func
            }
        )

    def run(self):
        # Drodown to select the page to run  
        page = st.sidebar.selectbox(
            'App Navigation', 
            self.pages, 
            format_func=lambda page: page['title']
        )

        ## About the app title
        st.sidebar.text("") # spacing
        st.sidebar.header('About the App')

        # General expander section
        about_expander = st.sidebar.expander("General")
 
        about_expander.markdown("""
        * **Authors:** [Vetle Frantzvaag](https://github.com/vfrantzvaag) & [Kiriakos Tsalkitzidis](https://github.com/Tsalkitzidis)
        * **Background:**
        This dashboard was made as a proof of concept as part of the Authors' master thesis in Technology Entrepreneurship.
        """)

        # st.sidebar.image("images/dtu.png", width=100)
        st.sidebar.markdown('''<img src="https://designguide.dtu.dk/-/media/subsites/designguide/design-basics/logo/dtu_logo_corporate_red_rgb.png" 
        width="150" height="auto" style="margin-top:75%; margin-left:auto; margin-right:auto; display:block;">''', unsafe_allow_html=True)


        # run the app function 
        page['function']()