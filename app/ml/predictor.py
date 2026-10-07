import json
import os
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

_DEFAULT_ML_DIR = Path(__file__).resolve().parent.parent.parent
ML_DIR = Path(os.getenv("SENTRA_ML_DIR", str(_DEFAULT_ML_DIR)))
MODEL_PATH = ML_DIR / "saved_models" / "best_model.joblib"
METADATA_PATH = ML_DIR / "saved_models" / "metadata.json"
CLASS_ANCHORS = {"LOW": 10, "MEDIUM": 45, "HIGH": 72, "CRITICAL": 92}

FEATURE_DISPLAY = {
    "num__hour": "Time of day",
    "num__day_of_week": "Day of week",
    "num__is_weekend": "Weekend travel",
    "num__is_night": "Late-night travel",
    "num__incident_density_7d": "Recent incident density",
    "num__incident_severity_avg": "Average incident severity",
    "num__lighting_score": "Street lighting",
    "num__transit_access": "Transit availability",
    "num__crowd_density": "Crowd density",
    "num__route_length_km": "Route length",
    "num__user_baseline_deviation": "Deviation from usual journey",
    "num__is_solo": "Travelling alone",
    "num__has_live_share": "Live location shared",
    "cat__area_type_residential": "Residential area",
    "cat__area_type_commercial": "Commercial area",
    "cat__area_type_isolated": "Isolated area",
    "cat__area_type_transit_hub": "Transit hub",
    "cat__area_type_industrial": "Industrial area",
    "cat__journey_type_walk": "Walking",
    "cat__journey_type_public_transport": "Public transport",
    "cat__journey_type_cab": "Cab",
    "cat__journey_type_solo_car": "Solo car",
    "cat__journey_type_shared_ride": "Shared ride",
}


class RiskPredictor:
    def __init__(self):
        if not MODEL_PATH.exists() or not METADATA_PATH.exists():
            raise FileNotFoundError(
                "Risk model artifacts not found. Run the ML pipeline first: "
                "python -m src.train"
            )
        self.pipeline = joblib.load(MODEL_PATH)
        self.metadata = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
        self.classes = self.metadata["classes"]

    def _score_from_probs(self, probs):
        return int(round(sum(probs.get(c, 0.0) * CLASS_ANCHORS[c] for c in self.classes)))

    def _level_from_score(self, score):
        if score < 35:
            return "LOW"
        if score < 65:
            return "MEDIUM"
        if score < 85:
            return "HIGH"
        return "CRITICAL"

    def _evidence_score(self, row):
        score = 100
        if row.get("incident_density_7d", 0) == 0:
            score -= 15
        if row.get("route_length_km", 10) < 1:
            score -= 10
        if row.get("user_baseline_deviation", 0) == 0:
            score -= 10
        return int(max(30, min(100, score)))

    def _explain(self, row_df, k=5):
        prep = self.pipeline.named_steps["prep"]
        clf = self.pipeline.named_steps["clf"]
        Xt = prep.transform(row_df)
        names = prep.get_feature_names_out()

        if hasattr(clf, "coef_"):
            coef = clf.coef_
            x = np.asarray(Xt).ravel()
            if coef.shape[0] == 1:
                w = coef[0]
            else:
                pred_idx = int(np.argmax(self.pipeline.predict_proba(row_df)[0]))
                w = coef[pred_idx]
            contributions = w * x
            order = np.argsort(-np.abs(contributions))[:k]
            out = []
            for i in order:
                name = names[i]
                val = float(contributions[i])
                out.append({
                    "factor": FEATURE_DISPLAY.get(name, name),
                    "contribution": abs(val),
                    "direction": "+" if val > 0 else "-",
                })
            if out and out[0]["contribution"] > 0:
                scale = 15.0 / out[0]["contribution"]
                for o in out:
                    o["contribution"] = round(o["contribution"] * scale, 1)
            return out
        else:
            imp = getattr(clf, "feature_importances_", None)
            if imp is None:
                return []
            order = np.argsort(-imp)[:k]
            return [
                {
                    "factor": FEATURE_DISPLAY.get(names[i], names[i]),
                    "contribution": round(float(imp[i]) * 100, 1),
                    "direction": "+",
                }
                for i in order
            ]

    def predict(self, context):
        row_df = pd.DataFrame([{
            "hour": context["hour"],
            "day_of_week": context["day_of_week"],
            "is_weekend": int(context["day_of_week"] >= 5),
            "is_night": int(context["hour"] >= 22 or context["hour"] <= 5),
            "area_type": context["area_type"],
            "journey_type": context["journey_type"],
            "incident_density_7d": context["incident_density_7d"],
            "incident_severity_avg": context["incident_severity_avg"],
            "lighting_score": context["lighting_score"],
            "transit_access": context["transit_access"],
            "crowd_density": context["crowd_density"],
            "route_length_km": context["route_length_km"],
            "user_baseline_deviation": context["user_baseline_deviation"],
            "is_solo": int(context["is_solo"]),
            "has_live_share": int(context["has_live_share"]),
        }])

        probs_arr = self.pipeline.predict_proba(row_df)[0]
        probs = {c: float(p) for c, p in zip(self.pipeline.classes_, probs_arr)}

        risk_score = self._score_from_probs(probs)
        risk_level = self._level_from_score(risk_score)

        model_conf = int(round(probs.get(risk_level, 0.0) * 100))
        evidence = self._evidence_score(context)
        combined = int(round(0.7 * model_conf + 0.3 * evidence))

        return {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "confidence": combined,
            "model_confidence": model_conf,
            "evidence_score": evidence,
            "factors": self._explain(row_df),
            "model_name": self.metadata["best_model"],
            "model_version": self.metadata.get("trained_at", "unknown"),
        }


_predictor = None


def get_predictor():
    global _predictor
    if _predictor is None:
        try:
            _predictor = RiskPredictor()
        except Exception:
            _predictor = None
    return _predictor
