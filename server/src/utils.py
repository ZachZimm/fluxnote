import os
import json
from typing import Any, Dict, Type
from pydantic import BaseModel
from models.Summary import Summary

def read_config(config_path: str) -> dict: 
    if os.path.exists(config_path):     
        with open(config_path, "r") as file:
            return json.load(file)
    else:
        return {}


def get_all_keys(schema: Dict[str, Any], parent_key: str = '') -> set:
    keys = set()
    if 'properties' in schema:
        for key, value in schema['properties'].items():
            new_key = f"{parent_key}.{key}" if parent_key else key
            keys.add(new_key)
            keys.update(get_all_keys(value, new_key))
    elif 'items' in schema and isinstance(schema['items'], dict):
        keys.update(get_all_keys(schema['items'], parent_key))
    return keys

def parse_llm_output(model_class: Type[BaseModel], llm_output: str) -> Dict[str, Any]:
    result: Dict[str, Any] = {"error": False, "object": None}
    
    try:        
        llm_output = llm_output[llm_output.find('{'):llm_output.rfind('}')+1]
        # Extract the expected keys from the model
        expected_keys = get_all_keys(model_class.model_json_schema())
        
        # Replace keys surrounded by single quotes with double quotes
        for key in expected_keys:
            llm_output = llm_output.replace(f"'{key}'", f'"{key}"')
            print(key)
        llm_output = llm_output.replace('\n', '').replace('\t', '')
        # Replace single quotes within idea strings
        llm_output = llm_output.replace(': \'', ': "').replace('\'}', '"}')

        # this code is specific to the Summary model, it may or may not even be necessary
        if model_class.__name__ == "Summary":
            # Ensure the JSON structure has the required square brackets
            if '[' not in llm_output:
                pre = '{ "summary": ['
                llm_output = pre + llm_output
            if ']' not in llm_output:
                post = ' ] }'
                llm_output = llm_output + post
        
        # Parse the JSON string into a dictionary
        summary_dict = json.loads(llm_output.strip())
        
        # Validate and create the model object
        summary_obj = model_class(**summary_dict)
        
        result["object"] = summary_obj
    
    except Exception as e:
        print(e)
        print(llm_output)
        print("\n\nError parsing summary.")
        result["error"] = True
    
    return result