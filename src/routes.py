import os
from flask import render_template, request, send_file, flash, redirect, url_for
from src.steganography import DCTSteganography

def init_routes(app):
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
            
            # Embed message menggunakan DCT langsung dari file object
            result_img, status = DCTSteganography.embed_message(image_file, message)
            
            if result_img is None:
                flash(f'Embedding failed: {status}', 'error')
                return redirect(url_for('index'))
            
            # Konversi hasil ke bytes
            from io import BytesIO
            output_buffer = BytesIO()
            result_img.save(output_buffer, format='PNG')
            output_buffer.seek(0)
            
            # Generate nama file output
            name, _ = os.path.splitext(image_file.filename)
            output_filename = f"embedded_{name}.png"
            
            flash('Message embedded successfully!', 'success')
            return send_file(
                output_buffer,
                mimetype='image/png',
                as_attachment=True,
                download_name=output_filename
            )
            
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
            
            # Extract message menggunakan DCT langsung dari file object
            extracted_message = DCTSteganography.extract_message(image_file)
            
            if extracted_message and extracted_message != "No hidden message found":
                flash(f'Extracted message: {extracted_message}', 'success')
            else:
                flash('No hidden message found in the image', 'error')
            
            return redirect(url_for('index'))
            
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')
            return redirect(url_for('index'))