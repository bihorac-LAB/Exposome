# This Manual Directly Gives you the Exact Commands to run from Start to Finish
Copy & Pasting is encouraged!

**DO NOT BE IN A WINDOWS ENVIRONMENT - WSL or LINUX** 

- `git clone https://github.com/bihorac-LAB/Exposome`

## DOCKER Address_to_FIPS.py
- `cd Exposome/Tools/SDOH`
- `mkdir Address-to-fips`
- `mkdir Address-to-fips/input` *<-- place input files here*
- `docker build --no-cache -t exposome-geocode-pipeline .`
- `docker run -it --rm   -v "$(pwd)":/workspace   -v /var/run/docker.sock:/var/run/docker.sock   -e HOST_PWD="$(pwd)"   -w /workspace   exposome-geocode-pipeline   /app/code/Address_to_FIPS.py -i Address-to-fips/input`

Directory names shown above can be modified to your preference. If you decide to change it, then make sure to also modify the path given for the *-i* flag in the docker run command

## Prerequisites
    - Have Docker Desktop downloaded and running 🚢
    - Have WSL or be in a Linux environment 💻