import osmnx as ox
import networkx as nx
import pandas as pd
import streamlit as st

from utils.predictor_new import predict_impact


# ==========================================================
# LOAD GRAPH
# ==========================================================

@st.cache_resource
def load_graph():

    graph_path = "graph/bangalore_graph.graphml"

    return ox.load_graphml(graph_path)


G = load_graph()


# ==========================================================
# IMPACT RADIUS
# ==========================================================

def get_impact_radius(impact_class):

    radius_map = {

        "Low": 200,

        "Medium": 500,

        "High": 1000

    }

    return radius_map.get(impact_class, 500)


# ==========================================================
# CONGESTION FACTOR
# ==========================================================

def get_congestion_factor(impact_class):

    congestion = {

        "Low": 1.20,

        "Medium": 1.80,

        "High": 3.00

    }

    return congestion.get(impact_class, 1.50)


# ==========================================================
# POLICE DEPLOYMENT
# ==========================================================

def calculate_police_required(

        impact_class,

        affected_roads,

        total_roads_in_graph,

        station_risk,

        max_station_risk,

        event_cause,

        rush_hour,

        route_distance

):

    # ----------------------------------------
    # Impact Severity
    # ----------------------------------------

    severity_score = {

        "Low": 0.30,

        "Medium": 0.65,

        "High": 1.00

    }.get(impact_class, 0.50)

    # ----------------------------------------
    # Network Impact
    # ----------------------------------------

    area_score = min(

        1.0,

        affected_roads /

        max(

            1,

            total_roads_in_graph * 0.05

        )

    )

    # ----------------------------------------
    # Station Risk
    # ----------------------------------------

    if max_station_risk > 0:

        station_score = (

            station_risk /

            max_station_risk

        )

    else:

        station_score = 0

    # ----------------------------------------
    # Event Urgency
    # ----------------------------------------

    cause_score = {

        "accident": 1.00,

        "public_event": 1.00,

        "vip_movement": 1.00,

        "tree_fall": 0.80,

        "procession": 0.80,

        "water_logging": 0.70,

        "congestion": 0.60,

        "vehicle_breakdown": 0.50,

        "construction": 0.30,

        "pot_holes": 0.20,

        "road_conditions": 0.20,

        "others": 0.10

    }.get(

        event_cause,

        0.50

    )

    # ----------------------------------------
    # Route Distance Score
    # ----------------------------------------

    route_score = min(

        1.0,

        route_distance / 30000

    )

    # ----------------------------------------
    # Rush Hour
    # ----------------------------------------

    rush_score = 1 if rush_hour else 0

    # ----------------------------------------
    # Final Demand Score
    # ----------------------------------------

    demand_score = (

        0.25 * severity_score +

        0.15 * area_score +

        0.15 * station_score +

        0.15 * cause_score +

        0.20 * route_score +

        0.10 * rush_score

    )

    # ----------------------------------------
    # Officer Limits
    # ----------------------------------------

    MIN_OFFICERS = 2

    MAX_OFFICERS = 100

    police_required = round(

        MIN_OFFICERS +

        demand_score *

        (MAX_OFFICERS - MIN_OFFICERS)

    )

    police_required = max(

        MIN_OFFICERS,

        police_required

    )

    return police_required


# ==========================================================
# FIND NEAREST NODE
# FIXES MAP LOCATION BUG
# ==========================================================

def get_node(lat, lon):

    node = ox.distance.nearest_nodes(

        G,

        X=lon,

        Y=lat

    )

    return node


# ==========================================================
# DEBUG LOCATION MATCHING
# ==========================================================

def verify_location(node, lat, lon):

    graph_lat = G.nodes[node]["y"]

    graph_lon = G.nodes[node]["x"]

    return {

        "selected_lat": lat,

        "selected_lon": lon,

        "graph_lat": graph_lat,

        "graph_lon": graph_lon

    }

