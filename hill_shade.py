
from imports import *


# Function to get band data from the TIFF
def get_band_data(dataset, band_number):
    band = dataset.GetRasterBand(band_number)
    return band.ReadAsArray()

# Function to apply hillshade
def hillshade(array, azimuth=315, angle_altitude=45):
    x, y = np.gradient(array)
    slope = np.pi/2. - np.arctan(np.sqrt(x*x + y*y))
    aspect = np.arctan2(-x, y)
    azimuthrad = azimuth * np.pi / 180.
    altituderad = angle_altitude * np.pi / 180.
    shaded = np.sin(altituderad) * np.sin(slope) + np.cos(altituderad) * np.cos(slope) * np.cos(azimuthrad - aspect)
    shaded = (shaded - shaded.min()) / (shaded.max() - shaded.min())
    return shaded

# Function to apply bathymetric colormap
def apply_bathymetric_colormap(data):
    # Normalize the data to have values between 0 and 1
    normed_data = (data - data.min()) / (data.max() - data.min())
    
    # Define bathymetry colormap using a diverging color scheme
    cmap = plt.get_cmap('terrain')  # 'terrain' is suitable for bathymetric and elevation data

    return cmap(normed_data)

# Function to apply other color maps
def apply_colormap(data, colormap):
    if colormap == 'gray':
        cmap = plt.get_cmap('gray')
    elif colormap == 'viridis':
        cmap = plt.get_cmap('viridis')
    elif colormap == 'inferno':
        cmap = plt.get_cmap('inferno')
    elif colormap == 'plasma':
        cmap = plt.get_cmap('plasma')
    elif colormap == 'hsv':
        cmap = plt.get_cmap('hsv')
    elif colormap == 'bathymetry':
        return apply_bathymetric_colormap(data)  # Custom bathymetry colormap
    else:
        cmap = plt.get_cmap('gray')

    normed_data = (data - data.min()) / (data.max() - data.min())
    return cmap(normed_data)