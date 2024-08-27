import streamlit as st
import pandas as pd
import json
from api_utils import fetch_clients, fetch_sites, fetch_building, fetch_levels
from datetime import datetime

def extract_beacons_from_json(data):
    """Extract beacons from uploaded JSON data."""
    return [
        {
            "uuid": beacon["uuid"].upper(),
            "major": int(beacon["major"]),
            "minor": int(beacon["minor"])
        }
        for beacon in data.get("beaconData", [])
    ]

#st.markdown("#### Advanced Profiler") 

# Check if the token is set and valid
token = st.session_state.get('token')
if not token:
    st.write("Please log in to access the list.")

# Fetch or cache clients
if 'clients' not in st.session_state:
    with st.spinner("Loading clients..."):
        st.session_state.clients = fetch_clients(token)

clients = st.session_state.clients
if clients:
    client_id_name = {client["name"]: client["_id"] for client in clients}
    client_names = sorted(client_id_name.keys())
    
    # Create columns for dropdowns
    col1, col2, col3 = st.columns(3)
    
    # Dropdown for clients
    with col1:
        selected_client_name = st.selectbox("Select Client", client_names, key='client_selectbox_client')
        selected_client_id = client_id_name[selected_client_name]
    
    # Fetch or cache sites
    if 'sites' not in st.session_state or st.session_state.selected_client_id != selected_client_id:
        with st.spinner("Loading sites..."):
            st.session_state.selected_client_id = selected_client_id
            st.session_state.sites = fetch_sites(selected_client_id, token)
    
    sites = st.session_state.sites
    if sites:
        site_id_name = {site["name"]: site["_id"] for site in sites}
        site_names = sorted(site_id_name.keys())
        
        # Dropdown for sites
        with col2:
            selected_site_name = st.selectbox("Select Site", site_names, key='client_selectbox_site')
            selected_site_id = site_id_name[selected_site_name]
        
        # Fetch or cache buildings
        if 'buildings' not in st.session_state or st.session_state.selected_site_id != selected_site_id:
            with st.spinner("Loading buildings..."):
                st.session_state.selected_site_id = selected_site_id
                st.session_state.buildings = fetch_building(selected_site_id, token)
        
        buildings = st.session_state.buildings
        if buildings:
            building_id_name = {building["name"]: building["_id"] for building in buildings}
            building_names = sorted(building_id_name.keys())
            
            # Dropdown for buildings
            with col3:
                selected_building_name = st.selectbox("Select Building", building_names, key='client_selectbox_building')
                selected_building_id = building_id_name[selected_building_name]
            
            # Fetch or cache levels
            if 'levels' not in st.session_state or st.session_state.selected_building_id != selected_building_id:
                with st.spinner("Loading levels..."):
                    st.session_state.selected_building_id = selected_building_id
                    st.session_state.levels = fetch_levels(selected_building_id, token)
            
            levels = st.session_state.levels
            if levels:
                level_id_name = {level["shortName"]: level["_id"] for level in levels}
                level_names = sorted(level_id_name.keys())
                level_names.insert(0, "All")
                
                # Dropdown for levels
                selected_level_name = st.selectbox("Select Level", level_names, key='client_selectbox_level')
                
                # Upload recordings
                st.markdown("##### Upload Recordings")
                uploaded_files = st.file_uploader("Choose Multiple JSON Recordings if you have:", type="json", accept_multiple_files=True)
                
                # Start Analyze button
                if st.button("Unheard List"):
                    if uploaded_files:
                        # Create a set of beacon identifiers from uploaded files
                        uploaded_beacons_set = set(
                            (beacon["uuid"], beacon["major"], beacon["minor"])
                            for uploaded_file in uploaded_files
                            for beacon in extract_beacons_from_json(json.loads(uploaded_file.read()))
                        )

                        # Store missing beacons by level in a DataFrame
                        missing_beacons_df = pd.DataFrame(columns=["Level", "UUID", "Major", "Minor"])

                        # Process selected level
                        if selected_level_name == "All":
                            # Check across all levels
                            for level in levels:
                                level_beacons_set = set(
                                    (beacon["uuid"].upper(), int(beacon["major"]), int(beacon["minor"]))
                                    for beacon in level.get("placedBeacons", [])
                                )
                                missing_beacons = level_beacons_set - uploaded_beacons_set
                                for beacon in missing_beacons:
                                    missing_beacons_df.loc[len(missing_beacons_df)] = {
                                        "Level": level["shortName"],
                                        "UUID": beacon[0],
                                        "Major": beacon[1],
                                        "Minor": beacon[2]
                                    }
                        else:
                            # Check for the specific level
                            selected_level_id = level_id_name[selected_level_name]
                            selected_level = next((level for level in levels if level["_id"] == selected_level_id), {})
                            level_beacons_set = set(
                                (beacon["uuid"].upper(), int(beacon["major"]), int(beacon["minor"]))
                                for beacon in selected_level.get("placedBeacons", [])
                            )
                            missing_beacons = level_beacons_set - uploaded_beacons_set
                            for beacon in missing_beacons:
                                missing_beacons_df.loc[len(missing_beacons_df)] = {
                                    "Level": selected_level_name,
                                    "UUID": beacon[0],
                                    "Major": beacon[1],
                                    "Minor": beacon[2]
                                }

                        # Display the missing beacons DataFrame
                        st.write(missing_beacons_df)
                    else:
                        st.write("Please upload beacon JSON files.")
            else:
                st.write("No levels found for the selected building.")
        else:
            st.write("No buildings found for the selected site.")
    else:
        st.write("No sites found for the selected client.")
else:
    st.write("No clients found or an error occurred.")

