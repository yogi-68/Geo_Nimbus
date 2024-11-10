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

def save_cropped_tiff(file_path, north, south, east, west, colorized=True):
    try:
        with rasterio.open(file_path) as dataset:
            window = rasterio.windows.from_bounds(west, south, east, north, dataset.transform)
            data = dataset.read(1, window=window)

            if data.size == 0:
                return None

            metadata = dataset.meta.copy()
            metadata.update({
                'height': window.height,
                'width': window.width,
                'transform': dataset.window_transform(window)
            })

            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.tif')

            if colorized:
                norm = Normalize(vmin=np.nanmin(data), vmax=np.nanmax(data))
                cmap = plt.get_cmap('terrain')
                colored_data = cmap(norm(data))[:, :, :3] * 255

                metadata.update({'count': 3, 'dtype': 'uint8'})

                with rasterio.open(temp_file.name, 'w', **metadata) as dst:
                    for i in range(3):
                        dst.write((colored_data[:, :, i]).astype(np.uint8), i + 1)
            else:
                with rasterio.open(temp_file.name, 'w', **metadata) as dst:
                    dst.write(data, 1)

            return temp_file.name

    except Exception as e:
        print(f"An error occurred while saving the cropped TIFF file: {e}")
        return None

def extract_bathymetric_data(global_file, region_file):
    with rasterio.open(global_file) as global_src:
        global_bounds = global_src.bounds

        with rasterio.open(region_file) as region_src:
            region_bounds = region_src.bounds
            window = global_src.window(region_bounds.left, region_bounds.bottom,
                                       region_bounds.right, region_bounds.top)
            global_data = global_src.read(1, window=window)
            global_transform = global_src.window_transform(window)

            return global_data, global_transform, region_bounds

def save_extracted_image(global_data, global_transform, crs, image_filename='extracted_image.png'):
    image = np.clip(global_data, 0, 255).astype(np.uint8)
    with rasterio.open(image_filename, 'w', driver='PNG', height=image.shape[0],
                       width=image.shape[1], count=1, dtype='uint8', crs=crs,
                       transform=global_transform) as dst:
        dst.write(image, 1)
    return image_filename

def create_map_with_overlay(image_filename, region_bounds, map_html='map.html'):
    center = [(region_bounds.top + region_bounds.bottom) / 2, (region_bounds.left + region_bounds.right) / 2]
    m = folium.Map(location=center, zoom_start=8)

    folium.raster_layers.ImageOverlay(
        image=image_filename,
        bounds=[[region_bounds.bottom, region_bounds.left], [region_bounds.top, region_bounds.right]],
        opacity=0.6
    ).add_to(m)

    m.save(map_html)
    return map_html