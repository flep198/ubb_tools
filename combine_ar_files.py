import psrchive
import numpy as np
import matplotlib.pyplot as plt
import sys
import os
import matplotlib
from scipy.stats import skew,kurtosis
import matplotlib.font_manager as fm

plt.rcParams["font.family"]="Quicksand"


plot_time=20 #milliseconds before and after the burst
burst_toa=500 #milliseconds after start of file
freq_downsample=1 #downsampling factor for channels
time_downsample=1 #downsampling factor for time bins
plot_output_folder="plot_folder" #output folder to store plots and .npz dynamic spectra

if not os.path.isdir(plot_output_folder):
    os.system("mkdir "+plot_output_folder)


file_list=sys.argv[1:]
archives=[]
dms=[]
dts=[]
dfs=[]
freq_los=[]
freq_highs=[]
imshow_datas=[]

for archive_file in file_list:
    
    # Load the pulsar archive file
    archive = psrchive.Archive_load(archive_file)

    nbins=len(archive[0].get_Profile(0,0))
    nchan=archive.get_nchan()

    #downsampling
    nchan=int(nchan/freq_downsample)
    nbins=int(nbins/time_downsample)
    archive.fscrunch_to_nchan(nchan)
    archive.bscrunch_to_nbin(nbins)

    archive.dedisperse()
    archive.remove_baseline()

    dm = archive.get_dispersion_measure()
    data = archive.get_data()
    center_freq = archive.get_centre_frequency()

    file_duration=archive[0].get_duration()*1000
    bandwidth=archive.get_bandwidth() #for some reason need /2 here if we have combined two .ar files!!

    dt=file_duration/nbins
    df=bandwidth/archive.get_nchan()

    #calculate start and end indices
    start_t=burst_toa-plot_time
    end_t=burst_toa+plot_time

    start_ind=int(start_t/dt)
    end_ind=int(end_t/dt)

    #calculate lowest and highest frequency
    freq_lo = center_freq - bandwidth/2.0
    freq_high = center_freq + bandwidth/2.0
    
    # Data to be plotted
    imshow_data = data[:,0,:,start_ind:end_ind].mean(0)
    archives.append(archive)
    dms.append(dm)
    dts.append(dt)
    dfs.append(df)
    freq_los.append(freq_lo)
    freq_highs.append(freq_high)
    imshow_datas.append(imshow_data)

if False: #len(np.unique(dfs))>1 or len(np.unique(dts))>1 or len(np.unique(dms))>1:
    print(dts,dfs,dms)
    raise Exception("Please use the same time and frequency sampling for all input files and same DM!")
else:
    #sort archives by frequency
    inds=np.argsort(freq_los)
    archives=np.array(archives)[inds]
    dms=np.array(dms)[inds]
    dts=np.array(dts)[inds]
    dfs=np.array(dfs)[inds]
    freq_los=np.array(freq_los)[inds]
    freq_highs=np.array(freq_highs)[inds]
    imshow_datas=np.array(imshow_datas)[inds]

#append data into one big array
imshow_data=imshow_datas[0]
for i in range(len(archives)-1):
    if freq_highs[i] == freq_los[i+1]:
        #band is continuous, we can simply attach
        imshow_data=np.append(imshow_data,imshow_datas[i+1],axis=0)        
    else:
        #in this case we need to handle a frequency gap between the two bands
        n_diff=int((freq_los[i+1]-freq_highs[i])/df)
        for j in range(n_diff):
            imshow_data=np.append(imshow_data,[np.zeros(end_ind-start_ind)],axis=0)
        imshow_data=np.append(imshow_data,imshow_datas[i+1],axis=0)
        
freq_lo=freq_los[0]
freq_high=freq_highs[-1]
bandwidth=freq_high-freq_lo
  

#load RFI channel masks from ar file
mask=np.all(imshow_data!=0,axis=1)

# Summing over the y-axis (frequency) for the top subplot
summed_y = np.average(imshow_data[mask],axis=0)  #Jy


# Summing over the x-axis (time) for the right subplot
summed_x = np.average(imshow_data,axis=1)


# Create the subplots
fig, ax = plt.subplots(2, 2, figsize=(10, 8), 
                       gridspec_kw={'width_ratios': [4, 1], 'height_ratios': [1, 4], 'wspace': 0.05, 'hspace': 0.05})

# Main imshow plot
#make sure that flagged channels are not shown
imshow_data[~mask]=np.nan
im = ax[1, 0].imshow(imshow_data, extent=(-plot_time, plot_time, freq_high, freq_lo), aspect='auto', cmap='viridis')
ax[1,0].invert_yaxis()

# Plot summed data on the top subplot
ax[0, 0].plot(np.linspace(-plot_time,+plot_time,len(summed_y)), summed_y)

# Add x-ticks without labels to ax[0, 0]
ax[0, 0].xaxis.set_ticks_position('bottom')
ax[0, 0].set_xticks(ax[1,0].get_xticks())
ax[0, 0].set_xticklabels([])
ax[0, 0].set_ylim(0, summed_y.max())
ax[0, 0].set_xlim(-plot_time,plot_time)
ax[0, 0].set_xticks([])  # Remove x-axis labels 
#ax[0, 0].set_title(file_list[0].split("/")[-1])


# Add y-label to ax[0, 0]
ax[0, 0].set_ylabel("Flux Density (mJy)")

# Plot summed data on the right subplot
freq_mask=np.where(summed_x!=0)[0]
ax[1, 1].plot(summed_x[freq_mask], np.linspace(freq_high, freq_lo, summed_x.shape[0])[freq_mask])
ax[1, 1].set_xlabel("Flux Density [mJy]")
ax[1, 1].set_yticks(ax[1,0].get_yticks())
ax[1, 1].set_yticklabels([])
ax[1, 1].set_ylim(ax[1,0].get_ylim())
ax[1, 1].invert_yaxis()

# Labels for main plot
ax[1, 0].set_xlabel("Time [ms]")
ax[1, 0].set_ylabel("Frequency [MHz]")


# Hide the empty top-right subplot
ax[0, 1].axis('off')
ax[1, 1].axis('off')
# Adjust layout
plt.tight_layout()

plt.savefig(plot_output_folder+"/"+file_list[0].split("/")[-1]+".pdf",dpi=300)
plt.savefig(plot_output_folder+"/"+file_list[0].split("/")[-1]+".png",dpi=300)
plt.close()

#Export full UBB snippet as .npz file (e.g. to read with frbgui)

wfall = imshow_data
burstmetadata = {
	'dfs': np.linspace(freq_lo,freq_high,len(imshow_data)), 
	'DM': dms[0],
	'bandwidth': (freq_high-freq_lo),
	'duration': plot_time*2/1000,
	'center_f': (freq_high-freq_lo)/2+freq_lo,
	'freq_unit': "MHz",
	'time_unit': "ms",
	'int_unit': "mJy",
	'telescope':"Effelsberg"
}

np.savez(plot_output_folder+"/"+file_list[0].split("/")[-1]+".npz",wfall=wfall,**burstmetadata)
