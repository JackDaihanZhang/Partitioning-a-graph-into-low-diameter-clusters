# Partitioning a graph into low-diameter clusters

This is the GitHub repository for the paper "Partitioning a graph into low-diameter clusters" by Jack Zhang, Lucas Silveira, Hamidreza Validi, Logan Smith, Austin Buchanan, and Illya V. Hicks.

The minimum s-club partitioning problems seeks finding a partition of the vertex set such that the diameter of each part in its corresponding subgraph is at most s. 

The following figures show a minimum 2-club and 3-club partition for the social network of the [Zachary's karate club](https://en.wikipedia.org/wiki/Zachary%27s_karate_club).


A minimum 2-club partition             |  A minimum 3-club partition
:-------------------------:|:-------------------------:
![](readme_images/karate_s2.png?raw=true "a minimum 2-club partition of the karate graph")   |  ![](readme_images/karate_s3.png?raw=true "a minimum 3-club partition of the karate graph")


## Requirement
To run the code, you will need to install [Gurobi](https://www.gurobi.com/).

## Run
You can run the code from command line, like this:

```
C:\Partitioning-a-graph-into-low-diameter-clusters\src>python main.py config.json 1>>log-file.txt 2>>error-file.txt
```

## config.json
The config file can specify a batch of runs. A particular run might look like this:
* "Model": "LB+UB"
* "s": 2
* "Instance": "karate"
* "Binary search": false

The config.json file might look like this:
```
{
    "run1": {
        "Model": "LB+UB",
        "s": 2,
        "Instance": "karate",
	"Binary search": false
    },
    "run2": {
        "Model": "LB+UB",
        "s": 2,
        "Instance": "chesapeake",
	"Binary search": false
    },
    "run3": {
        "Model": "LB+UB",
        "s": 2,
        "Instance": "dolphins",
	"Binary search": false
    },
    "run4": {
        "Model": "LB+UB",
        "s": 2,
        "Instance": "lesmis",
	"Binary search": false
    },
    "run5": {
        "Model": "LB+UB",
        "s": 2,
        "Instance": "polbooks",
	"Binary search": false
    },
    "run6": {
        "Model": "LB+UB",
        "s": 2,
        "Instance": "adjnoun",
	"Binary search": false
    },
    "run7": {
        "Model": "LB+UB",
        "s": 2,
        "Instance": "football",
	"Binary search": false
    },
    "run8": {
        "Model": "LB+UB",
        "s": 2,
        "Instance": "jazz",
	"Binary search": false
    },
    "run9": {
        "Model": "LB+UB",
        "s": 2,
        "Instance": "celegansneural",
	"Binary search": false
    },
    "run10": {
        "Model": "LB+UB",
        "s": 2,
        "Instance": "celegans_metabolic",
	"Binary search": false
    },
    "run11": {
        "Model": "LB+UB",
        "s": 2,
        "Instance": "netscience",
	"Binary search": false
    },
    "run12": {
        "Model": "LB+UB",
        "s": 2,
        "Instance": "polblogs",
	"Binary search": false
    },
    "run13": {
        "Model": "LB+UB",
        "s": 2,
        "Instance": "email",
	"Binary search": false
    },
    "run14": {
        "Model": "LB+UB",
        "s": 2,
        "Instance": "data",
	"Binary search": false
    }
}
```

## Config options
Generally, each run should pick from the following options:
* "Problem": {"LB+UB", "Partitioning", "Covering"}
* "Model": {"IP", "APX", "GRE", "ext_label", "Sasha"}
* "s" : any integer greater than or equal to 2
* "Instance": {"karate", "chesapeake", "dolphins", "lesmis", "polbooks","adjnoun",
    "football", "jazz", "celegansneural", "celegans_metabolic",
    "netscience", "polblogs", "email", "data"}
 
