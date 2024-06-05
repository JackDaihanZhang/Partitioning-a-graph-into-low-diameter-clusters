# Partitioning a graph into low-diameter clusters

This is the GitHub repository for the paper "Partitioning a graph into low-diameter clusters" by Jack Zhang, Lucas Silveira, Hamidreza Validi, Logan Smith, Austin Buchanan, and Illya V. Hicks.

The minimum s-club partitioning problems seeks finding a partition of the vertex set such that the diameter of each part in its corresponding subgraph is at most s. 

The following figures show a minimum 2-club and 3-club partition for the social network of the [Zachary's karate club](https://en.wikipedia.org/wiki/Zachary%27s_karate_club).

 
![Figure 1](readme_images/karate_s2.png?raw=true "a minimum 2-club partition of the karate graph")  ![Figure 2](readme_images/karate_s3.png?raw=true "a minimum 3-club partition of the karate graph")


## Require
To run the code, you will need installations of [Gurobi](https://www.gurobi.com/).

## Run
You can run the code from command line, like this:

```
C:\Linear-size-formulations-for-connected-planar-graph-partitioning-and-political-districting\src>python Main.py config.json 1>>log-file.txt 2>>error-file.txt
```

## config.json
The config file can specify a batch of runs. A particular run might look like this:
* state: AL
* model: Williams
* num_district: 7
* warm_start: false

The config.json file might look like this:
```
{
    "run1": { "state": "AL", "model": "Williams", "num_district": 7, "warm_start": false },
    "run2": { "state": "AR", "model": "Williams", "num_district": 4, "warm_start": false },
    "run3": { "state": "IA", "model": "Williams", "num_district": 4, "warm_start": false },
    "run4": { "state": "KS", "model": "Williams", "num_district": 4, "warm_start": false },
    "run5": { "state": "ME", "model": "Williams", "num_district": 2, "warm_start": false },
    "run6": { "state": "MS", "model": "Williams", "num_district": 4, "warm_start": false },
    "run7": { "state": "NE", "model": "Williams", "num_district": 3, "warm_start": false },
    "run8": { "state": "NM", "model": "Williams", "num_district": 3, "warm_start": false },
    "run9": { "state": "WV", "model": "Williams", "num_district": 2, "warm_start": false },
    "run10": { "state": "ID", "model": "Williams", "num_district": 2, "warm_start": false },
    "run11": { "state": "MT", "model": "Williams", "num_district": 2, "warm_start": false },
    "run12": { "state": "AL", "model": "Hess", "num_district": 7, "warm_start": false },
    "run13": { "state": "AR", "model": "Hess", "num_district": 4, "warm_start": false },
    "run14": { "state": "IA", "model": "Hess", "num_district": 4, "warm_start": false },
    "run15": { "state": "KS", "model": "Hess", "num_district": 4, "warm_start": false },
    "run16": { "state": "ME", "model": "Hess", "num_district": 2, "warm_start": false },
    "run17": { "state": "MS", "model": "Hess", "num_district": 4, "warm_start": false },
    "run18": { "state": "NE", "model": "Hess", "num_district": 3, "warm_start": false },
    "run19": { "state": "NM", "model": "Hess", "num_district": 3, "warm_start": false },
    "run20": { "state": "WV", "model": "Hess", "num_district": 2, "warm_start": false },
    "run21": { "state": "ID", "model": "Hess", "num_district": 2, "warm_start": false },
    "run22": { "state": "MT", "model": "Hess", "num_district": 2, "warm_start": false }
}
```

## Config options
Generally, each run should pick from the following options:
* state : {AL, AK, AZ, AR, CA, ... } 
  * [See list of 2-letter codes](https://en.wikipedia.org/wiki/List_of_U.S._state_and_territory_abbreviations)
* model : {Hess, Williams} 
  * Hess model uses binary variables x_ij that equal one when vertex i is assigned to the district rooted at vertex j
  * Williams employs a linear-size and compact formulation for partitioning a state into districts. It uses flow to capture population balance and compactness.
* num_district
* warm_start : {true, false}
  * If true, will use a warm start obtained from Hess or Williams model
  
## References
In this repository, we employed parts of the following repositories. 

```
Validi, H., & Buchanan, A. (2022). Political districting to minimize cut edges (Version 0.0.1) [Computer software]. https://doi.org/10.5281/zenodo.6374373

Najt, L., & Deford, D. (2019). Face finder [Computer software]. https://github.com/vrdi/NetworksWeek5/blob/master/PlanarEmbeddings/face_finder.py
```
