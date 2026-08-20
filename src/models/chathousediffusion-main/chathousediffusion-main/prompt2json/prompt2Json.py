from .jsonFormatting import convert_json_string
from .extractInformation import extract_information
from .extractInformation import update_floor_plan_with_new_description
from .extractInformation import client
import os
from datetime import datetime

def save_string_to_file(string, folder_path):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    file_name = f"{timestamp}.txt"
    file_path = os.path.join(folder_path, file_name)
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(string)

def prompt2json(prompt, client=client, model="llama3:instruct"):

    # Call the functions to process the input and convert it into a JSON-formatted string
    structured_data = extract_information(prompt, client=client, model=model)

    # save_string_to_file(structured_data, 'IntermediateRes')

    json_string = convert_json_string(structured_data)

    return json_string, structured_data

def updatePrompt(original_json_str, new_description, client=client, model="llama3:instruct"):
    # Call the function to update the JSON with the new description
    updated_json = update_floor_plan_with_new_description(original_json_str, new_description, client=client, model=model)

    json_string = convert_json_string(updated_json)

    return json_string, updated_json