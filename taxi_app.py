import streamlit as st
import pandas as pd
import psycopg2 as psycopg
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
from scipy import stats

# Set page configuration
st.set_page_config(
    page_title="NYC Taxi Driver Insights",
    page_icon="🚕",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Database connection function - FIXED to create a new connection each time
def get_connection():
    """Create a new connection every time - no caching"""
    try:
        conn = psycopg.connect(
            host="localhost",
            port='5432',
            dbname="Taxi_Project",
            user="postgres",
            password="123"
        )
        conn.autocommit = True
        return conn
    except Exception as e:
        st.error(f"Database connection error: {e}")
        return None

# Function to execute queries and return dataframes - FIXED
def execute_query(query):
    """Create a fresh connection for each query"""
    conn = None
    try:
        conn = get_connection()
        if conn:
            df = pd.read_sql_query(query, conn)
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Query execution error: {e}")
        return pd.DataFrame()
    finally:
        if conn:
            conn.close()

# Helper function to convert time strings to hour categories
def categorize_hour(time_str):
    try:
        hour = int(time_str.split(':')[0])
        if 6 <= hour < 9:
            return '6am-9am'
        elif 9 <= hour < 12:
            return '9am-12pm'
        elif 12 <= hour < 15:
            return '12pm-3pm'
        elif 15 <= hour < 18:
            return '3pm-6pm'
        elif 18 <= hour < 21:
            return '6pm-9pm'
        elif 21 <= hour < 24:
            return '9pm-12am'
        else:
            return '12am-6am'
    except:
        return 'Unknown'

# Add custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 36px;
        font-weight: bold;
        color: #FFD700;
        text-align: center;
        background-color: #1E1E1E;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 30px;
    }
    .feature-header {
        font-size: 24px;
        font-weight: bold;
        color: #FFD700;
        background-color: #2E2E2E;
        padding: 10px;
        border-radius: 5px;
        margin-top: 20px;
        margin-bottom: 20px;
    }
    .metric-card {
        background-color: #3E3E3E;
        padding: 15px;
        border-radius: 5px;
        text-align: center;
    }
    .metric-value {
        font-size: 32px;
        font-weight: bold;
        color: #4CAF50;
    }
    .metric-title {
        font-size: 16px;
        color: #BBBBBB;
    }
