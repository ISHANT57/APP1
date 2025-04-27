/**
 * Global Air Quality Monitoring Dashboard - Main JS Module
 * This module handles general page initialization and functionality
 */

// Safely add event listeners
function addSafeEventListener(element, eventType, handler) {
    if (element) {
        element.addEventListener(eventType, handler);
        return true;
    }
    return false;
}

// Safe document ready function
function onDocumentReady(fn) {
    if (document.readyState !== 'loading') {
        fn();
    } else {
        document.addEventListener('DOMContentLoaded', fn);
    }
}

// Main initialization
onDocumentReady(function() {
    console.log('Air Quality Dashboard initialized');
    
    // Initialize bootstrap tooltips
    if (window.bootstrap && window.bootstrap.Tooltip) {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function(tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
    
    // Initialize page-specific functionality
    const currentPage = document.body.dataset.page;
    
    if (currentPage === 'index') {
        initHomePage();
    } else if (currentPage === 'map') {
        initMapPage();
    } else if (currentPage === 'historical') {
        initHistoricalPage();
    } else if (currentPage === 'most-polluted') {
        initMostPollutedPage();
    } else if (currentPage === 'heatmap') {
        // Heatmap is initialized in its own page
        console.log('Heatmap page loaded');
    }
    
    // Handle mobile navigation menu
    const navbarToggler = document.querySelector('.navbar-toggler');
    const navbarCollapse = document.querySelector('.navbar-collapse');
    
    if (navbarToggler && navbarCollapse) {
        addSafeEventListener(navbarToggler, 'click', function() {
            navbarCollapse.classList.toggle('show');
        });
        
        // Close mobile menu when clicking a link
        const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
        navLinks.forEach(link => {
            addSafeEventListener(link, 'click', function() {
                navbarCollapse.classList.remove('show');
            });
        });
    }
    
    // Initialize dark mode
    initDarkMode();

    // Initialize Chart.js defaults and theme handling
    if (window.Chart) {
        // Update chart colors based on current theme
        function updateChartColors() {
            const isDarkMode = document.body.classList.contains('dark-mode');
            Chart.defaults.color = isDarkMode ? '#fff' : '#666';
            Chart.defaults.borderColor = isDarkMode ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)';
        }

        // Initial color update
        updateChartColors();

        // Listen for theme changes
        document.addEventListener('themeChanged', updateChartColors);
    }
});

/**
 * Initialize the home page
 */
function initHomePage() {
    console.log('Initializing home page');
    
    // Load featured countries chart if element exists
    const featuredCountriesChart = document.getElementById('featured-countries-chart');
    if (featuredCountriesChart) {
        // Get top 10 most polluted countries
        const countriesTable = document.getElementById('top-countries-table');
        if (countriesTable) {
            const rows = countriesTable.querySelectorAll('tbody tr');
            const countries = [];
            const aqiValues = [];
            
            rows.forEach(row => {
                const cols = row.querySelectorAll('td');
                if (cols.length >= 3) {
                    countries.push(cols[1].textContent);
                    aqiValues.push(parseFloat(cols[2].textContent));
                }
            });
            
            createPollutionBarChart(
                'featured-countries-chart',
                'Most Polluted Countries (2024)',
                countries,
                aqiValues
            );
        }
    }
    
    // Initialize map if the container exists
    const mapContainer = document.getElementById('map-container');
    if (mapContainer) {
        // Fetch marker data
        fetch('/static/data/marker_data.json')
            .then(response => response.json())
            .then(data => {
                // Initialize map with data
                if (typeof initMap === 'function') {
                    initMap(data);
                }
            })
            .catch(error => {
                console.error('Error loading marker data:', error);
                mapContainer.innerHTML = '<div class="alert alert-danger">Error loading map data. Please try again.</div>';
            });
    }
}

/**
 * Initialize the map page with IQAir-style interface
 */
function initMapPage() {
    console.log('Initializing interactive air quality map page');
    
    // Show loading indicator
    const mapLoadingElement = document.getElementById('map-loading');
    if (mapLoadingElement) {
        mapLoadingElement.style.display = 'block';
    }
    
    // Check if we should start with real-time India data
    const realtimeToggle = document.getElementById('realtime-toggle');
    const useRealtimeData = realtimeToggle ? realtimeToggle.checked : true;
    
    if (useRealtimeData) {
        // Try to get real-time India data first
        fetch('/api/india-aqi-data')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                // Initialize map with real-time data
                if (typeof initMap === 'function') {
                    initMap(data);
                }
                
                // Initialize map filters
                if (typeof initMapFilters === 'function') {
                    initMapFilters();
                }
                
                // Update timestamp
                updateLastUpdated(new Date().toISOString());
                
                // Hide loading indicator
                if (mapLoadingElement) {
                    mapLoadingElement.style.display = 'none';
                }
            })
            .catch(error => {
                console.error('Error loading real-time data, falling back to static data:', error);
                
                // Fallback to static marker data
                fetchStaticMarkerData();
            });
    } else {
        // Use static data
        fetchStaticMarkerData();
    }
    
    // Function to fetch static marker data (used as fallback)
    function fetchStaticMarkerData() {
        fetch('/static/data/marker_data.json')
            .then(response => response.json())
            .then(data => {
                // Initialize map with static data
                if (typeof initMap === 'function') {
                    initMap(data);
                }
                
                // Initialize map filters
                if (typeof initMapFilters === 'function') {
                    initMapFilters();
                }
                
                // Hide loading indicator
                if (mapLoadingElement) {
                    mapLoadingElement.style.display = 'none';
                }
            })
            .catch(error => {
                console.error('Error loading marker data:', error);
                const mapContainer = document.getElementById('map-container');
                if (mapContainer) {
                    mapContainer.innerHTML = '<div class="alert alert-danger mt-3">Error loading map data. Please try again.</div>';
                }
                
                // Hide loading indicator
                if (mapLoadingElement) {
                    mapLoadingElement.style.display = 'none';
                }
            });
    }
    
    // Add timestamp to the page showing when data was last updated
    const now = new Date();
    const timestampElement = document.getElementById('last-updated-time');
    if (timestampElement) {
        timestampElement.textContent = now.toLocaleString();
    }
}

