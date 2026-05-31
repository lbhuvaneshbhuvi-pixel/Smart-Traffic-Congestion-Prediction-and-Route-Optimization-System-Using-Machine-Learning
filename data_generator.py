import pandas as pd
import numpy as np
import datetime
import os

# Define Tamil Nadu State Highway Transit Hubs
JUNCTIONS = {
    1: {"name": "Chennai (GST Highway Node)", "type": "Highway", "lat": 13.0827, "lon": 80.2707, "base_volume": 2500, "free_speed": 75},
    2: {"name": "Kanchipuram (NH 4 Silk Corridor)", "type": "Arterial", "lat": 12.8387, "lon": 79.7016, "base_volume": 1200, "free_speed": 55},
    3: {"name": "Vellore (NH 4 Bengaluru Highway)", "type": "Highway", "lat": 12.9165, "lon": 79.1325, "base_volume": 1600, "free_speed": 65},
    4: {"name": "Salem (Central Highway Junction)", "type": "Highway", "lat": 11.6643, "lon": 78.1460, "base_volume": 1800, "free_speed": 65},
    5: {"name": "Coimbatore (NH 544 Western Bypass)", "type": "Highway", "lat": 11.0168, "lon": 76.9558, "base_volume": 2000, "free_speed": 70},
    6: {"name": "Trichy (GST Central Junction)", "type": "Highway", "lat": 10.7905, "lon": 78.7047, "base_volume": 1700, "free_speed": 65},
    7: {"name": "Madurai (Southern Highway Ring)", "type": "Highway", "lat": 9.9252, "lon": 78.1198, "base_volume": 1800, "free_speed": 65},
    8: {"name": "Tirunelveli (Deep South Bypass)", "type": "Arterial", "lat": 8.7139, "lon": 77.7567, "base_volume": 1100, "free_speed": 55},
    9: {"name": "Kanyakumari (Southern Coastal Terminal)", "type": "Local", "lat": 8.0883, "lon": 77.5385, "base_volume": 800, "free_speed": 45}
}

