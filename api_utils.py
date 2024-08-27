# api_utils.py

import requests
import streamlit as st

def fetch_clients(token):
    api_url = "https://planner.pointr.tech/api/clients"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        #st.write("START client API call")
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"An error occurred while fetching clients: {str(e)}")
        return []

def fetch_sites(client_id, token):
    api_site_url = f"https://planner.pointr.tech/api/client/{client_id}/sites"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        #st.write("Start sites API")
        response = requests.get(api_site_url, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"An error occurred while fetching sites: {str(e)}")
        return []

def fetch_building(site_id, token):
    api_building_url = f"https://planner.pointr.tech/api/site/{site_id}/buildings"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        #st.write("Start building API")
        response = requests.get(api_building_url, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"An error occurred while fetching buildings: {str(e)}")
        return []

def fetch_levels(building_id, token):
    api_level_url = f"https://planner.pointr.tech/api/building/{building_id}/levels"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        #st.write("Start level API")
        response = requests.get(api_level_url, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"An error occurred while fetching levels: {str(e)}")
        return []


def fetch_GeoJson(levelId,token): 
    api_geoJson_url=f"https://planner.pointr.tech/api/level/{levelId}/geoJson"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response= requests.get(api_geoJson_url,headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"An error occured: {str(e)}")
        return[]

def fetch_beaconsType(site_id,token):
    api_fetchBeaconType_url=f"https://planner.pointr.tech/api/site/{site_id}/beacon-types"
    headers= {"Authorization": f"Bearer {token}"}
    try:
        response=requests.get(api_fetchBeaconType_url,headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"An error occured: {str(e)}")
        return []