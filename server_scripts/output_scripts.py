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
    # get list of locations from db
    location_list = db.getPlants(projectID)
    # get list of techs from db
    tech_list = db.getTechnologies(projectID)
    # get population clusters and parameters from db
    populations = db.getPopulations(projectID)
    params = db.getParams(projectID)
    # we need to calculate populations at the end of project (for capacity calculation)
    lifespan = db.getInputSize(projectID)['durations']
    for p in populations:
        p['end_pr'] = p['pr'] * (1+p['growthrate'])**lifespan

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

            # calculate capacities
            if len(clus_index) == 0:
                receiving_cap_m3y = 0
                receiving_cap_mgd = 0
                sending_cap_m3y = 0
                sending_cap_mgd = 0
            else:
                total_population = sum([p['end_pr'] for p in populations if str(p['index']) in clus_index])
                mu = [p['value'] for p in params if p['label']=='mu'][0]
                alpha = [p['value'] for p in params if p['label']=='alpha'][0]
                receiving_cap_m3y = round(total_population*mu, 2)
                receiving_cap_mgd = round(receiving_cap_m3y/365/3785.41178, 2)
                sending_cap_m3y   = round(alpha*receiving_cap_m3y, 2)
                sending_cap_mgd   = round(alpha*receiving_cap_mgd, 2)

            # append to output2_return
            output2_return.append([str(SolutionID), str(location['index']), location['locationname'], tech_name, tech_scale, cluster_str, receiving_cap_m3y, sending_cap_m3y, receiving_cap_mgd, sending_cap_mgd])

    return(output1_return, output2_return)
