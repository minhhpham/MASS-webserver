############### functions to render output data from optimizer to web pages ####################
import csv

def output_values(username, project_id):
    values = [] # output array
    # this is for demonstration on sample output
    # read from csv files
    with open('output/values-username-projectid.csv', 'r') as csvfile:
        csvreader = csv.reader(csvfile)
        next(csvreader) # skip header row
        for row in csvreader:
            values.append((row[0], row[1], row[2]))
    return(values)
            
