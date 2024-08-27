import streamlit as st
from datetime import datetime, timedelta
import requests
from utils import (
 validate_email   
)


if "role" not in st.session_state:
    st.session_state.role = None  

if 'Token' not in st.session_state: 
    st.session_state.Token="None" 

if 'token_expiry' not in st.session_state: 
    st.session_state.token_expiry="1970-01-10" 

TOKEN_EXPIRY_TIME = timedelta(hours=1)  # Define token expiry time    

def loginPage(): 
    # Input fields
    email = st.text_input("Email")
    password = st.text_input("Password", type="password") 
    st.markdown("###### Login using your BP Credentials")  
    # Validate email and password
    if st.button("Login"):
        if not email or not password:
            st.error("Both email and password are required.")
        elif not validate_email(email):
            st.error("Invalid email format. Please enter a valid email address.")
        else:
            try:
                token = login(email, password)
                if token:
                    st.session_state.token = token
                    st.session_state.token_expiry = datetime.now() + TOKEN_EXPIRY_TIME 
                    st.success("Login successful!")
                    st.session_state.role="Pointr"
                    st.rerun()  # Rerun to display the content of the next page 
                else:
                    st.error("Login failed. Check your username/password.")
            except Exception as e:
                st.error(f"An error occurred during the login process: {str(e)}")    


def login(email, password):
    payload = {"email": email, "password": password}
    try:
        LOGIN_API_URL = "https://planner.pointr.tech/login-api/login"
        response = requests.post(LOGIN_API_URL, json=payload)
        response.raise_for_status()  # Raise an error for bad responses
        data = response.json()
        token = data.get("token") 
        return token
    except requests.RequestException as e: 
        return None


def validate_email(email):
    """Validate the email format."""
    import re
    email_regex = r'^\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    if re.match(email_regex, email):
        return True
    return False

def logout():
    st.session_state.role = None
    st.rerun()

role = st.session_state.role
logout_page = st.Page(logout, title="Log out", icon=":material/logout:") 


basicProfiler = st.Page(
    "basicProfiler.py",
    title="Basic Profiler",
    icon=":material/view_array:",
    default=(role == "Pointr"),
)
UnheardMapView=st.Page(
    "UnheardMapView.py",
    title="Unheard in Map View", 
    icon=":material/map:", 
) 
unheardList=st.Page(
    "unheardList.py",
    title="Unheard Beacon List", 
    icon=":material/warning:", 
)

account_pages = [logout_page]
profiler_pages = [basicProfiler, unheardList,UnheardMapView]  

st.markdown("#### OPS Tool kit")
st.logo("images/horizontal_blue.png", icon_image="images/icon_blue.png")   

page_dict = {}

if st.session_state.role == "Pointr":
    page_dict["Profiler"] = profiler_pages      
if len(page_dict) > 0:  
    pg = st.navigation({"Account": account_pages} | page_dict)  
else:
    pg = st.navigation([st.Page(loginPage)])  
pg.run()