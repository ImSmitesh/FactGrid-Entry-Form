import requests
from urllib.parse import quote
import json
import os

ids = ['Q16200', 'Q11295', 'Q704192', 'Q141469', 'Q8', 'Q153166']

def fetch_items_by_pid(pid, save_path=None):
    endpoint = "https://database.factgrid.de/sparql"
    
    sparql = f"""
    PREFIX fg: <https://database.factgrid.de/entity/>
    PREFIX fgt: <https://database.factgrid.de/prop/direct/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

    SELECT DISTINCT ?item ?itemLabel WHERE {{
      {{ ?item fgt:P2 fg:{pid} }} 
      UNION 
      {{ ?item fgt:P3 fg:{pid} }} .
      ?item rdfs:label ?itemLabel .
      FILTER(LANG(?itemLabel) = "en")
    }}
    """

    headers = {"Accept": "application/sparql-results+json"}
    url = f"{endpoint}?query={quote(sparql)}"

    resp = requests.get(url, headers=headers)
    resp.raise_for_status()

    data = resp.json()
    
    results = [(b["item"]["value"].rsplit("/", 1)[-1], b["itemLabel"]["value"])
               for b in data["results"]["bindings"]]

    #print(results[:5])
    
    if save_path:
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
            #print(f'{idx}.json saved')
    
    return results


for idx in ids:
    save_file = f'../static/data/{idx}.json' 
    items = fetch_items_by_pid(idx, save_path=save_file)
