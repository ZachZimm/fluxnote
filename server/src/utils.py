import os
import re
import json
from typing import Any, Dict, Type
from pydantic import BaseModel
# from models.Summary import Summary

def read_config(config_path: str) -> dict: 
    if os.path.exists(config_path):     
        with open(config_path, "r") as file:
            return json.load(file)
    else:
        return {}

def get_all_keys(schema: Dict[str, Any], parent_key: str = '') -> set: # TODO this still does not get nested keys
    keys = set()                                                    # as far as I can tell
    if 'properties' in schema:
        for key, value in schema['properties'].items():
            new_key = f"{parent_key}.{key}" if parent_key else key
            keys.add(new_key)
            keys.update(get_all_keys(value, new_key))
    elif 'items' in schema and isinstance(schema['items'], dict):
        keys.update(get_all_keys(schema['items'], parent_key))
    return keys

def replace_double_quotes_within_string(json_string):
    pattern = r'(?=[a-z]<![:\[\{])\s*"\s*(?=[a-zA-Z0-9_\.]<![,])\s'
    replacement = "'"
    result = re.sub(pattern, replacement, json_string)
    return result

# This function is only used for the Summary model, maybe it should be renamed and/or moved
def parse_llm_output(model_class: Type[BaseModel], llm_output: str, summary_title: str = "", summary_tags: list[str] = []) -> Dict[str, Any]:
    # This function santizes JSON output from the LLM and returns an object of the model type passed in 
    result: Dict[str, Any] = {"error": False, "object": None}
    try:        
        llm_output = llm_output.replace('"', "'") # Replace all double quotes with single quotes and then replace them back later
        llm_output = llm_output.replace("' }", '"}')
        llm_output = llm_output[llm_output.find('{'):llm_output.rfind('}')+1]
        # Extract the expected keys from the model
        
        llm_output = llm_output.replace('\n', '').replace('\t', '')       
        # Replace keys surrounded by single quotes with double quotes
        

        llm_output = llm_output.strip()
        llm_output = llm_output.replace("\n", " ")
        llm_output = llm_output.replace("\t","")
        llm_output = llm_output.replace("  ", "") # Remove double spaces
        llm_output = llm_output.replace("  ", "") # do it again in case of an odd number of spaces
        llm_output = llm_output.replace("} {", "}, {").replace("}{", "},{") # Add missing commas between objects
        llm_output = llm_output.replace("\\", "") # Remove backslashes
        llm_output = replace_double_quotes_within_string(llm_output) # Replace double quotes within strings

        # Now we need to ensure that the keys and values are enclosed in double quotes
        # First single quote replacement pass, not totally sure what it does anymore, it tried to do eveything
        llm_output = llm_output.replace(': \'', ': "').replace('\'}', '"}').replace("':", '":').replace(":'", ':"')
        # Replace single quotes around inner keys that were missed by the previous step
        llm_output = llm_output.replace('{\'', '{"').replace('\':', '":')#.replace('\',', '",')
        # Replace single quotes around a string with double quotes
        llm_output = llm_output.replace('": \'', '": "').replace('\'}', '"}')
        llm_output = llm_output.replace("' {", '"{')
        
        llm_output = llm_output.replace("' s", "'s") # Fix possessive 's - not sure why this is necessary
        expected_keys = get_all_keys(model_class.model_json_schema())
        for key in expected_keys:
            llm_output = llm_output.replace(f"'{key}'", f'"{key}"')
            llm_output = llm_output.replace(f"'{key}\"", f'"{key}"')
            llm_output = llm_output.replace(f"\"{key}'", f'"{key}"')

        # this code is specific to the Summary model
        if model_class.__name__ == "Summary":
            # find the three most common words with length > 3
            # and use them as the title
            if summary_title == "":
                word_count = {}
                for word in llm_output.split():
                    word = word.strip().replace('"', "").replace("'", "")
                    if len(word) > 3:
                        if word in word_count:
                            word_count[word] += 1
                        else:
                            word_count[word] = 1

                sorted_words = sorted(word_count.items(), key=lambda x: x[1], reverse=True)
                if len(sorted_words) > 1:
                    summary_title = f"{sorted_words[0][0]} {sorted_words[1][0]} {sorted_words[2][0]}"
                else:
                    summary_title = sorted_words[0][0]
            summary_title = summary_title.replace('"', "").replace("'", "")
            # Ensure the JSON structure has the required square brackets, this is not ususally necessary
            if '[' not in llm_output:
                pre = '{ "summary": ['
                llm_output = pre + llm_output
            if ']' not in llm_output:
                post = ' ] }'
                llm_output = llm_output + post
        
        # Parse the JSON string into a dictionary
        summary_dict = json.loads(llm_output.strip())

        # Add the fields that the LLM does not generate in its initial output
        summary_dict["title"] = summary_title
        summary_dict["tags"] = summary_tags
        # Validate and create the model object
        summary_obj = model_class(**summary_dict)
        result["object"] = summary_obj
    
    except Exception as e:
        print(e)
        print(llm_output)
        print("\n\nError parsing summary.")
        result["error"] = True
    
    return result
