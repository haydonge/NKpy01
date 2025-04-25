import os
from datetime import datetime

class Config:
    DEBUG = True
    DATABASE = 'test_reports.sqlite'
    UPLOAD_FOLDER = 'uploads'
    XML_DIRECTORY = 'testReports'
    DATE_FORMAT = "%Y%m%d-%H%M%S"  # Format for dates in XML

    @staticmethod
    def init_app(app):
        # Create directories if they don't exist
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(Config.XML_DIRECTORY, exist_ok=True)