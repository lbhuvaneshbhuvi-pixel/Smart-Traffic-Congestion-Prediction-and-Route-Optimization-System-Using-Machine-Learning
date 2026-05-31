import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'traffic_congestion_prediction_secret_key_12983')
    
    # Database Configuration
    # SQLite is used as the out-of-the-box default database for simple setup and instant running.
    # To switch to MySQL (as per project requirements), simply uncomment the MySQL URI below and provide credentials.
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        f'sqlite:///{os.path.join(BASE_DIR, "traffic_system.db")}'
    )
    
    # For MySQL:
    # SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://username:password@localhost/traffic_db'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # API Settings (Optional placeholders for live integrations)
    OPENWEATHER_API_KEY = os.environ.get('OPENWEATHER_API_KEY', 'your_openweather_api_key_here')
    GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY', 'your_google_maps_api_key_here')
