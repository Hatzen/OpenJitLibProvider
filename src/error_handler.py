import os
import datetime
import traceback
import sys
from io import StringIO

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
    log_dir = os.path.join("/logs", organization, module, version)
    
    # Ensure the target folder exists
    os.makedirs(log_dir, exist_ok=True)
    
    log_file_path = os.path.join(log_dir, f"{file_name}-{timestamp}.txt")
    
    # Backup current stdout and stderr
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    
    # Redirect stdout and stderr to StringIO objects
    sys.stdout = StringIO()
    sys.stderr = StringIO()
    
    try:
        output = method(*args, **kwargs)
        # Write output to log file

        # Restore original stdout and stderr
        sys.stdout = original_stdout
        sys.stderr = original_stderr
        print("Sucess for " + file_name)
        '''
       
        with open(log_file_path, 'w') as log_file:
            log_file.write("Standard Output:\n")
            log_file.write(sys.stdout.getvalue())
            log_file.write("\nStandard Error:\n")
            log_file.write(sys.stderr.getvalue())
            log_file.write("\nResult:\n")
            log_file.write(str(output))
       
       '''
        
        # TODO: Should we remove the long build logs?
        # print(sys.stdout.getvalue())
        print("Sucess for " + file_name)
        return output
            
    except Exception as e:
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

        # Restore original stdout and stderr
        sys.stdout = original_stdout
        sys.stderr = original_stderr
        
            
        print("Error for " + file_name + " see log " + log_file_path)
    