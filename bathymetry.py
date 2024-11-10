# bathymetry.py
from imports import *

def get_bathymetry_image(file_path, north, south, east, west, colorized=True):
    try:
        with rasterio.open(file_path) as dataset:
            window = rasterio.windows.from_bounds(west, south, east, north, dataset.transform)
            data = dataset.read(1, window=window)

            if data.size == 0:
                return None

            data_min, data_max = np.nanmin(data), np.nanmax(data)
            norm = Normalize(vmin=data_min, vmax=data_max)

            if colorized:
                cmap = plt.get_cmap('terrain')
                colored_data = cmap(norm(data))
                img = Image.fromarray((colored_data[:, :, :3] * 255).astype(np.uint8))
            else:
                grayscale_data = norm(data) * 255
                img = Image.fromarray(grayscale_data.astype(np.uint8), mode='L')

            fig, ax = plt.subplots(figsize=(2, 12))
            plt.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=('terrain' if colorized else 'gray')), ax=ax, orientation='vertical')
            ax.set_title('Elevation (m)')
            scale_bytes = io.BytesIO()
            plt.savefig(scale_bytes, format='PNG', bbox_inches='tight', pad_inches=0)
            plt.close(fig)
            scale_bytes.seek(0)
            scale_data = base64.b64encode(scale_bytes.getvalue()).decode('utf-8')

            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG')
            img_bytes.seek(0)

            img_combined = Image.new('RGB', (img.width + 150, img.height))
            img_combined.paste(img, (150, 0))
            scale_bar = Image.open(io.BytesIO(base64.b64decode(scale_data)))
            img_combined.paste(scale_bar, (0, 0))

            img_combined_bytes = io.BytesIO()
            img_combined.save(img_combined_bytes, format='PNG')
            img_combined_bytes.seek(0)

            return base64.b64encode(img_combined_bytes.getvalue()).decode('utf-8')

    except Exception as e:
        print(f"An error occurred while processing the TIFF file: {e}")
        return None