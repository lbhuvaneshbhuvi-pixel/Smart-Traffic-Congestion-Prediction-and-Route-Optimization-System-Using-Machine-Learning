from flask_sqlalchemy import SQLAlchemy
import datetime

db = SQLAlchemy()

class Junction(db.Model):
    __tablename__ = 'junctions'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    road_type = db.Column(db.String(50), nullable=False) # e.g. Highway, Arterial, Local
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    base_volume = db.Column(db.Integer, nullable=False)
    free_speed = db.Column(db.Float, nullable=False)
    
    predictions = db.relationship('TrafficPrediction', backref='junction', lazy=True)
    historical_data = db.relationship('HistoricalTrafficData', backref='junction', lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "road_type": self.road_type,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "base_volume": self.base_volume,
            "free_speed": self.free_speed
        }


class TrafficPrediction(db.Model):
    __tablename__ = 'traffic_predictions'
    
    id = db.Column(db.Integer, primary_key=True)
    junction_id = db.Column(db.Integer, db.ForeignKey('junctions.id'), nullable=False)
    prediction_time = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)
    horizon = db.Column(db.Integer, nullable=False) # 15, 30, 60 minutes
    temperature = db.Column(db.Float, nullable=False)
    rainfall = db.Column(db.Float, nullable=False)
    humidity = db.Column(db.Float, nullable=False)
    visibility = db.Column(db.Float, nullable=False)
    event_type = db.Column(db.String(50), nullable=False, default='None')
    holiday_indicator = db.Column(db.Integer, nullable=False, default=0)
    
    # Model Predictions
    predicted_congestion = db.Column(db.String(50), nullable=False) # Low, Moderate, Heavy, Severe
    predicted_speed = db.Column(db.Float, nullable=False)
    predicted_volume = db.Column(db.Integer, nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "junction_id": self.junction_id,
            "junction_name": self.junction.name if self.junction else "Unknown",
            "prediction_time": self.prediction_time.strftime("%Y-%m-%d %H:%M:%S"),
            "horizon": self.horizon,
            "temperature": self.temperature,
            "rainfall": self.rainfall,
            "humidity": self.humidity,
            "visibility": self.visibility,
            "event_type": self.event_type,
            "holiday_indicator": self.holiday_indicator,
            "predicted_congestion": self.predicted_congestion,
            "predicted_speed": self.predicted_speed,
            "predicted_volume": self.predicted_volume,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S")
        }


class HistoricalTrafficData(db.Model):
    __tablename__ = 'historical_traffic_data'
    
    id = db.Column(db.Integer, primary_key=True)
    junction_id = db.Column(db.Integer, db.ForeignKey('junctions.id'), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    hour = db.Column(db.Integer, nullable=False)
    day_of_week = db.Column(db.Integer, nullable=False)
    month = db.Column(db.Integer, nullable=False)
    is_weekend = db.Column(db.Integer, nullable=False)
    
    # Features
    traffic_volume = db.Column(db.Integer, nullable=False)
    average_speed = db.Column(db.Float, nullable=False)
    vehicle_count = db.Column(db.Integer, nullable=False)
    temperature = db.Column(db.Float, nullable=False)
    humidity = db.Column(db.Integer, nullable=False)
    rainfall = db.Column(db.Float, nullable=False)
    wind_speed = db.Column(db.Float, nullable=False)
    visibility = db.Column(db.Float, nullable=False)
    holiday_indicator = db.Column(db.Integer, nullable=False)
    festival_indicator = db.Column(db.Integer, nullable=False)
    event_type = db.Column(db.String(50), nullable=False)
    
    # Targets
    congestion_level = db.Column(db.String(50), nullable=False)
    congestion_label = db.Column(db.Integer, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "junction_id": self.junction_id,
            "junction_name": self.junction.name if self.junction else "Unknown",
            "timestamp": self.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "hour": self.hour,
            "day_of_week": self.day_of_week,
            "traffic_volume": self.traffic_volume,
            "average_speed": self.average_speed,
            "congestion_level": self.congestion_level
        }