/**
 * Initialize the historical data page
 */
function initHistoricalPage() {
    console.log('Initializing historical page');
    
    // Get DOM elements
    const countrySelect = document.getElementById('country-select');
    const citySelect = document.getElementById('city-select');
    const loadCountryBtn = document.getElementById('load-country-btn');
    const loadCityBtn = document.getElementById('load-city-btn');
    const countrySelect1 = document.getElementById('country-select-1');
    const countrySelect2 = document.getElementById('country-select-2');
    const citySelect1 = document.getElementById('city-select-1');
    const citySelect2 = document.getElementById('city-select-2');
    const compareCountriesBtn = document.getElementById('compare-countries-button');
    const compareCitiesBtn = document.getElementById('compare-cities-button');
    
    // Load initial data if needed
    if (countrySelect && countrySelect.value && typeof loadCountryData === 'function') {
        loadCountryData(countrySelect.value);
    }
    
    // Handle single country data loading
    if (loadCountryBtn) {
        addSafeEventListener(loadCountryBtn, 'click', function() {
            if (countrySelect && countrySelect.value && typeof loadCountryData === 'function') {
                loadCountryData(countrySelect.value);
                const container = document.getElementById('country-data-container');
                if (container) container.style.display = 'block';
            } else {
                alert('Please select a country to load its data.');
            }
        });
    }
    
    // Handle country selection change
    if (countrySelect && typeof loadCountryData === 'function') {
        addSafeEventListener(countrySelect, 'change', function() {
            if (this.value) {
                loadCountryData(this.value);
                const container = document.getElementById('country-data-container');
                if (container) container.style.display = 'block';
            }
        });
    }
    
    // Handle city selection change
    if (citySelect && typeof loadCityData === 'function') {
        addSafeEventListener(citySelect, 'change', function() {
            if (this.value) {
                const [city, state] = this.value.split('|');
                loadCityData(city, state);
                const container = document.getElementById('city-data-section');
                if (container) container.style.display = 'block';
            } else {
                const container = document.getElementById('city-data-section');
                if (container) container.style.display = 'none';
            }
        });
    }
    
    // Handle single city data loading
    if (loadCityBtn) {
        addSafeEventListener(loadCityBtn, 'click', function() {
            if (citySelect && citySelect.value && typeof loadCityData === 'function') {
                const [city, state] = citySelect.value.split('|');
                loadCityData(city, state);
                const container = document.getElementById('city-data-section');
                if (container) container.style.display = 'block';
            } else {
                alert('Please select a city to load its data.');
            }
        });
    }
    
    // Handle country-to-country comparison
    if (compareCountriesBtn) {
        addSafeEventListener(compareCountriesBtn, 'click', function() {
            if (countrySelect1 && countrySelect2 && 
                countrySelect1.value && countrySelect2.value && 
                typeof createComparisonChart === 'function') {
                
                const country1 = countrySelect1.value;
                const country2 = countrySelect2.value;
                
                Promise.all([
                    fetch(`/api/country-data/${country1}`).then(response => response.json()),
                    fetch(`/api/country-data/${country2}`).then(response => response.json())
                ])
                .then(([country1Data, country2Data]) => {
                    // Create comparison chart
                    createComparisonChart(
                        'country-comparison-chart',
                        `${country1Data.country} vs ${country2Data.country} (2024)`,
                        country1Data.months,
                        country1Data.monthly_data,
                        country1Data.country,
                        country2Data.monthly_data,
                        country2Data.country
                    );
                    
                    // Show comparison section
                    const container = document.getElementById('country-comparison-section');
                    if (container) container.style.display = 'block';
                })
                .catch(error => {
                    console.error('Error loading country comparison data:', error);
                    alert('Error loading country comparison data. Please try again.');
                });
            } else {
                alert('Please select two countries to compare.');
            }
        });
    }
    
    // Handle city-to-city comparison
    if (compareCitiesBtn) {
        addSafeEventListener(compareCitiesBtn, 'click', function() {
            if (citySelect1 && citySelect2 && 
                citySelect1.value && citySelect2.value && 
                typeof createComparisonChart === 'function') {
                
                const [city1, state1] = citySelect1.value.split('|');
                const [city2, state2] = citySelect2.value.split('|');
                
                Promise.all([
                    fetch(`/api/city-data/${city1}/${state1}`).then(response => response.json()),
                    fetch(`/api/city-data/${city2}/${state2}`).then(response => response.json())
                ])
                .then(([city1Data, city2Data]) => {
                    // Create comparison chart
                    createComparisonChart(
                        'city-comparison-chart',
                        `${city1Data.city}, ${city1Data.state} vs ${city2Data.city}, ${city2Data.state} (2024)`,
                        city1Data.months,
                        city1Data.monthly_data,
                        `${city1Data.city}, ${city1Data.state}`,
                        city2Data.monthly_data,
                        `${city2Data.city}, ${city2Data.state}`
                    );
                    
                    // Show comparison section
                    const container = document.getElementById('city-comparison-section');
                    if (container) container.style.display = 'block';
                })
                .catch(error => {
                    console.error('Error loading city comparison data:', error);
                    alert('Error loading city comparison data. Please try again.');
                });
            } else {
                alert('Please select two cities to compare.');
            }
        });
    }
}

