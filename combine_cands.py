import sys
import numpy as np

def read_data_from_file(filename):
    data = []
    with open(filename, 'r') as file:
        for line in file:
            components = line.split()
            if len(components) < 11:
                continue  # Skip malformed lines
            mjd = float(components[2])
            snr = float(components[5])
            dm = components[3]
            psrfits_file = components[10]
            freq = float(components[7])
            data.append((mjd, snr, dm, psrfits_file, line,freq))
    return data

def combine_files(data1, data2, tolerance=0.2/86400):
    combined_data = []
    overlap_count = 0
    
    all_data = data1 + data2
    all_data.sort(key=lambda x: x[0])  # Sort by MJD

    used_indices = set()
    snr_highest_entries = {}  # Track highest SNR entries for overlaps
    
    for i, current_entry in enumerate(all_data):
        if i in used_indices:
            continue  # Skip already processed entries
        
        mjd, snr, dm, psrfits_file, line, freq= current_entry
        overlap_found = False

        # Check for overlaps within the tolerance window
        for j in range(i + 1, len(all_data)):
            if j in used_indices:
                continue  # Skip already processed entries

            next_entry = all_data[j]
            next_mjd, next_snr, next_dm, next_psrfits_file, next_line , next_freq = next_entry

            #correct MJD to the same frequency
            next_mjd_corr = next_mjd + 4.15*float(next_dm)*1e3*(1/freq**2-1/next_freq**2)/60/60/24

            if np.abs(next_mjd_corr - mjd) <= tolerance:
                print("Overlap at MJD " + "{:.10f}".format(mjd) + " ("+ str(freq)+" MHz)"+"\n"+"{:.10f}".format(next_mjd) + " ("+str(next_freq)+" MHz)")
                overlap_found = True
                if next_snr > snr:
                    current_entry = next_entry
                    mjd, snr, dm, psrfits_file, line, freq = current_entry
                overlap_count += 1
                used_indices.add(j)
            else:
                break
        
        combined_data.append(current_entry)
        used_indices.add(i)

    # Ensure all data is included without duplicates
    combined_data = list(dict.fromkeys(combined_data))

    return combined_data, overlap_count

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python combine_files.py <file1> <file2> <output_file>")
        sys.exit(1)

    file1 = sys.argv[1]
    file2 = sys.argv[2]
    output_file = sys.argv[3]

    data1 = read_data_from_file(file1)
    data2 = read_data_from_file(file2)
    
    combined_data, overlap_count = combine_files(data1, data2)
    
    with open(output_file, 'w') as out_file:
        for entry in combined_data:
            out_file.write(entry[4])
    
    print(f"Combined data written to {output_file}")
    print(f"Number of overlaps found: {overlap_count}")
    print(f"Number of lines in {file1}: {len(data1)}")
    print(f"Number of lines in {file2}: {len(data2)}")
    print(f"Number of lines in combined output: {len(combined_data)}")