</style>
""", unsafe_allow_html=True)

# Main app title
st.markdown('<div class="main-header">NYC Taxi Driver Insights 🚕</div>', unsafe_allow_html=True)

# Sidebar for navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Select a Tool", 
    ["Best Time & Place Recommender", "Trip Profitability Analyzer", "Custom Trip Filter & Stats"])

# Test database connection
try:
    conn_test = get_connection()
    if conn_test:
        conn_test.close()
        db_connected = True
    else:
        db_connected = False
except:
    db_connected = False

if db_connected:
    # Load boroughs and zones for dropdowns
    def load_location_data():
        boroughs_query = "SELECT DISTINCT pickup_borough FROM taxi_trips WHERE pickup_borough != '' ORDER BY pickup_borough"
        boroughs_df = execute_query(boroughs_query)
        boroughs = boroughs_df['pickup_borough'].tolist() if not boroughs_df.empty else []
        
        zones_query = "SELECT DISTINCT pickup_zone FROM taxi_trips WHERE pickup_zone != '' ORDER BY pickup_zone"
        zones_df = execute_query(zones_query)
        zones = zones_df['pickup_zone'].tolist() if not zones_df.empty else []
        
        return boroughs, zones
    
    # Load data with proper error handling
    try:
        boroughs, zones = load_location_data()
    except Exception as e:
        st.error(f"Error loading location data: {e}")
        boroughs, zones = [], []
    
    # 1. "Best Time and Place to Work" Recommender
    if page == "Best Time & Place Recommender":
        st.markdown('<div class="feature-header">🔍 Best Time and Place to Work Recommender</div>', unsafe_allow_html=True)
        st.write("Find the optimal time and location to maximize your earnings.")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            selected_day = st.selectbox("Select day of week", days)
            
        with col2:
            time_ranges = ["6am-9am", "9am-12pm", "12pm-3pm", "3pm-6pm", "6pm-9pm", "9pm-12am", "12am-6am"]
            selected_time = st.selectbox("Select time range", time_ranges)
            
        with col3:
            selected_borough = st.selectbox("Select pickup borough", ["All"] + boroughs)
        
        # Convert day selection to matching pattern in your data
        if st.button("Find Optimal Locations", type="primary"):
            with st.spinner("Analyzing data..."):
                # Build the SQL query based on user selections
                time_condition = ""
                if selected_time == "6am-9am":
                    time_condition = "EXTRACT(HOUR FROM pickup_time::time) BETWEEN 6 AND 8"
                elif selected_time == "9am-12pm":
                    time_condition = "EXTRACT(HOUR FROM pickup_time::time) BETWEEN 9 AND 11"
                elif selected_time == "12pm-3pm":
                    time_condition = "EXTRACT(HOUR FROM pickup_time::time) BETWEEN 12 AND 14"
                elif selected_time == "3pm-6pm":
                    time_condition = "EXTRACT(HOUR FROM pickup_time::time) BETWEEN 15 AND 17"
                elif selected_time == "6pm-9pm":
                    time_condition = "EXTRACT(HOUR FROM pickup_time::time) BETWEEN 18 AND 20"
                elif selected_time == "9pm-12am":
                    time_condition = "EXTRACT(HOUR FROM pickup_time::time) BETWEEN 21 AND 23"
                else:  # 12am-6am
                    time_condition = "EXTRACT(HOUR FROM pickup_time::time) BETWEEN 0 AND 5"
                
                borough_condition = f"pickup_borough = '{selected_borough}'" if selected_borough != "All" else "1=1"
                
                # This assumes you can extract day of week from pickup_date
                # Adjust based on your actual data format
                day_condition = f"TO_CHAR(TO_DATE(pickup_date, 'YYYY-MM-DD'), 'Day') LIKE '{selected_day}%'"
                
                query = f"""
                SELECT 
                    pickup_zone,
                    COUNT(*) as trip_count,
                    AVG(fare_amount) as avg_fare,
                    AVG(tip_amount) as avg_tip,
                    AVG(total_amount) as avg_total
                FROM 
                    taxi_trips
                WHERE 
                    {day_condition} AND
                    {time_condition} AND
                    {borough_condition}
                GROUP BY 
                    pickup_zone
                ORDER BY 
                    AVG(total_amount) DESC
                LIMIT 10
                """
                
                results = execute_query(query)
                
                if not results.empty:
                    st.success(f"Found {len(results)} optimal pickup zones.")
                    
                    # Display metrics
                    metric_cols = st.columns(3)
                    with metric_cols[0]:
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-value">${results['avg_total'].mean():.2f}</div>
                            <div class="metric-title">Average Total Fare</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with metric_cols[1]:
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-value">${results['avg_tip'].mean():.2f}</div>
                            <div class="metric-title">Average Tip</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with metric_cols[2]:
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-value">{results['trip_count'].sum()}</div>
                            <div class="metric-title">Total Trips</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Create bar chart for top zones
                    st.subheader(f"Top 10 Most Profitable Pickup Zones")
                    
                    fig = px.bar(
                        results,
                        x='pickup_zone',
                        y='avg_total',
                        color='avg_tip',
                        labels={'pickup_zone': 'Pickup Zone', 'avg_total': 'Average Total Fare ($)', 'avg_tip': 'Average Tip ($)'},
                        title=f"Most Profitable Pickup Zones on {selected_day} during {selected_time}",
                        height=500
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Show the detailed data
                    st.subheader("Detailed Results")
                    # Format to 2 decimal places for dollar amounts
                    results['avg_fare'] = results['avg_fare'].round(2)
                    results['avg_tip'] = results['avg_tip'].round(2)
                    results['avg_total'] = results['avg_total'].round(2)
                    
                    # Rename columns for better display
                    results.columns = ['Pickup Zone', 'Trip Count', 'Avg Fare ($)', 'Avg Tip ($)', 'Avg Total ($)']
                    
                    st.dataframe(results, use_container_width=True)
                    
                    st.download_button(
                        label="Download Data as CSV",
                        data=results.to_csv(index=False).encode('utf-8'),
                        file_name=f"best_zones_{selected_day}_{selected_time.replace('-', 'to')}.csv",
                        mime='text/csv',
                    )
                else:
                    st.warning("No data found for your selection. Try different criteria.")
    
    # 2. "Trip Profitability Analyzer"
    elif page == "Trip Profitability Analyzer":
        st.markdown('<div class="feature-header">💸 Trip Profitability Analyzer</div>', unsafe_allow_html=True)
        st.write("Simulate how trip characteristics impact your earnings.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            trip_distance = st.slider("Trip Distance (miles)", 0.0, 30.0, 5.0, 0.5)
            
            time_ranges = ["6am-9am", "9am-12pm", "12pm-3pm", "3pm-6pm", "6pm-9pm", "9pm-12am", "12am-6am"]
            selected_time = st.selectbox("Time of Day", time_ranges)
        
        with col2:
            # Payment type (simplified for this app)
            payment_types = ["Credit Card", "Cash"]
            payment_type = st.selectbox("Payment Type", payment_types)
            
            selected_pickup_borough = st.selectbox("Pickup Borough", boroughs if boroughs else ["Manhattan"])
            selected_dropoff_borough = st.selectbox("Dropoff Borough", boroughs if boroughs else ["Brooklyn"])
        
        # User clicks analyze
        if st.button("Analyze Trip Profitability", type="primary"):
            with st.spinner("Calculating profitability..."):
                # Convert time selection to hour range for query
                time_condition = ""
                if selected_time == "6am-9am":
                    time_condition = "EXTRACT(HOUR FROM pickup_time::time) BETWEEN 6 AND 8"
                elif selected_time == "9am-12pm":
                    time_condition = "EXTRACT(HOUR FROM pickup_time::time) BETWEEN 9 AND 11"
                elif selected_time == "12pm-3pm":
                    time_condition = "EXTRACT(HOUR FROM pickup_time::time) BETWEEN 12 AND 14"
                elif selected_time == "3pm-6pm":
                    time_condition = "EXTRACT(HOUR FROM pickup_time::time) BETWEEN 15 AND 17"
                elif selected_time == "6pm-9pm":
                    time_condition = "EXTRACT(HOUR FROM pickup_time::time) BETWEEN 18 AND 20"
                elif selected_time == "9pm-12am":
                    time_condition = "EXTRACT(HOUR FROM pickup_time::time) BETWEEN 21 AND 23"
                else:  # 12am-6am
                    time_condition = "EXTRACT(HOUR FROM pickup_time::time) BETWEEN 0 AND 5"
                
                # Distance range (e.g., +/- 1 mile)
                distance_lower = max(0, trip_distance - 1)
                distance_upper = trip_distance + 1
                
                # Build query to find similar trips
                query = f"""
                SELECT 
                    AVG(fare_amount) as avg_fare,
                    AVG(tip_amount) as avg_tip,
                    AVG(extra) as avg_extra,
                    AVG(tolls_amount) as avg_tolls,
                    AVG(congestion_surcharge) as avg_congestion,
                    AVG(total_amount) as avg_total,
                    COUNT(*) as trip_count
                FROM 
                    taxi_trips
                WHERE 
                    trip_distance BETWEEN {distance_lower} AND {distance_upper} AND
                    {time_condition} AND
                    pickup_borough = '{selected_pickup_borough}' AND
                    dropoff_borough = '{selected_dropoff_borough}'
                """
                
                # Add filter for payment type if needed
                # This would need a payment_type column in your data
                
                results = execute_query(query)
                
                if not results.empty and results['trip_count'].iloc[0] > 0:
                    # Get values from results
                    avg_fare = results['avg_fare'].iloc[0]
                    avg_tip = results['avg_tip'].iloc[0]
                    avg_extra = results['avg_extra'].iloc[0]
                    avg_tolls = results['avg_tolls'].iloc[0]
                    avg_congestion = results['avg_congestion'].iloc[0]
                    avg_total = results['avg_total'].iloc[0]
                    trip_count = results['trip_count'].iloc[0]
                    
                    # Display results
                    st.success(f"Analysis based on {int(trip_count)} similar trips")
                    
                    # Main metrics
                    metric_cols = st.columns(3)
                    with metric_cols[0]:
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-value">${avg_fare:.2f}</div>
                            <div class="metric-title">Estimated Base Fare</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with metric_cols[1]:
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-value">${avg_tip:.2f}</div>
                            <div class="metric-title">Estimated Tip</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with metric_cols[2]:
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-value">${avg_total:.2f}</div>
                            <div class="metric-title">Total Trip Value</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Calculate hourly rate estimate (assuming average NYC taxi speed of 12mph)
                    estimated_trip_time = trip_distance / 12  # hours
                    hourly_rate = avg_total / estimated_trip_time if estimated_trip_time > 0 else 0
                    
                    st.subheader("Trip Breakdown")
                    
                    # Create the fare breakdown chart
                    breakdown_data = {
                        'Component': ['Base Fare', 'Tip', 'Extra', 'Tolls', 'Congestion'],
                        'Amount': [avg_fare, avg_tip, avg_extra, avg_tolls, avg_congestion]
                    }
                    breakdown_df = pd.DataFrame(breakdown_data)
                    breakdown_df = breakdown_df[breakdown_df['Amount'] > 0]  # Only show components > 0
                    
                    # Create a pie chart for the breakdown
                    fig_breakdown = px.pie(
                        breakdown_df,
                        values='Amount',
                        names='Component',
                        title="Trip Fare Breakdown",
                        hole=0.4,
                        color_discrete_sequence=px.colors.sequential.Plasma_r
                    )
                    
                    # Modify layout
                    fig_breakdown.update_traces(textposition='inside', textinfo='percent+label')
                    fig_breakdown.update_layout(
                        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
                    )
                    
                    st.plotly_chart(fig_breakdown, use_container_width=True)
                    
                    # Profitability assessment
                    st.subheader("Profitability Assessment")
                    
                    # Get average trip profitability from the database
                    avg_query = f"""
                    SELECT 
                        AVG(total_amount) as overall_avg_total,
                        AVG(total_amount / NULLIF(trip_distance, 0)) as per_mile_avg
                    FROM 
                        taxi_trips
                    WHERE 
                        trip_distance > 0
                    """
                    
                    avg_results = execute_query(avg_query)
                    
                    if not avg_results.empty:
                        overall_avg = avg_results['overall_avg_total'].iloc[0]
                        per_mile_avg = avg_results['per_mile_avg'].iloc[0]
                        
                        per_mile_current = avg_total / trip_distance if trip_distance > 0 else 0
                        
                        cols = st.columns(2)
                        with cols[0]:
                            profit_gauge = go.Figure(go.Indicator(
                                mode = "gauge+number+delta",
                                value = avg_total,
                                title = {'text': "Trip Value vs. Average"},
                                delta = {'reference': overall_avg, 'relative': True, 'valueformat': '.1%'},
                                gauge = {
                                    'axis': {'range': [0, max(overall_avg * 2, avg_total * 1.2)]},
                                    'bar': {'color': "darkblue"},
                                    'steps': [
                                        {'range': [0, overall_avg * 0.8], 'color': "red"},
                                        {'range': [overall_avg * 0.8, overall_avg * 1.1], 'color': "yellow"},
                                        {'range': [overall_avg * 1.1, max(overall_avg * 2, avg_total * 1.2)], 'color': "green"}
                                    ],
                                    'threshold': {
                                        'line': {'color': "red", 'width': 4},
                                        'thickness': 0.75,
                                        'value': overall_avg
                                    }
                                }
                            ))
                            profit_gauge.update_layout(height=300)
                            st.plotly_chart(profit_gauge, use_container_width=True)
                        
                        with cols[1]:
                            mile_gauge = go.Figure(go.Indicator(
                                mode = "gauge+number+delta",
                                value = per_mile_current,
                                title = {'text': "$ Per Mile vs. Average"},
                                number = {'prefix': "$", 'valueformat': '.2f'},
                                delta = {'reference': per_mile_avg, 'relative': True, 'valueformat': '.1%'},
                                gauge = {
                                    'axis': {'range': [0, max(per_mile_avg * 2, per_mile_current * 1.2)]},
                                    'bar': {'color': "darkblue"},
                                    'steps': [
                                        {'range': [0, per_mile_avg * 0.8], 'color': "red"},
                                        {'range': [per_mile_avg * 0.8, per_mile_avg * 1.1], 'color': "yellow"},
                                        {'range': [per_mile_avg * 1.1, max(per_mile_avg * 2, per_mile_current * 1.2)], 'color': "green"}
                                    ],
                                    'threshold': {
                                        'line': {'color': "red", 'width': 4},
                                        'thickness': 0.75,
                                        'value': per_mile_avg
                                    }
                                }
                            ))
                            mile_gauge.update_layout(height=300)
                            st.plotly_chart(mile_gauge, use_container_width=True)
                    
                    # Estimated hourly rate
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">${hourly_rate:.2f}/hr</div>
                        <div class="metric-title">Estimated Hourly Rate (Based on avg. speed of 12mph)</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Profitability recommendation
                    st.subheader("Recommendation")
                    
                    if avg_total > overall_avg * 1.1:
                        st.success(f"✅ This trip is more profitable than average! It's {((avg_total/overall_avg)-1)*100:.1f}% above the average trip value.")
                    elif avg_total < overall_avg * 0.9:
                        st.error(f"⚠️ This trip is less profitable than average. It's {((overall_avg/avg_total)-1)*100:.1f}% below the average trip value.")
                    else:
                        st.info(f"ℹ️ This trip has average profitability.")
                    
                    # Additional insights
                    if avg_tip > avg_fare * 0.15:
                        st.markdown("💡 **Tip Insight:** This route typically receives good tips!")
                        
                    if selected_time in ["6am-9am", "3pm-6pm"] and avg_congestion > 0:
                        st.markdown("💡 **Rush Hour:** This is during rush hour - congestion charges apply.")
                else:
                    st.warning("Not enough data for this trip profile. Try different parameters.")
    
    # 3. "Custom Trip Filter & Stats Explorer"
    elif page == "Custom Trip Filter & Stats":
        st.markdown('<div class="feature-header">📊 Custom Trip Filter & Stats Explorer</div>', unsafe_allow_html=True)
        st.write("Explore trends in NYC taxi data.")
        
        # Filter sidebar
        st.sidebar.subheader("Filters")
        
        # Date range filter (adapts to your data format)
        # This assumes pickup_date is in YYYY-MM-DD format
        min_date_query = "SELECT MIN(pickup_date) FROM taxi_trips"
        max_date_query = "SELECT MAX(pickup_date) FROM taxi_trips"
        
        try:
            min_date_result = execute_query(min_date_query)
            max_date_result = execute_query(max_date_query)
            
            min_date_str = min_date_result.iloc[0, 0] if not min_date_result.empty else "2023-01-01"
            max_date_str = max_date_result.iloc[0, 0] if not max_date_result.empty else "2023-12-31"
            
            try:
                min_date = datetime.strptime(min_date_str, "%Y-%m-%d").date()
                max_date = datetime.strptime(max_date_str, "%Y-%m-%d").date()
            except:
                # Fallback if date format is different
                min_date = datetime(2023, 1, 1).date()
                max_date = datetime(2023, 12, 31).date()
                
            # Date range selector
            date_range = st.sidebar.date_input(
                "Date Range",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date
            )
            
            if len(date_range) == 2:
                start_date, end_date = date_range
                start_date_str = start_date.strftime("%Y-%m-%d")
                end_date_str = end_date.strftime("%Y-%m-%d")
            else:
                start_date_str = min_date_str
                end_date_str = max_date_str
        except Exception as e:
            st.sidebar.warning(f"Could not load date range from database: {e}")
            start_date_str = "2023-01-01"
            end_date_str = "2023-12-31"
        
        # Trip distance filter
        distance_min, distance_max = st.sidebar.slider(
            "Trip Distance (miles)",
            0.0,
            30.0,
            (0.0, 30.0),
            0.5
        )
        
        # Borough filters
        pickup_borough = st.sidebar.multiselect(
            "Pickup Borough",
            options=boroughs,
            default=boroughs[:1] if boroughs else []
        )
        
        dropoff_borough = st.sidebar.multiselect(
            "Dropoff Borough",
            options=boroughs,
            default=boroughs[:1] if boroughs else []
        )
        
        # Analysis execution
        if st.button("Run Analysis", type="primary"):
            with st.spinner("Running analysis..."):
                # Build the WHERE clause
                conditions = []
                conditions.append(f"pickup_date BETWEEN '{start_date_str}' AND '{end_date_str}'")
                conditions.append(f"trip_distance BETWEEN {distance_min} AND {distance_max}")
                
                if pickup_borough:
                    borough_list = "', '".join(pickup_borough)
                    conditions.append(f"pickup_borough IN ('{borough_list}')")
                    
                if dropoff_borough:
                    borough_list = "', '".join(dropoff_borough)
                    conditions.append(f"dropoff_borough IN ('{borough_list}')")
                
                where_clause = " AND ".join(conditions)
                
                # Main metrics query
                metrics_query = f"""
                SELECT 
                    COUNT(*) as trip_count,
                    AVG(trip_distance) as avg_distance,
                    AVG(fare_amount) as avg_fare,
                    AVG(tip_amount) as avg_tip,
                    AVG(total_amount) as avg_total,
                    SUM(total_amount) as total_revenue
                FROM 
                    taxi_trips
                WHERE 
                    {where_clause}
                """
                
                metrics_results = execute_query(metrics_query)
                
                if not metrics_results.empty:
                    # Display main metrics
                    st.subheader("Summary Metrics")
                    
                    metrics = st.columns(3)
                    with metrics[0]:
                        st.metric("Total Trips", f"{int(metrics_results['trip_count'].iloc[0]):,}")
                        st.metric("Avg Distance", f"{metrics_results['avg_distance'].iloc[0]:.2f} miles")
                    
                    with metrics[1]:
                        st.metric("Avg Fare", f"${metrics_results['avg_fare'].iloc[0]:.2f}")
                        st.metric("Avg Tip", f"${metrics_results['avg_tip'].iloc[0]:.2f}")
                    
                    with metrics[2]:
                        st.metric("Avg Total", f"${metrics_results['avg_total'].iloc[0]:.2f}")
                        st.metric("Total Revenue", f"${metrics_results['total_revenue'].iloc[0]:,.2f}")
                    
                    # Visualizations section
                    st.subheader("Data Visualizations")
                    
                    viz_tabs = st.tabs(["Trips by Hour", "Trips by Borough", "Fare Analysis"])
                    
                    # Tab 1: Trips by Hour
                    with viz_tabs[0]:
                        hour_query = f"""
                        SELECT 
                            EXTRACT(HOUR FROM pickup_time::time) as hour,
                            COUNT(*) as trip_count,
                            AVG(total_amount) as avg_total
                        FROM 
                            taxi_trips
                        WHERE 
                            {where_clause}
                        GROUP BY 
                            EXTRACT(HOUR FROM pickup_time::time)
                        ORDER BY 
                            hour
                        """
                        
                        hour_results = execute_query(hour_query)
                        
                        if not hour_results.empty:
                            # Create hour labels
                            hour_results['hour_label'] = hour_results['hour'].apply(lambda x: f"{int(x)}:00")
                            
                            # Create the chart
                            fig = px.bar(
                                hour_results,
                                x='hour_label',
                                y='trip_count',
                                color='avg_total',
                                labels={
                                    'hour_label': 'Hour of Day',
                                    'trip_count': 'Number of Trips',
                                    'avg_total': 'Avg Total Fare ($)'
                                },
                                title="Trip Distribution by Hour of Day",
                                color_continuous_scale=px.colors.sequential.Viridis
                            )
                            
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.info("No hourly data available for the selected filters.")
                    
                    # Tab 2: Trips by Borough
                    with viz_tabs[1]:
                        borough_query = f"""
                        SELECT 
                            pickup_borough,
                            dropoff_borough,
                            COUNT(*) as trip_count,
                            AVG(total_amount) as avg_total
                        FROM 
                            taxi_trips
                        WHERE 
                            {where_clause}
                        GROUP BY 
                            pickup_borough, dropoff_borough
                        ORDER BY 
                            trip_count DESC
                        """
                        
                        borough_results = execute_query(borough_query)
                        
                        if not borough_results.empty:
                            # Create a heatmap of pickup to dropoff borough
                            borough_pivot = borough_results.pivot_table(
                                index='pickup_borough',
                                columns='dropoff_borough',
                                values='trip_count',
                                fill_value=0
                            )
                            
                            # Create the heatmap
                            fig = px.imshow(
                                borough_pivot,
                                labels=dict(x="Dropoff Borough", y="Pickup Borough", color="Trip Count"),
                                x=borough_pivot.columns,
                                y=borough_pivot.index,
                                title="Trip Count Heatmap: Pickup to Dropoff Borough",
                                color_continuous_scale="Viridis",
                                text_auto=True
                            )
                            
                            fig.update_layout(height=500)
                            st.plotly_chart(fig, use_container_width=True)
                            
                            # Also show average fare by borough
                            borough_avg_query = f"""
                            SELECT 
                                pickup_borough,
                                AVG(fare_amount) as avg_fare,
                                AVG(tip_amount) as avg_tip,
                                AVG(total_amount) as avg_total,
                                COUNT(*) as trip_count
                            FROM 
                                taxi_trips
                            WHERE 
                                {where_clause}
                            GROUP BY 
                                pickup_borough
                            ORDER BY 
                                avg_total DESC
                            """
                            
                            borough_avg_results = execute_query(borough_avg_query)
                            
                            if not borough_avg_results.empty:
                                # Create a bar chart
                                fig = px.bar(
                                    borough_avg_results,
                                    x='pickup_borough',
                                    y=['avg_fare', 'avg_tip'],
                                    labels={
                                        'pickup_borough': 'Borough',
                                        'value': 'Amount ($)',
                                        'variable': 'Type'
                                    },
                                    title="Average Fare and Tip by Pickup Borough",
                                    barmode='group',
                                    color_discrete_map={
                                        'avg_fare': '#636EFA',
                                        'avg_tip': '#EF553B'
                                    }
                                )
                                
                                # Add trip count as text
                                for i, row in enumerate(borough_avg_results.itertuples()):
                                    fig.add_annotation(
                                        x=row.pickup_borough,
                                        y=max(row.avg_fare, row.avg_tip) + 1,
                                        text=f"{row.trip_count} trips",
                                        showarrow=False
                                    )
                                
                                st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.info("No borough data available for the selected filters.")
                    
                    # Tab 3: Fare Analysis
                    with viz_tabs[2]:
                        fare_query = f"""
                        SELECT 
                            trip_distance,
                            fare_amount,
                            tip_amount,
                            total_amount
                        FROM 
                            taxi_trips
                        WHERE 
                            {where_clause} AND
                            trip_distance > 0 AND
                            trip_distance < 30
                        LIMIT 5000
                        """
                        
                        fare_results = execute_query(fare_query)
                        
                        if not fare_results.empty:
                            # Create scatterplot of distance vs. fare
                            fig = px.scatter(
                                fare_results,
                                x='trip_distance',
                                y='total_amount',
                                color='tip_amount',
                                labels={
                                    'trip_distance': 'Trip Distance (miles)',
                                    'total_amount': 'Total Fare ($)',
                                    'tip_amount': 'Tip Amount ($)'
                                },
                                title="Fare vs. Distance Analysis",
                                color_continuous_scale="Viridis",
                                opacity=0.7
                            )
                            
                            # Add trendline
                            fig.update_traces(marker=dict(size=8))
                            
                            # Add a linear regression trendline
                            slope, intercept, r_value, p_value, std_err = stats.linregress(
                                fare_results['trip_distance'],
                                fare_results['total_amount']
                            )
                            
                            # Create trendline data
                            x_range = np.linspace(fare_results['trip_distance'].min(), fare_results['trip_distance'].max(), 100)
                            y_pred = slope * x_range + intercept
                            
                            # Add trendline to plot
                            fig.add_trace(
                                go.Scatter(
                                    x=x_range,
                                    y=y_pred,
                                    mode='lines',
                                    name=f'Trend (${slope:.2f}/mile)',
                                    line=dict(color='red', width=3)
                                )
                            )
                            
                            st.plotly_chart(fig, use_container_width=True)
                            
                            # Show the correlation
                            correlation = fare_results['trip_distance'].corr(fare_results['total_amount'])
                            st.info(f"Correlation between distance and fare: {correlation:.2f}")
                            
                            # Tip percentage analysis
                            fare_results['tip_percentage'] = (fare_results['tip_amount'] / fare_results['fare_amount'] * 100).clip(0, 100)
                            
                            # Create a histogram of tip percentages
                            fig = px.histogram(
                                fare_results,
                                x='tip_percentage',
                                nbins=20,
                                labels={
                                    'tip_percentage': 'Tip Percentage (%)',
                                    'count': 'Number of Trips'
                                },
                                title="Distribution of Tip Percentages",
                                color_discrete_sequence=['#636EFA']
                            )
                            
                            # Add average line
                            avg_tip_pct = fare_results['tip_percentage'].mean()
                            fig.add_vline(
                                x=avg_tip_pct,
                                line_dash="dash",
                                line_color="red",
                                annotation_text=f"Avg: {avg_tip_pct:.1f}%",
                                annotation_position="top right"
                            )
                            
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.info("No fare data available for the selected filters.")
                    
                    # Download section
                    st.subheader("Download Filtered Data")
                    
                    download_query = f"""
                    SELECT 
                        trip_distance,
                        fare_amount,
                        tip_amount,
                        total_amount,
                        pickup_borough,
                        dropoff_borough,
                        pickup_zone,
                        dropoff_zone,
                        pickup_date,
                        pickup_time
                    FROM 
                        taxi_trips
                    WHERE 
                        {where_clause}
                    LIMIT 10000
                    """
                    
                    download_data = execute_query(download_query)
                    
                    if not download_data.empty:
                        st.write(f"Showing {len(download_data)} records (limited to 10,000 for download)")
                        st.dataframe(download_data, use_container_width=True)
                        
                        csv = download_data.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label="Download as CSV",
                            data=csv,
                            file_name="filtered_taxi_data.csv",
                            mime="text/csv",
                        )
                    else:
                        st.warning("No data available for download with current filters.")
                else:
                    st.warning("No data matches your filter criteria. Please adjust and try again.")

# Add Research Questions section
st.sidebar.markdown("---")
st.sidebar.markdown("### Research Questions")
if st.sidebar.checkbox("Show Research Questions"):
    st.sidebar.markdown("""
    1. How does trip distance influence total earnings and tipping behavior?
    2. Does a certain time of day result in higher average tips?
    3. Are trips from specific boroughs/neighborhoods more profitable?
    """)

# Footer
st.markdown("""
<div style="text-align: center; margin-top: 40px; margin-bottom: 20px; font-size: 12px; color: #666;">
    NYC Taxi & Events Analysis Dashboard - Data from June to December 2023
</div>
""", unsafe_allow_html=True)