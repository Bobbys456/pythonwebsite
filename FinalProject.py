"""
Robert Sullivan
Final Project
5/5/2022

"""

import streamlit as st
import pandas as pd
import csv
import numpy as np
import plotly.express as px
from PIL import Image
import pydeck as pdk

#Outside module used here for determining the distance in miles between two sets of coordinates on a map
from geopy.geocoders import Nominatim
import geopy.distance
geolocator = Nominatim(user_agent="Project 4")

def get_addy():

    """
    This sections splits up the inputted address into its component parts used in the geolocater
    """
    street = st.text_input(label = 'Street Name', value="", max_chars=None, key=None, type="default", help=None, autocomplete=None, on_change=None, args=None, kwargs=None, placeholder=None, disabled=False)
    house_num = st.number_input(label = 'House Number', min_value=None, max_value=None, step=None, format=None, key=None, help=None, on_change=None, args=None, kwargs=None,disabled=False)
    city = st.text_input(label = 'City', value="", max_chars=None, key=None, type="default", help=None, autocomplete=None, on_change=None, args=None, kwargs=None, placeholder=None, disabled=False)
    return city,street,int(house_num)

def find_distance(coords_1, coords_2):
    """
    This method returhs the distance between two coordinates
    """

    return geopy.distance.geodesic(coords_1, coords_2).miles

def get_coords(location):
    return (location.latitude, location.longitude)

def crimes_type_freq(data):
    crimes = {}

    #Gets all crime names in a dictionary along with their frequencies
    for crime in data['OFFENSE_DESCRIPTION']:
        if crime in crimes:
            crimes[crime] += 1
        else:
            crimes[crime] = 1

    #transaltes dictionary into two lists that can be returned
    crime_name = []
    crime_frq = []
    for crime in crimes:
        crime_name.append(str(crime))
        crime_frq.append(crimes[crime])

    #all option appended for use by other methods
    crime_name.append('All')
    crime_frq.append(0)

    return crime_name, crime_frq

def get_top_crimes(crime_names, crime_frq):

    #This method presents the user with a select slider to get the users specified amount of crimes organized by frequency
    nums = []
    for i in range(21):
        nums.append(i)
    top_x = st.select_slider(label = 'Number of Crimes', options = nums)

    df = pd.DataFrame(list(zip(crime_names, crime_frq)),columns =['Name', 'FRQ'])

    return(df.sort_values(by=['FRQ'], ascending=False).iloc[0:top_x])

def selection(crime_name, title = 'Crime Types'):

    #provides the user with a select box with all of the crime types as the otpions and returns the select4ed option
    selection = st.selectbox(title, crime_name, index=0, key=None, help=None, on_change=None, args=None, kwargs=None, disabled=False)
    return(selection)

def make_bar(bar_data):

    #creates a plotly bar chart from the passed data
    fig = px.bar(bar_data, x = "Name", y = "FRQ")

    st.plotly_chart(fig)

def make_map(locations):

    #This mapping function allows for the user to select a specific crime and plot all occurences of said crime with each point colorcoded to identify different districts

    locations = locations[locations['Long'] != 0]

    locations.rename(columns = {'Lat': 'latitude','Long': 'longitude'}, inplace = True)
    
    view_state = pdk.ViewState(latitude=locations['latitude'].mean(), longitude=locations['longitude'].mean(), zoom= 12)

    #Create layers with randomley generated colors for the dots
    layer = []
    for district in locations['DISTRICT']:
        layed = pdk.Layer("ScatterplotLayer", data= locations[locations['DISTRICT'] == district],get_position='[longitude, latitude]', get_radius=100, pickable=True, filled=True, get_color = [np.random.randint(0,255), np.random.randint(0,255),np.random.randint(0,255)])
        layer.append(layed)

    tool_tip = {'html': 'Listing:<br><b>{name}</b>', 'style': {'backgroundcolor': 'steelblue', 'color': 'white'}}
    map = pdk.Deck(map_style='mapbox://styles/mapbox/light-v9',
                   initial_view_state= view_state,
                   layers=layer,
                   tooltip=tool_tip)

    st.pydeck_chart(map)



def get_coordinates(select, data):

   #THis method allows the user to filer the coordinates for only those that have the selected crime
    if select == 'All':
        df = data[['OFFENSE_DESCRIPTION', 'Lat', 'Long']]
    else:
        df = data[['DISTRICT','OFFENSE_DESCRIPTION', 'Lat', 'Long']]
        df = df[df['OFFENSE_DESCRIPTION'] == select]

    return df

def get_data(filepath):
    with open(filepath, "r") as file_data:
        info = pd.read_csv(file_data)

    return info

