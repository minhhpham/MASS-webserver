# This is supposed to be run as a service.
# This is an infinite loop to periodically check for processing requests (request_queue in the database)
# and execute the optimizer per request.
# Then save results and status in the database.

OPTIMIZER_DIR = '../MASS-Optimizer/optimizer'

from server_scripts import database as db
from server_scripts import Parse
import time

while True:
    # check the request queue in DB
    # if the queue is not empty, process the requests
    if db.isQueueNotEmpty():
        # pop the queue and get the first projectID to process
        projecID = db.popQueue()['projectid']
        # gather data from db and write to tsv file on disk
        misc.write_input_to_tsv(projectID, config['optimizer_data_dir'], filename = 'data.txt')
        # update project status in the db
        db.updateProjectStatus(projectID, 'input uncompleted, optimizer is processing')
        # run optimizer and export log 
        os.system('sh ./optimizer.sh > {0}/log 2>&1'.format(OPTIMIZER_DIR))

        # save output data and log to db
        ## parse output data
        output1, output2 = Parse.parse_optimizer_output('{0}/optimizer_output_file1.txt'.format(OPTIMIZER_DIR), '{0}/optimizer_output_file2.txt'.format(OPTIMIZER_DIR))
        log = Parse.read_optimizer_log('{0}/log'.format(OPTIMIZER_DIR))
        ## save to db

        # update project status in the db
        db.updateProjectStatus(projectID, 'input completed, optimized solutions is ready ')

    


    else: # if the queue is empty, check again in 1 minute
        time.sleep(60)
