# Import the dependencies.
from flask import Flask, jsonify

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

import numpy as np
import pandas as pd
import datetime as dt


#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(engine)

# Save references to each table
Measurement = Base.classes.measurement
Station = Base.classes.station

# Create our session (link) from Python to the DB


#################################################
# Flask Routes
#################################################

# index route
@app.route("/")
def home():
    #print request recieved to terminal
    print(f"Server recieved request for index route")

    #return all avaliable routes to app
    return (
        f"Welcome to Hawaii Climate API! <br/>"
        '<br/>'     #skip line
        '<br/>'     #skip line
        f"Available Routes:<br/>"
        '<br/>'     #skip line
        f"---Route: /api/v1.0/precipitation <br/>"
        f"---Description: Displays all precipitation data from 2017-08-23 to 2018-08-23 <br/>"
        '<br/>'     #skip line
        f"---Route: /api/v1.0/stations <br/>"
        f"---Description: Displays list of all Stations <br/>"
        '<br/>'     #skip line
        f"---Route: /api/v1.0/tobs <br/>"
        f"---Description: Displays dates and temperature observations from most active station for the previous year <br/>"
        '<br/>'     #skip line
        f"---Route: /api/v1.0/YYYY-MM-DD ** NOT FINISHED: NEEDS CHECK FOR DATE **<br/>" 
        f"---Description: Displays min, max, and avg temperatures for date provided through last date in dataset (date required as end arguement e.g. 2017-07-23) <br/>"
        '<br/>'     #skip line
        f"---Route: /api/v1.0/YYYY-MM-DD/YYYY-MM-DD ** NOT FINISHED: NEEDS CHECK FOR DATE **<br/>" 
        f"---Description: Displays min, mac, and avg temperatures from start date to end date (start date and end date required as end arguement e.g. 2017-06-23/2017-07-23) <br/>"

    )

#create route that returns most recent 12 months of precip data
@app.route("/api/v1.0/precipitation")
def precipitation():
    # Create our session (link)
    session = Session(engine)

    #get most recent date and date one year ago
    recent_date = get_recent_date()                 ### def on line 36 ###
    one_year_string = get_year_ago(recent_date)     ### def on line 44 ###

    # Perform a query to retrieve the data and precipitation scores
    prcp_results = session.query(Measurement.date, Measurement.prcp).\
                            filter(Measurement.date <=recent_date).\
                            filter(Measurement.date >=one_year_string).all()
    session.close()

    #create empty dict to store data
    prcp_dict = {}
    for date, prcp in prcp_results:
        prcp_dict.update({date:prcp})
    #return dict
    return jsonify(prcp_dict)

#create route to return a list of all stations
@app.route("/api/v1.0/stations")
def stations():

    session = Session(engine)
    #make query to get list of all stations
    stations = session.query(Measurement.station,
                            Station.name,
                            Station.latitude,
                            Station.longitude,
                            Station.elevation,
                            func.min(Measurement.prcp),
                            func.max(Measurement.prcp),
                            func.avg(Measurement.prcp),
                            func.min(Measurement.tobs),
                            func.max(Measurement.tobs),
                            func.avg(Measurement.tobs)).\
                        filter(Measurement.station == Station.station).\
                        group_by(Measurement.station).all()
    session.close()

    station_list = []           #empty list for storing dicts
    for station, name, latitude, longitude, elevation, min_prcp, max_prcp, avg_prcp, min_temp, max_temp,avg_temp in stations:
        station_dict = {}       #empty dict to store current iteration
        #add key:value pairs to dict
        station_dict.update({'Station_ID':station})
        station_dict.update({'Station Name':name})
        station_dict.update({'Location':{'Latitude':latitude, 'Longitude':longitude}})
        station_dict.update({'Climate_Data':{
                'Temperature':{'max_temp':max_temp,'min_temp':min_temp,'avg_temp':avg_temp},
                'Precipitation':{'max_prcp':max_prcp,'min_prcp':min_prcp,'avg_prcp':avg_prcp}}})
        #add dict subset to list
        station_list.append(station_dict)
    return jsonify(station_list)

#route to return 12 months of temp data
@app.route("/api/v1.0/tobs")
def tobs():
    # Design a query to retrieve the last 12 months of precipitation data
    # Starting from the most recent data point in the database. 
    recent_date = get_recent_date()
    one_year_string = get_year_ago(recent_date)

    #find most active station
    session = Session(engine)
    station_measurement_counts = session.query(Measurement.station, func.count(Measurement.station)).\
                                        group_by(Measurement.station).\
                                        order_by(func.count(Measurement.station).desc())
    
    #query to get most active stations data
    most_act_station_data = session.query(Measurement.station,Measurement.date, Measurement.prcp, Measurement.tobs).\
                                    filter(Measurement.station == station_measurement_counts[0][0]).\
                                    filter(Measurement.date <=recent_date).\
                                    filter(Measurement.date >=one_year_string).all()
    session.close()

    #for loop to add data to list of dicts
    station_data_list = []
    for name,date,prcp,temp in most_act_station_data:
        station_data_dict = {}
        #add key:value pairs to dict{}
        station_data_dict.update({'Station ID':name})
        station_data_dict.update({'Date':date})
        station_data_dict.update({'Precip':prcp})
        station_data_dict.update({'Temp':temp})

        #add subset
        station_data_list.append(station_data_dict)
    return jsonify(station_data_list)

# route to return temp data from start date to end of dataset
@app.route("/api/v1.0/<start_date>")
def one_date(start_date):
    end_date = get_recent_date()
    session = Session(engine)
    # create query to get date and temp data
    #filter by date range
    temp_data = session.query(Measurement.date, func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)).\
                        filter(Measurement.date <=end_date).\
                        filter(Measurement.date >= start_date).\
                        group_by(Measurement.date).\
                        order_by(Measurement.date)
    session.close()
    # add data to list of dictionaries
    date_range_list = []
    for date, tmin, tavg, tmax in temp_data:
        date_range_dict = {}
        date_range_dict.update({'Date': date})
        date_range_dict.update({'TMIN': tmin})
        date_range_dict.update({'TAVG': tavg})
        date_range_dict.update({'TMAX': tmax})

        date_range_list.append(date_range_dict)
    return jsonify(date_range_list)

#route to return temp data for date range
@app.route("/api/v1.0/<start_date>/<end_date>")
def two_date(start_date,end_date):
    session = Session(engine)
    #query to get temp data for date range
    temp_data = session.query(Measurement.date, func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)).\
                        filter(Measurement.date <= end_date).\
                        filter(Measurement.date >= start_date).\
                        group_by(Measurement.date).\
                        order_by(Measurement.date)
    session.close()
    # add data to list of dicts
    date_range_list = []
    for date, tmin, tavg, tmax in temp_data:
        date_range_dict = {}
        date_range_dict.update({'Date': date})
        date_range_dict.update({'TMIN': tmin})
        date_range_dict.update({'TAVG': tavg})
        date_range_dict.update({'TMAX': tmax})

        date_range_list.append(date_range_dict)
    return jsonify(date_range_list)
### run the app if main is called ###
if __name__ == "__main__":
    app.run(debug=True)