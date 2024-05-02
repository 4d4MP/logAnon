import os
import threading

def get_files(ignore_list):
    source_directory = os.path.join(os.getcwd(), 'source')
    
    print("Reading files from: " + source_directory)
    file_list = []

    for root, dirs, files in os.walk(source_directory):
        for file in files:
            if not any(file.endswith(ignore) for ignore in ignore_list):
                file_path = os.path.join(root, file)
                file_list.append(file_path)
            else:
                print("Ignoring file: " + file)

    return file_list

def get_ignore_list():
    ignore_list = []
    ignore_file = os.path.join(os.getcwd(), 'ignore.list')
    print(ignore_file)
    with open(ignore_file, 'r') as file:
        ignore_list = file.readlines()

    return ignore_list

def get_rules():
    rules_file = os.path.join(os.getcwd(), 'main.rule')
    rules = []
    with open(rules_file, 'r') as file:
        rules = file.readlines()
    return rules

def process_file(file):
    # Add your code here to modify the file
    print("Processing file:", file)

def process_files(files):
    threads = []
    for file in files:
        thread = threading.Thread(target=process_file, args=(file,))
        thread.start()
        threads.append(thread)

    # Wait for all threads to finish
    for thread in threads:
        thread.join()
        
    ## TODO: Check file names and modify them as per the rules



def __main__():
    files = get_files(get_ignore_list())
    for file in files:
        #print(file)
        continue
    
    # Call the function to process the files
    process_files(files)
        
__main__()
