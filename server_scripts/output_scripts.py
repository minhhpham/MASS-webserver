############### functions to render output data from optimizer (saved in db) to web pages ####################
import csv
from server_scripts import database as db

def get_output(projectID):
    """ read output values (ZE,ZC) from optimizer's output in the db"""
    output1_raw, output2_raw = db.get_optimizer_output(projectID)
    
    output1_return = []
    for row in output2_raw:
        output1_return.append([row['solution_label'], row['zc'], row['ze']])

    # get list of unique solutions
    solution_list = []
    for row in output1_raw:
        if row['solution_label'] not in solution_list:
            solution_list.append(row['solution_label'])
    # get list of locations
    location_list = db.getPlants(projectID)
    # get list of techs
    tech_list = db.getTechnologies(projectID)

    # format output2
    output2_return = []
    for SolutionID in solution_list:
        for location in location_list:
            # find tech index selected for this solution in output1_raw
            tech_index = [r['t'] for r in output1_raw if r['var']=='w' and r['k']==location['index'] and r['solution_label']==SolutionID]
            if len(tech_index) > 0:
                tech_index = tech_index[0]
                tech_name  = [r['technologyname'] for r in tech_list if r['index']==tech_index][0]
                tech_scale = [r['scale'] for r in tech_list if r['index']==tech_index][0]
            else:
                tech_name  = 'Not Installed'
                tech_scale = 'Not Installed'

            # find servicing clusters for this solution and location in output1_raw
            clus_index = [str(r['r']) for r in output1_raw if r['var']=='q' and r['k']==location['index'] and r['solution_label']==SolutionID]
            if len(clus_index) > 0:
                cluster_str = ', '.join(clus_index)
            else:
                cluster_str = ''

            # append to output2_return
            output2_return.append([str(SolutionID), str(location['index']), location['locationname'], tech_name, tech_scale, cluster_str])

    return(output1_return, output2_return)
