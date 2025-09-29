import os

class Config:
    """Konfigurasi aplikasi Flask"""
    SECRET_KEY = 'steganography_secret_key'

    @staticmethod
    def init_app(app):
        """Inisialisasi konfigurasi aplikasi"""
        pass  # Tidak ada folder yang perlu diinisialisasi