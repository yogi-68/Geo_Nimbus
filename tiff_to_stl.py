from imports import *



tiff_to_stl_bp = Blueprint('tiff_to_stl', __name__)
UPLOAD_FOLDER = 'uploads'
STATIC_FOLDER = 'static'

def calculate_elevation_stats(file_path):
    with rasterio.open(file_path) as src:
        elevation_data = src.read(1)
        mean_elevation = np.mean(elevation_data)
        min_elevation = np.min(elevation_data)
        max_elevation = np.max(elevation_data)
    return elevation_data, mean_elevation, min_elevation, max_elevation

def generate_stl(file_path, vertical_exaggeration, width_mm):
    elevation_data, mean_elevation, min_elevation, max_elevation = calculate_elevation_stats(file_path)
    rows, cols = elevation_data.shape
    scale = width_mm / cols
    vertices = []
    faces = []

    for i in range(rows):
        for j in range(cols):
            vertices.append([i * scale, j * scale, elevation_data[i, j] * vertical_exaggeration])

    for i in range(rows - 1):
        for j in range(cols - 1):
            idx = i * cols + j
            faces.append([idx, idx + 1, idx + cols])
            faces.append([idx + 1, idx + cols + 1, idx + cols])

    vertices = np.array(vertices)
    faces = np.array(faces)
    terrain_mesh = mesh.Mesh(np.zeros(faces.shape[0], dtype=mesh.Mesh.dtype))
    for i, face in enumerate(faces):
        for j in range(3):
            terrain_mesh.vectors[i][j] = vertices[face[j], :]

    stl_file_path = os.path.join(STATIC_FOLDER, 'terrain.stl')
    terrain_mesh.save(stl_file_path)
    return stl_file_path, mean_elevation, min_elevation, max_elevation

@tiff_to_stl_bp.route('/convert_stl', methods=['GET', 'POST'])
def convert_stl():
    if request.method == 'POST':
        file = request.files['file']
        if file and file.filename.endswith(('.tif', '.tiff')):
            filename = secure_filename(file.filename)
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(file_path)

            try:
                vertical_exaggeration = float(request.form['vertical_exaggeration'])
                width = float(request.form['width'])

                stl_file, mean_elevation, min_elevation, max_elevation = generate_stl(file_path, vertical_exaggeration, width)
                return render_template('tiff_to_stl.html', mean_elevation=mean_elevation, min_elevation=min_elevation, max_elevation=max_elevation, stl_url=f'/static/terrain.stl')
            except Exception as e:
                return render_template('tiff_to_stl.html', error=str(e))
        else:
            return render_template('tiff_to_stl.html', error="Invalid file format. Please upload a .tif or .tiff file.")
    return render_template('tiff_to_stl.html')

# Ensure the upload and static folders exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
if not os.path.exists(STATIC_FOLDER):
    os.makedirs(STATIC_FOLDER)