/**
 * Initialize the most polluted page
 */
function initMostPollutedPage() {
    console.log('Initializing most polluted page');
    
    // Load countries chart if element exists
    const countriesChart = document.getElementById('polluted-countries-chart');
    if (countriesChart && typeof createPollutionBarChart === 'function') {
        // Get top polluted countries
        const countriesTable = document.getElementById('polluted-countries-table');
        if (countriesTable) {
            const rows = countriesTable.querySelectorAll('tbody tr');
            const countries = [];
            const aqiValues = [];
            
            // Limit to top 20 for better visibility
            const maxRows = Math.min(rows.length, 20);
            
            for (let i = 0; i < maxRows; i++) {
                const cols = rows[i].querySelectorAll('td');
                if (cols.length >= 3) {
                    countries.push(cols[1].textContent);
                    aqiValues.push(parseFloat(cols[2].textContent));
                }
            }
            
            createPollutionBarChart(
                'polluted-countries-chart',
                'Top 20 Most Polluted Countries (2024)',
                countries,
                aqiValues
            );
        }
    }
    
    // Load cities data if select exists
    const citySelect = document.getElementById('city-state-select');
    if (citySelect && typeof loadCityData === 'function') {
        addSafeEventListener(citySelect, 'change', function() {
            const value = this.value;
            if (value) {
                const [city, state] = value.split('|');
                loadCityData(city, state);
                
                // Show city data section
                const container = document.getElementById('city-data-section');
                if (container) container.style.display = 'block';
            }
        });
    }
    
    // Calculate AQI category distribution if element exists
    const categoryDistChart = document.getElementById('category-distribution-chart');
    if (categoryDistChart && typeof createAQICategoryPieChart === 'function') {
        // Get AQI values from the table
        const countriesTable = document.getElementById('polluted-countries-table');
        if (countriesTable) {
            const rows = countriesTable.querySelectorAll('tbody tr');
            const categories = {
                'Good': 0,
                'Moderate': 0,
                'Unhealthy for Sensitive Groups': 0,
                'Unhealthy': 0,
                'Very Unhealthy': 0,
                'Hazardous': 0
            };
            
            rows.forEach(row => {
                const cols = row.querySelectorAll('td');
                if (cols.length >= 3) {
                    const aqi = parseFloat(cols[2].textContent);
                    if (aqi <= 50) {
                        categories['Good']++;
                    } else if (aqi <= 100) {
                        categories['Moderate']++;
                    } else if (aqi <= 150) {
                        categories['Unhealthy for Sensitive Groups']++;
                    } else if (aqi <= 200) {
                        categories['Unhealthy']++;
                    } else if (aqi <= 300) {
                        categories['Very Unhealthy']++;
                    } else {
                        categories['Hazardous']++;
                    }
                }
            });
            
            createAQICategoryPieChart(
                'category-distribution-chart',
                'AQI Category Distribution',
                Object.values(categories)
            );
        }
    }
}

