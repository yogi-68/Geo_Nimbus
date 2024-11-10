// static/script.js
document.addEventListener('DOMContentLoaded', function() {
    var map = L.map('map').setView([20, 77], 5);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

    var drawnItems = new L.FeatureGroup().addTo(map);
    var drawControl = new L.Control.Draw({
        edit: {
            featureGroup: drawnItems
        }
    });
    map.addControl(drawControl);

    map.on(L.Draw.Event.CREATED, function(event) {
        var layer = event.layer;
        drawnItems.addLayer(layer);

        var bounds = layer.getBounds();
        var north = bounds.getNorthEast().lat;
        var south = bounds.getSouthWest().lat;
        var east = bounds.getNorthEast().lng;
        var west = bounds.getSouthWest().lng;

        document.getElementById('north').value = north.toFixed(6);
        document.getElementById('south').value = south.toFixed(6);
        document.getElementById('east').value = east.toFixed(6);
        document.getElementById('west').value = west.toFixed(6);
    });

    window.handleFeatureSelect = function() {
        var feature = document.getElementById('feature-select').value;
        if (feature === 'locate_tiff') {
            window.location.href = '/upload_region';
        } else if (feature === 'path_profile') {
            window.location.href = '/path_profile';
        } else if (feature === 'convert_stl') {
            window.location.href = '/convert_stl';
        } else if (feature === 'convert_csv') {
            window.location.href = '/convert_csv';
        }
        else if (feature === 'hill_shade') {
            window.location.href = '/hill_shade';
        }
    }

    window.openVisualization = function() {
        var imageData = document.getElementById('image-data').value;
        var scaleData = document.getElementById('scale-data').value;
        var newWindow = window.open('', '_blank', 'width=800,height=600');
        newWindow.document.write('<html><head><title>Visualization</title></head><body style="margin: 0; display: flex; align-items: center; justify-content: center; background-color: #f0f4f8;">');
        newWindow.document.write('<div style="position: relative; box-shadow: 0 4px 20px rgba(0,0,0,0.1); border-radius: 8px; overflow: hidden;">');
        newWindow.document.write('<img src="data:image/png;base64,' + imageData + '" style="max-width: 100%; max-height: 100%; display: block;" />');
        newWindow.document.write('<div style="position: absolute; bottom: 20px; left: 20px; background-color: rgba(255, 255, 255, 0.9); padding: 10px; border-radius: 5px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">');
        newWindow.document.write('<img src="data:image/png;base64,' + scaleData + '" />');
        newWindow.document.write('</div></div>');
        newWindow.document.write('</body></html>');
        newWindow.document.close();
    }

    window.downloadCOG = function() {
        var formData = new FormData(document.getElementById('cog-download-form'));
        formData.append('view_mode', document.querySelector('select[name="view_mode"]').value);

        fetch('/download_cog', {
            method: 'POST',
            body: formData
        })
        .then(response => response.blob())
        .then(blob => {
            var url = window.URL.createObjectURL(blob);
            var a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = 'cropped_bathymetry_cog.tif';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
        })
        .catch(error => console.error('Error:', error));
    }
});