def generate_traffic_dataset(days=90, output_file="traffic_data.csv"):
    print(f"Generating realistic state-wide Tamil Nadu traffic data for the last {days} days...")
    
    np.random.seed(42)
    start_date = datetime.datetime.now() - datetime.timedelta(days=days)
    records = []
    
    dates_range = [start_date + datetime.timedelta(hours=h) for h in range(days * 24)]
    
    for dt in dates_range:
        hour = dt.hour
        day_of_week = dt.weekday()  # 0: Monday, 6: Sunday
        month = dt.month
        is_weekend = int(day_of_week >= 5)
        
        # Holiday and Event Logic
        is_holiday = 0
        is_festival = 0
        event_type = "None"
        
        # Public holidays in Tamil Nadu (e.g. Pongal, Diwali, Independence Day)
        if (month == 1 and dt.day in [14, 15, 16]) or (month == 8 and dt.day == 15) or (month == 10 and dt.day == 2) or (month == 5 and dt.day == 1):
            is_holiday = 1
            if month == 1:
                is_festival = 1
                event_type = "Festival"
                
        # Weekends might see holiday/leisure travel spikes
        if is_weekend and np.random.rand() < 0.15:
            event_choice = np.random.choice(["Sports", "Political", "Festival"])
            event_type = event_choice
            if event_choice == "Festival":
                is_festival = 1
        
        # Simulated Weather for Tamil Nadu
        # Monsoon seasons: Southwest (June-Sep) and Northeast (Oct-Dec - highly active in TN)
        is_monsoon = month in [10, 11, 12, 6, 7, 8, 9]
        
        # Temperature (Tropical: Salem/Madurai are very hot, Kanyakumari is breezy)
        base_temp = 31
        temp = base_temp + np.random.normal(0, 2)
        if 11 <= hour <= 16:
            temp += 3
        elif 0 <= hour <= 5:
            temp -= 4
            
        # Humidity
        humidity = 65 + np.random.normal(0, 5)
        if is_monsoon:
            humidity += 18
        humidity = min(max(humidity, 35), 100)
        
        # Rainfall
        rainfall = 0.0
        if is_monsoon and np.random.rand() < 0.22:
            rainfall = np.random.exponential(7.0) # Downpours
        elif np.random.rand() < 0.04:
            rainfall = np.random.exponential(1.5)
        rainfall = np.round(rainfall, 1)
        
        # Wind speed
        wind_speed = 7.0 + np.random.normal(0, 3)
        if rainfall > 5:
            wind_speed += 10
        wind_speed = max(wind_speed, 1.0)
        
        # Visibility
        visibility = 10.0
        if rainfall > 12:
            visibility = 2.5 + np.random.uniform(-0.5, 0.5)
        elif rainfall > 3:
            visibility = 5.5 + np.random.uniform(-1.0, 1.0)
            
        for j_id, j_info in JUNCTIONS.items():
            base_vol = j_info["base_volume"]
            free_speed = j_info["free_speed"]
            road_type = j_info["type"]
            
            # 1. Hour of Day Traffic Multiplier
            # Peak hours: Morning office departure (8-10 AM) and evening return (5-8 PM)
            if hour in [8, 9, 10]:
                hour_mult = 2.0 + np.random.normal(0, 0.12)
            elif hour in [17, 18, 19, 20]:
                hour_mult = 2.3 + np.random.normal(0, 0.15)
            elif 0 <= hour <= 5:
                hour_mult = 0.3 + np.random.normal(0, 0.05)
            else:
                hour_mult = 1.2 + np.random.normal(0, 0.08)
                
            # 2. Weekend Multiplier
            # Highways connecting tourist/commuter spots (Kanyakumari, Kanchipuram) spike on weekends
            # Industrial highways (Salem, Coimbatore) stay relatively flat but office travel drops
            if is_weekend:
                if j_id in [9, 2]:  # Kanyakumari tourism, Kanchi silk tourism
                    weekend_mult = 1.4
                elif j_id in [1, 3]: # Chennai exit, Vellore corridor
                    weekend_mult = 1.2
                else:
                    weekend_mult = 0.85
            else:
                weekend_mult = 1.0
                
            # 3. Holiday and Festival Multiplier
            # Festival/Holidays trigger massive transit flows on GST road (Chennai, Trichy, Madurai exits)
            # Industrial bypasses (Coimbatore) see reduced commercial load
            holiday_mult = 1.0
            if is_holiday:
                if j_id in [1, 6, 7]: # Chennai, Trichy, Madurai GST exits
                    holiday_mult = 1.5
                elif j_id == 9: # Kanyakumari beach tourism
                    holiday_mult = 1.6
                else:
                    holiday_mult = 0.7
                    
            festival_mult = 1.0
            if is_festival:
                if j_id in [1, 6, 7]: # Huge travel south during Pongal/Diwali
                    festival_mult = 1.8
                elif j_id == 2: # Festival silk shopping in Kanchi
                    festival_mult = 1.5
                    
            # 4. Special Event Multiplier
            event_mult = 1.0
            if event_type == "Sports" and j_id in [1, 5]: # Sports matches in Chennai/Coimbatore
                event_mult = 1.3
            elif event_type == "Political" and j_id in [1, 7]: # Rallies in Chennai/Madurai
                event_mult = 1.4
                
            # Calculate final Traffic Volume
            volume = base_vol * hour_mult * weekend_mult * holiday_mult * festival_mult * event_mult
            volume = int(max(volume + np.random.normal(0, volume * 0.08), 40))
            
            # Calculate Vehicle Count (Highways see more heavy trucks/buses)
            vehicle_count = int(volume * np.random.uniform(0.85, 1.15))
            
            # Speed reduction curve
            capacity = base_vol * 1.6
            vc_ratio = volume / capacity
            speed_mult = 1.0 / (1.0 + (vc_ratio ** 2.4))
            
            # Weather speed penalties
            weather_speed_mult = 1.0
            if rainfall > 15:
                weather_speed_mult = 0.50 # heavy flooding on highway
            elif rainfall > 5:
                weather_speed_mult = 0.70
            elif rainfall > 0.5:
                weather_speed_mult = 0.88
                
            if visibility < 3:
                weather_speed_mult *= 0.78
            elif visibility < 6:
                weather_speed_mult *= 0.92
                
            # Final Speed
            speed = free_speed * speed_mult * weather_speed_mult
            speed = speed + np.random.normal(0, speed * 0.06)
            speed = np.round(min(max(speed, 6.0), free_speed + 5), 1)
            
            # Congestion level mapping
            speed_ratio = speed / free_speed
            if speed_ratio >= 0.82:
                congestion = "Low Traffic"
                congestion_label = 0
            elif speed_ratio >= 0.58:
                congestion = "Moderate Traffic"
                congestion_label = 1
            elif speed_ratio >= 0.32:
                congestion = "Heavy Traffic"
                congestion_label = 2
            else:
                congestion = "Severe Traffic"
                congestion_label = 3
                
            records.append({
                "Date": dt.strftime("%Y-%m-%d"),
                "Time": dt.strftime("%H:%M:%S"),
                "Hour": hour,
                "Day_of_Week": day_of_week,
                "Month": month,
                "Is_Weekend": is_weekend,
                "Junction_ID": j_id,
                "Junction_Name": j_info["name"],
                "Road_Type": road_type,
                "Traffic_Volume": volume,
                "Average_Speed": speed,
                "Vehicle_Count": vehicle_count,
                "Temperature": np.round(temp, 1),
                "Humidity": int(humidity),
                "Rainfall": rainfall,
                "Wind_Speed": np.round(wind_speed, 1),
                "Visibility": np.round(visibility, 1),
                "Holiday_Indicator": is_holiday,
                "Festival_Indicator": is_festival,
                "Event_Type": event_type,
                "Congestion_Level": congestion,
                "Congestion_Label": congestion_label
            })
            
    df = pd.DataFrame(records)
    df.to_csv(output_file, index=False)
    print(f"Dataset successfully created: '{output_file}' with {len(df)} rows.")
    return df

if __name__ == "__main__":
    generate_traffic_dataset()
