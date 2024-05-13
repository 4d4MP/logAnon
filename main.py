import os
import threading
import re

maintain_character_length = True

def get_files(source_directory, ignore_list):
    print("Reading files from: " + source_directory)
    file_list = []

    for root, dirs, files in os.walk(source_directory):
        for file in files:
            file_path = os.path.join(root, file)
            file_list.append(file_path)
            
    # Remove files in ignore list
    for ignore in ignore_list:
        ignore = ignore.strip()
        for file in file_list:
            if file.endswith(ignore):
                file_list.remove(file)
                print("File ignored:", file)
                
    return file_list

def get_ignore_list():
    ignore_list = []
    ignore_file = os.path.join(os.getcwd(), 'ignore.list')
    print(ignore_file)
    with open(ignore_file, 'r') as file:
        ignore_list = file.readlines()

    return ignore_list

def get_rules():
    print("Reading rules from: " + os.path.join(os.getcwd(), 'main.rule'))
    rules_file = os.path.join(os.getcwd(), 'main.rule')
    rules = []
    with open(rules_file, 'r') as file:
        rules = file.readlines()
        
    for rule in rules:
        if rule.startswith("#"):
            rules.remove(rule)
            
            
    print("Rules to be applied:")
    for rule in rules:
        print("      - " + rule)
        
    # Return rules string as regex
    regex_rules = []
    for i in range(len(rules)):
        rule = rules[i].strip()
        regex_rule = re.escape(rule)  # Convert rule to regex expression
        regex_rules.append(regex_rule)
    
    return regex_rules

def process_file(file, result_directory, rules):
    result_list = []
    if file.endswith('.xel'):
        return None
    
    with open(file, 'r') as f:
        lines = f.readlines()
        
    for line in lines:
        for rule in rules:
            #print("Checking for rule:", rule, "in line:", line)
            if re.search(rule, line):
                # Modify the line, so the rule is not present
                print("Rule found in file:", file.split('\\')[-1], "\n    Rule:", rule, "\n    Line:", line)
                line = line.replace(rule, get_replace_str(rule))
                print("Line modified:", line)
        result_list.append(line)
    
    # Write the modified content to a new file in the results directory
    with open(os.path.join(result_directory, os.path.basename(file)), 'w') as file:
        file.writelines(result_list)
        
    print("File processed:", file.name)

def process_files(files, result_directory, rules):
    threads = []
    for file in files:
        if file != None:
            thread = threading.Thread(target=process_file, args=(file,result_directory,rules,))
            thread.name = file + " Thread"
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
                new_file_name = file_name.replace(rule, get_replace_str(rule))
                old_file_path = os.path.join(result_directory, file_name)
                new_file_path = os.path.join(result_directory, new_file_name)
                os.rename(old_file_path, new_file_path)
                print("File name modified:", file_name, "->", new_file_name)

def get_replace_str(rule):
    if maintain_character_length:
        return "*" * len(rule)
    else:
        return ""
        

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
