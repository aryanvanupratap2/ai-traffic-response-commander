import joblib
import pandas as pd

# Load everything once

model = joblib.load(
    "models/final_catboost_model.pkl"
)

kmeans = joblib.load(
    "models/kmeans.pkl"
)

event_cause_encoder = joblib.load(
    "models/event_cause_encoder.pkl"
)

event_type_encoder = joblib.load(
    "models/event_type_encoder.pkl"
)

target_encoder = joblib.load(
    "models/target_encoder.pkl"
)

corridor_risk_map = joblib.load(
    "models/corridor_risk_map.pkl"
)

station_risk_map = joblib.load(
    "models/station_risk_map.pkl"
)

feature_columns = joblib.load(
    "models/feature_columns.pkl"
)

# Feature Engineering

def prepare_features(df):

    df = df.copy()

    df["start_datetime"] = pd.to_datetime(
        df["start_datetime"],
        format="mixed"
    )

    df["hour"] = df["start_datetime"].dt.hour

    df["dayofweek"] = (
        df["start_datetime"]
        .dt.dayofweek
    )

    df["month"] = (
        df["start_datetime"]
        .dt.month
    )

    df["weekend"] = (
        df["dayofweek"] >= 5
    ).astype(int)

    df["rush_hour"] = (
        (
            (df["hour"] >= 7)
            &
            (df["hour"] <= 10)
        )
        |
        (
            (df["hour"] >= 17)
            &
            (df["hour"] <= 20)
        )
    ).astype(int)

    df["event_cause_encoded"] = (
        event_cause_encoder
        .transform(
            df["event_cause"]
        )
    )

    df["event_type_encoded"] = (
        event_type_encoder
        .transform(
            df["event_type"]
        )
    )

    df["corridor_risk"] = (

    df["corridor"]

    .map(corridor_risk_map)

)

    df["station_risk"] = (

    df["police_station"]

    .map(station_risk_map)

)

    if df["corridor_risk"].isnull().any():

        raise ValueError(

            "Please select a valid corridor."

    )

    if df["station_risk"].isnull().any():

        raise ValueError(

            "Please select a valid police station."

    )
    coords = df[
        [
            "latitude",
            "longitude"
        ]
    ]

    df["location_cluster"] = (
        kmeans.predict(coords)
    )

    # --------------------------------------------------
    # NOTE: feature_columns is the slice the MODEL actually
    # consumes. corridor_risk / station_risk may or may not
    # be inside it. We grab their values from `df` (the full
    # frame) BEFORE slicing, so we can hand them back to the
    # caller regardless of whether the model itself uses them.
    # --------------------------------------------------

    X = df[feature_columns]

    # --------------------------------------------------
    # station_risk_map_max is included so downstream code
    # (stimulator.py's police deployment formula) can
    # normalize station_risk to a 0-1 scale without needing
    # to reload/reimport station_risk_map itself.
    # --------------------------------------------------

    if isinstance(station_risk_map, dict):
        max_station_risk = max(station_risk_map.values())
    else:
        max_station_risk = station_risk_map.max()

    risk_info = {
        "corridor_risk": float(df["corridor_risk"].iloc[0]),
        "station_risk": float(df["station_risk"].iloc[0]),
        "station_risk_map_max": float(max_station_risk),
    }

    return X, risk_info

# Prediction Function

def predict_impact(event_df):

    X, risk_info = prepare_features(
        event_df
    )

    # --------------------------------------------------
    # DEBUG: uncomment to inspect exactly what's reaching
    # the model on each run. Useful for confirming whether
    # frozen inputs (e.g. hardcoded start_datetime) are why
    # Impact Class keeps coming back the same every time.
    # --------------------------------------------------
    # print(X.to_dict(orient="records"))
    # if hasattr(model, "predict_proba"):
    #     print(model.predict_proba(X))

    pred = model.predict(X)

    pred = pred.flatten()

    label = (
        target_encoder
        .inverse_transform(
            pred.astype(int)
        )
    )

    # --------------------------------------------------
    # Now returns impact label PLUS the risk scores, so
    # downstream code (e.g. police deployment sizing in
    # stimulator.py) doesn't need to re-load the risk maps
    # or recompute them separately.
    # --------------------------------------------------

    return label[0], risk_info
