from PIL import Image
import numpy as np
import cv2
import math

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
        temp_text = ''
        
        # Konversi binary ke teks
        for i in range(0, len(binary), 8):
            if i + 8 <= len(binary):
                byte = binary[i:i+8]
                try:
                    char_code = int(byte, 2)
                    char = chr(char_code)
                    text += char
                    
                    # Jika karakter valid, tambahkan ke temp_text
                    if 32 <= char_code <= 126:  # Printable ASCII
                        temp_text += char
                        # Cek delimiter setiap kali menambah karakter valid
                        if DCTSteganography.DELIMITER in temp_text:
                            return temp_text.split(DCTSteganography.DELIMITER)[0]
                except ValueError:
                    continue
                except UnicodeEncodeError:
                    continue
        
        # Jika tidak menemukan delimiter tapi ada teks yang terbaca
        if temp_text:
            # Coba ambil bagian awal yang masih bisa dibaca
            readable_text = ''
            for char in temp_text:
                if 32 <= ord(char) <= 126:
                    readable_text += char
                else:
                    break
            return readable_text if readable_text else "No readable message found"
            
        return "No readable message found"
    
    @staticmethod
    def embed_message(image_data, message):
        """Embed pesan ke dalam gambar menggunakan DCT pada channel biru"""
        try:
            # Buka gambar dari bytes atau file dan pertahankan format RGB
            if isinstance(image_data, str):
                img = Image.open(image_data)
            else:
                img = Image.open(image_data)
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
                                    # Set koefisien positif
                                    dct_block[u, v] = DCTSteganography.STEP if abs(dct_block[u, v]) < DCTSteganography.STEP else abs(dct_block[u, v])
                                else:
                                    # Set koefisien negatif
                                    dct_block[u, v] = -DCTSteganography.STEP if abs(dct_block[u, v]) < DCTSteganography.STEP else -abs(dct_block[u, v])
                                
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
    def extract_message(image_data):
        """Extract pesan dari gambar menggunakan DCT pada channel biru"""
        try:
            # Buka gambar dari bytes atau file dan pastikan format RGB
            if isinstance(image_data, str):
                img = Image.open(image_data)
            else:
                img = Image.open(image_data)
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
                            
                            # Cek setiap 8 bits (1 byte)
                            if len(message_bin) % 8 == 0:
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