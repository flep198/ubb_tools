from dm_phase import get_dm, _dedisperse_waterfall
import numpy as np
import sys
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from matplotlib.patches import Ellipse
import matplotlib.ticker as mticker
from astropy.cosmology import FlatLambdaCDM
import astropy.units as u

plt.rcParams["font.family"]="Quicksand"
cosmo = FlatLambdaCDM(H0=67.4,Om0=0.315)

file_name=sys.argv[1] #input files to plot
plot_output_folder="." 
redshift=0.13
d_l=float(cosmo.luminosity_distance(redshift).to(u.cm).value)

#import frb file
data=np.load(file_name)
	
wfall=data["wfall"]

burstmetadata = {
    	'dfs': data['dfs'],
    	'DM': data['DM'].item(),
    	'bandwidth': data['bandwidth'].item(),
    	'duration': data['duration'].item(),
 	'center_f': data['center_f'].item(),
    	'freq_unit': data['freq_unit'].item(),
    	'time_unit': data['time_unit'].item(),
    	'int_unit': data['int_unit'].item(),
    	'telescope': data['telescope'].item()
}
                	
t_res = burstmetadata["duration"]/len(wfall[0])
f_channels = burstmetadata["dfs"]

#mask nan values
x = np.linspace(0,burstmetadata["duration"],len(wfall[0]))
y = burstmetadata["dfs"]
x,y = np.meshgrid(x,y)
mask=~np.isnan(wfall)
x_data=x[mask]
y_data=y[mask]
data_values=wfall[mask]
xy_data=np.vstack((x_data,y_data))

f_res=f_channels[1]-f_channels[0]

imshow_data=np.nansum([wfall],axis=0)

#plot the burst
#load RFI channel masks from ar file
mask=np.all(imshow_data!=0,axis=1)

# Summing over the y-axis (frequency) for the top subplot
summed_y = np.average(imshow_data[mask],axis=0)  #Jy
fluence=summed_y.sum()*t_res*1000
observed_bw=np.count_nonzero(mask)*f_res
observed_energy=fluence*1e-6*observed_bw*1e6*1e-23
intrinsic_energy=4*np.pi*d_l**2*observed_energy/(1+redshift)

print("Fluence: " + str(fluence) + " mJy ms")
print("Non flagged bandwidth: "+ str(observed_bw) +" MHz")
print("Observed energy density: " + str(observed_energy) +"erg cm^-2")
print("Intrinsic Radio Energy: " + str(intrinsic_energy) + "erg")

# Summing over the x-axis (time) for the right subplot
summed_x = np.average(imshow_data,axis=1)

# Create the subplots
fig, ax = plt.subplots(2, 1, figsize=(8, 8), 
        gridspec_kw={'width_ratios': [1], 'height_ratios': [1, 4], 'wspace': 0.05, 'hspace': 0.05})

# Main imshow plot
#make sure that flagged channels are not shown
imshow_data[~mask]=0#np.nan
plot_time=burstmetadata["duration"]/2*1000
freq_high=burstmetadata["center_f"]+burstmetadata["bandwidth"]/2
freq_lo=burstmetadata["center_f"]-burstmetadata["bandwidth"]/2
im = ax[1].imshow(imshow_data, extent=(-plot_time,plot_time,freq_high, freq_lo), aspect='auto', cmap='afmhot')#,vmin=0)

#plot flagged channels
flagging=imshow_data
flagging[~mask]=0.35
flagging[mask]=np.nan
flag_im = ax[1].imshow(flagging, extent=(-plot_time,-plot_time+plot_time*0.2,freq_high,freq_lo),aspect='auto',cmap="Greys",vmin=0,vmax=1)#,cmap='RdYlGn')
ax[1].invert_yaxis()
ax[1].set_xlim(-plot_time,plot_time)

# Plot summed data on the top subplot
ax[0].plot(np.linspace(-plot_time,+plot_time,len(summed_y)), summed_y,drawstyle="steps-post",c="black")

# Add x-ticks without labels to ax[0, 0]
ax[0].xaxis.set_ticks_position('bottom')
ax[0].set_xticks(ax[1].get_xticks())
ax[0].set_xticklabels([])
ax[0].set_yticklabels(ax[0].get_yticks(),fontsize=15)
ax[0].set_ylim(summed_y.min(), summed_y.max()*1.1)
ax[0].set_xlim(-plot_time,plot_time)
ax[0].set_xticks([])  # Remove x-axis labels

# Add y-label to ax[0, 0]
ax[0].set_ylabel("Flux Density [mJy]",fontsize=17,fontweight="bold")

# Labels for main plot
ax[1].set_xlabel("Time [ms]",fontsize=17,fontweight="bold")
ax[1].set_ylabel("Frequency [MHz]",fontsize=17,fontweight="bold")
ax[1].set_yticklabels(ax[1].get_yticks(),fontsize=15)
ax[1].set_xticklabels(ax[1].get_xticks(),fontsize=15)

#adjust frame
for spine in ax[0].spines.values():
    spine.set_linewidth(1)  # Set thickness
    spine.set_color('black')  # Set color

for spine in ax[1].spines.values():
    spine.set_linewidth(1.5)
    spine.set_color("black")

#Adjust Ticks
def no_decimals(x,pos):
    return f'{int(x)}'

ax[0].yaxis.set_major_formatter(mticker.FuncFormatter(no_decimals))
ax[1].yaxis.set_major_formatter(mticker.FuncFormatter(no_decimals))

# Adjust layout
plt.tight_layout()

plt.savefig(plot_output_folder+"/plot.pdf",dpi=300)
plt.savefig(plot_output_folder+"/plot.png",dpi=300)
plt.close()
