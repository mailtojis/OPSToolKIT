import json
import pandas as pd
from collections import defaultdict
from io import StringIO
from datetime import datetime, timezone
from geopy.geocoders import Nominatim
import streamlit as st

def upload_file():
    """Display the file uploader widget and return the uploaded JSON data."""
    
    st.markdown("### Upload Your Recording File")
    uploaded_file = st.file_uploader("Choose a recording", type="json")
   
    if uploaded_file is not None:
        try:
            # Read and parse the JSON file
            file_contents = uploaded_file.read()
            data = json.loads(file_contents)
            return data
        except json.JSONDecodeError:
            st.error("The file is not a valid JSON.")
        except Exception as e:
            st.error(f"An error occurred: {e}")
    
    st.markdown('</div>', unsafe_allow_html=True)
    return None

def group_and_sort_beacon_data(beacon_data):
    grouped_data = defaultdict(lambda: defaultdict(set))

    for entry in beacon_data:
        try:
            uuid = entry.get("uuid")
            major = entry.get("major")
            minor = entry.get("minor")

            if uuid is not None and major is not None and minor is not None:
                if minor < 0:
                    minor += 65336
                if major <0:
                    major +=65336
                grouped_data[uuid][major].add(minor)
            else:
                st.warning(f"Skipping invalid entry (missing key): {entry}")

        except Exception as e:
            st.error(f"Error processing entry {entry}: {e}")

    return grouped_data

def create_csv_download_link(df, filename="beacon_data.csv"):
    """Create a CSV download link."""
    buffer = StringIO()
    df.to_csv(buffer, index=False)
    buffer.seek(0)
    return buffer.getvalue()

def format_timestamp(ts):
    # """Convert timestamp to a human-readable UTC datetime string."""
    try:
        if ts:
        #     return datetime.fromtimestamp(ts / 1000, timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
            date_time = datetime.fromtimestamp(ts) 
            return (date_time.strftime("%Y-%m-%d %H:%M:%S"))
        else:
            return 'N/A'
    except Exception as e:
        return datetime.fromtimestamp(ts / 1000, timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')

def get_location_from_coordinates(lat, lon):
    """Get a location and country name from latitude and longitude."""
    geolocator = Nominatim(user_agent="beacon_data_viewer")
    try:
        location = geolocator.reverse((lat, lon), language='en', exactly_one=True)
        if location:
            address = location.raw.get('address', {})
            location_name = address.get('town', address.get('city', address.get('village', 'Unknown Location')))
            country_name = address.get('country', 'Unknown Country')
            return f"{location_name}, {country_name}"
        else:
            return "Location not found"
    except Exception as e:
        return "Error obtaining location"


def get_styles():
    """Get custom styles for the Streamlit app."""
    return """
    <style>
    .dataframe-container {
        margin: 0 auto;
        width: 100%;
        max-width: 1200px;
    }
    </style>
    """
def validate_email(email):
    """Validate the email format."""
    import re
    email_regex = r'^\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    if re.match(email_regex, email):
        return True
    return False