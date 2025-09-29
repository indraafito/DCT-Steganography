import os

class Config:
    """Konfigurasi aplikasi Flask"""
    SECRET_KEY = 'steganography_secret_key'
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    OUTPUT_FOLDER = os.path.join(BASE_DIR, 'outputs')

    @staticmethod
    def init_app(app):
        """Inisialisasi folder yang dibutuhkan"""
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)