import json


with open("formatted_data.json", "r") as file:
    json_data = file.read()

json_obj = json.loads(json_data)

with open("channels.txt", 'w') as new_f:
    count = 1
    for data in json_obj['adjacency']:
        if len(data) != 0:
            for elem in data:    
                new_f.write(f"Channel {count}:\n")
                count += 1
                for key, values in elem.items():
                    new_f.write(f"\t{key}: {values}\n")
            
    new_f.close()