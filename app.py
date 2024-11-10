import base64
from io import BytesIO
from flask import Flask, request, render_template, send_file, jsonify, redirect, url_for, send_from_directory
import os
from matplotlib import pyplot as plt
import numpy as np
import rasterio
import folium
from werkzeug.utils import secure_filename
from osgeo import gdal
from bathymetry import get_bathymetry_image
from tiff_utils import save_cropped_tiff
from tiff_processing import tiff_processing_bp
from geotiff_utils import load_geotiff, tiff_to_csv
from bathymetric_utils import extract_bathymetric_data, save_extracted_image, create_map_with_overlay
from tiff_to_stl import tiff_to_stl_bp
from compressed_tiff import compress_tiff, convert_to_cog
from hill_shade import get_band_data, hillshade, apply_colormap

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'tif', 'tiff'}

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Register the blueprints
app.register_blueprint(tiff_processing_bp)
app.register_blueprint(tiff_to_stl_bp)

# Check for allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/hill_shade')
def hill_shade_page():
    return render_template('hill_shade.html')

@app.route('/upload_hillshade', methods=['POST'])
def upload_hillshade():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'})

    # Save the uploaded file
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename))
    file.save(file_path)

    # Open the TIFF file using GDAL
    dataset = gdal.Open(file_path)
    if not dataset:
        return jsonify({'error': 'Failed to open TIFF file'})

    band_number = int(request.form.get('band', 1))
    
    colormap = request.form.get('colormap', 'bathymetry')  # Default to 'bathymetry'
    apply_hillshade = request.form.get('hillshade', 'false') == 'true'

    # Get band data
    data = get_band_data(dataset, band_number)

    # Apply hillshade if selected
    if apply_hillshade:
        data = hillshade(data)

    # Apply color map
    colored_data = apply_colormap(data, colormap)

    # Convert to image
    fig, ax = plt.subplots()
    ax.imshow(colored_data, aspect='auto')
    ax.axis('off')

    # Add color bar for bathymetry
    if colormap == 'bathymetry':
        cbar = fig.colorbar(plt.cm.ScalarMappable(cmap='terrain', norm=plt.Normalize(vmin=data.min(), vmax=data.max())), ax=ax)
        cbar.set_label('Elevation (meters)')

    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0)
    plt.close(fig)
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')

    return jsonify({'image': img_base64, 'filename': file.filename})

@app.route('/upload_region', methods=['GET', 'POST'])
def upload_region():
    if request.method == 'POST':
        # Save the uploaded files
        global_file = 'datasetss.tif'
        region_file = 'region.tif'

        # Load the global bathymetric data
        with rasterio.open(global_file) as global_src:
            global_bounds = global_src.bounds

            # Read the region bounds
            region_file = request.files['region_file']
            region_file.save(region_file.filename)
            with rasterio.open(region_file.filename) as region_src:
                region_bounds = region_src.bounds
                region_transform = region_src.transform
                
                # Calculate the window from the region bounds
                window = global_src.window(region_bounds.left, region_bounds.bottom,
                                          region_bounds.right, region_bounds.top)

                # Read the data from the global dataset within the window
                global_data = global_src.read(1, window=window)
                global_transform = global_src.window_transform(window)

                # Convert global data to image
                image = np.clip(global_data, 0, 255).astype(np.uint8)
                
                # Save the image to be used by folium
                image_filename = 'extracted_image.png'
                with rasterio.open(image_filename, 'w', driver='PNG', height=image.shape[0],
                                   width=image.shape[1], count=1, dtype='uint8', crs=global_src.crs,
                                   transform=global_transform) as dst:
                    dst.write(image, 1)

            # Create a Folium map
            center = [(region_bounds.top + region_bounds.bottom) / 2, (region_bounds.left + region_bounds.right) / 2]
            m = folium.Map(location=center, zoom_start=8)

            # Add the raster layer to the map
            folium.raster_layers.ImageOverlay(
                image=image_filename,
                bounds=[[region_bounds.bottom, region_bounds.left], [region_bounds.top, region_bounds.right]],
                opacity=0.6
            ).add_to(m)

            # Save the map to an HTML file
            map_html = 'map.html'
            m.save(map_html)

        return send_from_directory('.', map_html)

    # If GET request, render the upload template
    return render_template('upload.html')

