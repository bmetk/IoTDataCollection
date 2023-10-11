import random
import json
from datetime import datetime, timedelta
import analytics as an

# Function to generate a random float array with 1024 elements
def generate_float_array():
    return str([round(random.uniform(0, 100), 2) for _ in range(1024)])

# Function to generate a random timestamp
def generate_random_timestamp():
    start = datetime(2023, 8, 3, 13, 18, 50)
    end = start + timedelta(seconds=random.randint(1, 3600))  # Random time within an hour
    return end.isoformat()

def generate_incremented_timestamp(count):
    #start = datetime(2023, 8, 3, 13, 18, 50)
    #end = start + timedelta(seconds=count * 2)  # Increment time by 2 seconds per count
    return datetime.today()

# Define the variable names and their value ranges
variables = [
    {"variable": "rpm", "min": 0, "max": 2500},
    {"variable": "tempC", "min": 22, "max": 60},
    {"variable": "cur", "min": 0, "max": 10},
    {"variable": "vibX_fft"},
    {"variable": "vibY_fft"},
    {"variable": "vibZ_fft"}
]
variables_analytics = [
    {"variable": "rpm", "min": 0, "max": 2500},
    {"variable": "tempC", "min": 22, "max": 60},
    {"variable": "cur", "min": 0, "max": 10},
    {"variable": "vibX_psd"},
    {"variable": "vibY_psd"},
    {"variable": "vibZ_psd"},
    {"variable": "vibX_rms"},
    {"variable": "vibY_rms"},
    {"variable": "vibZ_rms"},
]
# Generate the JSON data


def generate_new_data():
    data = []
    count = 0
    for variable_info in variables:
        variable_name = variable_info["variable"]
        measurement_name = "lathe"

        if "vib" in variable_name:
            value = an.calculate_fft(an.string_to_array(generate_float_array()))
            #value = generate_float_array()
            measurement_name += "_analytics"
        elif variable_name == "cur":
            value = str([round(random.uniform(0, 100), 2) for _ in range(3)])
            measurement_name += "_strings"
        else:
            value = random.randint(variable_info["min"], variable_info["max"])

        entry = {
            "result": "_result",
            "table": count,
            "_time": str(datetime.today()) + "+00:00",
            "_value": value,
            "_measurement": measurement_name,
            "variable": variable_name,
        }
        count += 1
        data.append(entry)

        # Convert the data to JSON format
    json_data = json.dumps(data, indent=2)
    return json_data


def generate_new_analytics():
    data = []
    count = 0
    points = 20
    for _ in range(points):    
        for variable_info in variables_analytics:
            variable_name = variable_info["variable"]
            measurement_name = "lathe"
            
            if "rms" in variable_name:
                value = an.calculate_rms(an.string_to_array(generate_float_array()))
                measurement_name += "_analytics"
            elif "psd" in variable_name:
                value = an.get_psd(an.string_to_array(generate_float_array()))
                measurement_name += "_analytics"
            elif variable_name == "cur":
                value = str([round(random.uniform(0, 100), 2) for _ in range(3)])
                measurement_name += "_strings"
            else:
                value = random.randint(variable_info["min"], variable_info["max"])
            


            entry = {
                "result": "_result",
                "table": count,
                "_time": str(datetime.today()) + "+00:00",
                "_value": value,
                "_measurement": measurement_name,
                "variable": variable_name,
            }
            
            data.append(entry)
        count += 1
        # Convert the data to JSON format
    json_data = json.dumps(data, indent=2)
    return json_data

if __name__ == "__main__":
    with open('./querydata_gen_an.json', 'w') as f:
                #for list in df:
                #    dfAsString += list.to_csv()
        f.write(generate_new_analytics())
        f.close()