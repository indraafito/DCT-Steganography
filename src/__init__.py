# Membuat src menjadi Python package
import os
from flask import Flask
from src.config import Config
from src.routes import init_routes

def create_app():
    """Factory function untuk membuat aplikasi Flask"""
    root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    app = Flask(__name__, 
                template_folder=os.path.join(root_path, 'templates'), 
                static_folder=os.path.join(root_path, 'static'),
                root_path=root_path)
    
    # Load konfigurasi
    app.config.from_object(Config)
    Config.init_app(app)
    
    # Inisialisasi routes
    init_routes(app)
    
    return app