import os
import datetime
import traceback
import sys
from io import StringIO
from consts import LOCAL_LOGS_PATH

import threading                                                                
import functools                                                                
import time                                                                     

import os
import datetime
import traceback
import sys
from io import StringIO
from consts import LOCAL_LOGS_PATH

import threading                                                                
import functools                                                                
import time                                                                     

def synchronized(wrapped):                                                      
    lock = threading.Lock()                                                                    
    @functools.wraps(wrapped)                                                   
    def _wrap(*args, **kwargs):                                                 
        with lock:                                                              
            result = wrapped(*args, **kwargs)                                   
            return result                                                       
    return _wrap                                                                


@synchronized   
def log_method_output(method, args=None, kwargs=None, organization="", repo="", *extra):
    """
    Executes a method and logs its output and errors to a file while preventing stdout and stderr output to the console.

    Supports both signatures:
    - (method, args, kwargs, organization, repo, version, file_name)
    - (method, args, kwargs, organization, repo, module, version, file_name)
    """
    if args is None:
        args = ()
    if kwargs is None:
        kwargs = {}

    module = ""
    version = ""
    file_name = "build"

    if len(extra) == 2:
        version, file_name = extra
    elif len(extra) == 3:
        module, version, file_name = extra
    elif len(extra) > 3:
        module = extra[0]
        version = extra[1]
        file_name = extra[2]

    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    if module and module != repo:
        log_dir = os.path.join(LOCAL_LOGS_PATH, organization, repo, module, version)
    else:
        log_dir = os.path.join(LOCAL_LOGS_PATH, organization, repo, version)
    
    os.makedirs(log_dir, exist_ok=True)
    log_file_path = os.path.join(log_dir, f"{file_name}-{timestamp}.txt")

    original_stdout = sys.stdout
    original_stderr = sys.stderr
    sys.stdout = StringIO()
    sys.stderr = StringIO()

    result = None
    try:
        result = method(*args, **kwargs)
    except Exception as e:
        with open(log_file_path, 'w', encoding='utf-8') as log_file:
            log_file.write("Method failed:\n")
            log_file.write(f"Method: {method.__name__}\n")
            log_file.write(f"Args: {args}\n")
            log_file.write(f"Kwargs: {kwargs}\n")
            log_file.write("\nTraceback:\n")
            traceback.print_exc(file=log_file)
            log_file.write("\nException Message:\n")
            log_file.write(str(e) + "\n")
            log_file.write("\nStdout:\n")
            log_file.write(sys.stdout.getvalue())
            log_file.write("\nStderr:\n")
            log_file.write(sys.stderr.getvalue())
        print(f"Error for {file_name}, see log at {log_file_path}", file=original_stderr)
    finally:
        sys.stdout = original_stdout
        sys.stderr = original_stderr
        return result

            
        
    