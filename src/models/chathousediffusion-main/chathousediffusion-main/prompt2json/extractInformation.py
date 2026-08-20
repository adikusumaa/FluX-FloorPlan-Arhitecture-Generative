from langchain_core.pydantic_v1 import BaseModel, Field, PrivateAttr
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from typing import List, Dict, Optional
from enum import Enum
from openai import OpenAI
import re
import uuid

client = OpenAI(
    base_url ="http://localhost:11434/v1",
    api_key='not-needed', 
)

class RoomType(Enum):
    LivingRoom = "LivingRoom"
    MasterRoom = "MasterRoom"
    Kitchen = "Kitchen"
    Bathroom = "Bathroom"
    DiningRoom = "DiningRoom"
    CommonRoom = "CommonRoom"
    SecondRoom = "SecondRoom"
    ChildRoom = "ChildRoom"
    StudyRoom = "StudyRoom"
    GuestRoom = "GuestRoom"
    Balcony = "Balcony"
    Entrance = "Entrance"
    Storage = "Storage"

class LocationType(Enum):
    north = "north"
    northwest = "northwest"
    west = "west"
    southwest = "southwest"
    south = "south"
    southeast = "southeast"
    east = "east"
    northeast = "northeast"
    center = "center"

class SizeType(Enum):
    XL = "XL"
    L = "L"
    M = "M"
    S = "S"
    XS = "XS"

class Room(BaseModel):
    name: str = Field(description="The name of the room. Ensure it is unique.")
    type: Optional[RoomType] = Field(description="The type of the room.")
    link: list[Optional[str]] = Field(description="The names of the rooms this room is connected to. Make sure two rooms are adjacent.")
    location: Optional[LocationType] = Field(description="The location of the room within the layout. Top represents the north, bottom represents the south.")
    size: Optional[SizeType] = Field(description="The size of the room, calculated as a proportion of the entire layout outline.")

    __id: uuid.UUID = PrivateAttr(default_factory=uuid.uuid4)

    def __hash__(self):
        return self.__id

class FloorPlan(BaseModel):
    rooms: List[Room]

    def __init__(self, rooms):
        super().__init__(rooms=rooms)

    def find_room(self, name):
        for room in self.rooms:
            if room.name == name:
                return room
        return None

    def get_rooms(self):
        return [
            {
                "name": room.name,
                "type": room.type.value if room.type else "Unknown",
                "link": room.link if room.link else "Unknown",
                "location": room.location.value if room.location else "Unknown",
                "size": room.size.value if room.size else "Unknown"
            }
            for room in self.rooms
        ]

extract_template = """\
For the following text, identify and extract information about each room in the floor plan.

text: {text}

{format_instructions}

Please provide the JSON content only.
"""

update_template = """\
Given the existing floor plan and the following additional description, update the floor plan accordingly.

Existing floor plan:
{floor_plan}

Additional description:
{text}

{format_instructions}

Ensure the updated floor plan maintains all previous details unless explicitly modified by the new description. Please provide the JSON content only.
"""

parser = JsonOutputParser(pydantic_object=FloorPlan)
prompt = PromptTemplate(
    template=extract_template,
    input_variables=["text"],
    partial_variables={
        "format_instructions": parser.get_format_instructions()},
)

def extract_json_from_text(text):
    start = text.find('{')
    if start == -1:
        return None
    
    stack = []
    for i in range(start, len(text)):
        if text[i] == '{':
            stack.append('{')
        elif text[i] == '}':
            stack.pop()
            if not stack:
                end = i
                break
    else:
        return None

    json_text = text[start:end + 1]
    return json_text

def clean_and_fix_json(json_text):
    def remove_comments(json_string):
        pattern = r'//.*?(?=\n)|/\*.*?\*/'
        cleaned_string = re.sub(pattern, '', json_string, flags=re.DOTALL)
        return cleaned_string

    def remove_trailing_commas(json_string):
        cleaned_string = re.sub(r',(\s*[}\]])', r'\1', json_string)
        return cleaned_string

    def fix_key_value_pairs(json_string):
        json_string = re.sub(r'"type":\s*"(.*?)"', r'"type": "\1"', json_string)
        json_string = re.sub(r'"location":\s*"(.*?)"', r'"location": "\1"', json_string)
        json_string = re.sub(r'"size":\s*"(.*?)"', r'"size": "\1"', json_string)
        return json_string

    cleaned_json_text = remove_comments(json_text)
    cleaned_json_text = remove_trailing_commas(cleaned_json_text)
    cleaned_json_text = fix_key_value_pairs(cleaned_json_text)

    return cleaned_json_text

def extract_information(floor_plan_description, client = client, model="llama3:instruct"):
    
    formatted_prompt = prompt.format(text=floor_plan_description)
        
    response = client.chat.completions.create(
        model = model,
        messages = [{"role": "user", "content": formatted_prompt}]
    )
    res = response.choices[0].message.content
            
    json_text = extract_json_from_text(res)
    json_text = clean_and_fix_json(json_text)
                
    parsed_json = parser.parse(json_text)
    return str(parsed_json)

def update_floor_plan_with_new_description(original_json_str, new_description, client=client, model="llama3:instruct"):
    new_prompt = PromptTemplate(
        template=update_template,
        input_variables=["floor_plan", "text"],
        partial_variables={
        "format_instructions": parser.get_format_instructions()},
    )

    formatted_prompt = new_prompt.format(floor_plan=original_json_str, text=new_description)
        
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": formatted_prompt}]
    )
    
    res = response.choices[0].message.content
            
    json_text = extract_json_from_text(res)
    json_text = clean_and_fix_json(json_text)
                
    updated_floor_plan = parser.parse(json_text)
    return str(updated_floor_plan)