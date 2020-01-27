############### functions to render output data from optimizer to web pages ####################
import csv

def output_values(projectID):
    """ read output values (ZE,CE) from optimizer's output """
    values = [] # output array
    # this is for demonstration on sample output
    # read from csv files
    with open('output/values-username-projectid.csv', 'r') as csvfile:
        csvreader = csv.reader(csvfile)
        next(csvreader) # skip header row
        for row in csvreader:
            values.append((row[0], row[1], row[2]))
    return(values)
            
def output_solutions(projectID):
    """ read and transform binary output """
    # only reading transformed output for now
    solution_details = []
    with open('output/transformed output.csv', 'r') as csvfile:
        csvreader = csv.reader(csvfile)
        next(csvreader) # skip header row
        for row in csvreader:
            solution_details.append((row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9]))
        return(solution_details)