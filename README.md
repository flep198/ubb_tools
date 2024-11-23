
ls

This repository is meant as collection of scripts to deal with timing data produced by the Effelsberg Ultra Broad Band (UBB) receiver. This repository was created to extract dynamic spectra of fast radio bursts combined over all sub-bands of the UBB. If you make use of any of these scripts please cite Eppel et al. 2024 (in prep.).

Requirements:
The python scripts require a couple of standard packages and pulsar software to be installed on your system: [dspsr](https://dspsr.sourceforge.net/), [psrchive](https://psrchive.sourceforge.net/manuals/python/) (python interface), [dm_phase](https://github.com/danielemichilli/DM_phase), matplotlib, numpy, scipy


# Folder Structure

First, the data should be organized in a way that the psrfits-files obtained from the UBB are located in sub-folders for every sub-band, i.e., there should be folders called "search1", "search2", "search3", etc. in your working directory. These folders should contain the psrfits-files of each band and a candidate list following the format used by [TransientX](https://github.com/ypmen/TransientX). Before running any of the scripts in this repository, you need to run a burst search first, e.g., using [TransientX](https://github.com/ypmen/TransientX) to create those candidate files. Your setup should look something like this:

WorkingDirectory/
├── search1/
│   ├─ search1.cands
│   └── UBB_observation_search1.fits (usually multiple files)
├── search2/
│   ├─ search2.cands
│   └─ UBB_observation_search2.fits (usually multiple files)
└─ ......


## Step 1: Combine Candidate Files

Before extracting candidates across the different bands, it is useful to check for overlapping candidates that were detected in more than one band. This can be done with the script **combine_cands.py** which reads in two candidate files and writes a combined candidate file. If there are any overlapping candidates found it will keep the candidate with the highest SNR. It should be run in the following way:

    python3 combine_cands.py input1.cands input2.cands output.cands

In order to combine candidate files of all 5 UBB sub-bands you can simply run this multiple times, e.g. by starting to combine band 1 + 2 like 

	python3 combine_cands.py search1/search1.cands search2/search2.cands combined1+2.cands

and then combining this with the other candidate files subsequently.
> Note: The console output will provide some information on how many matches were found between the candidate files. You can also use the script to combine candidate files from different search strategies in the same band, only keeping the highest SNR detections.

## Step 2: Extracting .ar files

Once you have compiled a final combined candidates file following Step 1, you can extract archive (.ar) file snippets in all sub-bands for every candidate. This is done using the **extract_ar_files.py** script. It is important to set the variable `dspsr_executable` in the beginning of the script, since this script will use `dspsr` to extract the .ar files. Moreover, you can choose the extraction length in seconds around the burst by adjusting the `length` parameter. You will have to choose the input candidate file by adjusting the parameter `input_cands` and you can choose the name of the output directory `output_dir` where all the .ar files will be dumped.

The **extract_ar_files.py** script needs to be run in every sub-band folder separately and will create .ar files for all candidates listed in the `input_cands` candidate file. This can simply be run as:

    python3 extract_ar_files.py

> Note: The extracted .ar files are dedispersed according to the DM given in the `input_cands` file.

## Step 3: Combining .ar files across sub-bands

Now that we have extracted .ar snippets for all candidates in every sub-band, we need to combine them across sub-bands to obtain a full UBB dynamic spectrum. 

>  Note: This can in principle also be done using `psradd` with appropriate flags, however, the frequency gap between search2 and search3 of the UBB receiver causes issues with this approach.

At this stage it is recommended to perform additional calibration steps (polcal, fluxcal, rfi flagging) to the .ar files **before** combining them across sub-bands. 
Combining multiple .ar files across the sub-bands can be done by executing:

    python3 combine_ar_files.py file1.ar file2.ar file3.ar ...

The script will create a plot (.png & .pdf) of the combined spectrum, as well as a a combined .npz numpy array file.

Within the **combine_ar_files.py** script, one can adjust the `plot_time` to extract (milliseconds to use before and after the bursts), `burst_toa` (time of arrival of the burst in milliseconds, relative to the start of the .ar files), `freq_downsample` and `time_downsample` to choose down sampling factors, `plot_output_folder` to specify where a combined plot will be stored.

**Important**: This script assumes that the time and frequency sampling across all .ar files is the same!

## Step 4: Creating nice plots!

While the previous step already creates some plots, there is a dedicated script that reads in the .npz files and creates some more advanced plots and also calculates useful quantities such as the burst fluence and isotropic equivalent energy release, given a redshift. This script is called `plot_frb.py` and can be run in the following way:

    python3 plot_frb.py frb.npz

where `frb.npz` is a numpy archive file created by Step 3. It will output a "plot.pdf" and "plot.png" file, as well some information on burst properties in the terminal. It is important to adjust the `redshift`parameter if you are interested in the energy release. Also note, that the fluence and energy values provided in the terminal output are only valid, if proper flux calibration was performed.


