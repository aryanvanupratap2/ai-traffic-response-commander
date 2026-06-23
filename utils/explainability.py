def explain_prediction(
        impact_class,
        delay,
        affected_roads,
        police_required
):

    reasons = []

    if impact_class == "High":

        reasons.append(
            "High impact classification generated."
        )

    if delay > 500:

        reasons.append(
            "Large expected traffic delay."
        )

    if affected_roads > 1000:

        reasons.append(
            "Large portion of road network affected."
        )

    if police_required > 10:

        reasons.append(
            "Significant police deployment required."
        )

    return reasons
