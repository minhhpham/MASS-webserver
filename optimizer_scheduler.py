# This is supposed to be run as a service.
# This is an infinite loop to periodically check for processing requests (request_queue in the database)
# and execute the optimizer per request.
# Then save results and status in the database.


from server_scripts import database as db
from server_scripts import Parse, misc
import time, yaml, os, sys, pytz, multiprocessing, sys, shutil
from datetime import datetime

global config
with open("server_config.yaml", 'r') as stream:
    try:
        config = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        print(exc)
        sys.exit()

worker_id = sys.argv[1]

# set up working environment
optimizer_dir = "../MASS-Optimizer" + str(worker_id) + "/optimizer"
if os.path.exists("../MASS-Optimizer" + str(worker_id)):
    shutil.rmtree("../MASS-Optimizer" + str(worker_id))
os.system("cp -r ../MASS-Optimizer ../MASS-Optimizer"+str(worker_id))


been_sleeping = False
while True:
    try:
        # check the request queue in DB
        # if the queue is not empty, process the requests
        if db.isQueueNotEmpty():
            # pop the queue and get the first projectID to process
            projectID = db.popQueue()
            print('--[worker {0}]: processing projectID {1} '.format(worker_id, projectID), flush=True)
            # gather data from db and write to tsv file on disk
            misc.write_input_to_tsv(projectID, optimizer_dir, filename = 'Input_File.txt')
            print('--[worker {0}]: wrote input to tsv, projectID {1}'.format(worker_id, projectID), flush=True)
            # update project status in the db
            db.updateProjectStatus(projectID, 'input completed, optimizer is processing')
            print('--[worker {0}]: updated project status, projectID {1}'.format(worker_id, projectID), flush=True)

            # run optimizer and export log 
            start_time = time.time() # measure elapsed time
            print('--[worker {0}]: projectID {1} - running optimizer ...'.format(worker_id, projectID), flush=True)
            optimizer_status = os.system('sh ./run_optimizer.sh {0} 2> {0}/log'.format(optimizer_dir))
            elapsed_time_minutes = int((time.time() - start_time)/60)

            if optimizer_status == 0: # success
                print('--[worker {0}]: success! projectID {1}'.format(worker_id, projectID), flush=True)
                # save output data and log to db
                log = Parse.read_optimizer_log('{0}/log'.format(optimizer_dir))
                print(log)
                ## parse output data
                output1, output2 = Parse.parse_optimizer_output('{0}/optimizer_output_file1.txt'.format(optimizer_dir), '{0}/optimizer_output_file2.txt'.format(optimizer_dir))
                if output1 != -1: # check that no weird output value
                    print (output1)
                    print (output2)
                ## save to db
                    db.save_optimizer_output(projectID, output1, output2)
                    db.save_optimizer_log(projectID, log)

                    # update project status in the db
                    db.updateProjectStatus(projectID, 'input completed, optimized solutions is ready')
                    # update last time optimized
                    now = datetime.now(pytz.timezone('EST')).strftime("%Y-%m-%d %H:%M:%S %z")
                    db.updateProjectLastOptimized(projectID, now, elapsed_time_minutes)
                else:
                    print ('--[worker {0}]: OUTPUT HAS NON-BINARY VALUES !!! projectID {1}'.format(worker_id, projectID), flush=True)
                    db.save_optimizer_log(projectID, log)
                    db.updateProjectStatus(projectID, 'input completed, optimizer failed')
                    continue

            else:
                print('--[worker {0}]: failed! projectID {1}', flush=True)
                log = Parse.read_optimizer_log('{0}/log'.format(optimizer_dir))
                print(log)
                db.save_optimizer_log(projectID, 'optimizer failed')
                db.updateProjectStatus(projectID, 'input completed, optimizer failed')
                db.updateProjectLastOptimized(projectID, now, elapsed_time_minutes)

            been_sleeping = False

        else: # if the queue is empty, check again in 1 minute
            if not been_sleeping:
                print('--[worker {0}]: sleeping -------'.format(worker_id), flush=True)
                been_sleeping = True
            time.sleep(30)

        # delete data older than 30 days
        #print('purge old data')
        db.delete_data()
    except Exception as e:
        print(e)
