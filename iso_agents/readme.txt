ISO_AGENTS USAGE

Assuming project name is 'montage', experiment name is 'bbb105'.

Step 1: Log in to users
ssh <username>@users.isi.deterlab.net

Step 2: From users, log in to clientnode-1 in the experiment network
ssh clientnode-1.bbb105.montage.isi.deterlab.net

Step 4: cd to the experiment directory
cd /proj/montage/magi-modules/iso_agents/

Step 3: Generate config files for 'scenario 2', which is the 105-agent scenario
cd config/
python configure_scenario.py input/scenario2_vpp.csv input/scenario2_params.csv output/star105.tcl output/star105.aal output/star105.json
[This will generate the necessary AAL and JSON config files with the paths given at the command line -- the TCL file is irrelevant at this point.]

Step 5: Orchestrate
Assuming you're still in config,
magi_orchestrator.py --project montage --experiment bbb105 --events output/star105.aal

Step 6: Compare experimental results to reference files
cd ../test/
python compare_results.py reference-files/scenario2_combined_output.csv montage bbb105
[This will generate a basic output comparing all 6 stats at each output]

Step 7: Export CSV for viewing [optional]
Assuming you're still in /proj/montage/magi-modules/iso_agents/test/
python compare_results.py export <output file name> montage bbb105

Step 8: Explore the data with pymongo
from pymongo import MongoClient
db = MongoClient('localhost', 27018)['magi']['experiment_data']
# Then you can run arbitrary queries like:
x = db.find({"agent": "iso_server_agent", "t": 9, "statsType": "iso_stats"})