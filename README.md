<p align="center">
  <img src="hotel-bookings-analysis/reports/project_cover.png" alt="Hotel booking cancellation analysis" width="100%">
</p>

# Hotel Booking Cancellation Analysis

I built this end-to-end project to understand hotel booking cancellations and test how well booking-time information can help identify at-risk reservations. The work covers data cleaning, exploratory analysis, feature preparation, model comparison, and a shareable report.

The data contains bookings for City Hotel and Resort Hotel from 2015 to 2017.

## Project overview

- **119,390** rows in the source data
- **31,994** exact duplicate rows removed before analysis
- **87,396** rows in the cleaned dataset
- **27.5%** cancellation rate after removing exact duplicates

Cancellation rates differ between the two hotel types: **30.0%** for City Hotel and **23.5%** for Resort Hotel. Canceled bookings also have a longer median lead time: 80 days, compared with 38 days for completed bookings.

## Model results

I compared Logistic Regression and Random Forest using a stratified 75/25 train-test split. Preprocessing is fitted within each model pipeline, and fields that can reveal the final outcome are excluded.

| Model | ROC-AUC | Precision | Recall | F1 |
|---|---:|---:|---:|---:|
| Logistic Regression | 0.856 | 0.551 | 0.810 | 0.656 |
| Random Forest | **0.875** | 0.539 | **0.849** | **0.659** |

Random Forest had the stronger ROC-AUC and recall on this split. These results are exploratory and do not guarantee performance on future bookings.

## Charts

<p align="center">
  <img src="hotel-bookings-analysis/reports/cancellation_by_hotel.png" alt="Cancellation rate by hotel type" width="32%">
  <img src="hotel-bookings-analysis/reports/cancellation_by_lead_time.png" alt="Cancellation rate by lead time" width="32%">
  <img src="hotel-bookings-analysis/reports/cancellation_by_month.png" alt="Cancellation rate by arrival month" width="32%">
</p>

## Run the project

Requires Python 3.10 or newer.

```bash
cd hotel-bookings-analysis
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python src/analyze.py
```

The script reads `data/hotel_bookings.csv` and writes charts, model metrics, and classification reports to `reports/`.

## Files

- [HTML report](hotel-bookings-analysis/reports/report.html) · [Markdown report](hotel-bookings-analysis/reports/report.md)
- [Analysis script](hotel-bookings-analysis/src/analyze.py) · [Model metrics](hotel-bookings-analysis/reports/metrics.json)
- [Project details and dataset notes](hotel-bookings-analysis/README.md)

## Dataset and tools

The dataset is **Hotel Booking Demand**, published by Antonio, de Almeida, and Nunes in *Data in Brief* (2019). [Dataset paper](https://doi.org/10.1016/j.dib.2018.11.126).

Built with Python, pandas, scikit-learn, and Matplotlib.
