from PBTK import *
import json
import numpy as np
import os
import matplotlib.pyplot as plt
import numpy as np

# Custom serializer for non-serializable data types
def custom_serializer(obj):
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    else:
        raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")

def determine_result(amino_acid, measured_result, ref_db):
    index = amino_acid

    optimal_bottom = ref_db.at[index,'optimal_bottom']
    optimal_up = ref_db.at[index,'optimal_up']
    if optimal_bottom <= measured_result <= optimal_up:
        interpretation_result = ref_db.at[index,'result_optimal']
    elif measured_result <= optimal_bottom :
        interpretation_result = ref_db.at[index,'result_low']
    elif measured_result >= optimal_bottom :
        interpretation_result = ref_db.at[index,'result_high']

    return interpretation_result

def normalize_value(x, min, max):
    """
    Normalize a value x in the range [a, d] to a new range [0, 100].
    
    Parameters:
    - x: The value to normalize.
    - a: The minimum value of the original range.
    - d: The maximum value of the original range.
    
    Returns:
    - The normalized value of x in the range [0, 100].
    """
    # Ensure a < d to avoid division by zero and incorrect normalization
    if max - min == 0:
        raise ValueError("The minimum and maximum values cannot be the same.")
    
    normalized_value = ((x - min) * 100) / (max - min)
    return normalized_value

def create_gauge_chart(measured_result, amino_acid, ref_db, outdir_path):
    index = amino_acid
    reference_range_bottom = ref_db.at[index,'reference_range_bottom']
    optimal_bottom = ref_db.at[index,'optimal_bottom']
    optimal_up = ref_db.at[index,'optimal_up']
    reference_range_up = ref_db.at[index,'reference_range_up']

    value = measured_result
    #normalize_value(measured_result, min=reference_range_bottom, max=reference_range_up)
    
    normalized_reference_range_bottom = normalize_value(reference_range_bottom, min=reference_range_bottom, max=reference_range_up)
    normalized_optimal_bottom = normalize_value(optimal_bottom, min=reference_range_bottom, max=reference_range_up)
    normalized_optimal_up = normalize_value(optimal_up, min=reference_range_bottom, max=reference_range_up)
    normalized_reference_range_up = normalize_value(reference_range_up, min=reference_range_bottom, max=reference_range_up)
    normalized_value = normalize_value(value, min=reference_range_bottom, max=reference_range_up)



    reference_range_bottom = normalized_reference_range_bottom
    optimal_bottom = normalized_optimal_bottom
    optimal_up = normalized_optimal_up
    reference_range_up = normalized_reference_range_up


    regions = {
        "Low": {"range": [reference_range_bottom, optimal_bottom], "color": "#ff0404"},
        "Optimal": {"range": [optimal_bottom, optimal_up], "color": "#70b344"}, #85e62c
        "High": {"range": [optimal_up, reference_range_up], "color": "#ff0404"},
    }

    # Create figure and axis
    fig, ax = plt.subplots(figsize=(10, 1.5))
    ax.set_xlim(reference_range_bottom-2, reference_range_up+2)
    ax.set_ylim(0, 1)

    # Remove y-axis and unnecessary spines
    ax.yaxis.set_visible(False)
    ax.spines[['top', 'right', 'left']].set_visible(False)  # Keep bottom spine for X axis

    # Plot each region
    for region in regions.values():
        ax.barh(0.5, region["range"][1]-region["range"][0], left=region["range"][0], color=region["color"], height=0.5)

    # Set ticks for the region boundaries
    #boundaries = [0] + [region["range"][1] for region in regions.values()]
    #boundaries = [region["range"][1] for region in regions.values()]
    
    boundaries = [reference_range_bottom] + [region["range"][1] for region in regions.values()]
    ax.set_xticks(boundaries)
    ax.set_xticklabels(['','','',''])

    #ax.xaxis.set_visible(False)

    # Assuming the rest of your plot setup code remains the same
    # Determine the minimum and maximum thresholds
    #min_threshold = regions["Low"]["range"][0]
    #max_threshold = regions["High"]["range"][1]

    # Adjust the current value if it's outside the thresholds
    adjusted_value = max(min(normalized_value, reference_range_up), reference_range_bottom)
    #normalized_adjusted_value = normalize_value(adjusted_value, min=reference_range_bottom, max=reference_range_up)
    #adjusted_value = normalized_adjusted_value

    # Calculate total x-axis range
    total_range = reference_range_up - reference_range_bottom  # Since your x-axis goes from 0 to 100

    # Determine marker width as a percentage of the total range
    # For example, making the marker's width 1% of the total range
    marker_width_percent = 1
    #marker_width = (total_range / 100) * marker_width_percent
    marker_width = 1
    # Adjust marker position and width dynamically
    # Note: You might need to adjust the marker's center position slightly to ensure it aligns properly with the value
    
    square_left = adjusted_value - (marker_width / 2)
    triangle_points = [[adjusted_value - (marker_width / 2), 0.25], [adjusted_value + (marker_width / 2), 0.25], [adjusted_value, 0.05]]


    # Create a square with a triangle at the bottom pointing downwards using the dynamic width
    # Square
    ax.add_patch(plt.Rectangle((square_left, 0.25), marker_width, 0.5, color='black'))
    # Triangle pointing downwards
    ax.add_patch(plt.Polygon(triangle_points, color='black'))


    # Display the current value above the marker
    #ax.text(adjusted_value, 1.05, f'Your Result', ha='center', va='center', color='black', fontsize=15)
    ax.text(adjusted_value, 1, value, ha='center', va='center', color='black', fontsize=15, weight='bold')

    ax.text((reference_range_bottom+optimal_bottom)/2, -0.45, 'Low', ha='center', fontsize=15) 
    ax.text((optimal_bottom+optimal_up)/2, -0.45, 'Optimal', ha='center', fontsize=15)
    ax.text((optimal_up+reference_range_up)/2, -0.45, 'High', ha='center', fontsize=15)


    #plt.tight_layout()
    #plt.show()

    image_save_path = os.path.join(outdir_path, amino_acid+"_graph.png")
    plt.savefig(image_save_path, dpi=400, bbox_inches='tight')

