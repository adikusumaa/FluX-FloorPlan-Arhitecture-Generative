import json
import random
import re
from fuzzywuzzy import fuzz
from fuzzywuzzy import process

probabilities = {
    "ChildRoom": 0.032,
    "StudyRoom": 0.125,
    "SecondRoom": 0.836,
    "GuestRoom": 0.007
}

class FormatErrorException(Exception):
    pass

def choose_new_type():
    return random.choices(list(probabilities.keys()), list(probabilities.values()))[0]

def convert_quotes(json_string):
    return json_string.replace("'", '"')

def normalize_string(s):
    normalized = re.sub(r'\W+', '', s).lower()
    return normalized if normalized else s

def find_and_replace(target, string_list):
    if not isinstance(target, str):
        target = str(target)
    
    normalized_target = normalize_string(target)
    
    sorted_string_list = sorted(string_list, key=lambda x: len(normalize_string(x)), reverse=True)

    for item in sorted_string_list:
        normalized_item = normalize_string(item)
        if normalized_item in normalized_target:
            target = item
            return True, target
    
    return False, target

def get_best_match(target, string_list, threshold=60):

    preprocessed_target = normalize_string(target)

    if not preprocessed_target.strip():
        return False, "Unknown" 
    
    preprocessed_choices = [normalize_string(choice) for choice in string_list]
    best_match = process.extractOne(preprocessed_target, preprocessed_choices, scorer=fuzz.token_set_ratio)
    
    if best_match[1] >= threshold:
        return True, string_list[preprocessed_choices.index(best_match[0])]
    else:
        return False, target

def check_json_format(json_data):
    """
    Check if the input JSON data conforms to the specified format requirements.
    
    Args:
    - json_data (dict): Input JSON data to be checked.
    
    Returns:
    - bool: True if the JSON data conforms to the specified format, False otherwise.
    """
    # Define lists of valid room types, locations, and sizes
    valid_room_types = ["LivingRoom", "MasterRoom", "Kitchen", "Bathroom", "DiningRoom", 
                        "ChildRoom", "StudyRoom", "SecondRoom", "GuestRoom", "Balcony", 
                        "Entrance", "Storage", "Unknown", "CommonRoom"]
    valid_locations = ["north", "northwest", "west", "southwest", "south", "southeast", 
                       "east", "northeast", "center", "Unknown"]
    valid_sizes = ["XL", "L", "M", "S", "XS", "Unknown"]
    
    # Iterate through each room in the JSON data
    if 'rooms' not in json_data:
        return False
    
    # Collect all room names for link validation
    room_names = {room.get('name', "") for room in json_data['rooms']}


    for room in json_data['rooms']:
        # Check if the room type is valid
        if 'type' not in room:
            return False
        
        found, room['type'] = get_best_match(room['type'], ["CommonRoom"])
        if found:
            room['type'] = choose_new_type()
        else:
            found, room['type'] = get_best_match(room['type'], valid_room_types)
            if not found:
                room['type'] = "Unknown"
        
        # Check if the location is valid
        room.setdefault('location', "")
        found, room['location'] = get_best_match(room['location'], valid_locations)
        if not found:
            room['location'] = "Unknown"

        # Check if the size is valid
        room.setdefault('size', "")
        found, room['size'] = get_best_match(room['size'], valid_sizes)
        if not found:
            room['size'] = "Unknown"
        
        # Fill in empty strings for attributes without values
        room.setdefault('link', "")

        # Validate the links
        # if isinstance(room['link'], list):
        #     new_links = []
        #     for link in room['link']:
        #         matched_link, res = get_best_match(link, list(room_names), threshold=60)
        #         if matched_link:
        #             new_links.append(res)
        #     room['link'] = new_links
        
    return True

def convert_json_string(input_json_string):
    """
    Convert the input JSON string to match the structure of JsonFormatExample.json.
    
    Args:
    - input_json_string (str): Input JSON string.
    
    Returns:
    - str: Transformed JSON string matching the structure of JsonFormatExample.json.
    """
    # Convert the input JSON string to a Python dictionary
    print(input_json_string)
    input_json_string = convert_quotes(input_json_string)
    input_data = json.loads(input_json_string)

    if input_data.get('properties'):
        input_data = input_data['properties']
    
    # Check the format of the input JSON data
    if not check_json_format(input_data):
        raise FormatErrorException(f"Failed format check.")
    
    # Process the input data and convert it to the desired format
    transformed_data = convert_json_file(input_data)
    
    # Convert the transformed data to a JSON string
    output_json_string = json.dumps(transformed_data, indent=2)
    
    return output_json_string

def convert_json_file(input_data):
    """
    Convert the input JSON data to match the structure of JsonFormatExample.json.
    
    Args:
    - input_data (dict): Input JSON data.
    
    Returns:
    - dict: Transformed data matching the structure of JsonFormatExample.json.
    """
    # Define a dictionary to map room types from JsonOutputByLLM.json to the corresponding types in JsonFormatExample.json
    room_type_mapping = {
        "LivingRoom": "LivingRoom",
        "MasterRoom": "MasterRoom",
        "Kitchen": "Kitchen",
        "ChildRoom": "ChildRoom",
        "GuestRoom": "GuestRoom",
        "SecondRoom": "SecondRoom",
        "StudyRoom": "StudyRoom",
        "Bathroom": "Bathroom",
        "DiningRoom": "DiningRoom",
        "Balcony": "Balcony",
        "Entrance": "Entrance",
        "Storage": "Storage",
        "Unknown": "Unknown"
    }
    
    # Initialize an empty dictionary to hold the transformed data
    transformed_data = {}
    
    # Iterate through each room in the input data
    for room in input_data['rooms']:
        # Get the type of the current room
        room_type = room['type']
        
        # Check if the room type is present in the room_type_mapping
        if room_type in room_type_mapping:
            # If the room type is present, get the corresponding type from JsonFormatExample.json
            new_room_type = room_type_mapping[room_type]
            
            # Create a new room dictionary with the required fields
            new_room = {
                "name": room['name'],
                "link": [],
                "location": room['location'],
                "size": room['size']
            }
            
            # If the room has a link, add it to the new room's link list
            if room['link'] is not None:
                new_room['link'].append(room['link'])
            
            # Check if the new room type is already present in the transformed data dictionary
            if new_room_type in transformed_data:
                # If present, append the new room to the list of rooms under the corresponding type
                transformed_data[new_room_type]['rooms'].append(new_room)
                # Increment the number of rooms of the corresponding type
                transformed_data[new_room_type]['num'] += 1
            else:
                # If not present, create a new entry for the new room type
                transformed_data[new_room_type] = {
                    "num": 1,
                    "rooms": [new_room]
                }
    
    # Delete room types whose num is 0 in the roommap
    for room_type, room_data in transformed_data.items():
        if room_data['num'] == 0:
            del transformed_data[room_type]
    
    return transformed_data