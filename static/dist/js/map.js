document.addEventListener('DOMContentLoaded', function () {
    // Initialize map
    var map = L.map('map').setView([51.505, -0.09], 13);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);

    var marker = L.marker([51.505, -0.09]).addTo(map);

    // Custom Leaflet control for the search bar
    var searchControl = L.Control.extend({
        onAdd: function(map) {
            var div = L.DomUtil.create('div', 'leaflet-bar');  // Create a container
            div.innerHTML = '<input type="text" id="location-input" placeholder="Enter a location" class="border border-gray-300 p-2 shadow-md w-64"><button id="search-btn" class="bg-blue-500 text-white p-2 hover:bg-blue-600">Search</button>';
            return div;
        }
    });

    // Add search control to the map at the top-right corner
    map.addControl(new searchControl({ position: 'topright' }));

    // Function to search for a location using Nominatim API
    function searchLocation(location) {
        var url = `https://nominatim.openstreetmap.org/search?format=json&q=${location}`;
        fetch(url)
            .then(response => response.json())
            .then(data => {
                if (data.length > 0) {
                    var lat = data[0].lat;
                    var lon = data[0].lon;
                    map.setView([lat, lon], 13);  // Set map to the searched location
                    marker.setLatLng([lat, lon]).bindPopup(location).openPopup();  // Move the marker to the location
                } else {
                    alert("Location not found");
                }
            })
            .catch(error => {
                console.error("Error fetching location:", error);
                alert("An error occurred while searching for the location.");
            });
    }

    // Handle click event for the search button
    document.addEventListener('click', function (event) {
        if (event.target && event.target.id === 'search-btn') {
            var location = document.getElementById('location-input').value;
            if (location) {
                searchLocation(location);
            } else {
                alert("Please enter a location.");
            }
        }
    });
});
