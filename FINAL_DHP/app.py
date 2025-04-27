import os
import logging
from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
import pandas as pd
import json
from datetime import datetime
import data_processing
import api_utils


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
# create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev_key_for_testing")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)  # needed for url_for to generate with https

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# configure the database, relative to the app instance folder
# Handle SQLAlchemy URL conversion for Postgres (if needed)
database_url = os.environ.get("DATABASE_URL")
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url or "sqlite:///air_quality.db"
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.logger.debug(f"Using database URL: {app.config['SQLALCHEMY_DATABASE_URI']}")

# initialize the app with the extension
db.init_app(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def create_user(username, email, password):
    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash('Email already registered')
            return redirect(url_for('register'))

        user = create_user(username, email, password)
        login_user(user)
        return redirect(url_for('index'))

    return render_template('register.html', now=datetime.now())

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user is None or not user.check_password(password):
            flash('Invalid username or password')
            return redirect(url_for('login'))

        login_user(user)
        next_page = request.args.get('next')
        return redirect(next_page if next_page else url_for('index'))

    return render_template('login.html', now=datetime.now())

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# Load data
try:
    # Load marker data for the map
    with open('static/data/marker_data.json', 'r') as f:
        marker_data = json.load(f)

    # Load countries data
    with open('static/data/countries_data.json', 'r') as f:
        countries_data = json.load(f)

    # Load cities monthly data
    with open('static/data/cities_monthly_data.json', 'r') as f:
        cities_monthly_data = json.load(f)

    app.logger.info("Successfully loaded data files")
except Exception as e:
    app.logger.error(f"Error loading data files: {e}")
    marker_data = []
    countries_data = []
    cities_monthly_data = []

# Routes
@app.route('/')
def index():
    # Get unique continents, countries, and cities for filters
    continents = sorted(list(set([m.get('Continent', 'Unknown') for m in marker_data if 'Continent' in m])))
    countries = sorted(list(set([m.get('Country', 'Unknown') for m in marker_data if 'Country' in m])))
    cities = sorted(list(set([m.get('City', 'Unknown') for m in marker_data if 'City' in m])))

    # Calculate global average AQI
    if countries_data:
        global_avg_aqi = sum([c.get('2024 Avg', 0) for c in countries_data]) / len(countries_data)
    else:
        global_avg_aqi = 0

    # Get top 10 most polluted countries
    top_polluted_countries = sorted(countries_data, key=lambda x: x.get('2024 Avg', 0), reverse=True)[:10]

    # Get current date for the last updated timestamp
    now = datetime.now()

    return render_template('index.html', 
                           continents=continents, 
                           countries=countries, 
                           cities=cities,
                           global_avg_aqi=global_avg_aqi,
                           top_polluted_countries=top_polluted_countries,
                           now=now)

@app.route('/map')
def map_view():
    # Get unique continents from marker data
    continents = sorted(list(set([m.get('Continent', 'Unknown') for m in marker_data if 'Continent' in m])))
    
    # Get countries from the CSV file
    try:
        countries_df = pd.read_csv('attached_assets/world_most_polluted_countries_.csv')
        countries = sorted(list(set(countries_df['Country'].tolist())))
    except Exception as e:
        app.logger.error(f"Error loading countries data: {e}")
        countries = sorted(list(set([m.get('Country', 'Unknown') for m in marker_data if 'Country' in m])))
    
    # Get cities from the AQI and Lat Long CSV file
    try:
        cities_df = pd.read_csv('attached_assets/AQI and Lat Long of Countries.csv')
        cities = sorted(list(set(cities_df['City'].tolist())))
    except Exception as e:
        app.logger.error(f"Error loading cities data: {e}")
        cities = sorted(list(set([m.get('City', 'Unknown') for m in marker_data if 'City' in m])))

    # Get current date for the last updated timestamp
    now = datetime.now()

    return render_template('map.html', 
                           continents=continents, 
                           countries=countries, 
                           cities=cities,
                           now=now)

@app.route('/historical')
def historical():
    # Load all countries from the world_most_polluted_countries_.csv file
    try:
        countries_df = pd.read_csv('attached_assets/world_most_polluted_countries_.csv')
        countries_list = sorted(list(set(countries_df['Country'].tolist())))
    except Exception as e:
        app.logger.error(f"Error loading countries data: {e}")
        countries_list = sorted(list(set([c.get('Country', '') for c in countries_data])))

    # Get cities with monthly data for states from CSV file
    cities_with_states = []
    try:
        cities_df = pd.read_csv('attached_assets/updated_polluted_cities_monthly_with_states.csv')
        for _, row in cities_df.iterrows():
            cities_with_states.append({
                'city': row['City'],
                'state': row['State'] if not pd.isna(row['State']) else ''
            })
        cities_with_states = sorted(cities_with_states, key=lambda x: x['city'])
    except Exception as e:
        app.logger.error(f"Error loading cities data: {e}")
        if cities_monthly_data:
            for city_data in cities_monthly_data:
                if 'City' in city_data and 'State' in city_data:
                    cities_with_states.append({
                        'city': city_data['City'],
                        'state': city_data['State']
                    })

    # Get current date for the last updated timestamp
    now = datetime.now()

    return render_template('historical.html', 
                          countries=countries_list,
                          cities_with_states=cities_with_states,
                          now=now)

@app.route('/most_polluted')
def most_polluted():
    # Load all countries from the world_most_polluted_countries_.csv file
    try:
        countries_df = pd.read_csv('attached_assets/world_most_polluted_countries_.csv')
        # Drop duplicates keeping first occurrence (which will be the correct ranking)
        countries_df = countries_df.drop_duplicates(subset=['Country'], keep='first')
        # Sort by 2024 Avg in descending order
        countries_df = countries_df.sort_values(by='2024 Avg', ascending=False)
        # Take the top 50 countries
        top_polluted_countries = countries_df.head(50).to_dict('records')
    except Exception as e:
        app.logger.error(f"Error loading countries data: {e}")
        return render_template('error.html', error="Error loading countries data")

    # Get cities with monthly data for states from CSV file
    cities_with_states = []
    try:
        cities_df = pd.read_csv('attached_assets/updated_polluted_cities_monthly_with_states.csv')
        for _, row in cities_df.iterrows():
            cities_with_states.append({
                'city': row['City'],
                'state': row['State'] if not pd.isna(row['State']) else ''
            })
        cities_with_states = sorted(cities_with_states, key=lambda x: x['city'])
    except Exception as e:
        app.logger.error(f"Error loading cities data: {e}")
        if cities_monthly_data:
            for city_data in cities_monthly_data:
                if 'City' in city_data and 'State' in city_data:
                    cities_with_states.append({
                        'city': city_data['City'],
                        'state': city_data['State']
                    })

    # Get current date for the last updated timestamp
    now = datetime.now()

    return render_template('most_polluted.html', 
                           top_polluted_countries=top_polluted_countries,
                           cities_with_states=cities_with_states,
                           now=now)

@app.route('/about')
def about():
    # Get current date for the last updated timestamp
    now = datetime.now()
    return render_template('about.html', now=now)

@app.route('/api/filter-markers')
def filter_markers():
    continent = request.args.get('continent', 'All')
    country = request.args.get('country', 'All')
    city = request.args.get('city', 'All')
    use_api = request.args.get('use_api', 'false').lower() == 'true'

    if use_api and country == 'India':
        # Try to get real-time data from AQICN API for India
        try:
            # First check if we have cached data
            india_markers = api_utils.get_cached_map_data()

            # If no cached data, fetch from API
            if not india_markers:
                india_markers = api_utils.get_india_air_quality_map_data()

            filtered_markers = india_markers

            # Further filter by city if specified
            if city != 'All':
                filtered_markers = [m for m in filtered_markers if city.lower() in m.get('City', '').lower()]

            return jsonify(filtered_markers)
        except Exception as e:
            app.logger.error(f"Error fetching API data: {e}")
            # Fall back to static data if API fails

    # Use static data
    filtered_markers = marker_data

    if continent != 'All':
        filtered_markers = [m for m in filtered_markers if m.get('Continent') == continent]

    if country != 'All':
        filtered_markers = [m for m in filtered_markers if m.get('Country') == country]

    if city != 'All':
        filtered_markers = [m for m in filtered_markers if m.get('City') == city]

    return jsonify(filtered_markers)

@app.route('/heatmap')
def heatmap():
    # Add current date for last updated timestamp
    now = datetime.now()
    return render_template('heatmap.html', now=now)

@app.route('/api/heatmap-data')
def get_heatmap_data():
    # Read the cities data with monthly AQI values
    cities_df = pd.read_csv('attached_assets/updated_polluted_cities_monthly_with_states.csv')
    
    # Read the coordinates data
    latlong_df = pd.read_csv('attached_assets/AQI and Lat Long of Countries.csv')
    
    # Dictionary to store city coordinates (from the latlong file)
    city_coords = {}
    
    # Extract city coordinates from latlong_df
    for _, row in latlong_df.iterrows():
        if row['Country'] == 'India':  # Only include Indian cities
            city_name = row['City']
            city_coords[city_name] = {
                'lat': row['lat'],
                'lng': row['lng']
            }
    
    # Default coordinates for India (used as fallback)
    default_coords = {
        'Delhi': {'lat': 28.6139, 'lng': 77.2090},
        'Mumbai': {'lat': 19.0760, 'lng': 72.8777},
        'Kolkata': {'lat': 22.5726, 'lng': 88.3639},
        'Chennai': {'lat': 13.0827, 'lng': 80.2707},
        'Bangalore': {'lat': 12.9716, 'lng': 77.5946},
        'Hyderabad': {'lat': 17.3850, 'lng': 78.4867},
        'Pune': {'lat': 18.5204, 'lng': 73.8567},
        'Ahmedabad': {'lat': 23.0225, 'lng': 72.5714},
        'Jaipur': {'lat': 26.9124, 'lng': 75.7873}
    }
    
    # For cities in the cities_df that don't have coordinates in city_coords,
    # assign them coordinates from the default_coords if available
    for city in default_coords:
        if city not in city_coords:
            city_coords[city] = default_coords[city]
    
    # Process cities data
    data = []
    for _, row in cities_df.iterrows():
        city_name = row['City']
        
        # Calculate monthly average AQI
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        valid_months = [float(row[month]) for month in months if str(row[month]) != '--']
        
        if valid_months:
            monthly_avg = sum(valid_months) / len(valid_months)
        else:
            monthly_avg = 0  # Default if no valid data
        
        # Get coordinates for the city
        coords = city_coords.get(city_name, None)
        
        if coords:
            data.append({
                'city': city_name,
                'state': row['State'],
                'value': monthly_avg,
                'latitude': coords['lat'],
                'longitude': coords['lng']
            })
        else:
            # For cities without coordinates, estimate based on similar city names
            found = False
            for coord_city in city_coords:
                if city_name in coord_city or coord_city in city_name:
                    data.append({
                        'city': city_name,
                        'state': row['State'],
                        'value': monthly_avg,
                        'latitude': city_coords[coord_city]['lat'],
                        'longitude': city_coords[coord_city]['lng']
                    })
                    found = True
                    break
            
            # If no match found, skip this city
            if not found:
                logging.warning(f"No coordinates found for {city_name}, {row['State']}")
    
    return jsonify(data)

@app.route('/api/india-aqi-data')
def india_aqi_data():
    """
    API endpoint to get real-time air quality data for India
    """
    try:
        # Try to get cached data first
        india_markers = api_utils.get_cached_map_data()

        # If no cached data or force refresh requested, fetch new data
        if not india_markers or request.args.get('refresh') == 'true':
            india_markers = api_utils.get_india_air_quality_map_data()

        return jsonify(india_markers)
    except Exception as e:
        app.logger.error(f"Error in india_aqi_data: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/city-aqi/<city_name>')
def city_aqi(city_name):
    """
    API endpoint to get real-time air quality data for a specific city
    """
    try:
        city_data = api_utils.get_city_air_quality(city_name)
        if city_data:
            return jsonify(city_data)
        else:
            return jsonify({"error": f"No data found for {city_name}"}), 404
    except Exception as e:
        app.logger.error(f"Error in city_aqi: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/country-data/<country>')
def country_data(country):
    try:
        # Load countries directly from CSV file
        countries_df = pd.read_csv('attached_assets/world_most_polluted_countries_.csv')
        
        # Find the country data
        country_row = countries_df[countries_df['Country'] == country]
        
        if country_row.empty:
            # Log the error and provide detailed information about what's available
            available_countries = countries_df['Country'].tolist()
            app.logger.error(f"Country not found: {country}. Available countries: {available_countries[:10]}...")
            return jsonify({
                'error': 'Country not found', 
                'message': f"Could not find data for {country}",
                'suggestion': f"Available countries include: {', '.join(available_countries[:5])}"
            }), 404
        
        country_info = country_row.iloc[0]
        
        # Prepare monthly data
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        # Handle missing data more gracefully
        monthly_data = []
        for month in months:
            try:
                value = country_info[month]
                if pd.isna(value) or value == '--':
                    monthly_data.append(0)
                else:
                    monthly_data.append(float(value))
            except (ValueError, TypeError, KeyError):
                app.logger.warning(f"Could not get value for {country}/{month}, using 0")
                monthly_data.append(0)
        
        # Get the average AQI
        try:
            avg_aqi = float(country_info['2024 Avg'])
        except (ValueError, TypeError, KeyError):
            # Calculate average from monthly data if 2024 Avg is not available
            valid_values = [v for v in monthly_data if v > 0]
            avg_aqi = sum(valid_values) / len(valid_values) if valid_values else 0
        
        # Get the rank
        try:
            rank = int(country_info['Rank'])
        except (ValueError, TypeError, KeyError):
            rank = "N/A"
        
        return jsonify({
            'country': country,
            'avg_aqi': float(avg_aqi),
            'months': months,
            'monthly_data': monthly_data,
            'rank': rank
        })
    
    except Exception as e:
        app.logger.error(f"Error fetching country data from CSV: {e}")
        
        # Fallback to original implementation if CSV fails
        country_info = next((c for c in countries_data if c.get('Country') == country), None)
        
        if not country_info:
            # Log the error and provide detailed information about what's available
            available_countries = [c.get('Country') for c in countries_data if 'Country' in c]
            app.logger.error(f"Country not found: {country}. Available countries: {available_countries[:10]}...")
            return jsonify({
                'error': 'Country not found', 
                'message': f"Could not find data for {country}",
                'suggestion': f"Available countries include: {', '.join(available_countries[:5])}"
            }), 404
    
        # Prepare monthly data
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        # Handle missing data more gracefully
        monthly_data = []
        for month in months:
            value = country_info.get(month, None)
            # Convert to number if possible, otherwise use 0
            try:
                if value is None or value == '--':
                    monthly_data.append(0)
                else:
                    monthly_data.append(float(value))
            except (ValueError, TypeError):
                app.logger.warning(f"Could not convert value '{value}' for {country}/{month} to number, using 0")
                monthly_data.append(0)
        
        # Calculate average AQI if not provided
        avg_aqi = country_info.get('2024 Avg', None)
        if avg_aqi is None or avg_aqi == '--':
            valid_values = [v for v in monthly_data if v > 0]
            avg_aqi = sum(valid_values) / len(valid_values) if valid_values else 0
    
        return jsonify({
            'country': country,
            'avg_aqi': float(avg_aqi),
            'months': months,
            'monthly_data': monthly_data,
            'rank': country_info.get('Rank', 'N/A')
        })

@app.route('/api/city-data/<city>/<state>')
def city_data(city, state):
    try:
        # Load cities directly from CSV file
        cities_df = pd.read_csv('attached_assets/updated_polluted_cities_monthly_with_states.csv')
        
        # Find the city data
        city_row = cities_df[(cities_df['City'] == city) & (cities_df['State'] == state)]
        
        if city_row.empty:
            # Check if the state exists
            state_exists = state in cities_df['State'].values
            
            # Get available cities in this state
            if state_exists:
                available_cities = cities_df[cities_df['State'] == state]['City'].tolist()
                message = f"City not found. Available cities in {state} include: {', '.join(available_cities[:5])}"
            else:
                available_states = sorted(cities_df['State'].unique().tolist())
                message = f"State {state} not found. Available states include: {', '.join(available_states[:5])}"
            
            app.logger.error(f"City not found: {city}, {state}.")
            
            return jsonify({
                'error': 'City not found',
                'message': message
            }), 404
        
        city_info = city_row.iloc[0]
        
        # Prepare monthly data
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        # Handle missing data more gracefully
        monthly_data = []
        for month in months:
            try:
                value = city_info[month]
                if pd.isna(value) or value == '--':
                    monthly_data.append(0)
                else:
                    monthly_data.append(float(value))
            except (ValueError, TypeError, KeyError):
                app.logger.warning(f"Could not get value for {city}/{state}/{month}, using 0")
                monthly_data.append(0)
        
        return jsonify({
            'city': city,
            'state': state,
            'country': 'Unknown',  # CSV doesn't have country, could be added in future
            'months': months,
            'monthly_data': monthly_data
        })
    
    except Exception as e:
        app.logger.error(f"Error fetching city data from CSV: {e}")
        
        # Fallback to original implementation if CSV fails
        city_info = next((c for c in cities_monthly_data if c.get('City') == city and c.get('State') == state), None)
        
        if not city_info:
            # Log the error and provide useful information
            available_cities = [(c.get('City'), c.get('State')) for c in cities_monthly_data 
                              if 'City' in c and 'State' in c and c.get('State') == state]
            app.logger.error(f"City not found: {city}, {state}. Available cities in this state: {available_cities[:10]}...")
            
            # Provide a helpful error message
            if available_cities:
                message = f"City not found. Available cities in {state} include: {', '.join([c[0] for c in available_cities[:5]])}"
            else:
                # Check if the state exists at all
                states = set(c.get('State') for c in cities_monthly_data if 'State' in c)
                if state in states:
                    message = f"No cities found in {state}."
                else:
                    message = f"State {state} not found. Available states include: {', '.join(list(states)[:5])}"
            
            return jsonify({
                'error': 'City not found',
                'message': message
            }), 404
        
        # Prepare monthly data
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        # Handle missing data more gracefully
        monthly_data = []
        for month in months:
            value = city_info.get(month, None)
            try:
                if value is None or value == '--':
                    monthly_data.append(0)
                else:
                    monthly_data.append(float(value))
            except (ValueError, TypeError):
                app.logger.warning(f"Could not convert value '{value}' for {city}/{state}/{month} to number, using 0")
                monthly_data.append(0)
        
        return jsonify({
            'city': city,
            'state': state,
            'country': city_info.get('Country', 'Unknown'),
            'months': months,
            'monthly_data': monthly_data
        })

# IQAir API Endpoints

@app.route('/api/iqair/countries')
def iqair_countries():
    """
    API endpoint to get list of countries supported by IQAir API
    """
    try:
        countries = api_utils.get_iqair_countries()
        return jsonify(countries)
    except Exception as e:
        app.logger.error(f"Error in iqair_countries: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/iqair/states/<country>')
def iqair_states(country):
    """
    API endpoint to get list of states/regions for a country supported by IQAir API
    """
    try:
        states = api_utils.get_iqair_states(country)
        return jsonify(states)
    except Exception as e:
        app.logger.error(f"Error in iqair_states: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/iqair/cities/<country>/<state>')
def iqair_cities(country, state):
    """
    API endpoint to get list of cities for a state/region supported by IQAir API
    """
    try:
        cities = api_utils.get_iqair_cities(country, state)
        return jsonify(cities)
    except Exception as e:
        app.logger.error(f"Error in iqair_cities: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/iqair/city/<country>/<state>/<city>')
def iqair_city_data(country, state, city):
    """
    API endpoint to get air quality data for a specific city using IQAir API
    """
    try:
        city_data = api_utils.get_iqair_city_data(country, state, city)
        if city_data:
            return jsonify(city_data)
        else:
            return jsonify({"error": f"No data found for {city} in {state}, {country}"}), 404
    except Exception as e:
        app.logger.error(f"Error in iqair_city_data: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/iqair/nearest')
def iqair_nearest_city():
    """
    API endpoint to get air quality data for the nearest city using IQAir API
    """
    try:
        lat = request.args.get('lat')
        lon = request.args.get('lon')

        if not lat or not lon:
            return jsonify({"error": "Latitude and longitude parameters are required"}), 400

        city_data = api_utils.get_iqair_nearest_city(lat, lon)
        if city_data:
            return jsonify(city_data)
        else:
            return jsonify({"error": "No data found for the provided coordinates"}), 404
    except Exception as e:
        app.logger.error(f"Error in iqair_nearest_city: {e}")
        return jsonify({"error": str(e)}), 500

# Initialize database
with app.app_context():
    # Import models here to avoid circular imports
    from models import User, AQIData, CountryAQI, CityAQI
    db.create_all()
    app.logger.info("Database tables created")

# Initial data processing when app starts
with app.app_context():
    try:
        # Prepare data files if they don't exist
        if not os.path.exists('static/data'):
            os.makedirs('static/data')
            app.logger.info("Created data directory")

            # Process the provided datasets
            data_processing.process_initial_data()
            app.logger.info("Initial data processed")
    except Exception as e:
        app.logger.error(f"Error during initial data processing: {e}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)