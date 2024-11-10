# compressed_tiff.py
from imports import *


UPLOAD_FOLDER = 'uploads'

def compress_geotiff(input_path, output_path):
    gdal_translate_cmd = [
        'gdal_translate',
        '-co', 'COMPRESS=DEFLATE',
        input_path,
        output_path
    ]
    subprocess.run(gdal_translate_cmd, check=True)

def compress_tiff(file):
    if file.filename == '':
        return "No selected file", 400
    filename = secure_filename(file.filename)
    input_path = os.path.join(UPLOAD_FOLDER, filename)
    output_path = os.path.join(UPLOAD_FOLDER, 'compressed_' + filename)
    file.save(input_path)
    try:
        compress_geotiff(input_path, output_path)
        return send_file(output_path, as_attachment=True)
    except subprocess.CalledProcessError:
        return "Error compressing the TIFF file", 500

def convert_to_cog(input_path):
    output_path = os.path.splitext(input_path)[0] + '_cog.tif'
    gdal_translate_cmd = [
        'gdal_translate',
        '-of', 'COG',
        input_path,
        output_path
    ]
    subprocess.run(gdal_translate_cmd, check=True)
    return output_path

def ensure_upload_folder_exists():
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

ensure_upload_folder_exists()