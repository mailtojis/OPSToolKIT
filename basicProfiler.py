import streamlit as st
import pandas as pd
from utils import (
    upload_file, 
    group_and_sort_beacon_data, 
    create_csv_download_link, 
    format_timestamp, 
    get_location_from_coordinates
)
 
st.markdown("#### Basic Beacon Data Viewer") 
# Inject custom CSS
#st.markdown(get_styles(), unsafe_allow_html=True)

# File uploader widget
data = upload_file()  # Call the function to handle file upload

if data:
    try:
        # Extract and process optional notes
        optional_notes = data.get("optionalNotes", "No notes provided") 
        # Extract and process recording info
        recording_info = data.get("recordingInfo", {})
        gps_data = data.get("gpsData", [])
        has_gps_data = len(gps_data) > 0

        # Get the first GPS location if available
        gps_location = ''
        if has_gps_data:
            first_gps_point = gps_data[0]
            latitude = first_gps_point['latitude']
            longitude = first_gps_point['longitude']
            gps_location = get_location_from_coordinates(latitude, longitude)

        # Recording Information DataFrame
        recording_info_df = pd.DataFrame({
            "Item": [
                "Start Time",
                "End Time",
                "Duration", 
                "Device Model",
                "GPS Location",     # Added GPS Location here
                "OS",
                "Manufacturer",
                "OS Version",
                "Recorder Version",
                "Added UUIDs",
                "Optional Notes" # Added Optional Notes here  
            ],
            "Value": [
                format_timestamp(recording_info.get("recordingStartTime", 0)),
                format_timestamp(recording_info.get("recordingEndTime", 0)),
                f"{recording_info.get('recordingDuration', 0):.2f} seconds", 
                recording_info.get('deviceModel', 'N/A'),
                gps_location,  # Display the first GPS location
                recording_info.get('os', 'N/A'),
                recording_info.get('manufacturer', 'N/A'),
                recording_info.get('osVersion', 'N/A'),
                recording_info.get('recorderAppVersion', 'N/A'),
                ', '.join(recording_info.get('uuids', [])),
                optional_notes 
            ]
        })

        # Extract data counts
        sensor_data_count = len(data.get("sensorData", []))
        gps_data_count = len(data.get("gpsData", []))
        beacon_data_count = len(data.get("beaconData", []))  # Total beacon data readings

        # Data Counts DataFrame
        data_counts_df = pd.DataFrame({
            "Data Type": ["Sensor Data", "GPS Data", "Beacon Data"],
            "Count": [sensor_data_count, gps_data_count, beacon_data_count]
        })

        col1, col2 = st.columns([2, 1])

        with col1:
            st.write("### Recording Summary")
            st.markdown('<div class="dataframe-container">', unsafe_allow_html=True)
            st.dataframe(recording_info_df, use_container_width=True, hide_index=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with col2:
            st.write("### Data Counts")
            st.dataframe(data_counts_df, use_container_width=True, hide_index=True)

        # Extract and process beacon data
        beacon_data = data.get("beaconData", [])

        if not isinstance(beacon_data, list):
            st.error("'beaconData' should be a list.")
        else:
            # Organize and sort beacon data
            grouped_beacon_data = group_and_sort_beacon_data(beacon_data)

            # Prepare data for DataFrame
            rows = []
            for uuid, majors in grouped_beacon_data.items():
                for major, minors in majors.items():
                    minor_list = sorted(minors)
                    minor_str = ", ".join(map(str, minor_list))
                    rows.append([uuid, major, minor_str])

            # Create DataFrame
            df = pd.DataFrame(rows, columns=["UUID", "Major", "Minors"])

            # Create and display data in an accordion format
            st.markdown("### Captured Beacon Values")

            for uuid, majors in grouped_beacon_data.items():
                with st.expander(f"UUID: {uuid}"):
                    for major, minors in majors.items():
                        minor_list = sorted(minors)
                        minor_str = ", ".join(map(str, minor_list))
                        st.markdown(f"""
                            **Major: {major}**
                            | Minors |
                            |--------|
                            | {minor_str} |
                        """)

            # Generate CSV download link
            csv_data = create_csv_download_link(df)
            st.download_button(
                label="Download CSV",
                data=csv_data,
                file_name="beacon_data.csv",
                mime="text/csv"
            )

    except Exception as e:
        st.error(f"An error occurred: {e}")
