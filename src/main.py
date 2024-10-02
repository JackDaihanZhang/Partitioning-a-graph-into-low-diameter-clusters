###########################
# Imports
###########################
import networkx as nx
import sys
import time
import heuristic
import json
import os
import read
import lb
import s_club_ext_label
import sasha
from datetime import date
import csv
from csv import DictWriter

#################
# Instances
#################
instances = {
    'karate', 'chesapeake', 'dolphins', 'lesmis', 'polbooks','adjnoun',
    'football', 'jazz', 'celegansneural', 'celegans_metabolic',
    'netscience', 'polblogs', 'email', 'data'
}

###############################################
# Read configs/inputs and set parameters
###############################################
if len(sys.argv) > 1:
    # name your own config file in command line, like this:
    #       python main.py usethisconfig.json
    # to keep logs of the experiments, redirect to file, like this:
    #       python main.py usethisconfig.json 1>>log_file.txt 2>>error_file.txt
    config_filename = sys.argv[1]
else:
    config_filename = 'config.json'  # default

print("Here is the config name: ", config_filename)
print("Reading config from ", config_filename)

config_filename_wo_extension = config_filename.rsplit('.', 1)[0]
configs_file = open(config_filename, 'r')
batch_configs = json.load(configs_file)
configs_file.close()

# create directory for results
path = os.path.join("..", "results_for_" + config_filename_wo_extension)
os.mkdir(path)

# print results to csv file
today = date.today()
today_string = today.strftime("%Y_%b_%d")  # Year_Month_Day, like 2019_Sept_16
results_filename = "../results_for_" + config_filename_wo_extension + "/results_" + config_filename_wo_extension +\
                   "_" + today_string + ".csv"
# Delete the last field
fields = ["Instance", "Problem", "s", "Model", "|V|", "|E|", "LB", "LB Time (seconds)",
          "UB", "UB Time (seconds)", "Total Time (seconds)", "Objective Value", "Objective Bound"]


################################################
# Summarize computational results to csv file
################################################
def append_dict_as_row(file_name, dict_of_elem, field_names):
    # Open file in append mode
    with open(file_name, 'a+', newline='') as write_obj:
        # Create a writer object from csv module
        dict_writer = DictWriter(write_obj, fieldnames=field_names)
        # Add dictionary as a row in the csv
        dict_writer.writerow(dict_of_elem)


# prepare csv file by writing column headers
with open(results_filename, 'w', newline='') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fields)
    writer.writeheader()

############################################################
# Run experiments for each config in batch_config file
############################################################
# Read through the config files to run all instances
for key in batch_configs.keys():
    # Read in the instance configuration
    config = batch_configs[key]
    problem = config['Problem']
    s = config['s']
    base = config['Model']
    instance = config['Instance']
    if problem not in ["Partitioning", "Covering", "LB+UB"]:
        print("Invalid problem.")
        sys.exit()
    if problem == "LB+UB":
        models = False
        UB_mode = base
    else:
        models = True
        UB_mode = "IP"
    if s < 2:
        print("Invalid s.")
        sys.exit()
    print("Solving " + instance + " under " + base + " model:")

    # Start the time counter
    total_start = time.time()

    # Read file
    G_original = read.read_files("../data/", instance)
    print("# of nodes of G: ", len(G_original.nodes))
    print("# of edges of G: ", len(G_original.edges))

    # Find connected components of G
    G_induced_subgraphs = [G_original.subgraph(component) for component in nx.connected_components(G_original)]

    # Initialize final variables
    if problem == "LB+UB":
        obj_Value = "N/A"
        obj_Bound = "N/A"
    else:
        obj_Value = 0
        obj_Bound = 0
    LB = 0
    LB_Time = 0
    UB = 0
    UB_Time = 0

    for iteration in range(len(G_induced_subgraphs)):
        # Display the information of G
        G = nx.convert_node_labels_to_integers(G_induced_subgraphs[iteration])

        # Lower bound
        print("Starting the lower bound calculation")
        H = nx.power(G, s)
        start_indep_set = time.time()
        potential_roots = lb.find_max_indep_set(H)
        stop_indep_set = time.time()
        LB_Time += round(stop_indep_set - start_indep_set, 2)
        LB_iteration = len(potential_roots)
        LB += LB_iteration

        # Upper bound
        print("Starting the upper bound calculation through heuristic")
        start_heur = time.time()
        if s % 2 == 0:
            feasible_partitions = heuristic.calculate_UB_even(G, s, UB_mode, problem)
        else:
            feasible_partitions = heuristic.calculate_UB_odd(G, s, UB_mode, problem)
        finish_heur = time.time()
        UB_iteration = len(feasible_partitions)
        UB_Time += finish_heur - start_heur
        UB += UB_iteration

        # Solve to optimality if the base is not LB+UB
        if problem != "LB+UB":
            if LB_iteration == UB_iteration:
                print("LB = UB in this iteration, and the optimal is found")
                # Add iteration variables to final variables
                obj_Value += LB_iteration
                obj_Bound += LB_iteration
            else:
                # Solve the s-club problem with the selected model
                if base == "ext_label":
                    opt_obj, obj_bound, status = s_club_ext_label.solve_s_club_ext_label(
                        G, s, potential_roots, feasible_partitions, UB_iteration, problem)
                elif base == "Sasha":
                    opt_obj, obj_bound, status = sasha.solve_s_club_with_sasha(G, s, potential_roots,
                                                                               feasible_partitions, UB_iteration, problem)
                else:
                    print("Please enter a correct base model")
                    sys.exit()

                # Add iteration variables to final variables
                obj_Value += opt_obj
                obj_Bound += max(obj_bound, LB_iteration)



    # Finish time counter
    finish_time = time.time()
    total_time = finish_time - total_start

    # Put final results at .csv file
    result = {}
    result["Instance"] = instance
    result["Problem"] = problem
    result["Model"] = base
    result["s"] = s
    result["|V|"] = len(G_original.nodes)
    result["|E|"] = len(G_original.edges)
    result["LB"] = LB
    result["LB Time (seconds)"] = '{0:.2f}'.format(LB_Time)
    result["UB"] = UB
    result["UB Time (seconds)"] = '{0:.2f}'.format(UB_Time)
    result["Total Time (seconds)"] = '{0:.2f}'.format(total_time)
    result["Objective Value"] = obj_Value
    result["Objective Bound"] = obj_Bound
    append_dict_as_row(results_filename, result, fields)
