let map;
let markers = [];

document.addEventListener('DOMContentLoaded', function() {
    // Initialize map
    map = L.map('map').setView([20, 0], 2);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);

    // Load initial data
    fetch('/static/data/marker_data.json')
        .then(response => response.json())
        .then(data => {
            updateMarkers(data);
            initializeFilters(data);
            initializeControls(); // Integrate original initializeControls
            // Use current location
            document.getElementById('use-location').addEventListener('click', function() {
                if (navigator.geolocation) {
                    navigator.geolocation.getCurrentPosition(position => {
                        map.setView([position.coords.latitude, position.coords.longitude], 12);
                    });
                }
            });

        })
        .catch(error => console.error('Error loading marker data:', error));
});

function updateMarkers(data) {
    // Clear existing markers
    markers.forEach(marker => map.removeLayer(marker));
    markers = [];

    // Add new markers
    data.forEach(location => {
        const marker = L.circleMarker([location.lat, location.lng], {
            radius: 8,
            fillColor: getColor(location['AQI Value']),
            color: '#fff',
            weight: 1,
            opacity: 1,
            fillOpacity: 0.8
        });

        marker.bindPopup(`
            <b>${location.City}, ${location.Country}</b><br>
            AQI: ${location['AQI Value']}<br>
            Category: ${location['AQI Category']}
        `);

        marker.addTo(map);
        markers.push(marker);
    });
}

function getColor(aqi) {
    if (aqi <= 50) return '#00e400';      // Good
    if (aqi <= 100) return '#ffff00';     // Moderate
    if (aqi <= 150) return '#ff7e00';     // Unhealthy for Sensitive Groups
    if (aqi <= 200) return '#ff0000';     // Unhealthy
    if (aqi <= 300) return '#8f3f97';     // Very Unhealthy
    return '#7e0023';                     // Hazardous
}

function initializeFilters(data) {
    const continentSelect = document.getElementById('continent-select');
    const countrySelect = document.getElementById('country-select');
    const citySelect = document.getElementById('city-select'); // Added citySelect
    const resetBtn = document.getElementById('reset-btn'); // Added reset button

    function filterData() {
        const selectedContinent = continentSelect.value;
        const selectedCountry = countrySelect.value;
        const selectedCity = citySelect.value; // Added selectedCity

        const filteredData = data.filter(location => {
            const matchContinent = selectedContinent === 'All' || location.continent === selectedContinent;
            const matchCountry = selectedCountry === 'All' || location.Country === selectedCountry;
            const matchCity = selectedCity === 'All' || location.City === selectedCity; // Added city filter
            return matchContinent && matchCountry && matchCity;
        });

        updateMarkers(filteredData);
        updateWeatherInfo(); //Added to update weather info after filtering
    }

    continentSelect.addEventListener('change', filterData);
    countrySelect.addEventListener('change', filterData);
    citySelect.addEventListener('change', filterData); // Added event listener for citySelect
    resetBtn.addEventListener('click', () => { //Added reset button functionality
        continentSelect.value = 'All';
        countrySelect.value = 'All';
        citySelect.value = 'All'; // Reset city select
        updateMarkers(data);
        updateWeatherInfo(); //Added to update weather info after reset
    });
}

