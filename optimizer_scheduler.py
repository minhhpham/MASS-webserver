# This is supposed to be run as a service.
# This is an infinite loop to periodically check for processing requests (request_queue in the database)
# and execute the optimizer per request.
# Then save results and status in the database.


from server_scripts import database as db
from server_scripts import Parse, misc
import time, yaml, os, sys

global config
with open("server_config.yaml", 'r') as stream:
    try:
        config = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        print(exc)
        sys.exit()

been_sleeping = False

while True:
    # check the request queue in DB
    # if the queue is not empty, process the requests
    if db.isQueueNotEmpty():
        # pop the queue and get the first projectID to process
        projectID = db.popQueue()
        print('----------- processing projectID {} ---------'.format (projectID))
        # gather data from db and write to tsv file on disk
        misc.write_input_to_tsv(projectID, config['optimizer_data_dir'], filename = 'Input_File.txt')
        print('wrote input to tsv')
        # update project status in the db
        db.updateProjectStatus(projectID, 'input completed, optimizer is processing')
        print('updated project status')

        # run optimizer and export log 
        print('running optimizer ...')
        optimizer_status = os.system('sh ./run_optimizer.sh > {0}/log 2>&1'.format(config['optimizer_data_dir']))

        if optimizer_status == 0: # success
            print('success!')
            # save output data and log to db
            ## parse output data
            output1, output2 = Parse.parse_optimizer_output('{0}/optimizer_output_file1.txt'.format(config['optimizer_data_dir']), '{0}/optimizer_output_file2.txt'.format(config['optimizer_data_dir']))
            if output1 != -1: # check that no weird output value
                print (output1)
                print (output2)
                log = Parse.read_optimizer_log('{0}/log'.format(config['optimizer_data_dir']))
                print(log)
            ## save to db
                db.save_optimizer_output(projectID, output1, output2)
                db.save_optimizer_log(projectID, log)

                # update project status in the db
                db.updateProjectStatus(projectID, 'input completed, optimized solutions is ready')
            else:
                print ('OUTPUT HAS NON-BINARY VALUES !!!')
                db.save_optimizer_log(projectID, log)
                db.updateProjectStatus(projectID, 'input completed, optimizer failed')
                continue

        else:
            print('failed!')
            log = Parse.read_optimizer_log('{0}/log'.format(config['optimizer_data_dir']))
            print(log)
            db.save_optimizer_log(projectID, 'optimizer failed')
            db.updateProjectStatus(projectID, 'input completed, optimizer failed')

        been_sleeping = False

    else: # if the queue is empty, check again in 1 minute
        if not been_sleeping:
            print('---- sleeping ... -------')
            been_sleeping = True
        time.sleep(60)
