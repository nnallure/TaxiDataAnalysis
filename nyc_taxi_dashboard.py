import streamlit as t
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import psycopg2
import calendar
from datetime import datetime, timedelta
import json

# Set page configuration
st.set_page_config(
    page_title="NYC Taxi & Events Analysis",
    page_icon="🚕",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS to match the dashboard design
st.markdown("""
<style>
    .main {
        background-color: #f5f5f7;
    }
    .css-1kyxreq {
        justify-content: center;
    }
    .dashboard-container {
        background-color: white;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .dashboard-title {
        font-size: 24px;
        font-weight: bold;
        margin-bottom: 5px;
    }
    .dashboard-subtitle {
        font-size: 14px;
        color: #666;
        margin-bottom: 20px;
    }
    .metric-container {
        background-color: white;
        border-radius: 8px;
        padding: 15px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .metric-title {
        font-size: 14px;
        color: #666;
        margin-bottom: 10px;
    }
    .metric-value {
        font-size: 28px;
        font-weight: bold;
        margin-bottom: 5px;
    }
    .metric-subtitle {
        font-size: 12px;
        color: #999;
    }
    .tab-active {
        border-bottom: 2px solid #0066cc;
        color: #0066cc;
        padding-bottom: 10px;
    }
    .tab-inactive {
        border-bottom: 2px solid transparent;
        padding-bottom: 10px;
    }
    .calendar-day {
        width: 32px;
        height: 32px;
        display: flex;
        justify-content: center;
        align-items: center;
        border-radius: 5px;
    }
    .calendar-day-selected {
        background-color: #ffefd5;
    }
    .calendar-day-other-month {
        color: #ccc;
    }
    .event-item {
        padding: 15px;
        border-bottom: 1px solid #eee;
    }
    .event-title {
        font-weight: bold;
        margin-bottom: 5px;
    }
    .event-location {
        font-size: 14px;
        color: #666;
        margin-bottom: 5px;
    }
    .event-time {
        font-size: 14px;
        color: #666;
        margin-bottom: 5px;
    }
    .event-note {
        font-size: 14px;
        color: #0066cc;
        margin-top: 10px;
    }
    .stButton>button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# Database connection function
@st.cache_resource
def init_connection():
    try:
        return psycopg2.connect(
            dbname=st.secrets["db_name"],
            user=st.secrets["db_user"],
            password=st.secrets["db_password"],
            host=st.secrets["db_host"],
            port=st.secrets["db_port"]
        )
    except Exception as e:
        st.error(f"Database connection error: {e}")
        # For demo purposes, return None so we can use sample data
        return None

# Execute query with caching
@st.cache_data(ttl=600)
def run_query(query):
    conn = init_connection()
    if conn is None:
        # Return sample data if connection failed
        return None
    
    try:
        return pd.read_sql_query(query, conn)
    except Exception as e:
        st.error(f"Query execution error: {e}")
        return None
    finally:
        conn.close()

# Sample data generator functions (used when DB connection fails or for development)
def get_sample_overview_data():
    return {
        "total_trips": "1.2M",
        "avg_daily_trips": "5,479",
        "peak_borough": "Manhattan",
        "peak_day": "Dec 15"
    }

def get_sample_monthly_data(month="July", year=2023):
    if month == "July":
        return {
            "total_trips": "88,000",
            "avg_daily": "5,867",
            "peak_day": "6,200",
            "peak_day_date": "Jul 4"
        }
    return {
        "total_trips": "85,000",
        "avg_daily": "5,750",
        "peak_day": "6,100",
        "peak_day_date": "Dec 15"
    }

def get_sample_daily_trips(month="July", year=2023):
    days = 31 if month in ["January", "March", "May", "July", "August", "October", "December"] else 30
    if month == "February":
        days = 29 if year % 4 == 0 else 28
    
    base = 5500
    data = []
    for day in range(1, days + 1):
        # Add some variation and peaks
        if day == 4 and month == "July":  # July 4th
            trips = 6200
            is_event = True
        elif day == 14 and month == "July":  # July 14th
            trips = 5900
            is_event = True
        elif day == 15 and month == "December":  # December 15th
            trips = 6700
            is_event = True
        else:
            trips = base + np.random.randint(-200, 300)
            is_event = False
        
        data.append({
            "date": f"{month[:3]} {day}",
            "trips": trips,
            "is_event": is_event
        })
    
    return pd.DataFrame(data)

def get_sample_borough_data():
    return pd.DataFrame({
        "borough": ["Manhattan", "Brooklyn", "Queens", "Bronx", "Staten Island"],
        "percentage": [65, 15, 12, 5, 3]
    })

def get_sample_correlation_data():
    # Generate sample data for Jun-Dec
    dates = pd.date_range(start='2023-06-01', end='2023-12-25', freq='14D')
    
    # Base values
    taxi_base = 5500
    event_base = 15
    
    data = []
    for date in dates:
        # Add some peaks for holidays and special days
        if date.month == 7 and date.day == 4:  # July 4th
            taxi_value = taxi_base + 1000
            event_value = event_base + 10
        elif date.month == 11 and date.day in range(23, 26):  # Thanksgiving
            taxi_value = taxi_base + 700
            event_value = event_base + 7
        elif date.month == 12 and date.day in range(15, 26):  # Holiday season
            taxi_value = taxi_base + 1200
            event_value = event_base + 10
        else:
            # Random variation
            taxi_value = taxi_base + np.random.randint(-300, 300)
            event_value = event_base + np.random.randint(-3, 3)
        
        data.append({
            "date": date.strftime("%b %d"),
            "taxi_trips": taxi_value,
            "events": event_value
        })
    
    return pd.DataFrame(data)

def get_sample_events_by_day(month="July", year=2023, day=14):
    # Sample events data
    if month == "July" and day == 14:
        return [
            {
                "title": "Street Fair",
                "location": "Manhattan",
                "time": "10:00 AM - 6:00 PM",
                "note": None
            },
            {
                "title": "Music Festival",
                "location": "Brooklyn",
                "time": "4:00 PM - 10:00 PM",
                "note": "Taxi demand increased by 23% on this day"
            }
        ]
    elif month == "July" and day == 4:
        return [
            {
                "title": "Independence Day Parade",
                "location": "Manhattan",
                "time": "10:00 AM - 12:00 PM",
                "note": None
            },
            {
                "title": "Fireworks Show",
                "location": "Brooklyn Bridge Park",
                "time": "8:00 PM - 10:00 PM",
                "note": "Taxi demand increased by 35% on this day"
            }
        ]
    else:
        return []

def generate_calendar_days(year, month):
    # Create a calendar for the selected month
    cal = calendar.monthcalendar(year, month)
    month_name = calendar.month_name[month]
    
    # Format the calendar data for display
    formatted_cal = []
    for week in cal:
        for day in week:
            if day == 0:
                # Add days from previous/next month
                formatted_cal.append({"day": "", "current_month": False})
            else:
                formatted_cal.append({"day": day, "current_month": True})
    
    return formatted_cal, month_name

# App Header
st.markdown("<div class='dashboard-title'>NYC Taxi & Events Analysis</div>", unsafe_allow_html=True)
st.markdown("<div class='dashboard-subtitle'>Interactive dashboard showing the relationship between NYC taxi demand and events</div>", unsafe_allow_html=True)

# Overview Section
st.markdown("<div class='dashboard-container'>", unsafe_allow_html=True)
st.markdown("<div class='dashboard-title' style='font-size: 20px;'>Overview</div>", unsafe_allow_html=True)
st.markdown("<div class='dashboard-subtitle'>Key metrics from NYC taxi trips and events (June-Dec 2023)</div>", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["Taxi Data", "Events Data"])

with tab1:
    # Attempt to get data from DB
    query = """
    SELECT 
        COUNT(*) as total_trips,
        AVG(daily_trips) as avg_daily_trips,
        MAX(peak_borough) as peak_borough,
        MAX(peak_day) as peak_day
    FROM nyc_taxi_overview
    """
    db_data = run_query(query)
    
    # Use sample data if DB query failed
    data = get_sample_overview_data() if db_data is None else {
        "total_trips": f"{db_data['total_trips'].iloc[0]/1000000:.1f}M",
        "avg_daily_trips": f"{db_data['avg_daily_trips'].iloc[0]:,.0f}",
        "peak_borough": db_data['peak_borough'].iloc[0],
        "peak_day": db_data['peak_day'].iloc[0]
    }
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("<div class='metric-container'>", unsafe_allow_html=True)
        st.markdown("<div class='metric-title'>Total Trips</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='metric-value'>{data['total_trips']}</div>", unsafe_allow_html=True)
        st.markdown("<div class='metric-subtitle'>Jan-Dec 2023</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("<div class='metric-container'>", unsafe_allow_html=True)
        st.markdown("<div class='metric-title'>Avg. Daily Trips</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='metric-value'>{data['avg_daily_trips']}</div>", unsafe_allow_html=True)
        st.markdown("<div class='metric-subtitle'>Per day</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col3:
        st.markdown("<div class='metric-container'>", unsafe_allow_html=True)
        st.markdown("<div class='metric-title'>Peak Borough</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='metric-value'>{data['peak_borough']}</div>", unsafe_allow_html=True)
        st.markdown("<div class='metric-subtitle'>Most trips</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col4:
        st.markdown("<div class='metric-container'>", unsafe_allow_html=True)
        st.markdown("<div class='metric-title'>Peak Day</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='metric-value'>{data['peak_day']}</div>", unsafe_allow_html=True)
        st.markdown("<div class='metric-subtitle'>Highest demand</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

with tab2:
    # Similar structure for Events tab (simplified for now)
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("<div class='metric-container'>", unsafe_allow_html=True)
        st.markdown("<div class='metric-title'>Total Events</div>", unsafe_allow_html=True)
        st.markdown("<div class='metric-value'>1,456</div>", unsafe_allow_html=True)
        st.markdown("<div class='metric-subtitle'>Jan-Dec 2023</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("<div class='metric-container'>", unsafe_allow_html=True)
        st.markdown("<div class='metric-title'>Avg. Daily Events</div>", unsafe_allow_html=True)
        st.markdown("<div class='metric-value'>4.2</div>", unsafe_allow_html=True)
        st.markdown("<div class='metric-subtitle'>Per day</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col3:
        st.markdown("<div class='metric-container'>", unsafe_allow_html=True)
        st.markdown("<div class='metric-title'>Top Event Type</div>", unsafe_allow_html=True)
        st.markdown("<div class='metric-value'>Street Fair</div>", unsafe_allow_html=True)
        st.markdown("<div class='metric-subtitle'>342 events</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col4:
        st.markdown("<div class='metric-container'>", unsafe_allow_html=True)
        st.markdown("<div class='metric-title'>Peak Month</div>", unsafe_allow_html=True)
        st.markdown("<div class='metric-value'>July</div>", unsafe_allow_html=True)
        st.markdown("<div class='metric-subtitle'>187 events</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# Daily Taxi Trips Section
st.markdown("<div class='dashboard-container'>", unsafe_allow_html=True)
col1, col2 = st.columns([3, 1])

with col1:
    st.markdown("<div class='dashboard-title' style='font-size: 20px;'>Daily Taxi Trips</div>", unsafe_allow_html=True)
    st.markdown("<div class='dashboard-subtitle'>Daily taxi trip volume by month</div>", unsafe_allow_html=True)

with col2:
    month_options = ["January", "February", "March", "April", "May", "June", 
                    "July", "August", "September", "October", "November", "December"]
    selected_month = st.selectbox("Select Month", month_options, index=6)  # Default to July

# Query for daily trips by month
query = f"""
SELECT 
    date_trunc('day', trip_datetime) as trip_date,
    COUNT(*) as trip_count,
    CASE WHEN EXISTS (
        SELECT 1 FROM nyc_events 
        WHERE DATE(event_datetime) = DATE(trip_datetime)
    ) THEN TRUE ELSE FALSE END as is_event_day
FROM nyc_taxi_trips
WHERE EXTRACT(MONTH FROM trip_datetime) = {month_options.index(selected_month) + 1}
AND EXTRACT(YEAR FROM trip_datetime) = 2023
GROUP BY trip_date
ORDER BY trip_date
"""
db_daily_data = run_query(query)

# Use sample data if DB query failed
daily_data = get_sample_daily_trips(selected_month) if db_daily_data is None else db_daily_data

# Monthly metrics
monthly_metrics = get_sample_monthly_data(selected_month)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("<div class='metric-container'>", unsafe_allow_html=True)
    st.markdown("<div class='metric-title'>Total Trips</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='metric-value'>{monthly_metrics['total_trips']}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with col2:
    st.markdown("<div class='metric-container'>", unsafe_allow_html=True)
    st.markdown("<div class='metric-title'>Average Daily</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='metric-value'>{monthly_metrics['avg_daily']}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with col3:
    st.markdown("<div class='metric-container'>", unsafe_allow_html=True)
    st.markdown("<div class='metric-title'>Peak Day</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='metric-value'>{monthly_metrics['peak_day']}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='metric-subtitle'>{monthly_metrics['peak_day_date']}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# Daily trips chart
fig = px.bar(daily_data, 
             x='date', 
             y='trips',
             color='is_event',
             color_discrete_map={True: '#6c5ce7', False: '#a29bfe'},
             labels={'date': '', 'trips': 'Taxi Trips', 'is_event': 'Event Day'})

fig.update_layout(
    height=350,
    margin=dict(l=20, r=20, t=30, b=20),
    paper_bgcolor='white',
    plot_bgcolor='white',
    hovermode='x unified',
    yaxis=dict(
        gridcolor='#f0f0f0',
        range=[4000, 7000]
    ),
    xaxis=dict(
        gridcolor='#f0f0f0'
    ),
    showlegend=False
)

st.plotly_chart(fig, use_container_width=True)

# Legend for event days
col1, col2 = st.columns([1, 3])
with col1:
    st.markdown("""
    <div style="display: flex; align-items: center; margin-right: 20px;">
        <div style="width: 12px; height: 12px; background-color: #6c5ce7; margin-right: 5px;"></div>
        <span style="font-size: 14px;">Event day</span>
    </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown("""
    <div style="display: flex; align-items: center;">
        <div style="width: 12px; height: 12px; background-color: #a29bfe; margin-right: 5px;"></div>
        <span style="font-size: 14px;">Regular day</span>
    </div>
    """, unsafe_allow_html=True)

# Event count
st.markdown("<div style='font-size: 14px; color: #666; margin-top: 10px;'>2 major events in July 2023</div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# Taxi Trips by Borough Section
st.markdown("<div class='dashboard-container'>", unsafe_allow_html=True)
st.markdown("<div class='dashboard-title' style='font-size: 20px;'>Taxi Trips by Borough</div>", unsafe_allow_html=True)
st.markdown("<div class='dashboard-subtitle'>Distribution of taxi pickups across NYC boroughs</div>", unsafe_allow_html=True)

# Query for borough data
query = """
SELECT 
    borough,
    COUNT(*) as trip_count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) as percentage
FROM nyc_taxi_trips
GROUP BY borough
ORDER BY trip_count DESC
"""
db_borough_data = run_query(query)

# Use sample data if DB query failed
borough_data = get_sample_borough_data() if db_borough_data is None else db_borough_data

# Borough pie chart
colors = ['#e74c3c', '#e67e22', '#f1c40f', '#ecf0f1', '#bdc3c7']
fig = px.pie(borough_data, 
             values='percentage', 
             names='borough',
             color_discrete_sequence=colors)

fig.update_traces(textposition='inside', textinfo='percent+label')
fig.update_layout(
    height=350,
    margin=dict(l=20, r=20, t=30, b=20),
    showlegend=False
)

st.plotly_chart(fig, use_container_width=True)

# Borough legend
col1, col2, col3, col4, col5 = st.columns(5)
boroughs = ["Manhattan", "Brooklyn", "Queens", "Bronx", "Staten Island"]
colors = ['#e74c3c', '#e67e22', '#f1c40f', '#ecf0f1', '#bdc3c7']

for i, col in enumerate([col1, col2, col3, col4, col5]):
    with col:
        st.markdown(f"""
        <div style="display: flex; align-items: center;">
            <div style="width: 12px; height: 12px; border-radius: 50%; background-color: {colors[i]}; margin-right: 5px;"></div>
            <span>{boroughs[i]}</span>
        </div>
        """, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# Correlation Analysis Section
st.markdown("<div class='dashboard-container'>", unsafe_allow_html=True)
col1, col2 = st.columns([3, 1])

with col1:
    st.markdown("<div class='dashboard-title' style='font-size: 20px;'>Correlation Analysis</div>", unsafe_allow_html=True)
    st.markdown("<div class='dashboard-subtitle'>Relationship between NYC events and taxi demand</div>", unsafe_allow_html=True)

with col2:
    time_options = ["All Time (Jun-Dec)", "Q2 2023", "Q3 2023", "Q4 2023"]
    selected_time = st.selectbox("Select Time Period", time_options)

tab1, tab2 = st.tabs(["Time Series", "Lag Analysis"])

with tab1:
    # Query for correlation data
    query = """
    SELECT 
        date_trunc('day', t.trip_datetime) as date,
        COUNT(DISTINCT t.id) as taxi_trips,
        COUNT(DISTINCT e.id) as events
    FROM nyc_taxi_trips t
    LEFT JOIN nyc_events e ON DATE(t.trip_datetime) = DATE(e.event_datetime)
    WHERE t.trip_datetime BETWEEN '2023-06-01' AND '2023-12-31'
    GROUP BY date
    ORDER BY date
    """
    db_correlation_data = run_query(query)
    
    # Use sample data if DB query failed
    correlation_data = get_sample_correlation_data() if db_correlation_data is None else db_correlation_data
    
    # Create time series chart
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Add taxi trips line
    fig.add_trace(
        go.Scatter(
            x=correlation_data['date'],
            y=correlation_data['taxi_trips'],
            name="Taxi Trips",
            line=dict(color='#a29bfe', width=2)
        ),
        secondary_y=False
    )
    
    # Add events line
    fig.add_trace(
        go.Scatter(
            x=correlation_data['date'],
            y=correlation_data['events'],
            name="Events",
            line=dict(color='#82e0aa', width=2)
        ),
        secondary_y=True
    )
    
    # Update layout
    fig.update_layout(
        height=350,
        margin=dict(l=20, r=20, t=30, b=20),
        paper_bgcolor='white',
        plot_bgcolor='white',
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    # Update y-axes
    fig.update_yaxes(
        title_text="Taxi Trips",
        range=[0, 8000],
        gridcolor='#f0f0f0',
        secondary_y=False
    )
    
    fig.update_yaxes(
        title_text="Events",
        range=[0, 28],
        secondary_y=True
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("""
    <div style="font-size: 14px; color: #666; margin-top: 10px;">
        The chart shows a positive correlation between the number of events and taxi trips during All Time (Jun-Dec 2023), 
        particularly on holidays and special event days.
    </div>
    """, unsafe_allow_html=True)

with tab2:
    # Placeholder for the Lag Analysis tab
    st.markdown("""
    <div style="text-align: center; padding: 100px 0;">
        <div style="font-size: 16px; color: #666;">Lag Analysis coming soon</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# Events Calendar Section
st.markdown("<div class='dashboard-container'>", unsafe_allow_html=True)
st.markdown("<div class='dashboard-title' style='font-size: 20px;'>Events Calendar</div>", unsafe_allow_html=True)
st.markdown("<div class='dashboard-subtitle'>Calendar view of NYC permitted events</div>", unsafe_allow_html=True)

# Month navigation
col1, col2, col3 = st.columns([1, 4, 1])
with col1:
    st.markdown("""
    <div style="display: flex; align-items: center; justify-content: center; height: 40px;">
        <a href="#" style="color: #333; text-decoration: none;">←</a>
    </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown("""
    <div style="display: flex; align-items: center; justify-content: center; height: 40px;">
        <div style="font-weight: bold; font-size: 16px;">December 2023</div>
    </div>
    """, unsafe_allow_html=True)
with col3:
    st.markdown("""
    <div style="display: flex; align-items: center; justify-content: center; height: 40px;">
        <a href="#" style="color: #333; text-decoration: none;">→</a>
    </div>
    """, unsafe_allow_html=True)

# Calendar grid
days_of_week = ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"]
col1, col2, col3, col4, col5, col6, col7 = st.columns(7)

# Header row
for i, col in enumerate([col1, col2, col3, col4, col5, col6, col7]):
    with col:
        st.markdown(f"""
        <div style="display: flex; align-items: center; justify-content: center; height: 32px; font-size: 14px; color: #666;">
            {days_of_week[i]}
        </div>
        """, unsafe_allow_html=True)

# Calendar data for December 2023
# This is simplified - in a real app you would generate this dynamically
calendar_data = [
    ["26", "27", "28", "29", "30", "1", "2"],
    ["3", "4", "5", "6", "7", "8", "9"],
    ["10", "11", "12", "13", "14", "15", "16"],
    ["17", "18", "19", "20", "21", "22", "23"],
    ["24", "25", "26", "27", "28", "29", "30"],
    ["31", "1", "2", "3", "4", "5", "6"]
]

# Generate calendar grid
for week in calendar_data:
    cols = st.columns(7)
    for i, day in enumerate(week):
        is_current_month = True
        if (int(day) > 20 and int(calendar_data[0][0]) > 20 and i < 3) or (int(day) < 10 and i > 3 and int(calendar_data[-1][-1]) < 10):
            is_current_month = False
        
        is_selected = day == "5"  # Example: Day 5 is selected
        
        bg_color = "#ffefd5" if is_selected else "white"
        text_color = "#ccc" if not is_current_month else "#333"
        
        with cols[i]:
            st.markdown(f"""
            <div style="display: flex; align-items: center; justify-content: center; height: 32px; background-color: {bg_color}; border-radius: 5px; margin: 2px; color: {text_color};">
                {day}
            </div>
            """, unsafe_allow_html=True)

# Display events for a specific day
st.markdown("<div style='margin-top: 30px;'>", unsafe_allow_html=True)
st.markdown("<div style='font-size: 18px; font-weight: bold; margin-bottom: 15px;'>July 14, 2023</div>", unsafe_allow_html=True)

# Sample events for demonstration
events = [
    {
        "title": "Street Fair",
        "location": "Manhattan",
        "time": "10:00 AM - 6:00 PM"
    },
    {
        "title": "Music Festival",
        "location": "Brooklyn",
        "time": "4:00 PM - 10:00 PM",
        "note": "Taxi demand increased by 23% on this day"
    }
]

for event in events:
    st.markdown("<div class='event-item'>", unsafe_allow_html=True)
    st.markdown(f"<div class='event-title'>{event['title']}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='event-location'>{event['location']}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='event-time'>{event['time']}</div>", unsafe_allow_html=True)
    if 'note' in event and event['note']:
        st.markdown(f"<div class='event-note'>{event['note']}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# Average Taxi Prices Section (Not shown in images but was in the code)
st.markdown("<div class='dashboard-container'>", unsafe_allow_html=True)
st.markdown("<div class='dashboard-title' style='font-size: 20px;'>Average Taxi Prices</div>", unsafe_allow_html=True)
st.markdown("<div class='dashboard-subtitle'>Analysis of taxi fares by borough and month (Jun-Dec 2023)</div>", unsafe_allow_html=True)

# Borough filter
col1, col2 = st.columns([3, 1])
with col2:
    borough_options = ["All Boroughs", "Manhattan", "Brooklyn", "Queens", "Bronx", "Staten Island"]
    selected_borough = st.selectbox("", borough_options, key="price_borough_filter")

# Tab selection for price analysis
price_tab1, price_tab2 = st.tabs(["Price Trends", "Borough Comparison"])

with price_tab1:
    # Price metrics for the selected filter
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("<div class='metric-container'>", unsafe_allow_html=True)
        st.markdown("<div class='metric-title'>Average Price</div>", unsafe_allow_html=True)
        st.markdown("<div class='metric-value'>$34.40</div>", unsafe_allow_html=True)
        st.markdown("<div class='metric-subtitle'>Per trip</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("<div class='metric-container'>", unsafe_allow_html=True)
        st.markdown("<div class='metric-title'>Price Range</div>", unsafe_allow_html=True)
        st.markdown("<div class='metric-value'>$31.88 - $39.28</div>", unsafe_allow_html=True)
        st.markdown("<div class='metric-subtitle'>Min to max</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col3:
        st.markdown("<div class='metric-container'>", unsafe_allow_html=True)
        st.markdown("<div class='metric-title'>Price Increase</div>", unsafe_allow_html=True)
        st.markdown("<div class='metric-value'>23.2%</div>", unsafe_allow_html=True)
        st.markdown("<div class='metric-subtitle'>Jun to Dec</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Create monthly price trend chart
    months = ['Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    prices = [32.0, 32.5, 32.2, 33.5, 35.0, 36.2, 39.5]
    
    price_trend_df = pd.DataFrame({
        'month': months,
        'price': prices
    })
    
    fig = px.line(price_trend_df, 
                 x='month', 
                 y='price',
                 markers=True,
                 line_shape='monotone')
    
    fig.update_traces(line=dict(color='#a29bfe', width=2),
                     marker=dict(color='#a29bfe', size=8))
    
    fig.update_layout(
        height=350,
        margin=dict(l=20, r=20, t=30, b=20),
        paper_bgcolor='white',
        plot_bgcolor='white',
        hovermode='x unified',
        yaxis=dict(
            title='Average Price ($)',
            gridcolor='#f0f0f0',
            range=[28, 44],
            tickpretickprefix='$'
    ),
    xaxis=dict(
        title='Month',
        gridcolor='#f0f0f0'
    )
    )
    
    st.plotly_chart(fig, use_container_width=True)

with price_tab2:
    # Placeholder for Borough Comparison tab
    st.markdown("""
    <div style="text-align: center; padding: 100px 0;">
        <div style="font-size: 16px; color: #666;">Borough price comparison coming soon</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# Footer
st.markdown("""
<div style="text-align: center; margin-top: 40px; margin-bottom: 20px; font-size: 12px; color: #666;">
    NYC Taxi & Events Analysis Dashboard - Data from June to December 2023
</div>
""", unsafe_allow_html=True)