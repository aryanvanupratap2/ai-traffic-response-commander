import streamlit as st
import pandas as pd
from datetime import datetime
from utils.stimulator_new import simulate_event
from utils.map_utils_new import create_map
from utils.copilot import generate_copilot_response
from utils.explainability import explain_prediction
from utils.gemini_copilot import ask_copilot
import joblib

from streamlit_folium import st_folium
from utils.geocoder import get_coordinates
import folium

@st.dialog("🤖 Traffic AI Copilot")
def ai_chat_popup(report):

    st.markdown("### Quick Questions")

    col1, col2 = st.columns(2)

    with col1:

        if st.button("🚓 Police Plan"):

            question = "Give police deployment strategy."

            answer = ask_copilot(
                question,
                report
            )

            st.session_state.messages.append(
                {
                    "role":"user",
                    "content":question
                }
            )

            st.session_state.messages.append(
                {
                    "role":"assistant",
                    "content":answer
                }
            )

            st.rerun()

        if st.button("📢 Public Advisory"):

            question = "Generate commuter advisory."

            answer = ask_copilot(
                question,
                report
            )

            st.session_state.messages.append(
                {
                    "role":"user",
                    "content":question
                }
            )

            st.session_state.messages.append(
                {
                    "role":"assistant",
                    "content":answer
                }
            )

            st.rerun()

    with col2:

        if st.button("🚧 Diversion Plan"):

            question = "Suggest diversion routes."

            answer = ask_copilot(
                question,
                report
            )

            st.session_state.messages.append(
                {
                    "role":"user",
                    "content":question
                }
            )

            st.session_state.messages.append(
                {
                    "role":"assistant",
                    "content":answer
                }
            )

            st.rerun()

        if st.button("⚠️ Risk Analysis"):

            question = "Assess overall traffic risk."

            answer = ask_copilot(
                question,
                report
            )

            st.session_state.messages.append(
                {
                    "role":"user",
                    "content":question
                }
            )

            st.session_state.messages.append(
                {
                    "role":"assistant",
                    "content":answer
                }
            )

            st.rerun()

    st.divider()

    for msg in st.session_state.messages:

        with st.chat_message(
            msg["role"]
        ):
            st.write(
                msg["content"]
            )

    user_prompt = st.chat_input(
        "Ask Traffic AI..."
    )

    if user_prompt:

        st.session_state.messages.append(
            {
                "role":"user",
                "content":user_prompt
            }
        )

        answer = ask_copilot(
            user_prompt,
            report
        )

        st.session_state.messages.append(
            {
                "role":"assistant",
                "content":answer
            }
        )

        st.rerun()

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------

st.set_page_config(
    page_title="Smart Traffic Management System",
    page_icon="🚦",
    layout="wide"
)

# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------

defaults = {

    "report": None,

    "event_lat": None,
    "event_lon": None,

    "origin_lat": None,
    "origin_lon": None,

    "destination_lat": None,
    "destination_lon": None,

    # NEW: tracks the last click already applied, so a stale/sticky
    # click returned by st_folium doesn't get re-applied to a
    # different mode after you switch the radio button.
    "last_applied_click": None,

    # AI Assistant
    "show_chat": False,

    "messages": []
}

for key, value in defaults.items():

    if key not in st.session_state:

        st.session_state[key] = value

if "messages" not in st.session_state:
    st.session_state.messages = []

# --------------------------------------------------
# TITLE
# --------------------------------------------------

st.title("🚦 Smart Traffic Management System")

st.markdown("""
Predict traffic impact, simulate congestion,
recommend diversions and police deployment.
""")

tab1, tab2 = st.tabs(
    [
        "📍 Search Locations",
        "🗺️ Select On Map"
    ]
)

