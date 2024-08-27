import streamlit as st
import json
import folium
import pandas as pd
from datetime import datetime
from streamlit_folium import folium_static
from folium.features import DivIcon
from api_utils import fetch_clients, fetch_sites, fetch_building, fetch_levels, fetch_GeoJson

def extract_beacons_from_geojson(placed_beacons):
    """Extract beacons from GeoJSON data."""
    return [
        {
            "uuid": beacon["uuid"].upper(),
            "major": int(beacon["major"]),
            "minor": int(beacon["minor"]),
            "coordinates": beacon["coordinates"]
        }
        for beacon in placed_beacons
    ]

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

# Check if the token is expired or not
token = st.session_state.get('token')
if not token:
    st.write("Please log in to access the map view.")
else:
    # Fetch or cache clients
    if 'clients' not in st.session_state:
        with st.spinner("Loading clients..."):
            st.session_state.clients = fetch_clients(token)
    
    clients = st.session_state.clients
    if clients:
        client_id_name = {client["name"]: client["_id"] for client in clients}
        client_names = sorted(client_id_name.keys())

        # Create columns for dropdowns
        col1, col2 = st.columns([2, 2])

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
                selected_building_name = st.selectbox("Select Building", building_names, key='client_selectbox_building')
                selected_building_id = building_id_name[selected_building_name]

                # Fetch or cache levels
                if 'levels' not in st.session_state or st.session_state.selected_building_id != selected_building_id:
                    with st.spinner("Loading levels..."):
                        st.session_state.selected_building_id = selected_building_id
                        st.session_state.levels = fetch_levels(selected_building_id, token)
                
                levels = st.session_state.levels
                if levels:
                    # Create a dictionary with longName included
                    level_display = {f"{level['shortName']} ({level['longName']})": level["_id"] for level in levels}
                    level_names = sorted(level_display.keys())

                    # Create columns for level dropdown
                    col3, col4 = st.columns([2, 2])

                    # Dropdown for levels
                    with col3:
                        selected_level_name = st.selectbox("Select Level", level_names, key='level_selectbox')
                        selected_level_id = level_display[selected_level_name]

                    # Fetch or cache GeoJSON data
                    if 'geojson' not in st.session_state or st.session_state.selected_level_id != selected_level_id:
                        with st.spinner("Loading data..."):
                            st.session_state.selected_level_id = selected_level_id
                            st.session_state.levelGeoJson = fetch_GeoJson(selected_level_id, token)
                    
                    levelGeoJson = st.session_state.levelGeoJson
                    if levelGeoJson:
                        # Extract beacons from GeoJSON
                        placed_beacons = levelGeoJson.get("placedBeacons", [])
                        geojson_beacons = extract_beacons_from_geojson(placed_beacons)

                        # File upload
                        st.markdown("##### Upload Recordings")
                        uploaded_files = st.file_uploader("Choose Multiple JSON Recordings if you have:", type="json", accept_multiple_files=True)

                        # Create columns for buttons
                        col5, col6 = st.columns([3, 1])

                        # Button to compare and find missing beacons
                        with col5:
                            if st.button("Check for Missing Beacons"):
                                if uploaded_files:
                                    # Create a set of beacon identifiers from uploaded files
                                    uploaded_beacons_set = set(
                                        (beacon["uuid"], beacon["major"], beacon["minor"])
                                        for uploaded_file in uploaded_files
                                        for beacon in extract_beacons_from_json(json.loads(uploaded_file.read()))
                                    )
                                    
                                    # Remove beacons from missing_beacons if they are found in uploaded_beacons
                                    missing_beacons = [
                                        beacon for beacon in geojson_beacons
                                        if (beacon["uuid"], beacon["major"], beacon["minor"]) not in uploaded_beacons_set
                                    ]
                                    
                                    if missing_beacons:
                                        # Remove missing beacons from GeoJSON
                                        updated_placed_beacons = [
                                            beacon for beacon in geojson_beacons
                                            if (beacon["uuid"], beacon["major"], beacon["minor"]) not in uploaded_beacons_set
                                        ]
                                        # Update GeoJSON data
                                        updated_geojson = levelGeoJson.copy()
                                        updated_geojson["placedBeacons"] = updated_placed_beacons

                                        # Initialize Folium map
                                        m = folium.Map(location=[0, 0], zoom_start=15)

                                        # Add updated GeoJSON features to the map
                                        geojson_features = updated_geojson.get("geoJson", {})
                                        if "features" in geojson_features:
                                            folium.GeoJson(geojson_features).add_to(m)

                                            # Center map based on the features' location
                                            bounds = []
                                            for feature in geojson_features["features"]:
                                                geometry_type = feature["geometry"]["type"]
                                                coordinates = feature["geometry"]["coordinates"]

                                                if geometry_type == "Point":
                                                    bounds.append((coordinates[1], coordinates[0]))
                                                elif geometry_type == "LineString":
                                                    bounds.extend([(coord[1], coord[0]) for coord in coordinates])
                                                elif geometry_type == "Polygon":
                                                    for ring in coordinates:
                                                        bounds.extend([(coord[1], coord[0]) for coord in ring])
                                            if bounds:
                                                m.fit_bounds(bounds)
                                            else:
                                                st.error("The fetched GeoJSON data does not contain valid geometries.")

                                        # Add beacons as custom icons
                                        for beacon in updated_geojson["placedBeacons"]:
                                            folium.Marker(
                                                location=[beacon["coordinates"][1], beacon["coordinates"][0]],
                                                icon=folium.DivIcon(
                                                    html=f"""
                                                    <div style="
                                                        background-color: yellow; 
                                                        border-radius: 50%; 
                                                        width: 20px; 
                                                        height: 20px; 
                                                        border: 2px dashed red;
                                                    "></div>
                                                    """,
                                                    icon_size=(10, 10)
                                                ),
                                                popup=folium.Popup(
                                                    f"UUID: {beacon['uuid']}<br>Major: {beacon['major']}<br>Minor: {beacon['minor']}",
                                                    max_width=300
                                                )
                                            ).add_to(m)

                                        # Display the updated map using Streamlit
                                        st.write(f"### Unheard Beacons in {selected_level_name}")
                                        folium_static(m, width=800, height=600)
                                        
                                        # Convert missing beacons to CSV for download
                                        df = pd.DataFrame(missing_beacons)
                                        csv = df.to_csv(index=False)
                                        
                                        # Show download button
                                        with col6:
                                            st.download_button(
                                                label="Download Missing Beacons",
                                                data=csv,
                                                file_name="missing_beacons.csv",
                                                mime="text/csv"
                                            )
                                    else:
                                        st.write("No beacons are missing.")
                                else:
                                    st.write("Please upload one or more JSON files.")
                    else:
                        st.write("No GeoJSON data found for the selected level.")
                else:
                    st.write("No GeoJSON data found for the selected level.")
            else:
                st.write("No buildings found for the selected site.")
        else:
            st.write("No sites found for the selected client.")
    else:
        st.write("No clients found or an error occurred.")