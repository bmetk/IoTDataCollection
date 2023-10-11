import random
import json
from datetime import datetime, timedelta
import analytics as an
from collections import deque

# Function to generate a random float array with 1024 elements
def generate_float_array():
    return str([round(random.uniform(0, 100), 2) for _ in range(1024)])

# Function to generate a random timestamp

def generate_incremented_timestamp(count):
    #start = datetime(2023, 8, 3, 13, 18, 50)
    #end = start + timedelta(seconds=count * 2)  # Increment time by 2 seconds per count
    return datetime.today()


variables_combined = [
    {"variable": "rpm", "min": 0, "max": 2500},
    {"variable": "tempC", "min": 22, "max": 60},
    {"variable": "cur", "min": 0, "max": 10},
    {"variable": "vibX_fft"},
    {"variable": "vibY_fft"},
    {"variable": "vibZ_fft"},
    {"variable": "vibX_psd"},
    {"variable": "vibY_psd"},
    {"variable": "vibZ_psd"},
    {"variable": "vibX_rms"},
    {"variable": "vibY_rms"},
    {"variable": "vibZ_rms"},
]


combined_deque = deque()

def generate_combined_data(points : int, reset : bool) -> str:
    data = []
    count = 0
    global combined_deque
    if reset:
        reset = False
        combined_deque = deque()
        
    
        
    for variable_info in variables_combined:
        variable_name = variable_info["variable"]
        measurement_name = "lathe"
        
        if "fft" in variable_name:
            value = an.calculate_fft(an.string_to_array(generate_float_array()))
            measurement_name += "_analytics"
        elif "rms" in variable_name:
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
        
        #data.append(entry)
        if len(combined_deque) >= len(variables_combined)*points:
            combined_deque.pop()
        combined_deque.appendleft(entry)
        data = list(combined_deque)
        
        # Convert the data to JSON format
    json_data = json.dumps(data, indent=2)
    return json_data

if __name__ == "__main__":
    with open('./querydata_gen_an.json', 'w') as f:
                #for list in df:
                #    dfAsString += list.to_csv()
        f.write(generate_combined_data())
        f.close()