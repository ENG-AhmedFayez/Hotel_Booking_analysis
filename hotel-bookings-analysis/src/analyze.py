
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (ConfusionMatrixDisplay, accuracy_score,
                             average_precision_score, classification_report,
                             f1_score, precision_score, recall_score,
                             roc_auc_score, roc_curve)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "hotel_bookings.csv"
REPORTS = ROOT / "reports"
RANDOM_STATE = 42


def main() -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    raw = pd.read_csv(DATA)
    duplicate_rows = int(raw.duplicated().sum())
    df = raw.drop_duplicates().copy()
    df["children"] = df["children"].fillna(0)
    df["agent"] = df["agent"].fillna(-1).astype(int).astype(str)
    df["arrival_month_num"] = pd.to_datetime(df["arrival_date_month"], format="%B").dt.month
    df["total_nights"] = df["stays_in_weekend_nights"] + df["stays_in_week_nights"]
    df["total_guests"] = df[["adults", "children", "babies"]].sum(axis=1)
    df["is_family"] = ((df["children"] + df["babies"]) > 0).astype(int)

    target = df["is_canceled"].astype(int)
    
    # These fields describe the realized outcome or can be updated after booking.
    
    leakage_columns = ["reservation_status", "reservation_status_date",
                       "assigned_room_type", "booking_changes"]
    drop_columns = ["is_canceled", "arrival_date_month", "arrival_date_week_number",
                    "arrival_date_day_of_month", "stays_in_weekend_nights",
                    "stays_in_week_nights", "adults", "children", "babies",
                    "company", *leakage_columns]
    X = df.drop(columns=drop_columns)
    numeric = X.select_dtypes(include="number").columns.tolist()
    categorical = X.select_dtypes(exclude="number").columns.tolist()
    preprocess = ColumnTransformer([
        ("num", Pipeline([("impute", SimpleImputer(strategy="median")),
                          ("scale", StandardScaler())]), numeric),
        ("cat", Pipeline([("impute", SimpleImputer(strategy="most_frequent")),
                          ("encode", OneHotEncoder(handle_unknown="ignore"))]), categorical),
    ])
    models = {
        "Logistic Regression": LogisticRegression(max_iter=1600, class_weight="balanced"),
        "Random Forest": RandomForestClassifier(n_estimators=250, max_depth=16,
                                                 min_samples_leaf=4,
                                                 class_weight="balanced_subsample",
                                                 random_state=RANDOM_STATE, n_jobs=-1),
    }
    X_train, X_test, y_train, y_test = train_test_split(
        X, target, test_size=0.25, random_state=RANDOM_STATE, stratify=target)

    metrics: dict[str, dict[str, float]] = {}
    probabilities: dict[str, object] = {}
    predictions: dict[str, object] = {}
    importances: dict[str, float] = {}
    fitted: dict[str, Pipeline] = {}
    for name, estimator in models.items():
        pipe = Pipeline([("preprocess", preprocess), ("classifier", estimator)])
        pipe.fit(X_train, y_train)
        pred = pipe.predict(X_test)
        prob = pipe.predict_proba(X_test)[:, 1]
        fitted[name], predictions[name], probabilities[name] = pipe, pred, prob
        metrics[name] = {
            "roc_auc": round(float(roc_auc_score(y_test, prob)), 4),
            "average_precision": round(float(average_precision_score(y_test, prob)), 4),
            "accuracy": round(float(accuracy_score(y_test, pred)), 4),
            "precision": round(float(precision_score(y_test, pred, zero_division=0)), 4),
            "recall": round(float(recall_score(y_test, pred, zero_division=0)), 4),
            "f1": round(float(f1_score(y_test, pred, zero_division=0)), 4),
        }
        slug = "logistic_regression" if name.startswith("Logistic") else "random_forest"
        (REPORTS / f"{slug}_classification_report.txt").write_text(
            classification_report(y_test, pred, target_names=["Completed", "Canceled"]), encoding="utf-8")
        if name == "Random Forest":
            names = pipe.named_steps["preprocess"].get_feature_names_out()
            values = pipe.named_steps["classifier"].feature_importances_
            importances = dict(zip(names, values))

    best_name = max(metrics, key=lambda name: metrics[name]["roc_auc"])
    hotel_cancel = (df.groupby("hotel", observed=True)["is_canceled"].agg(["size", "mean"])
                    .rename(columns={"size": "bookings", "mean": "cancellation_rate"}))
    deposit_cancel = (df.groupby("deposit_type", observed=True)["is_canceled"].agg(["size", "mean"])
                      .rename(columns={"size": "bookings", "mean": "cancellation_rate"}))
    lead_time_median = df.groupby("is_canceled", observed=True)["lead_time"].median()
    special_requests_mean = df.groupby("is_canceled", observed=True)["total_of_special_requests"].mean()
    result = {
        "source_rows": int(len(raw)), "exact_duplicate_rows_removed": duplicate_rows,
        "analysis_rows": int(len(df)), "columns_in_source": int(raw.shape[1]),
        "cancellation_rate_after_deduplication": round(float(target.mean()), 4),
        "target_counts_after_deduplication": {"completed": int((target == 0).sum()),
                                               "canceled": int((target == 1).sum())},
        "missing_values_source": {key: int(value) for key, value in raw.isna().sum().items() if value},
        "excluded_from_model": leakage_columns + ["company"],
        "test_rows": int(len(y_test)), "models": metrics,
        "highest_roc_auc_model": best_name,
        "median_lead_time_days": {"completed": float(lead_time_median.loc[0]),
                                  "canceled": float(lead_time_median.loc[1])},
        "mean_special_requests": {"completed": round(float(special_requests_mean.loc[0]), 3),
                                   "canceled": round(float(special_requests_mean.loc[1]), 3)},
        "hotel_cancellation_rate": {str(index): {"bookings": int(row.bookings),
                                                  "rate": round(float(row.cancellation_rate), 4)}
                                    for index, row in hotel_cancel.iterrows()},
        "deposit_cancellation_rate": {str(index): {"bookings": int(row.bookings),
                                                    "rate": round(float(row.cancellation_rate), 4)}
                                      for index, row in deposit_cancel.iterrows()},
        "split": {"type": "stratified random holdout", "test_size": 0.25,
                  "random_state": RANDOM_STATE},
    }
    (REPORTS / "metrics.json").write_text(json.dumps(result, indent=2), encoding="utf-8")

    # EDA figures
    hotel_cancel["cancellation_rate"].sort_values(ascending=False).mul(100).plot(
        kind="bar", color=["#315b73", "#6d9a91"], figsize=(7, 4.5))
    plt.title("Cancellation rate by hotel type")
    plt.xlabel("")
    plt.ylabel("Canceled bookings (%)")
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.savefig(REPORTS / "cancellation_by_hotel.png", dpi=170)
    plt.close()

    bins = [-1, 7, 30, 90, 180, 365, float("inf")]
    labels = ["0–7", "8–30", "31–90", "91–180", "181–365", "366+"]
    df["lead_time_band"] = pd.cut(df["lead_time"], bins=bins, labels=labels)
    lead_rates = df.groupby("lead_time_band", observed=False)["is_canceled"].mean().mul(100)
    lead_rates.plot(kind="bar", color="#c77b45", figsize=(8, 4.5))
    plt.title("Cancellation rate by booking lead time")
    plt.xlabel("Days between booking and arrival")
    plt.ylabel("Canceled bookings (%)")
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.savefig(REPORTS / "cancellation_by_lead_time.png", dpi=170)
    plt.close()

    month_order = ["January", "February", "March", "April", "May", "June",
                   "July", "August", "September", "October", "November", "December"]
    month_rates = (df.groupby("arrival_date_month", observed=True)["is_canceled"].mean()
                   .reindex(month_order).dropna().mul(100))
    month_rates.plot(kind="line", marker="o", color="#315b73", figsize=(9, 4.5))
    plt.title("Cancellation rate by arrival month")
    plt.xlabel("")
    plt.ylabel("Canceled bookings (%)")
    plt.xticks(rotation=35, ha="right")
    plt.tight_layout()
    plt.savefig(REPORTS / "cancellation_by_month.png", dpi=170)
    plt.close()

    plt.figure(figsize=(7, 6))
    for name in models:
        fpr, tpr, _ = roc_curve(y_test, probabilities[name])
        plt.plot(fpr, tpr, label=f"{name} (AUC {metrics[name]['roc_auc']:.3f})")
    plt.plot([0, 1], [0, 1], "--", color="#888888", label="No-skill baseline")
    plt.xlabel("False positive rate")
    plt.ylabel("True positive rate")
    plt.title("Cancellation risk model comparison")
    plt.legend()
    plt.tight_layout()
    plt.savefig(REPORTS / "roc_curve.png", dpi=170)
    plt.close()

    ConfusionMatrixDisplay.from_predictions(
        y_test, predictions[best_name], display_labels=["Completed", "Canceled"], cmap="Blues")
    plt.title(f"Confusion matrix | {best_name}")
    plt.tight_layout()
    plt.savefig(REPORTS / "confusion_matrix.png", dpi=170)
    plt.close()

    top = pd.Series(importances).sort_values().tail(12)
    top.index = [item.replace("num__", "").replace("cat__", "") for item in top.index]
    top.plot(kind="barh", color="#6d9a91", figsize=(8, 5.5))
    plt.title("Random Forest | Top feature importance")
    plt.xlabel("Impurity-based importance")
    plt.ylabel("")
    plt.tight_layout()
    plt.savefig(REPORTS / "feature_importance.png", dpi=170)
    plt.close()

    print(f"Rows after exact-deduplication: {len(df):,}")
    print(f"Best ROC-AUC: {best_name}: {metrics[best_name]['roc_auc']:.3f}")
    print(f"Report files saved in {REPORTS}")


if __name__ == "__main__":
    main()
