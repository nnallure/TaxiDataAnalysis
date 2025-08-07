# NYC Taxi Driver Insights

An interactive web app built with **Streamlit** to help NYC taxi drivers and analysts explore trip profitability, discover the best zones and times to drive, and analyze custom trip statistics based on historical data.

---

## What This App Does

This app connects to a **PostgreSQL** database containing real NYC taxi trip data and provides three core tools:

1. **Best Time & Place Recommender**  
   Find the most profitable pickup zones by time of day and borough.

2. **Trip Profitability Analyzer**  
   Simulate a trip’s potential earnings using factors like distance, boroughs, and time.

3. **Custom Trip Filter & Stats Explorer**  
   Analyze and visualize trends using filters for date, distance, borough, and more.

---

## Technologies Used

- **Python 3**
- **Streamlit**
- **PostgreSQL**
- **Pandas**
- **Plotly**
- **NumPy**
- **SciPy**

---

## How to Run Locally

### 1. PostgreSQL Database Setup

Create a database named Taxi_Project:

```bash
CREATE DATABASE Taxi_Project;
```
Create and populate a table called taxi_trips using cleaned NYC taxi data (June–Dec 2023).

Make sure the following columns are present (simplified):

pickup_date, pickup_time, pickup_borough, dropoff_borough, pickup_zone, trip_distance, fare_amount, tip_amount, total_amount, etc.

Update your database credentials in taxi_app.py:

```bash
conn = psycopg.connect(
    host="localhost",
    port='5432',
    dbname="Taxi_Project",
    user="postgres",
    password="your_password"
)
```
### 2. Open your terminal and navigate to your app folder:

```bash
cd "/Users/nikitha/Desktop/Managing Data/Managing Data Project"
```

2. (Optional) Create a virtual environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```
3. Install Python dependencies
If you don’t have a requirements.txt yet, use:
```bash
pip install streamlit pandas plotly psycopg2-binary numpy scipy
```
Or, if using a requirements.txt:
```bash
pip install -r requirements.txt
```

Launch the App
Once inside your project folder, run:
```bash
cd "/"
streamlit run taxi_app.py
```
Your browser will open at:
http://localhost:8501


Sample Use Cases
Discover best pickup zones by time/day

Evaluate trip value before accepting passengers

Explore tip patterns and fare trends by borough

Export filtered data for custom analysis