def json_create(report_df, ref_db, runfolder, workdir):
    for i in report_df.index:
        #####Create metadata
        report_dict = {'metadata':{},'test_result':{}}
        sample_enumerator = i
        report_dict['metadata']['Nama'] = report_df['nama'][sample_enumerator]

        patient_id = report_df['patient_id'][sample_enumerator]

        report_dict['metadata']['Age'] = report_df['usia'][sample_enumerator]
        report_dict['metadata']['Lab Number'] = report_df['lab_number'][sample_enumerator]
        report_dict['metadata']['Ref. Number'] = report_df['ref_number'][sample_enumerator]

        ##### Create out_folder
        out_folder = os.path.join(runfolder, patient_id)
        
        def get_parent_directory(path):
            return os.path.abspath(os.path.join(path, os.pardir))

        workdir_parent = get_parent_directory(workdir)

        outdir_path = os.path.join(workdir_parent, out_folder)
        # Check if the folder already exists
        if not os.path.exists(outdir_path):
            # Create the folder
            os.makedirs(outdir_path)


        #####Create test_result
        report_dict['test_result']
        for index in ref_db.index:
            report_dict['test_result'][index] = {"test_name":ref_db.at[index,'amino_acid']}
            report_dict['test_result'][index]['type'] = ref_db.at[index,'type']
            try: measured_value = int(report_df[index][sample_enumerator])
            except: measured_value = 0
            report_dict['test_result'][index]['measured_value'] = measured_value
            ref_value = str(ref_db.at[index,'reference_range_bottom']) + ' - '+ str(ref_db.at[index,'reference_range_up'])
            report_dict['test_result'][index]['ref_value'] = ref_value
            report_dict['test_result'][index]['result_interpretation'] = determine_result(amino_acid=index, measured_result=measured_value, ref_db=ref_db)
            ##### Create gauge charts
            create_gauge_chart(measured_result=measured_value, amino_acid=index,ref_db=ref_db,outdir_path=outdir_path)

        json_str = json.dumps(report_dict, indent=4, default=custom_serializer)
        #### Write JSON string to a file
        with open(f'{outdir_path}/{patient_id}_AminoAcidPanel.json', 'w') as file:
            file.write(json_str)