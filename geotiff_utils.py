# geotiff_utils.py
from imports import *


def load_geotiff(file_path):
    with rasterio.open(file_path) as dataset:
        data = dataset.read(1)
        transform = dataset.transform
        width = dataset.width
        height = dataset.height

    rows, cols = np.indices((height, width))
    lon, lat = rasterio.transform.xy(transform, rows, cols)
    lat = np.array(lat).flatten()
    lon = np.array(lon).flatten()
    data = data.flatten()

    return lat, lon, data

def tiff_to_csv(file_path, output_csv):
    lat, lon, data = load_geotiff(file_path)
    df = pd.DataFrame({'Latitude': lat, 'Longitude': lon, 'Value': data})
    df.to_csv(output_csv, index=False)
    return output_csv