function initializeControls() {
    const continentSelect = document.getElementById('continent-select');
    const countrySelect = document.getElementById('country-select');
    const citySelect = document.getElementById('city-select');
    const resetBtn = document.getElementById('reset-btn');
    const realtimeToggle = document.getElementById('realtime-toggle');
    const refreshBtn = document.getElementById('map-refresh-btn');
    const locateBtn = document.getElementById('map-locate-btn');
    const fullscreenBtn = document.getElementById('map-fullscreen-btn');
    const focusIndiaBtn = document.getElementById('focus-india-btn');
    const viewGlobalBtn = document.getElementById('view-global-btn');


    function filterData() {
        const continent = continentSelect.value;
        const country = countrySelect.value;
        const city = citySelect.value;

        const filtered = markerData.filter(item => {
            return (continent === 'All' || item.Continent === continent) &&
                   (country === 'All' || item.Country === country) &&
                   (city === 'All' || item.City === city);
        });

        updateMarkers(filtered);
        updateWeatherInfo(); //Added to update weather info after filtering
    }

    continentSelect.addEventListener('change', filterData);
    countrySelect.addEventListener('change', filterData);
    citySelect.addEventListener('change', filterData);
    resetBtn.addEventListener('click', () => {
        continentSelect.value = 'All';
        countrySelect.value = 'All';
        citySelect.value = 'All';
        updateMarkers(markerData);
        updateWeatherInfo(); //Added to update weather info after reset
    });

    if (realtimeToggle) {
        realtimeToggle.addEventListener('change', function() {
            //useRealtimeData = this.checked; //This line is not needed anymore
            //loadMapData(); //This line is not needed anymore.  Data is already loaded and filtering handles this.
        });
    }

    if (refreshBtn) {
        refreshBtn.addEventListener('click', refreshMapData);
    }

    if (locateBtn) {
        locateBtn.addEventListener('click', function() {
            locateUser();
        });
    }

    if (fullscreenBtn) {
        fullscreenBtn.addEventListener('click', function() {
            toggleFullscreen();
        });
    }
    if (focusIndiaBtn) {
        focusIndiaBtn.addEventListener('click', function() {
            map.setView([20.5937, 78.9629], 4);
            document.getElementById('country-select').value = 'India';
            currentCountry = 'India';
            filterMarkersForIndia();
            // Update weather info after region change
            updateWeatherInfo();
        });
    }

    if (viewGlobalBtn) {
        viewGlobalBtn.addEventListener('click', function() {
            map.setView([20.0, 0.0], 2);
            document.getElementById('country-select').value = 'All';
            currentCountry = 'All';
            filterData(); // Use filterData to update markers based on selections
            updateWeatherInfo();
        });
    }
    // Initial weather info update
    updateWeatherInfo();
    addLegend(); // Add legend after controls are initialized

}


function loadMarkerData() {
    //This function is no longer needed since data is loaded directly in the DOMContentLoaded event listener.
}

function refreshMapData() {
    // Show loading indicator
    document.getElementById('map-loading').style.display = 'block';

    if (useRealtimeData && currentCountry === 'India') {
        // Fetch real-time data from India API
        fetch('/api/india-aqi-data?refresh=true')
            .then(response => response.json())
            .then(data => {
                // Update the markers
                updateMarkers(data);
                // Hide loading indicator
                // Update weather info with the new marker data
                updateWeatherInfo();
                document.getElementById('map-loading').style.display = 'none';
                // Update last updated timestamp
                updateLastUpdated(new Date().toISOString());
            })
            .catch(error => {
                console.error('Error refreshing map data:', error);
                document.getElementById('map-loading').style.display = 'none';
                alert('Error refreshing data. Please try again.');
            });
    } else {
        // Use the regular filter API
        const continentSelect = document.getElementById('continent-select');
        const countrySelect = document.getElementById('country-select');
        const citySelect = document.getElementById('city-select');

        let apiUrl = `/api/filter-markers?continent=${continentSelect.value}&country=${countrySelect.value}&city=${citySelect.value}`;


        fetch(apiUrl)
            .then(response => response.json())
            .then(data => {
                // Update the markers
                updateMarkers(data);
                // Hide loading indicator
                // Update weather info with the new marker data
                updateWeatherInfo();
                document.getElementById('map-loading').style.display = 'none';
                // Update last updated timestamp
                updateLastUpdated(new Date().toISOString());
            })
            .catch(error => {
                console.error('Error refreshing map data:', error);
                document.getElementById('map-loading').style.display = 'none';
                alert('Error refreshing data. Please try again.');
            });
    }
}

function locateUser() {
    if (navigator.geolocation) {
        // Show loading indicator
        document.getElementById('map-loading').style.display = 'block';

        navigator.geolocation.getCurrentPosition(
            // Success callback
            function(position) {
                const lat = position.coords.latitude;
                const lng = position.coords.longitude;

                // Zoom to user's location
                map.setView([lat, lng], 10);

                // Create a temporary marker
                const userMarker = L.marker([lat, lng], {
                    icon: L.divIcon({
                        html: '<i class="fas fa-map-marker-alt" style="color: #0071bc; font-size: 24px;"></i>',
                        className: '',
                        iconSize: [24, 24]
                    })
                }).addTo(map);

                // Add a popup
                userMarker.bindPopup('Your location').openPopup();

                // Remove the marker after 5 seconds
                setTimeout(() => {
                    map.removeLayer(userMarker);
                }, 5000);

                // Hide loading indicator
                document.getElementById('map-loading').style.display = 'none';
            },
            // Error callback
            function(error) {
                console.error('Error getting user location:', error);
                alert('Unable to get your location. Please make sure location services are enabled in your browser.');
                // Hide loading indicator
                document.getElementById('map-loading').style.display = 'none';
            }
        );
    } else {
        alert('Geolocation is not supported by your browser.');
    }
}

