This is a simulator for a delay-tolerant friend-to-friend network. It was written for the purpose of evaluating the network performance of the anonymous wireless communication scheme [aDTN](https://www.seemoo.tu-darmstadt.de/team/ana-barroso/adtn).

## Instructions

Before you start, place your mobility input file in the input directory (create the directory if it doesn't exist yet). The lines of the file have following format:

    n1 n2 b0*e0 b1*e1 ... b2*e2
    
where n1 and n2 are integers that identify two nodes, and b_ and e_ define the beginning and end times of a contact between the two nodes. Time is an integer, given in seconds. The simulation starts at time 0.

To run the simulation, start by configuring parameters in config.yaml and run the following steps:

1. initialize the data model

        python3 model.py

2. read the mobility input from the input directory and generate the simulation events

        python3 initialize_data.py

3. handle the simulation events in order of occurrence and collect statistics

        python3 simulate.py 

4. process statistics and write them into the data directory (please create one if it doesn't already exist)

        python3 analyze_results.py


## Database connection
If you wish to extend the code, to get a session to the database, simply call:

    from bootstrap import get_mobility_session
    session = get_mobility_session()

## Requirements

- python3
- sqlalchemy
- numpy
- networkx
- the module for the database you will store the data in (we used psycopg2 for postgres)


## Usage in academic work

Please note that any use of the simulator which results in an academic publication or other publication which includes a bibliography must include a citation to this project. Please use the following BibTex citation code:

    @url{warplab-ofdm,
        Author = {Barroso, Ana and Hollick, Matthias},
        Title = {Delay-tolerant friend-to-friend network simulator},
        Url = {http://www.seemoo.tu-darmstadt.de/research/software/f2fdtnsim/}
    }