/**
 * Generate background gradient based on AQI
 * @param {number} aqi - Air Quality Index value
 * @returns {string} - CSS gradient
 */
function getAQIGradient(aqi) {
    let color;
    
    if (aqi <= 50) {
        color = '#009966'; // Good
    } else if (aqi <= 100) {
        color = '#ffde33'; // Moderate
    } else if (aqi <= 150) {
        color = '#ff9933'; // Unhealthy for Sensitive Groups
    } else if (aqi <= 200) {
        color = '#cc0033'; // Unhealthy
    } else if (aqi <= 300) {
        color = '#660099'; // Very Unhealthy
    } else {
        color = '#7e0023'; // Hazardous
    }
    
    return `linear-gradient(135deg, ${color}33 0%, ${color}aa 100%)`;
}

/**
 * Format date to localized string
 * @param {Date} date - Date object
 * @returns {string} - Formatted date string
 */
function formatDate(date) {
    return date.toLocaleDateString(undefined, {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

/**
 * Update last updated timestamp
 * @param {string} timestamp - ISO date string
 */
function updateLastUpdated(timestamp) {
    const lastUpdatedEl = document.getElementById('last-updated');
    if (lastUpdatedEl && timestamp) {
        const date = new Date(timestamp);
        lastUpdatedEl.textContent = formatDate(date);
    }
}

/**
 * Initialize dark mode functionality
 */
function initDarkMode() {
    // Get DOM elements safely
    const darkModeToggle = document.querySelector('#dark-mode-toggle');
    const darkModeToggleFloat = document.querySelector('.dark-mode-toggle-float');
    const themeText = document.querySelector('#theme-text');
    
    // Safely get icon elements if they exist
    const moonIcon = darkModeToggle ? darkModeToggle.querySelector('i') : null;
    const floatIcon = darkModeToggleFloat ? darkModeToggleFloat.querySelector('i') : null;
    
    // Check for saved theme preference or respect OS preference
    const prefersDarkMode = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    const savedTheme = localStorage.getItem('theme');
    
    // Apply theme based on saved preference or OS preference
    if (savedTheme === 'dark' || (!savedTheme && prefersDarkMode)) {
        document.body.classList.add('dark-mode');
        if (themeText) themeText.textContent = 'Light Mode';
        if (moonIcon) {
            moonIcon.classList.remove('fa-moon');
            moonIcon.classList.add('fa-sun');
        }
        if (floatIcon) {
            floatIcon.classList.remove('fa-moon');
            floatIcon.classList.add('fa-sun');
        }
    }
    
    // Helper function to toggle dark mode
    function toggleDarkMode(e) {
        if (e) e.preventDefault();
        
        // Toggle dark mode class on body
        document.body.classList.toggle('dark-mode');
        
        // Update button text and icon
        const isDarkMode = document.body.classList.contains('dark-mode');
        
        // Save preference
        localStorage.setItem('theme', isDarkMode ? 'dark' : 'light');
        
        // Update text if element exists
        if (themeText) {
            themeText.textContent = isDarkMode ? 'Light Mode' : 'Dark Mode';
        }
        
        // Update navbar icon if element exists
        if (moonIcon) {
            if (isDarkMode) {
                moonIcon.classList.remove('fa-moon');
                moonIcon.classList.add('fa-sun');
            } else {
                moonIcon.classList.remove('fa-sun');
                moonIcon.classList.add('fa-moon');
            }
        }
        
        // Update floating icon if element exists
        if (floatIcon) {
            if (isDarkMode) {
                floatIcon.classList.remove('fa-moon');
                floatIcon.classList.add('fa-sun');
            } else {
                floatIcon.classList.remove('fa-sun');
                floatIcon.classList.add('fa-moon');
            }
        }
        
        // Dispatch theme changed event for charts
        document.dispatchEvent(new Event('themeChanged'));
        
        // Update maps and charts for the new theme if function exists
        if (typeof updateChartsForTheme === 'function') {
            updateChartsForTheme();
        }
    }
    
    // Add click event listeners safely
    addSafeEventListener(darkModeToggle, 'click', toggleDarkMode);
    addSafeEventListener(darkModeToggleFloat, 'click', toggleDarkMode);
}

/**
 * Update chart colors for current theme
 */
function updateChartsForTheme() {
    // Update any existing charts with the new theme colors
    if (window.Chart && Chart.instances) {
        Object.values(Chart.instances).forEach(chart => {
            chart.update();
        });
    }
}