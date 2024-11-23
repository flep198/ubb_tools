import os
from astropy.io import fits
import numpy as np
import sys

length=1 #length in seconds to extract around burst
dspsr_executable = "singularity exec -B /hercules/results/feppel/:/data --bind $PWD /hercules/u/feppel/my-singularities_psrppd.sif dspsr" #path to the executabable of dspsr
input_cands="combined_cands.cands"
output_dir="extracted_ar_files"

def get_start_time(psrfits_file):
    try:
        with fits.open(psrfits_file) as hdul:
            header = hdul[0].header
            imjd = header['STT_IMJD']  # MJD integer part
            smjd = header['STT_SMJD']  # Seconds part of MJD day
            offs = header['STT_OFFS']  # Fractional seconds
            
            # Calculate absolute start time in MJD
            start_time_mjd = imjd + (smjd + offs) / 86400.0

            return start_time_mjd
    except Exception as e:
        print(f"Error getting start time for {psrfits_file}:\n{str(e)}")
        return None

def extract_ar_files(input_file, output_directory):
    # Create the output directory if it doesn't exist
    os.makedirs(output_directory, exist_ok=True)
    
    with open(input_file, 'r') as file:
        lines = file.readlines()
        
        for line in lines:
            # Split the line into components
            components = line.split()
            if len(components) < 11:
                continue  # Skip malformed lines
            
            mjd = float(components[2])
            snr = components[5]
            cand_freq = float(components[7])
            dm = components[3]
            psrfits_file = components[10].strip()

            #Determine center frequency of psrfits file
            with os.popen("psrstat -c freq -Q " + psrfits_file) as process:
                output = process.read()
            center_freq=float(output.split()[1])

            with os.popen("psrstat -c bw -Q " + psrfits_file) as process:
                output = process.read()
            bw=float(output.split()[1])

            dm_time_shift=4.15*float(dm)*1e3*(1/center_freq**2-1/cand_freq**2)/60/60/24

            # Get the start time of the observation
            start_time = get_start_time(psrfits_file)
            if start_time is None:
                continue  # Skip if start time could not be determined


            dm_frequency_offset=4.15*1e3*float(dm)*(1/(center_freq+bw/2)**2-1/cand_freq**2) #calculate difference in TOA for different frequency
            # Calculate relative start and end times in seconds
            start_offset = (mjd - start_time) * 86400 - 0.2*length + dm_frequency_offset
            end_offset = (mjd - start_time) * 86400 + 0.8*length + dm_frequency_offset
            
            # Create output file name
            output_file = os.path.join(output_directory, f"{mjd:.10f}_{snr}_{dm}")
            
            # Construct dspsr command
            dspsr_command = [
                dspsr_executable,    
	        "-b", "4096", #set number of bins according to expected intrachannel dispersion smearing (use script ~/intrachannel_dm_smearing.py)
                "-S", "{:.6f}".format(start_offset),
                "-c", "1",
                "-cepoch", "{:.10f}".format(mjd-length/2/86400+dm_time_shift),
                "-T", "1", 
                "-D", dm,
		"-d", "4", #extract all polarizations
                "-e", "ar",
		"--scloffs",
		"-O", output_file,
                psrfits_file
            ]
 
            print(mjd)# Print the dspsr command
            command_str = ' '.join(dspsr_command)
            print(f"Executing dspsr command: {command_str}")
            os.system(command_str)
            
   

if __name__ == "__main__":
    input_file = input_cands 
    output_directory = output_dir
    extract_ar_files(input_file, output_directory)