# --------------------------------------------------
# SEARCH LOCATIONS TAB
# --------------------------------------------------
with tab1:

    st.subheader(
        "Search Locations"
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        event_place = st.text_input(
            "Event Location",
            "Silk Board Junction"
        )

    with col2:

        origin_place = st.text_input(
            "Origin Location",
            "Electronic City"
        )

    with col3:

        destination_place = st.text_input(
            "Destination Location",
            "Kempegowda Airport"
        )

    if st.button(
        "Use Location Names"
    ):

        event_coords = get_coordinates(
            event_place
        )

        origin_coords = get_coordinates(
            origin_place
        )

        destination_coords = get_coordinates(
            destination_place
        )

        if (

            event_coords is None

            or

            origin_coords is None

            or

            destination_coords is None

        ):

            st.error(
                "Could not find one or more locations"
            )

        else:

            st.session_state.event_lat = event_coords[0]
            st.session_state.event_lon = event_coords[1]

            st.session_state.origin_lat = origin_coords[0]
            st.session_state.origin_lon = origin_coords[1]

            st.session_state.destination_lat = destination_coords[0]
            st.session_state.destination_lon = destination_coords[1]

            st.success(
                "Locations Loaded Successfully"
            )

# --------------------------------------------------
# CLICK ON MAP TAB
# --------------------------------------------------
with tab2:

    st.subheader(
        "Select Locations On Map"
    )

    mode = st.radio(

        "Select",

        [
            "Event",
            "Origin",
            "Destination"
        ]
    )

    selector_map = folium.Map(

        location=[
            12.9716,
            77.5946
        ],

        zoom_start=11
    )

    # ----------------------------------------------
    # SHOW ALREADY-SELECTED POINTS
    # so you can visually verify what's actually saved
    # before you click again.
    # ----------------------------------------------

    marker_specs = [
        ("Event", st.session_state.event_lat, st.session_state.event_lon, "red"),
        ("Origin", st.session_state.origin_lat, st.session_state.origin_lon, "green"),
        ("Destination", st.session_state.destination_lat, st.session_state.destination_lon, "blue"),
    ]

    for label, lat, lon, color in marker_specs:

        if lat is not None and lon is not None:

            folium.Marker(
                [lat, lon],
                popup=label,
                tooltip=label,
                icon=folium.Icon(color=color)
            ).add_to(selector_map)

    # ----------------------------------------------
    # NOTE: added a fixed `key` so this component keeps
    # a stable identity across reruns (radio switches etc).
    # ----------------------------------------------

    map_data = st_folium(

        selector_map,

        width=1200,

        height=500,

        returned_objects=[
            "last_clicked"
        ],

        key="selector_map"
    )

    if map_data and map_data.get("last_clicked"):

        lat = map_data["last_clicked"]["lat"]
        lon = map_data["last_clicked"]["lng"]

        click = (lat, lon)

        # ------------------------------------------
        # ONLY apply the click if it's actually a NEW
        # click. st_folium returns the same last_clicked
        # value on every rerun (including when you just
        # switch the "mode" radio button) until a fresh
        # click happens. Without this guard, switching
        # mode after clicking once would silently
        # re-apply the old click's coordinates to the
        # newly selected mode.
        # ------------------------------------------

        if click != st.session_state.last_applied_click:

            st.session_state.last_applied_click = click

            if mode == "Event":

                st.session_state.event_lat = lat
                st.session_state.event_lon = lon

            elif mode == "Origin":

                st.session_state.origin_lat = lat
                st.session_state.origin_lon = lon

            elif mode == "Destination":

                st.session_state.destination_lat = lat
                st.session_state.destination_lon = lon

            st.success(
                f"{mode} Location Saved"
            )

            st.rerun()

# --------------------------------------------------
# SHOW SELECTED LOCATIONS
# --------------------------------------------------
st.subheader(
    "Selected Locations"
)

st.write(

    "Event:",

    st.session_state.event_lat,

    st.session_state.event_lon
)

st.write(

    "Origin:",

    st.session_state.origin_lat,

    st.session_state.origin_lon
)

st.write(

    "Destination:",

    st.session_state.destination_lat,

    st.session_state.destination_lon
)

# --------------------------------------------------
# SIDEBAR FORM
# --------------------------------------------------

with st.sidebar.form("simulation_form"):

    st.header("Event Configuration")

    event_type = st.selectbox(
        "Event Type",
        [
            "planned",
            "unplanned"
        ]
    )

    event_cause = st.selectbox(
        "Event Cause",
        [
            "vehicle_breakdown",
            "pot_holes",
            "road_conditions",
            "congestion",
            "public_event",
            "procession",
            "vip_movement",
            "protest",
            "debris",
            "accident",
            "construction",
            "water_logging",
            "tree_fall",
            "others"
        ]
    )
    corridor_risk_map = joblib.load(
        "models/corridor_risk_map.pkl"
)

    station_risk_map = joblib.load(
        "models/station_risk_map.pkl"
)
    corridors = sorted(

        corridor_risk_map.keys()

)

    stations = sorted(

        station_risk_map.keys()

)

    corridor = st.selectbox(

        "Corridor",

        corridors

)

    police_station = st.selectbox(

        "Police Station",

        stations

)

    run_btn = st.form_submit_button(
        "🚀 Run Simulation"
    )

# --------------------------------------------------
# RUN SIMULATION
# --------------------------------------------------

if run_btn:

    try:

        event_lat = st.session_state.event_lat
        event_lon = st.session_state.event_lon

        origin_lat = st.session_state.origin_lat
        origin_lon = st.session_state.origin_lon

        destination_lat = st.session_state.destination_lat
        destination_lon = st.session_state.destination_lon

        if (

            event_lat is None

            or

            origin_lat is None

            or

            destination_lat is None

        ):

            st.error(
                "Please select all locations first."
            )

            st.stop()

        current_time = datetime.now()

        event_df = pd.DataFrame([{

            "latitude": event_lat,
            "longitude": event_lon,

            "event_type": event_type,
            "event_cause": event_cause,

            "corridor": corridor,
            "police_station": police_station,

            "start_datetime": current_time

        }])

        report = simulate_event(

            event_df=event_df,

            origin_lat=origin_lat,
            origin_lon=origin_lon,

            destination_lat=destination_lat,
            destination_lon=destination_lon
        )

        st.session_state.report = report

        st.session_state.event_lat = event_lat
        st.session_state.event_lon = event_lon

        st.success(
            "Simulation Completed Successfully"
        )

    except Exception as e:

        st.error(
            f"Simulation Error: {str(e)}"
        )

    if "show_chat" not in st.session_state:
        st.session_state.show_chat = False


# --------------------------------------------------
# DISPLAY REPORT
# --------------------------------------------------

if st.session_state.report is not None:

    report = st.session_state.report

    event_lat = st.session_state.event_lat
    event_lon = st.session_state.event_lon

    # ------------------------------------------
    # KPI CARDS
    # ------------------------------------------

    st.subheader("Simulation Results")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Impact Class",
        report["Impact Class"]
    )

    col2.metric(
        "Delay (sec)",
        report["Delay Seconds"]
    )

    col3.metric(
        "Police Required",
        report["Police Deployment"]
    )

    col4.metric(
        "Route Changed",
        str(report["Route Changed"])
    )

    # ------------------------------------------
    # RECOMMENDATION
    # ------------------------------------------

    st.success(
        f"Recommendation: {report['Recommendation']}"
    )

    # -----------------------------------
    # AI COPILOT
    # -----------------------------------

    # st.subheader(
    #     "🤖 AI Traffic Copilot"
    # )

    copilot_text = generate_copilot_response(
        report
    )

    st.markdown(
        copilot_text
    )

    # -----------------------------------
    # EXPLAINABLE AI
    # -----------------------------------

    st.subheader(
        "🧠 Why This Prediction?"
    )

    reasons = explain_prediction(

        report["Impact Class"],

        report["Delay Seconds"],

        report["Affected Roads"],

        report["Police Deployment"]
    )

    for reason in reasons:

        st.write(
            "✅", reason
    )

    # ------------------------------------------
    # ROUTE INFO
    # ------------------------------------------

    st.subheader("Route Information")

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Normal Distance (m)",
        report["Normal Distance"]
    )

    c2.metric(
        "Alternative Distance (m)",
        report["Alternative Distance"]
    )

    c3.metric(
        "Extra Distance (m)",
        report["Extra Distance"]
    )

    # ------------------------------------------
    # ETA INFO
    # ------------------------------------------

    st.subheader("ETA Information")

    c4, c5, c6 = st.columns(3)

    c4.metric(
        "Normal ETA (sec)",
        report["Normal ETA"]
    )

    c5.metric(
        "Alternative ETA (sec)",
        report["Alternative ETA"]
    )

    c6.metric(
        "Delay %",
        report["Delay Percentage"]
    )

    # ------------------------------------------
    # NETWORK INFO
    # ------------------------------------------

    st.subheader("Network Impact")

    c7, c8, c9 = st.columns(3)

    c7.metric(
        "Affected Nodes",
        report["Affected Nodes"]
    )

    c8.metric(
        "Affected Roads",
        report["Affected Roads"]
    )

    c9.metric(
        "Critical Junctions",
        report["Critical Junctions"]
    )

    st.subheader(
        "🚨 Traffic Command Center"
    )

    impact = report["Impact Class"]

    if impact == "High":

        st.error(
            """
            HIGH PRIORITY INCIDENT

            • Deploy response team

            • Activate diversions

            • Notify emergency services

            • Push commuter alerts
            """
        )

    elif impact == "Medium":

        st.warning(
            """
            MEDIUM PRIORITY INCIDENT

            • Monitor congestion

            • Adjust signal timing

            • Prepare diversion routes
            """
        )

    else:

        st.success(
            """
            LOW PRIORITY INCIDENT

            • Routine monitoring

            • No major intervention required
            """
        )

    playbooks = {

        "High":[
            "Deploy officers",
            "Activate diversions",
            "Issue commuter alerts",
            "Monitor every 5 minutes"
        ],

        "Medium":[
            "Monitor congestion",
            "Optimize traffic signals",
            "Prepare backup route"
        ],

        "Low":[
            "Routine monitoring"
        ]
    }

    st.subheader(
        "📋 Incident Playbook"
    )

    for step in playbooks[
        report["Impact Class"]
    ]:

        st.write(
            "➡️", step
        )

    # ------------------------------------------
    # REPORT
    # ------------------------------------------

    st.subheader("Detailed Report")

    st.json(report)

    # ------------------------------------------
    # MAP
    # ------------------------------------------

    st.subheader(
        "Digital Twin Traffic View"
    )

    try:

        traffic_map = create_map(
            report,
            event_lat,
            event_lon
        )

        st_folium(
            traffic_map,
            width=1200,
            height=700,
            returned_objects=[],
            key="result_map"
        )

    except Exception as e:

        st.error(
            f"Map Error: {str(e)}"
        )

    # ------------------------------------------
    # AI COPILOT BUTTON
    # ------------------------------------------

    st.markdown(
        """
        <style>
        .stButton button {
            border-radius: 50%;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns([9,1,1])

    with col3:

        if st.button(
            "🤖",
            key="traffic_copilot"
        ):
            st.session_state.chat_open = True

            if st.session_state.chat_open:
                ai_chat_popup(report)