@app.route('/', methods=['POST'])
def process_tiff():
    try:
        north = float(request.form['north'])
        south = float(request.form['south'])
        east = float(request.form['east'])
        west = float(request.form['west'])
        colorized = request.form.get('view_mode') == 'colored'

        file_path = 'datasetss.tif'

        img_data = get_bathymetry_image(file_path, north, south, east, west, colorized)

        if img_data:
            return render_template('index.html', image_data=img_data, file_path=file_path, north=north, south=south, east=east, west=west, colorized=colorized)
        else:
            return render_template('index.html', error="No data found for the specified bounding box.")
    except ValueError:
        return render_template('index.html', error="Invalid input. Please enter valid numeric values.")
    except Exception as e:
        print(f"An error occurred: {e}")
        return render_template('index.html', error="An unexpected error occurred.")

@app.route('/path_profile')
def path_profile():
    return send_from_directory('templates', 'Path_Profile.html')

@app.route('/download_tiff', methods=['POST'])
def download_tiff():
    try:
        file_path = request.form['file_path']
        north = float(request.form['north'])
        south = float(request.form['south'])
        east = float(request.form['east'])
        west = float(request.form['west'])
        colorized = request.form.get('colorized') == 'True'

        tiff_path = save_cropped_tiff(file_path, north, south, east, west, colorized)

        if tiff_path:
            return send_file(tiff_path, as_attachment=True, download_name="cropped_bathymetry.tif")
        else:
            return redirect(url_for('index', error="Failed to create the TIFF file."))
    except Exception as e:
        print(f"An error occurred: {e}")
        return redirect(url_for('index', error="An unexpected error occurred."))

@app.route('/convert_csv')
def convert_csv_page():
    return render_template('convert_csv.html')

@app.route('/convert_csv', methods=['POST'])
def convert_csv():
    try:
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            output_csv = os.path.join(app.config['UPLOAD_FOLDER'], f"{os.path.splitext(filename)[0]}.csv")
            tiff_to_csv(file_path, output_csv)

            return send_file(output_csv, as_attachment=True, download_name=f"{os.path.splitext(filename)[0]}.csv")
        else:
            return jsonify({'error': 'Invalid file type'})
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({'error': 'An unexpected error occurred'})

@app.route('/convert', methods=['POST'])
def convert():
    if 'tiff' not in request.files:
        return 'No file part', 400

    file = request.files['tiff']
    if allowed_file(file.filename):
        return compress_tiff(file)
    else:
        return 'Invalid file type', 400

@app.route('/download_cog', methods=['POST'])
def download_cog():
    try:
        file_path = request.form['file_path']
        north = float(request.form['north'])
        south = float(request.form['south'])
        east = float(request.form['east'])
        west = float(request.form['west'])
        view_mode = request.form['view_mode']
        colorized = view_mode == 'colored'

        # First, save the cropped TIFF
        tiff_path = save_cropped_tiff(file_path, north, south, east, west, colorized)

        if tiff_path:
            # Convert the cropped TIFF to COG
            cog_path = convert_to_cog(tiff_path)
            if cog_path:
                return send_file(cog_path, as_attachment=True, download_name="cropped_bathymetry_cog.tif")
            else:
                return redirect(url_for('index', error="Failed to create the COG file."))
        else:
            return redirect(url_for('index', error="Failed to create the TIFF file."))
    except Exception as e:
        print(f"An error occurred: {e}")
        return redirect(url_for('index', error="An unexpected error occurred."))

if __name__ == '__main__':
    app.run(debug=True, port=68)