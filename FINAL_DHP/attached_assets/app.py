import os
import pandas as pd
import folium
import json
from flask import Flask, render_template, send_from_directory, request

app = Flask(__name__)

# Simple continent lookup based on country (partial, extend as needed)
CONTINENT_MAP = {
    'Africa': [
        'Nigeria', 'Ethiopia', 'Egypt', 'Congo', 'Botswana', 'Mozambique', 'Uganda', 'Cameroon', 'Chad', 'Angola', 'Benin', 'Burundi', 'Rwanda', 'Ghana', 'South Africa', 'Senegal', 'Zambia', 'Zimbabwe', 'Namibia', 'Tanzania', 'Kenya', 'Sudan', 'Somalia', 'Libya', 'Algeria', 'Tunisia', 'Morocco', 'Ivory Coast', "Côte d'Ivoire", 'Madagascar', 'Malawi', 'Niger', 'Burkina Faso', 'Mali', 'Guinea', 'Sierra Leone', 'Togo', 'Central African Republic', 'Liberia', 'Mauritania', 'Eritrea', 'Gabon', 'Lesotho', 'Gambia', 'Botswana', 'Swaziland', 'Comoros', 'Cape Verde', 'Djibouti', 'Equatorial Guinea', 'Sao Tome and Principe', 'Seychelles'
    ],
    'Asia': [
        'India', 'China', 'Japan', 'Indonesia', 'Pakistan', 'Bangladesh', 'Philippines', 'Vietnam', 'Thailand', 'Myanmar', 'South Korea', 'North Korea', 'Malaysia', 'Nepal', 'Sri Lanka', 'Kazakhstan', 'Uzbekistan', 'Saudi Arabia', 'Iran', 'Iraq', 'Afghanistan', 'Yemen', 'Syria', 'Jordan', 'Israel', 'Lebanon', 'Kuwait', 'Oman', 'Qatar', 'Bahrain', 'United Arab Emirates', 'Singapore', 'Mongolia', 'Cambodia', 'Laos', 'Brunei', 'Timor-Leste', 'Armenia', 'Azerbaijan', 'Georgia'
    ],
    'Europe': [
        'France', 'Germany', 'Italy', 'Spain', 'United Kingdom of Great Britain and Northern Ireland', 'Netherlands', 'Belgium', 'Switzerland', 'Austria', 'Sweden', 'Norway', 'Denmark', 'Finland', 'Poland', 'Czechia', 'Slovakia', 'Hungary', 'Romania', 'Bulgaria', 'Greece', 'Portugal', 'Ireland', 'Croatia', 'Slovenia', 'Estonia', 'Latvia', 'Lithuania', 'Luxembourg', 'Iceland', 'Serbia', 'Montenegro', 'Bosnia and Herzegovina', 'North Macedonia', 'Albania', 'Moldova', 'Ukraine', 'Belarus', 'Russia'
    ],
    'North America': [
        'United States of America', 'Canada', 'Mexico', 'Guatemala', 'Honduras', 'El Salvador', 'Nicaragua', 'Costa Rica', 'Panama', 'Belize', 'Jamaica', 'Cuba', 'Haiti', 'Dominican Republic', 'Bahamas', 'Barbados', 'Saint Lucia', 'Grenada', 'Saint Vincent and the Grenadines', 'Trinidad and Tobago', 'Antigua and Barbuda', 'Saint Kitts and Nevis'
    ],
    'South America': [
        'Brazil', 'Argentina', 'Colombia', 'Peru', 'Venezuela (Bolivarian Republic of)', 'Chile', 'Ecuador', 'Bolivia (Plurinational State of)', 'Paraguay', 'Uruguay', 'Guyana', 'Suriname'
    ],
    'Oceania': [
        'Australia', 'New Zealand', 'Fiji', 'Papua New Guinea', 'Samoa', 'Tonga', 'Vanuatu', 'Solomon Islands', 'Micronesia', 'Palau', 'Marshall Islands', 'Kiribati', 'Tuvalu', 'Nauru'
    ]
}

def get_continent(country):
    for cont, countries in CONTINENT_MAP.items():
        if country in countries:
            return cont
    return 'Other'

def get_color(aqi):
    aqi = float(aqi)
    if aqi <= 50:
        return 'green'
    elif aqi <= 100:
        return 'yellow'
    elif aqi <= 150:
        return 'orange'
    elif aqi <= 200:
        return 'red'
    elif aqi <= 300:
        return 'purple'
    else:
        return 'maroon'

def generate_map(marker_data):
    m = folium.Map(location=[20, 0], zoom_start=2, tiles='cartodbpositron')

    # Add wind speed overlay (OpenWeatherMap tiles, requires API key)
    wind_tile = folium.raster_layers.TileLayer(
        tiles='https://tile.openweathermap.org/map/wind_new/{z}/{x}/{y}.png?appid=YOUR_OPENWEATHERMAP_API_KEY',
        attr='OpenWeatherMap',
        name='Wind Speed',
        overlay=True,
        control=True
    )
    wind_tile.add_to(m)

    # Add markers
    for marker in marker_data:
        folium.CircleMarker(
            location=[marker['Latitude'], marker['Longitude']],
            radius=6,
            color=marker['color'],
            fill=True,
            fill_color=marker['color'],
            fill_opacity=0.8,
            popup=folium.Popup(
                f"<b>City:</b> {marker['City']}<br>"
                f"<b>Country:</b> {marker['Country']}<br>"
                f"<b>Continent:</b> {marker['Continent']}<br>"
                f"<b>AQI:</b> {marker['AQI']}<br>"
                f"<b>Category:</b> {marker['AQI_Category']}<br>"
                f"<b>PM2.5:</b> {marker['PM2.5']} ({marker['PM2.5_Category']})<br>"
                f"<b>PM10:</b> {marker['PM10']} ({marker['PM10_Category']})<br>"
                f"<b>O3:</b> {marker['O3']} ({marker['O3_Category']})<br>"
                f"<b>NO2:</b> {marker['NO2']} ({marker['NO2_Category']})",
                max_width=300
            )
        ).add_to(m)

    folium.LayerControl().add_to(m)
    map_filename = 'static/interactive_air_quality_map.html'
    m.save(map_filename)
    return map_filename

@app.route('/')
def index():
    # Load and preprocess data
    df = pd.read_csv('AQI and Lat Long of Countries.csv', header=None)
    df.columns = [
        'Country', 'City', 'AQI', 'AQI_Category', 'PM10', 'PM10_Category', 'PM2.5', 'PM2.5_Category',
        'O3', 'O3_Category', 'NO2', 'NO2_Category', 'Latitude', 'Longitude'
    ]
    df['AQI'] = pd.to_numeric(df['AQI'], errors='coerce')
    df = df.dropna(subset=['AQI', 'Latitude', 'Longitude', 'Country', 'City'])
    df['Continent'] = df['Country'].apply(get_continent)
    df['color'] = df['AQI'].apply(get_color)

    # Prepare marker data for front-end filtering
    marker_data = df.to_dict(orient='records')
    with open('static/marker_data.json', 'w', encoding='utf-8') as f:
        json.dump(marker_data, f, ensure_ascii=False)

    # Generate the map
    generate_map(marker_data)

    # Prepare unique lists for selectors
    continents = sorted(df['Continent'].unique())
    countries = sorted(df['Country'].unique())
    cities = sorted(df['City'].unique())

    return render_template('index.html',
                           map_path='static/interactive_air_quality_map.html',
                           continents=continents,
                           countries=countries,
                           cities=cities)

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

if __name__ == "__main__":
    app.run(debug=True)
