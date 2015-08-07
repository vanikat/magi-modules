ISO_AGENTS SETUP

Step 1: Create raw experiment...
[ TO be completed...]

Step 2: Create containerized experiment
Create a new containerized experiment by running:
/share/containers/containerize.py montage <experiment name> /proj/montage/exp/BBBMagi105/tbdata/nsfile.ns --packing=12 --openvz-diskspace 15G --pnode-type MicroCloud,pc2133

Step 2: Ensure the agent code is in proper directory
From within your clone of the magi-modules repo you can run:
scp -r ./iso_agents/ <username>@users.isi.deterlab.net:/proj/montage/magi-modules/

Step 3: Generate config files for 'scenario 2'
cd /proj/montage/magi-modules/iso_agents/config/
python configure_scenario.py input/scenario2_vpp.csv input/scenario2_params.csv output/star100.tcl output/star100.aal output/star100.json
[This will generate the necessary AAL and JSON config files with the paths given at the command line -- the TCL file is irrelevant at this point.]

Step 4: Modify AAL for containerized agents
[This is where I need your help.]
Modify the contents of output/star100.aal as necessary.

Step 5: Orchestrate
python /share/magi/current/magi_orchestrator.py --project montage --experiment <experiment name> --events /proj/montage/magi-modules/iso_agents/output/star100.aal
[Assuming you used the same command-line args for your output file paths]

Step 6: Compare experimental results to reference files
cd /proj/montage/magi-modules/iso_agents/test/
python compare_results.py reference-files/scenario2_combined_output.csv montage <experiment name>
[This will generate a basic output comparing all 6 stats at each output]

Step 7: Export CSV for viewing [optional]
Assuming you're still in /proj/montage/magi-modules/iso_agents/test/
python compare_results.py export <output file path> montage BBBMagi105C