class Config:
    MYSQL_HOST = 'localhost'
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = ''   # EMPTY PASSWORD for XAMPP
    MYSQL_DB = 'farmer_market'
    UPLOAD_FOLDER = 'static/uploads'
    SECRET_KEY = 'farmer_market_secret_key_2025'
    SESSION_TYPE = 'filesystem'
    import os as _os
    OWNER_EMAIL = _os.environ.get('OWNER_EMAIL')
    OWNER_PASSWORD = _os.environ.get('OWNER_PASSWORD')