function toggleFullscreen() {
    const mapContainer = document.getElementById('map');
    const fullscreenBtn = document.getElementById('map-fullscreen-btn');

    if (!document.fullscreenElement) {
        // Enter fullscreen
        if (mapContainer.requestFullscreen) {
            mapContainer.requestFullscreen();
        } else if (mapContainer.mozRequestFullScreen) {
            mapContainer.mozRequestFullScreen();
        } else if (mapContainer.webkitRequestFullscreen) {
            mapContainer.webkitRequestFullscreen();
        } else if (mapContainer.msRequestFullscreen) {
            mapContainer.msRequestFullscreen();
        }

        // Change icon
        const icon = fullscreenBtn.querySelector('i');
        if (icon) {
            icon.className = 'fas fa-compress';
        }
    } else {
        // Exit fullscreen
        if (document.exitFullscreen) {
            document.exitFullscreen();
        } else if (document.mozCancelFullScreen) {
            document.mozCancelFullScreen();
        } else if (document.webkitExitFullscreen) {
            document.webkitExitFullscreen();
        } else if (document.msExitFullscreen) {
            document.msExitFullscreen();
        }

        // Change icon back
        const icon = fullscreenBtn.querySelector('i');
        if (icon) {
            icon.className = 'fas fa-expand';
        }
    }

    // Resize the map after a short delay to ensure it renders correctly
    setTimeout(() => {
        map.invalidateSize();
    }, 100);
}

function updateLastUpdated(timestamp) {
    const date = new Date(timestamp);
    const formattedDate = date.toLocaleString();

    // Update the timestamp in the UI if there's an element for it
    const timestampElement = document.getElementById('last-updated-time');
    if (timestampElement) {
        timestampElement.textContent = formattedDate;
    }
}

function updateWeatherInfo() {
    // Update main AQI display
    const currentAQI = document.getElementById('current-aqi');
    const aqiCategory = document.getElementById('aqi-category');
    const pm10Value = document.getElementById('pm10-value');
    const pm25Value = document.getElementById('pm25-value');
    const temperatureValue = document.getElementById('temperature-value');
    const humidityValue = document.getElementById('humidity-value');
    const windSpeedEl = document.getElementById('wind-speed');
    const windDirectionEl = document.getElementById('wind-direction');
    const uvIndexEl = document.getElementById('uv-index');
    const aqiMascot = document.getElementById('aqi-mascot');

    if (!windSpeedEl || !temperatureValue) {
        return; // Elements not found
    }

    // Find an appropriate marker with weather data
    if (markers && markers.length > 0) {
        // Set default values
        let windSpeed = "3.5 km/h";
        let temperature = "28°C";
        let windDirection = 120;
        let found = false;

        // Look for markers with weather data
        for (const marker of markers) {
            if (marker && marker.options && marker.options.data) {
                const data = marker.options.data;

                // Check if this marker has wind speed data
                if (data.wind_speed) {
                    windSpeed = `${data.wind_speed} km/h`;
                    found = true;
                }

                // Check if this marker has temperature data
                if (data.temperature) {
                    temperature = `${data.temperature}°C`;
                    found = true;
                }

                // Check if this marker has wind direction data
                if (data.wind_direction) {
                    windDirection = data.wind_direction;
                    found = true;
                }

                // If we found data, we can stop looking
                if (found) {
                    break;
                }
            }
        }

        // Update the wind speed display
        windSpeedEl.textContent = windSpeed;

        // Update the temperature display
        temperatureValue.textContent = temperature;

        // Rotate the wind icon based on wind direction
        const windIcon = document.querySelector('.iqair-wind i');
        if (windIcon) {
            windIcon.style.transform = `rotate(${windDirection}deg)`;
        }
    }
}

//Search functionality remains unchanged.  This section is long and doesn't directly conflict with the edited code.  Leaving it as is.

