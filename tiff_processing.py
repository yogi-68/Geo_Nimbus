# tiff_processing.py
from imports import *


tiff_processing_bp = Blueprint('tiff_processing', __name__)

UPLOAD_FOLDER = 'uploads'
STATIC_FOLDER = 'static'
ALLOWED_EXTENSIONS = {'tif', 'tiff'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_tiff(file_path):
    with rasterio.open(file_path) as src:
        band1 = src.read(1)
        img = Image.fromarray(band1.astype(np.uint8))
        img.save(os.path.join(STATIC_FOLDER, 'elevation_image.png'))
        np.save(os.path.join(STATIC_FOLDER, 'elevation_data.npy'), band1)

def get_profile_data(elevation_data, start, end):
    distances = []
    elevations = []
    
    x0, y0 = start
    x1, y1 = end
    
    # Compute line segment length and number of points
    length = math.sqrt((x1 - x0) ** 2 + (y1 - y0) ** 2)
    num_points = int(length)
    
    for i in range(num_points + 1):
        t = i / num_points
        x = int(x0 + t * (x1 - x0))
        y = int(y0 + t * (y1 - y0))
        
        # Ensure coordinates are within bounds
        if 0 <= x < elevation_data.shape[1] and 0 <= y < elevation_data.shape[0]:
            distances.append(i)
            elevations.append(float(elevation_data[y, x]))  # Convert to Python float
    
    return {
        "distances": distances,
        "elevations": elevations
    }

@tiff_processing_bp.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'})
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'})
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(file_path)
            process_tiff(file_path)
            return jsonify({'status': 'File uploaded and processed successfully'})
        else:
            return jsonify({'error': 'Invalid file type'})
    else:
        # If GET request, render the upload template
        return render_template('upload.html')

@tiff_processing_bp.route('/image')
def get_image():
    return send_from_directory(STATIC_FOLDER, 'elevation_image.png')

@tiff_processing_bp.route('/profile', methods=['POST'])
def profile():
    data = request.json
    start = tuple(data['start'])
    end = tuple(data['end'])
    
    # Load elevation data from .npy file
    data_path = os.path.join(STATIC_FOLDER, 'elevation_data.npy')
    if not os.path.exists(data_path):
        return jsonify({'error': 'Elevation data not found'})
    
    elevation_data = np.load(data_path)
    
    # Calculate profile data
    profile_data = get_profile_data(elevation_data, start, end)
    
    return jsonify(profile_data)