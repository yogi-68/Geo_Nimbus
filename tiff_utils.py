# tiff_utils.py
from imports import *


def save_cropped_tiff(file_path, north, south, east, west, colorized=True):
    try:
        # Open the original TIFF file
        with rasterio.open(file_path) as dataset:
            # Calculate the window to read based on the bounding box
            window = from_bounds(west, south, east, north, dataset.transform)
            data = dataset.read(1, window=window)

            if data.size == 0:
                return None

            # Copy metadata and update with new dimensions and transform
            metadata = dataset.meta.copy()
            metadata.update({
                'height': window.height,
                'width': window.width,
                'transform': dataset.window_transform(window)
            })

            # Create a temporary file to save the cropped TIFF
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.tif')

            if colorized:
                # Normalize and colorize the data
                norm = Normalize(vmin=np.nanmin(data), vmax=np.nanmax(data))
                cmap = plt.get_cmap('terrain')
                colored_data = cmap(norm(data))[:, :, :3] * 255

                # Update metadata for 3-band (RGB) data
                metadata.update({'count': 3, 'dtype': 'uint8'})

                # Write the colorized data to the temporary file
                with rasterio.open(temp_file.name, 'w', **metadata) as dst:
                    for i in range(3):
                        dst.write((colored_data[:, :, i]).astype(np.uint8), i + 1)
            else:
                # Write the grayscale data to the temporary file
                with rasterio.open(temp_file.name, 'w', **metadata) as dst:
                    dst.write(data, 1)

            return temp_file.name

    except Exception as e:
        print(f"An error occurred while saving the cropped TIFF file: {e}")
        return None