# This is supposed to be run as a service.
# This is an infinite loop to periodically check for processing requests (request_queue in the database)
# and execute the optimizer per request.
# Then save results and status in the database.


from server_scripts import database as db
from server_scripts import Parse, misc
import time, yaml, os, sys, pytz, multiprocessing
from datetime import datetime

global config
with open("server_config.yaml", 'r') as stream:
    try:
        config = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        print(exc)
        sys.exit()

def main():
    n_process = config['optimizer_n_process']
    with multiprocessing.Pool(n_process) as p:
        p.map(queue_worker, list(range(n_process)))

def queue_worker(worker_id):
    been_sleeping = False
    while True:
        try:
            # check the request queue in DB
            # if the queue is not empty, process the requests
            if db.isQueueNotEmpty():
                # pop the queue and get the first projectID to process
                projectID = db.popQueue()
                print('--[{0}]: processing projectID {1} '.format(worker_id, projectID))
                # gather data from db and write to tsv file on disk
                misc.write_input_to_tsv(projectID, config['optimizer_data_dir'], filename = 'Input_File.txt')
                print('--[{0}]: wrote input to tsv, projectID {1}'.format(worker_id, projectID))
                # update project status in the db
                db.updateProjectStatus(projectID, 'input completed, optimizer is processing')
                print('--[{0}]: updated project status, projectID {1}'.format(worker_id, projectID))

                # run optimizer and export log 
                start_time = time.time() # measure elapsed time
                print('--[{0}]: projectID {1} - running optimizer ...'.format(worker_id, projectID))
                optimizer_status = os.system('sh ./run_optimizer.sh | tee {0}/log'.format(config['optimizer_data_dir']))
                elapsed_time_minutes = int((time.time() - start_time)/60)

                if optimizer_status == 0: # success
                    print('--[{0}]: success! projectID {1}'.format(worker_id, projectID))
                    # save output data and log to db
                    log = Parse.read_optimizer_log('{0}/log'.format(config['optimizer_data_dir']))
                    print(log)
                    ## parse output data
                    output1, output2 = Parse.parse_optimizer_output('{0}/optimizer_output_file1.txt'.format(config['optimizer_data_dir']), '{0}/optimizer_output_file2.txt'.format(config['optimizer_data_dir']))
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
                        print ('--[{0}]: OUTPUT HAS NON-BINARY VALUES !!! projectID {1}'.format(worker_id, projectID))
                        db.save_optimizer_log(projectID, log)
                        db.updateProjectStatus(projectID, 'input completed, optimizer failed')
                        continue

                else:
                    print('--[{0}]: failed! projectID {1}')
                    log = Parse.read_optimizer_log('{0}/log'.format(config['optimizer_data_dir']))
                    print(log)
                    db.save_optimizer_log(projectID, 'optimizer failed')
                    db.updateProjectStatus(projectID, 'input completed, optimizer failed')
                    db.updateProjectLastOptimized(projectID, now, elapsed_time_minutes)

                been_sleeping = False

            else: # if the queue is empty, check again in 1 minute
                if not been_sleeping:
                    print('--[{0}]: sleeping -------'.format(worker_id))
                    been_sleeping = True
                time.sleep(30)
        except Exception as e:
            print(e)

if __name__ == '__main__':
    main()