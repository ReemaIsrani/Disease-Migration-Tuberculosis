File Description

dm_api.py
Flask API code for strategic planning.
Input - 

●	Location

Percent increase or decrease in:

●	RSPM

●	SO2

●	NO2

●	Rainfall

●	Relative Humidity

●	Average Temperature

Output -
Yearly new prediction of the given location with respective increase/decrease in input parameters.

api_request.py - 
Demo API request to the Flask API

loc_index.csv - 
Every location is encoded to a unique number. This file contains encoding information.

forecasted.csv -
Contains forecasted input data (climate and pollution data 2019-2025) 

total_cases.h5 and total_smearpositivecases.h5 -
Trained NN models for TB prediction.