document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('location-search');
    const searchResults = document.getElementById('search-results');
    let markers = [];

    // Load marker data
    fetch('/static/data/marker_data.json')
        .then(response => response.json())
        .then(data => {
            markers = data;
        });

    searchInput.addEventListener('input', function(e) {
        const searchTerm = e.target.value.toLowerCase();
        if (searchTerm.length < 2) {
            searchResults.style.display = 'none';
            return;
        }

        const filteredMarkers = markers.filter(marker =>
            marker.City.toLowerCase().includes(searchTerm) ||
            marker.Country.toLowerCase().includes(searchTerm)
        ).slice(0, 5);

        if (filteredMarkers.length > 0) {
            searchResults.innerHTML = filteredMarkers.map(marker => `
                <div class="search-result-item" data-lat="${marker.Latitude}" data-lng="${marker.Longitude}">
                    <i class="fas fa-map-marker-alt"></i>
                    <span>${marker.City}, ${marker.Country}</span>
                    <span class="search-result-aqi" style="background-color: ${getColor(marker.AQI)}">${Math.round(marker.AQI)}</span>
                </div>
            `).join('');
            searchResults.style.display = 'block';

            // Add click handlers to results
            document.querySelectorAll('.search-result-item').forEach(item => {
                item.addEventListener('click', function() {
                    const lat = parseFloat(this.dataset.lat);
                    const lng = parseFloat(this.dataset.lng);
                    map.setView([lat, lng], 12);
                    searchResults.style.display = 'none';
                    searchInput.value = this.querySelector('span').textContent;
                });
            });
        } else {
            searchResults.style.display = 'none';
        }
    });

    // Close search results when clicking outside
    document.addEventListener('click', function(e) {
        if (!searchResults.contains(e.target) && e.target !== searchInput) {
            searchResults.style.display = 'none';
        }
    });
});

function handleResize() {
    if (map) {
        map.invalidateSize();
    }
}

// Add event listener for window resize
window.addEventListener('resize', handleResize);

// Add event listener for tab changes that might affect map size
document.addEventListener('shown.bs.tab', function(e) {
    if (e.target.getAttribute('href') === '#map-tab') {
        handleResize();
    }
});

function addLegend() {
    const legend = L.control({ position: 'bottomright' });

    legend.onAdd = function(map) {
        const div = L.DomUtil.create('div', 'aqi-legend');
        div.innerHTML = `
            <div style="background: white; padding: 10px; border-radius: 5px; box-shadow: 0 1px 5px rgba(0,0,0,0.4)">
                <h6 style="margin-top: 0; margin-bottom: 5px;">Air Quality Index</h6>
                <div><i style="background: #00e400; width: 18px; height: 18px; display: inline-block; margin-right: 5px;"></i> Good (0-50)</div>
                <div><i style="background: #ffff00; width: 18px; height: 18px; display: inline-block; margin-right: 5px;"></i> Moderate (51-100)</div>
                <div><i style="background: #ff7e00; width: 18px; height: 18px; display: inline-block; margin-right: 5px;"></i> Unhealthy for Sensitive Groups (101-150)</div>
                <div><i style="background: #ff0000; width: 18px; height: 18px; display: inline-block; margin-right: 5px;"></i> Unhealthy (151-200)</div>
                <div><i style="background: #8f3f97; width: 18px; height: 18px; display: inline-block; margin-right: 5px;"></i> Very Unhealthy (201-300)</div>
                <div><i style="background: #7e0023; width: 18px; height: 18px; display: inline-block; margin-right: 5px;"></i> Hazardous (301+)</div>
            </div>
        `;
        return div;
    };

    legend.addTo(map);
}

function filterMarkersForIndia() {
    // Show loading indicator
    document.getElementById('map-loading').style.display = 'block';

    // Use real-time data if enabled
    fetch('/api/india-aqi-data')
        .then(response => response.json())
        .then(data => {
            // Update markers on the map
            updateMarkers(data);
            // Hide loading indicator
            document.getElementById('map-loading').style.display = 'none';
            updateWeatherInfo(); //Added to update weather info after India filter
        })
        .catch(error => {
            console.error('Error fetching India data:', error);
            // Fallback to regular filter
            //filterMarkers('Asia', 'India', 'All'); //This line is not needed anymore because filterData handles this
        });
}

function getComparisonText(rank, total) {
    return ""; // Placeholder - replace with actual implementation if needed
}