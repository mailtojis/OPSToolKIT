import streamlit as st
import json
import folium
import pandas as pd
from streamlit_folium import folium_static
from folium.features import DivIcon
from api_utils import fetch_clients, fetch_sites, fetch_building, fetch_levels, fetch_GeoJson

@st.cache_data
def fetch_clients_data(token):
    return fetch_clients(token)

@st.cache_data
def fetch_sites_data(client_id, token):
    return fetch_sites(client_id, token)

@st.cache_data
def fetch_building_data(site_id, token):
    return fetch_building(site_id, token)

@st.cache_data
def fetch_levels_data(building_id, token):
    return fetch_levels(building_id, token)

@st.cache_data
def fetch_geojson_data(level_id, token):
    return fetch_GeoJson(level_id, token)

def extract_beacons_from_geojson(placed_beacons):
    return [
        {"uuid": beacon["uuid"].upper(), "major": int(beacon["major"]), "minor": int(beacon["minor"]), "coordinates": beacon["coordinates"]}
        for beacon in placed_beacons
    ]

def extract_beacons_from_json(data):
    return [
        {"uuid": beacon["uuid"].upper(), "major": int(beacon["major"]), "minor": int(beacon["minor"])}
        for beacon in data.get("beaconData", [])
    ]

token = st.session_state.get('token')
if not token:
    st.write("Please log in to access the map view.")
else:
    if 'clients' not in st.session_state:
        with st.spinner("Loading clients..."):
            st.session_state.clients = fetch_clients_data(token)
    
    clients = st.session_state.clients
    if clients:
        client_id_name = {client["name"]: client["_id"] for client in clients}
        client_names = sorted(client_id_name.keys())

        col1, col2 = st.columns([2, 2])
        with col1:
            selected_client_name = st.selectbox("Select Client", client_names, key='client_selectbox_client')
            selected_client_id = client_id_name[selected_client_name]

        if 'sites' not in st.session_state or st.session_state.selected_client_id != selected_client_id:
            with st.spinner("Loading sites..."):
                st.session_state.selected_client_id = selected_client_id
                st.session_state.sites = fetch_sites_data(selected_client_id, token)
        
        sites = st.session_state.sites
        if sites:
            site_id_name = {site["name"]: site["_id"] for site in sites}
            site_names = sorted(site_id_name.keys())

            with col2:
                selected_site_name = st.selectbox("Select Site", site_names, key='client_selectbox_site')
                selected_site_id = site_id_name[selected_site_name]

            if 'buildings' not in st.session_state or st.session_state.selected_site_id != selected_site_id:
                with st.spinner("Loading buildings..."):
                    st.session_state.selected_site_id = selected_site_id
                    st.session_state.buildings = fetch_building_data(selected_site_id, token)
            
            buildings = st.session_state.buildings
            if buildings:
                building_id_name = {building["name"]: building["_id"] for building in buildings}
                building_names = sorted(building_id_name.keys())

                selected_building_name = st.selectbox("Select Building", building_names, key='client_selectbox_building')
                selected_building_id = building_id_name[selected_building_name]

                if 'levels' not in st.session_state or st.session_state.selected_building_id != selected_building_id:
                    with st.spinner("Loading levels..."):
                        st.session_state.selected_building_id = selected_building_id
                        st.session_state.levels = fetch_levels_data(selected_building_id, token)
                
                levels = st.session_state.levels
                if levels:
                    level_display = {f"{level['shortName']} ({level['longName']})": level["_id"] for level in levels}
                    level_names = sorted(level_display.keys())

                    col3, col4 = st.columns([2, 2])
                    with col3:
                        selected_level_name = st.selectbox("Select Level", level_names, key='level_selectbox')
                        selected_level_id = level_display[selected_level_name]

                    if 'geojson' not in st.session_state or st.session_state.selected_level_id != selected_level_id:
                        with st.spinner("Loading data..."):
                            st.session_state.selected_level_id = selected_level_id
                            st.session_state.levelGeoJson = fetch_geojson_data(selected_level_id, token)
                    
                    levelGeoJson = st.session_state.levelGeoJson
                    if levelGeoJson:
                        placed_beacons = levelGeoJson.get("placedBeacons", [])
                        geojson_beacons = extract_beacons_from_geojson(placed_beacons)

                        st.markdown("##### Upload Recordings")
                        uploaded_files = st.file_uploader("Choose Multiple JSON Recordings if you have:", type="json", accept_multiple_files=True)

                        col5, col6 = st.columns([3, 1])
                        with col5:
                            if st.button("Check for Missing Beacons"):
                                if uploaded_files:
                                    uploaded_beacons_set = set(
                                        (beacon["uuid"], beacon["major"], beacon["minor"])
                                        for uploaded_file in uploaded_files
                                        for beacon in extract_beacons_from_json(json.loads(uploaded_file.read()))
                                    )
                                    
                                    missing_beacons = [
                                        beacon for beacon in geojson_beacons
                                        if (beacon["uuid"], beacon["major"], beacon["minor"]) not in uploaded_beacons_set
                                    ]
                                    
                                    if missing_beacons:
                                        updated_placed_beacons = [
                                            beacon for beacon in geojson_beacons
                                            if (beacon["uuid"], beacon["major"], beacon["minor"]) not in uploaded_beacons_set
                                        ]
                                        updated_geojson = levelGeoJson.copy()
                                        updated_geojson["placedBeacons"] = updated_placed_beacons

                                        mapbox_token = "your_mapbox_token_here"
                                        m = folium.Map(
                                            location=[0, 0],
                                            zoom_start=15,
                                            tiles=f"https://api.mapbox.com/styles/v1/mapbox/streets-v11/tiles/{{z}}/{{x}}/{{y}}?access_token={mapbox_token}",
                                            attr="Mapbox"
                                        )

                                        geojson_features = updated_geojson.get("geoJson", {})
                                        if "features" in geojson_features:
                                            folium.GeoJson(geojson_features).add_to(m)

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
                                                        border: 2px solid red;
                                                    "></div>
                                                    """,
                                                    icon_size=(10, 10)
                                                ),
                                                popup=folium.Popup(
                                                    f"UUID: {beacon['uuid']}<br>Major: {beacon['major']}<br>Minor: {beacon['minor']}",
                                                    max_width=300
                                                )
                                            ).add_to(m)

                                        st.write(f"### Unheard Beacons in {selected_level_name}")
                                        folium_static(m, width=800, height=600)
                                        
                                        df = pd.DataFrame(missing_beacons)
                                        csv = df.to_csv(index=False)
                                        
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