def get_saftey_score(data):

    #Gets adress from user input and translates address into coordinates
    city,street,house_num = get_addy()
    address = geolocator.geocode((house_num,street,city,'MA'))
    coords = get_coordinates('All', data)
    address = get_coords(address)

    safety_score = 0

    Lat = [float(item) for item in coords['Lat'].tolist()]
    Long = [float(item) for item in coords['Long'].tolist()]
    desc = [str(item) for item in coords['OFFENSE_DESCRIPTION'].tolist()]
    locs = list(zip(Lat, Long, desc))

    crime_types = {}

    #For each crime committed the proximity to the given address is checked and if it is within .4 mile it is counted
    for set in locs:
        if find_distance(address, (set[0],set[1])) < .40 and set[2] not in ['SICK ASSIST','PROPERTY - LOST/ MISSING', 'TOWED MOTOR VEHICLE', 'INVESTIGATE PROPERTY', 'VERBAL DISPUTE', 'INVESTIGATE PERSON', 'SICK/INJURED/MEDICAL - PERSON', 'SICK ASSIST - DRUG RELATED ILLNESS', 'PROPERTY - FOUND']:
            safety_score += .1
            if set[2] in crime_types:
                crime_types[set[2]] += 1
            else:
                crime_types[set[2]] = 1



    names = []
    frq = []

    st.write("The safety score of", address, "is", safety_score)

    #The following code creates a bar chart with the highest frequency crimes withing .4 miles of the given address
    for crime in crime_types:
        names.append(crime)
        frq.append(crime_types[crime])


    top_names = get_top_crimes(names, frq)

    make_bar(top_names)


def get_time_graph(data, selected):

    data = data[data['OFFENSE_DESCRIPTION'] == selected]
    info = data[['OCCURRED_ON_DATE','OFFENSE_DESCRIPTION', 'DAY_OF_WEEK','MONTH']]

    #extracts the different time intervals from the data
    dates = [str(item).split(' ')[0] for item in data['OCCURRED_ON_DATE']]
    times = [int(str(item).split(' ')[1].split(':')[0]) for item in data['OCCURRED_ON_DATE']]
    weekday = [item for item in data['DAY_OF_WEEK']]
    month = [item for item in data['MONTH']]

    #allows the user to select what time intervals to use on the line chart
    select = selection(['times', 'weekday', 'month'], 'Select level for graph: ')
    if select == 'dates':
        chosen = dates
    elif select == 'times':
        chosen = times
    elif select == 'weekday':
        chosen = weekday
    elif select == 'month':
        chosen = month

    #zips together crime names and their asosciated timestamps depending on the interval chosen by the user
    crime_list = pd.DataFrame(zip(data['OFFENSE_DESCRIPTION'],chosen))
    crime_list.columns = ['Name', 'Occured']

    time_name = []
    time_frq = []
    times = {}

    #counts the frq for each time interval
    for time in crime_list['Occured']:
        if time in times:
            times[time] += 1
        else:
            times[time] = 1


    for time in times:
        if selected == 'times':
            time_name.append(int(time))
        else:
            time_name.append(str(time))
        time_frq.append(times[time])

    line_data = pd.DataFrame(zip(time_name, time_frq))
    line_data.columns = ['Name', 'Occured']

    #THis if else statement orders the data correctly so that the time intervals appear mostly in order on the line graph or else the graph data would not be as useful
    if select == 'times':
        cats = [ '1', '2', '3', '4', '5', '6', '5','6', '7', '8','9','10','11','12','13','14','15','16','17','18','19','20','21','22','23','24']
        line_data = line_data.sort_values('Name')
        line_data = line_data.groupby(['Name']).sum().reindex(cats)
        fig = px.line(line_data, x=line_data.index.values, y='Occured')
    elif select == 'weekday':
        cats = [ 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        line_data = line_data.groupby(['Name']).sum().reindex(cats)
        fig = px.line(line_data, x=line_data.index.values, y='Occured')
    else:
        line_data = line_data.sort_values('Name')
        line_data.columns = ['Name', 'Occured']
        fig = px.line(line_data, x='Name', y='Occured')


    st.plotly_chart(fig)

def make_pie(data, districts):

    #Allows the user to select a district to get the data from

    dist = selection(districts['DISTRICT_NAME'], 'Choose a District')

    #gets the data for the chosen district
    chosendist = list(districts[districts['DISTRICT_NAME'] == dist]['DISTRICT_NUMBER'])[0]
    data = data[data['DISTRICT'] == chosendist]

    #gets crime frq data for the chosen district
    crime_names, crime_frq = crimes_type_freq(data)
    top_names = get_top_crimes(crime_names, crime_frq)

    #plots the frq data in a plotly pie chart
    fig = px.pie(top_names, values='FRQ', names='Name', title='Crimes Committed')
    st.plotly_chart(fig)

def main():

    data = get_data(r'C:\Users\bobby\OneDrive\Desktop\SubmissionsFolder\CS230\testing\BostonCrime2022_8000_sample.csv')
    districts = get_data(r'C:\Users\bobby\OneDrive\Desktop\SubmissionsFolder\CS230\testing\BostonDistricts.csv')
    crime_names, crime_frq = crimes_type_freq(data)

    page = st.sidebar.selectbox(
        "Select a Page",
        [
            "Homepage",
            "Crimes locations",
            "Crimes FRQ's",
            "Saftey Score",
            'Across Time'
        ]
    )

    if page == "Homepage":
        st.header('Boston Crime Statistics')
        image = Image.open(r'C:\Users\bobby\OneDrive\Desktop\SubmissionsFolder\CS230\testing\BostonPic.png')
        st.image(image)
        st.write('The following pages present different views for analyzing Boston crime data for the first 3 months of 2022. ')


    if page == "Crimes FRQ's":

        make_pie(data, districts)

    if page == "Crimes locations":
        crime_selected = selection(crime_names)
        locations = get_coordinates(crime_selected, data)
        make_map(locations)

    if page == 'Saftey Score' :
        get_saftey_score(data)

    if page == 'Across Time' :
        crime_selected = selection(crime_names)
        get_time_graph(data, crime_selected)

main()


