import os
import threading

def get_files(source_directory, ignore_list):
    
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

def process_file(file, result_directory, rules):
    # Add your code here to modify the file
    print("Processing file:", file)
    result_list = []
    for line in file:
        for rule in rules:
            if rule in line:
                # Modify the line, so the rule is not present
                line = line.replace(rule, "")
        result_list.append(line)
    
    # Write the modified content to a new file in the results directory
    result_file = os.path.join(result_directory, os.path.basename(file))
    with open(result_file, 'w') as file:
        file.writelines(result_list)
        
    print("File processed:", file)

def process_files(files, result_directory, rules):
    threads = []
    for file in files:
        thread = threading.Thread(target=process_file, args=(file,result_directory,rules,))
        thread.start()
        threads.append(thread)

    # Wait for all threads to finish
    for thread in threads:
        thread.join()
  
    # Call the function to check and modify file names
    check_file_names(result_directory, rules)

def check_file_names(result_directory, rules):
    for file_name in os.listdir(result_directory):
        for rule in rules:
            if rule in file_name:
                # Modify the file name, so the rule is not present
                new_file_name = file_name.replace(rule, "")
                old_file_path = os.path.join(result_directory, file_name)
                new_file_path = os.path.join(result_directory, new_file_name)
                os.rename(old_file_path, new_file_path)
                print("File name modified:", file_name, "->", new_file_name)


def __main__():
    
    source_directory = os.path.join(os.getcwd(), 'source')
    results_directory = os.path.join(os.getcwd(), 'results')
    os.makedirs(results_directory, exist_ok=True)
    ignore_list = get_ignore_list()
    rules = get_rules()
    
    file_list = get_files(source_directory, ignore_list)
    
    # Call the function to process the files
    process_files(file_list, results_directory, rules)
        
__main__()
