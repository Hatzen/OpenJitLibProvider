import os
import datetime
import traceback
import sys
from io import StringIO
from consts import LOCAL_LOGS_PATH

import threading                                                                
import functools                                                                
import time                                                                     

# Use synchronize so error logs wont mix sys.stdout
# https://stackoverflow.com/a/29163532/8524651
def synchronized(wrapped):                                                      
    lock = threading.Lock()            
    id(lock)                                                        
    @functools.wraps(wrapped)                                                   
    def _wrap(*args, **kwargs):                                                 
        with lock:                                                              
            print ("Calling '%s' with Lock %s from thread %s [%s]"              
                   % (wrapped.__name__, id(lock),                               
                   threading.current_thread().name, time.time()))               
            result = wrapped(*args, **kwargs)                                   
            print ("Done '%s' with Lock %s from thread %s [%s]"                 
                   % (wrapped.__name__, id(lock),                               
                   threading.current_thread().name, time.time()))               
            return result                                                       
    return _wrap                                                                


@synchronized   
def log_method_output(method, args, kwargs, organization, module, version, file_name):
    """
    Executes a method and logs its output and errors to a file while preventing stdout and stderr output to the console.

    :param method: The method to execute.
    :param args: Positional arguments for the method.
    :param kwargs: Keyword arguments for the method.
    :param organization: The organization name for determining the folder path.
    :param module: The module name for determining the folder path.
    :param version: The version for determining the folder path.
    :param file_name: The base name of the file to include the timestamp.
    """
    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    log_dir = os.path.join(LOCAL_LOGS_PATH, organization, module, version)
    
    # Ensure the target folder exists
    os.makedirs(log_dir, exist_ok=True)
    
    log_file_path = os.path.join(log_dir, f"{file_name}-{timestamp}.txt")
    

    # TODO: Check if this leads to problem with multi threading, which would be expected. Temporarly resolved by synchronized call.
   
    # Redirect stdout and stderr to StringIO objects
    # Backup current stdout and stderr
    #original_stdout = sys.stdout
    #original_stderr = sys.stderr
    #sys.stdout = StringIO()
    #sys.stderr = StringIO()


    result = None
    resultText = "test"
    try:
        print("trying to run method")
        result = method(*args, **kwargs)
        resultText = "Sucess for " + file_name
            
    except Exception as e:
        print("failed to run method. With log path " + os.path.join(os.getcwd(), log_file_path))
        
        # Write error details to log file
        with open(log_file_path, 'w') as log_file:
            log_file.write("Method failed:\n")
            log_file.write(f"Method: {method.__name__}\n")
            log_file.write("Arguments:\n")
            log_file.write(f"Args: {args}\n")
            log_file.write(f"Kwargs: {kwargs}\n")
            log_file.write("\nTraceback:\n")
            traceback.print_exc(file=log_file)
            log_file.write("\nException Message:\n")
            log_file.write(str(e))
            log_file.write("\nStdout:\n")
            log_file.write(sys.stdout.getvalue())
            log_file.write("\StdErr:\n")
            log_file.write(sys.stderr.getvalue())

        resultText = "Error for " + file_name + " see log " + log_file_path
        print("resultText set to:", resultText)
    finally:
        print("finally arrived")
        # Restore original stdout and stderr
        #sys.stdout = original_stdout
        #sys.stderr = original_stderr
        
        print(resultText)
        return result
            
        
    