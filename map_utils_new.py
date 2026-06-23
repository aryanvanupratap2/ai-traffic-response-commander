import os
import osmnx as ox
import folium


# --------------------------------------------------
# LOAD GRAPH ONCE
# --------------------------------------------------

import streamlit as st

# --------------------------------------------------
# FIX: previously hardcoded to an absolute Windows path
# (C:\Users\admin\Desktop\...). This must point to the
# SAME graph file used in stimulator.py, otherwise node
# IDs won't match between the simulation (which computes
# routes) and the map (which draws them) — that mismatch
# is a common cause of routes/markers showing up in
# unexpected places.
# --------------------------------------------------


@st.cache_resource
def load_graph():
    return ox.load_graphml(
        r"C:\Users\admin\Desktop\Traffic Management\graph\bangalore_graph.graphml"
    )

G = load_graph()

# --------------------------------------------------
# CREATE DIGITAL TWIN MAP
# --------------------------------------------------

def create_map(
    report,
    event_lat,
    event_lon
):

    # ---------------------------------------------
    # IMPACT RADIUS
    # ---------------------------------------------

    radius_map = {

        "Low": 200,

        "Medium": 500,

        "High": 1000
    }

    impact_radius = radius_map.get(
        report["Impact Class"],
        500
    )

    # ---------------------------------------------
    # BASE MAP
    # ---------------------------------------------

    m = folium.Map(

        location=[
            event_lat,
            event_lon
        ],

        zoom_start=14,

        control_scale=True
    )

    # ---------------------------------------------
    # EVENT MARKER
    # ---------------------------------------------

    folium.Marker(

        location=[
            event_lat,
            event_lon
        ],

        popup=f"""
        Event Location

        Impact: {report['Impact Class']}
        """,

        tooltip="Traffic Event",

        icon=folium.Icon(
            color="red",
            icon="warning-sign"
        )

    ).add_to(m)
    print("Event Marker Done")

    # ---------------------------------------------
    # IMPACT ZONE
    # ---------------------------------------------

    folium.Circle(

        location=[
            event_lat,
            event_lon
        ],

        radius=impact_radius,

        color="red",

        fill=True,

        fill_opacity=0.2,

        popup=f"""
        Impact Zone

        Radius:
        {impact_radius} m
        """

    ).add_to(m)
    print("Impact Circle Done")

    # ---------------------------------------------
    # NORMAL ROUTE
    # ---------------------------------------------

    normal_route = report[
        "Normal Route"
    ]

    normal_coords = []

    for node in normal_route[::10]:

        normal_coords.append([

            G.nodes[node]["y"],

            G.nodes[node]["x"]

        ])

    folium.PolyLine(

        normal_coords,

        color="green",

        weight=6,

        opacity=0.8,

        tooltip="Normal Route"

    ).add_to(m)
    print("Normal Route Done")

    # ---------------------------------------------
    # ALTERNATIVE ROUTE
    # ---------------------------------------------

    alt_route = report[
        "Alternative Route"
    ]

    alt_coords = []

    for node in alt_route[::10]:

        alt_coords.append([

            G.nodes[node]["y"],

            G.nodes[node]["x"]

        ])

    folium.PolyLine(

        alt_coords,

        color="blue",

        weight=6,

        opacity=0.8,

        tooltip="Alternative Route"

    ).add_to(m)
    print("Alternative Route Done")

    print("Normal Route Length:", len(normal_route))
    print("Alternative Route Length:", len(alt_route))

    # ---------------------------------------------
    # START MARKER
    # ---------------------------------------------

    start_node = normal_route[0]

    folium.Marker(

        [

            G.nodes[start_node]["y"],

            G.nodes[start_node]["x"]

        ],

        popup="Origin",

        icon=folium.Icon(
            color="green"
        )

    ).add_to(m)

    # ---------------------------------------------
    # DESTINATION MARKER
    # ---------------------------------------------

    end_node = normal_route[-1]

    folium.Marker(

        [

            G.nodes[end_node]["y"],

            G.nodes[end_node]["x"]

        ],

        popup="Destination",

        icon=folium.Icon(
            color="blue"
        )

    ).add_to(m)

    # ---------------------------------------------
    # POLICE DEPLOYMENT INFO
    # ---------------------------------------------

    folium.Marker(

        [event_lat, event_lon],

        popup=f"""
        Police Units Required:
        {report['Police Deployment']}
        """,

        icon=folium.Icon(
            color="orange"
        )

    ).add_to(m)

    print(type(m))

    return m
