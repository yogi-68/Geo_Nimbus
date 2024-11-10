# imports.py
from flask import Flask, render_template, request, send_file, redirect, url_for, send_from_directory, jsonify, Blueprint
from werkzeug.utils import secure_filename
from flask_cors import CORS
import math
import rasterio
import numpy as np
from PIL import Image
import io
import os
import subprocess
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
import folium
from folium import raster_layers
import pandas as pd
from stl import mesh
import tempfile
import base64
from rasterio.windows import from_bounds
import os
from osgeo import gdal
import numpy as np
from skimage import exposure
import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend
import matplotlib.pyplot as plt
import base64
from io import BytesIO