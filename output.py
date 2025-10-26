import main
import json

data = main.get_children_nodes("Algebra")


with open("output.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)