from flask import Flask, render_template, request, send_file, flash, redirect, url_for
import os
from PIL import Image
import numpy as np
import cv2
import math

app = Flask(__name__)
app.secret_key = 'steganography_secret_key'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'outputs'

# Pastikan folder ada
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

class DCTSteganography:
    """
    Steganografi menggunakan DCT (Discrete Cosine Transform)
    dengan delimiter untuk menghilangkan kebutuhan input panjang pesan
    Mempertahankan gambar berwarna (RGB)
    """
    
    BLOCK_SIZE = 8  # Ukuran blok DCT
    STEP = 10       # Besarnya perubahan untuk representasi bit
    DELIMITER = "###END###"  # Delimiter untuk menandai akhir pesan
    
    @staticmethod
    def text_to_binary(text):
        """Konversi teks ke binary dengan delimiter"""
        # Tambahkan delimiter di akhir pesan
        full_message = text + DCTSteganography.DELIMITER
        binary = ''.join(format(ord(char), '08b') for char in full_message)
        return binary
    
    @staticmethod
    def binary_to_text(binary):
        """Konversi binary ke teks dan cari delimiter"""
        text = ''
        for i in range(0, len(binary), 8):
            if i + 8 <= len(binary):
                byte = binary[i:i+8]
                try:
                    char_code = int(byte, 2)
                    if 32 <= char_code <= 126:  # Printable ASCII
                        char = chr(char_code)
                        text += char
                    else:
                        # Skip non-printable characters
                        continue
                except ValueError:
                    continue
        
        # Cari delimiter dan ambil pesan sebelum delimiter
        delimiter_pos = text.find(DCTSteganography.DELIMITER)
        if delimiter_pos != -1:
            return text[:delimiter_pos]
        else:
            # Jika delimiter tidak ditemukan, coba cari pola yang masuk akal
            # Potong di karakter non-printable pertama atau return teks yang ada
            clean_text = ""
            for char in text:
                if 32 <= ord(char) <= 126:
                    clean_text += char
                else:
                    break
            return clean_text if clean_text else "No readable message found"
    
    @staticmethod
    def embed_message(image_path, message):
        """Embed pesan ke dalam gambar menggunakan DCT pada channel biru"""
        try:
            # Buka gambar dan pertahankan format RGB
            img = Image.open(image_path)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            img_array = np.array(img, dtype=np.float32)
            h, w, channels = img_array.shape
            print(f"Original image size: {h}x{w}x{channels}")
            
            # Ambil channel biru untuk embedding (channel 2)
            blue_channel = img_array[:, :, 2].copy()
            
            # Padding untuk memastikan dimensi adalah kelipatan BLOCK_SIZE
            padded_h = math.ceil(h / DCTSteganography.BLOCK_SIZE) * DCTSteganography.BLOCK_SIZE
            padded_w = math.ceil(w / DCTSteganography.BLOCK_SIZE) * DCTSteganography.BLOCK_SIZE
            
            padded_blue = np.zeros((padded_h, padded_w), dtype=np.float32)
            padded_blue[:h, :w] = blue_channel
            
            # Konversi pesan ke binary
            message_bin = DCTSteganography.text_to_binary(message)
            print(f"Message: '{message}'")
            print(f"Message with delimiter: '{message + DCTSteganography.DELIMITER}'")
            print(f"Binary message length: {len(message_bin)} bits")
            
            # Hitung kapasitas maksimum
            total_blocks = (padded_h // DCTSteganography.BLOCK_SIZE) * (padded_w // DCTSteganography.BLOCK_SIZE)
            max_capacity = total_blocks * (DCTSteganography.BLOCK_SIZE - 1) * (DCTSteganography.BLOCK_SIZE - 1)
            
            print(f"Total blocks: {total_blocks}")
            print(f"Maximum capacity: {max_capacity} bits ({max_capacity // 8} characters)")
            
            if len(message_bin) > max_capacity:
                return None, f"Message too long. Maximum capacity: {max_capacity // 8} characters, need: {len(message_bin) // 8}"
            
            # Embedding process
            idx = 0
            embedded_bits = 0
            
            for i in range(0, padded_h, DCTSteganography.BLOCK_SIZE):
                for j in range(0, padded_w, DCTSteganography.BLOCK_SIZE):
                    if idx >= len(message_bin):
                        break
                        
                    # Ambil blok 8x8
                    block = padded_blue[i:i+DCTSteganography.BLOCK_SIZE, j:j+DCTSteganography.BLOCK_SIZE]
                    
                    # Aplikasikan DCT
                    dct_block = cv2.dct(block)
                    
                    # Embed di koefisien mid-frequency (skip DC coefficient di [0,0])
                    for u in range(1, DCTSteganography.BLOCK_SIZE):
                        for v in range(1, DCTSteganography.BLOCK_SIZE):
                            if idx < len(message_bin):
                                original_coeff = dct_block[u, v]
                                
                                if message_bin[idx] == '1':
                                    # Set koefisien positif dengan magnitude minimal STEP
                                    if dct_block[u, v] >= 0:
                                        dct_block[u, v] = max(abs(dct_block[u, v]), DCTSteganography.STEP)
                                    else:
                                        dct_block[u, v] = max(abs(dct_block[u, v]), DCTSteganography.STEP)
                                else:
                                    # Set koefisien negatif dengan magnitude minimal STEP
                                    if dct_block[u, v] >= 0:
                                        dct_block[u, v] = -max(abs(dct_block[u, v]), DCTSteganography.STEP)
                                    else:
                                        dct_block[u, v] = -max(abs(dct_block[u, v]), DCTSteganography.STEP)
                                
                                if embedded_bits < 20:  # Debug first 20 bits
                                    print(f"Bit {embedded_bits}: '{message_bin[idx]}' at [{u},{v}]: {original_coeff:.2f} -> {dct_block[u, v]:.2f}")
                                
                                idx += 1
                                embedded_bits += 1
                            else:
                                break
                        if idx >= len(message_bin):
                            break
                    
                    # Inverse DCT
                    modified_block = cv2.idct(dct_block)
                    padded_blue[i:i+DCTSteganography.BLOCK_SIZE, j:j+DCTSteganography.BLOCK_SIZE] = modified_block
                
                if idx >= len(message_bin):
                    break
            
            # Kembalikan channel biru yang sudah dimodifikasi ke gambar asli
            img_array[:, :, 2] = padded_blue[:h, :w]
            
            # Clip values dan konversi ke PIL Image
            final_img_array = np.clip(img_array, 0, 255).astype(np.uint8)
            final_img = Image.fromarray(final_img_array, mode='RGB')
            
            print(f"Successfully embedded {embedded_bits} bits")
            return final_img, "Success"
            
        except Exception as e:
            print(f"Embedding error: {str(e)}")
            import traceback
            traceback.print_exc()
            return None, str(e)
    
    @staticmethod
    def extract_message(image_path):
        """Extract pesan dari gambar menggunakan DCT pada channel biru"""
        try:
            # Buka gambar dan pastikan format RGB
            img = Image.open(image_path)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            img_array = np.array(img, dtype=np.float32)
            h, w, channels = img_array.shape
            print(f"Image size for extraction: {h}x{w}x{channels}")
            
            # Ambil channel biru
            blue_channel = img_array[:, :, 2]
            
            # Padding untuk memastikan dimensi adalah kelipatan BLOCK_SIZE
            padded_h = math.ceil(h / DCTSteganography.BLOCK_SIZE) * DCTSteganography.BLOCK_SIZE
            padded_w = math.ceil(w / DCTSteganography.BLOCK_SIZE) * DCTSteganography.BLOCK_SIZE
            
            padded_blue = np.zeros((padded_h, padded_w), dtype=np.float32)
            padded_blue[:h, :w] = blue_channel
            
            # Extraction process
            message_bin = ''
            extracted_bits = 0
            
            for i in range(0, padded_h, DCTSteganography.BLOCK_SIZE):
                for j in range(0, padded_w, DCTSteganography.BLOCK_SIZE):
                    # Ambil blok 8x8
                    block = padded_blue[i:i+DCTSteganography.BLOCK_SIZE, j:j+DCTSteganography.BLOCK_SIZE]
                    
                    # Aplikasikan DCT
                    dct_block = cv2.dct(block)
                    
                    # Extract dari koefisien mid-frequency
                    for u in range(1, DCTSteganography.BLOCK_SIZE):
                        for v in range(1, DCTSteganography.BLOCK_SIZE):
                            # Bit adalah 1 jika koefisien positif, 0 jika negatif
                            bit = '1' if dct_block[u, v] > 0 else '0'
                            message_bin += bit
                            
                            if extracted_bits < 20:  # Debug first 20 bits
                                print(f"Extracted bit {extracted_bits}: '{bit}' from coeff [{u},{v}]: {dct_block[u, v]:.2f}")
                            
                            extracted_bits += 1
                            
                            # Cek delimiter setiap kelipatan 8 bits
                            if len(message_bin) >= len(DCTSteganography.DELIMITER) * 8 and len(message_bin) % 8 == 0:
                                temp_text = DCTSteganography.binary_to_text(message_bin)
                                if DCTSteganography.DELIMITER in temp_text:
                                    final_message = temp_text.split(DCTSteganography.DELIMITER)[0]
                                    print(f"Delimiter found! Extracted message: '{final_message}'")
                                    return final_message
                            
                            # Batas maksimal untuk menghindari infinite loop
                            if extracted_bits > 10000:  # Maksimal 10000 bits
                                break
                        
                        if extracted_bits > 10000:
                            break
                    
                    if extracted_bits > 10000:
                        break
                
                if extracted_bits > 10000:
                    break
            
            print(f"Total extracted bits: {extracted_bits}")
            print(f"Binary message (first 200 chars): {message_bin[:200]}")
            
            # Jika delimiter tidak ditemukan, coba decode semua yang ada
            message = DCTSteganography.binary_to_text(message_bin)
            print(f"Decoded message without delimiter: '{message}'")
            return message if message else "No hidden message found"
            
        except Exception as e:
            print(f"Extraction error: {str(e)}")
            import traceback
            traceback.print_exc()
            return f"Error: {str(e)}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/embed', methods=['POST'])
def embed():
    try:
        if 'image' not in request.files or 'message' not in request.form:
            flash('Please provide both image and message', 'error')
            return redirect(url_for('index'))
        
        image_file = request.files['image']
        message = request.form['message']
        
        if image_file.filename == '' or message.strip() == '':
            flash('Please provide both image and message', 'error')
            return redirect(url_for('index'))
        
        # Simpan file upload
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_file.filename)
        image_file.save(image_path)
        
        # Embed message menggunakan DCT
        result_img, status = DCTSteganography.embed_message(image_path, message)
        
        if result_img is None:
            flash(f'Embedding failed: {status}', 'error')
            return redirect(url_for('index'))
        
        # Simpan hasil
        name, ext = os.path.splitext(image_file.filename)
        output_filename = f"embedded_{name}.png"  # Simpan sebagai PNG untuk menghindari kompresi JPEG
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
        result_img.save(output_path, 'PNG')
        
        flash(f'Message embedded successfully! Download: {output_filename}', 'success')
        return send_file(output_path, as_attachment=True, download_name=output_filename)
        
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/extract', methods=['POST'])
def extract():
    try:
        if 'image' not in request.files:
            flash('Please provide an image file', 'error')
            return redirect(url_for('index'))
        
        image_file = request.files['image']
        
        if image_file.filename == '':
            flash('Please select an image file', 'error')
            return redirect(url_for('index'))
        
        # Simpan file upload
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_file.filename)
        image_file.save(image_path)
        
        # Extract message menggunakan DCT
        extracted_message = DCTSteganography.extract_message(image_path)
        
        if extracted_message and extracted_message != "No hidden message found":
            flash(f'Extracted message: {extracted_message}', 'success')
        else:
            flash('No hidden message found in the image', 'error')
        
        return redirect(url_for('index'))
        
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)