def simulate_event(

        event_df,

        origin_lat,
        origin_lon,

        destination_lat,
        destination_lon

):

    # ======================================================
    # STEP 1 : IMPACT PREDICTION
    # ======================================================

    impact_class, risk_info = predict_impact(event_df)

    corridor_risk = risk_info["corridor_risk"]

    station_risk = risk_info["station_risk"]

    max_station_risk = risk_info["station_risk_map_max"]

    # ======================================================
    # STEP 2 : EVENT DETAILS
    # ======================================================

    event_lat = event_df.iloc[0]["latitude"]

    event_lon = event_df.iloc[0]["longitude"]

    event_cause = event_df.iloc[0]["event_cause"]

    event_time = pd.to_datetime(

        event_df.iloc[0]["start_datetime"]

    )

    rush_hour = (

        (7 <= event_time.hour <= 10)

        or

        (17 <= event_time.hour <= 20)

    )

    # ======================================================
    # STEP 3 : IMPACT RADIUS
    # ======================================================

    impact_radius = get_impact_radius(

        impact_class

    )

    # ======================================================
    # STEP 4 : NODE MAPPING
    # ======================================================

    event_node = get_node(

        event_lat,

        event_lon

    )

    origin_node = get_node(

        origin_lat,

        origin_lon

    )

    destination_node = get_node(

        destination_lat,

        destination_lon

    )

    # ======================================================
    # STEP 5 : DEBUG LOCATION
    # ======================================================

    location_debug = {

        "event": verify_location(

            event_node,

            event_lat,

            event_lon

        ),

        "origin": verify_location(

            origin_node,

            origin_lat,

            origin_lon

        ),

        "destination": verify_location(

            destination_node,

            destination_lat,

            destination_lon

        )

    }

    # ======================================================
    # STEP 6 : AFFECTED NODES
    # ======================================================

    affected_nodes = []

    event_x = G.nodes[event_node]["x"]

    event_y = G.nodes[event_node]["y"]

    for node in G.nodes():

        node_x = G.nodes[node]["x"]

        node_y = G.nodes[node]["y"]

        distance = ox.distance.great_circle(

            event_y,

            event_x,

            node_y,

            node_x

        )

        if distance <= impact_radius:

            affected_nodes.append(node)

    affected_set = set(

        affected_nodes

    )

    # ======================================================
    # STEP 7 : NORMAL ROUTE
    # ======================================================

    normal_route = nx.shortest_path(

        G,

        origin_node,

        destination_node,

        weight="length"

    )

    normal_distance = nx.path_weight(

        G,

        normal_route,

        weight="length"

    )

    # ======================================================
    # STEP 8 : ETA
    # ======================================================

    average_speed = 10.5

    if rush_hour:

        average_speed *= 0.80

    normal_eta = (

        normal_distance /

        average_speed

    )

    # ======================================================
    # STEP 9 : COPY GRAPH
    # ======================================================

    G_temp = G.copy()

    congestion_penalty = get_congestion_factor(

        impact_class

    )

    for u, v, k, data in G_temp.edges(

            keys=True,

            data=True

    ):

        if (

                u in affected_set

                or

                v in affected_set

        ):

            data["length"] *= congestion_penalty

    # ======================================================
    # STEP 10 : ALTERNATIVE ROUTE
    # ======================================================

    try:

        alternative_route = nx.shortest_path(

            G_temp,

            origin_node,

            destination_node,

            weight="length"

        )

        alternative_distance = nx.path_weight(

            G_temp,

            alternative_route,

            weight="length"

        )

    except Exception:

        alternative_route = normal_route

        alternative_distance = normal_distance

    # ======================================================
    # STEP 11 : ALTERNATIVE ETA
    # ======================================================

    alternative_eta = (

        alternative_distance /

        average_speed

    )

    # ======================================================
    # STEP 12 : ROUTE CHANGE
    # ======================================================

    route_changed = (

        normal_route != alternative_route

    )

    # ======================================================
    # STEP 13 : DELAY
    # ======================================================

    delay_seconds = max(

        0,

        alternative_eta -

        normal_eta

    )

    delay_percentage = (

        delay_seconds /

        max(normal_eta, 1)

    ) * 100

        # ======================================================
    # STEP 14 : AFFECTED ROADS
    # ======================================================

    affected_roads = 0

    for u, v in G.edges():

        if (

            u in affected_set

            or

            v in affected_set

        ):

            affected_roads += 1

    total_roads = G.number_of_edges()

    # ======================================================
    # STEP 15 : CRITICAL JUNCTIONS
    # ======================================================

    degree_dict = dict(

        G.degree(

            affected_nodes

        )

    )

    critical_junctions = sorted(

        degree_dict,

        key=degree_dict.get,

        reverse=True

    )[:10]

    # ======================================================
    # STEP 16 : POLICE DEPLOYMENT
    # ======================================================

    police_required = calculate_police_required(

        impact_class=impact_class,

        affected_roads=affected_roads,

        total_roads_in_graph=total_roads,

        station_risk=station_risk,

        max_station_risk=max_station_risk,

        event_cause=event_cause,

        rush_hour=rush_hour,

        route_distance=normal_distance

    )

    # ======================================================
    # STEP 17 : ROUTE ANALYSIS
    # ======================================================

    route_nodes = set(

        normal_route

    )

    impacted_route_nodes = len(

        route_nodes.intersection(

            affected_set

        )

    )

    extra_distance = (

        alternative_distance -

        normal_distance

    )

    # ======================================================
    # STEP 18 : RECOMMENDATION
    # ======================================================

    if route_changed:

        recommendation = (

            "Use Alternative Route"

        )

    elif impact_class == "High":

        recommendation = (

            "Heavy Congestion Expected. Travel Only If Necessary."

        )

    elif impact_class == "Medium":

        recommendation = (

            "Expect Moderate Delays."

        )

    else:

        recommendation = (

            "Current Route Is Safe."

        )

    # ======================================================
    # STEP 19 : OPERATIONAL PRIORITY
    # ======================================================

    if (

        impact_class == "High"

        or

        police_required >= 20

    ):

        operational_priority = "HIGH"

    elif (

        impact_class == "Medium"

        or

        police_required >= 10

    ):

        operational_priority = "MEDIUM"

    else:

        operational_priority = "LOW"

    # ======================================================
    # STEP 20 : DEBUG OUTPUT
    # ======================================================

    debug = {

        "corridor_risk": corridor_risk,

        "station_risk": station_risk,

        "rush_hour": rush_hour,

        "location_match": location_debug

    }

    # ======================================================
    # STEP 21 : FINAL REPORT
    # ======================================================

    report = {

        # Prediction

        "Impact Class": impact_class,

        # Route

        "Origin Node": int(origin_node),

        "Destination Node": int(destination_node),

        "Event Node": int(event_node),

        "Normal Route": normal_route,

        "Alternative Route": alternative_route,

        "Route Changed": route_changed,

        # Distance

        "Normal Distance": round(

            normal_distance,

            2

        ),

        "Alternative Distance": round(

            alternative_distance,

            2

        ),

        "Extra Distance": round(

            extra_distance,

            2

        ),

        # ETA

        "Normal ETA": round(

            normal_eta,

            2

        ),

        "Alternative ETA": round(

            alternative_eta,

            2

        ),

        "Delay Seconds": round(

            delay_seconds,

            2

        ),

        "Delay Percentage": round(

            delay_percentage,

            2

        ),

        # Network

        "Affected Nodes": len(

            affected_nodes

        ),

        "Affected Roads": affected_roads,

        "Critical Junctions": len(

            critical_junctions

        ),

        "Nodes affected on route": impacted_route_nodes,

        # Police

        "Police Deployment": police_required,

        # Decision

        "Recommendation": recommendation,

        "Operational Priority": operational_priority,

        # Debug

        "Debug": debug

    }

    return report