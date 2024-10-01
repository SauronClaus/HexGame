import json
import pandas as pd
import numpy as np

# Load the JSON data
with open('Maps/TestMap.json', 'r') as file:
    data = json.load(file)


# Structure (City)
# Structure (Farm)
# Structure (Fortress)
# Structure is Player 0?
# Structure is Player 1?
# Terrain is Grasslands?
# Terrain is Hills?
# Terrain is Mountains?
# Terrain is Forest?
# Terrain is Water?
# Fog Level (Player 0) is 2
# Fog Level (Player 0) is 1
# Fog Level (Player 0) is 0
# Fog Level (Player 1) is 2
# Fog Level (Player 1) is 1
# Fog Level (Player 1) is 0
# Unit 1 is a Phalanx
# Unit 1 is a Cavalry
# Unit 1 is an Archer
# Unit 1 is a Garrison
# Unit 1 is owned by Player 0?
# Unit 1 is owned by Player 1?
# Unit 1 has four moves remaining?
# Unit 1 has three moves remaining?
# Unit 1 has two moves remaining?
# Unit 1 has one move remaining?
# Unit 1 has zero moves remaining
# Unit 2 is a Phalanx...

# Suggestion: Encode cavalry/archer/units and structures with the player as the leading bit and as separate for each


# Define the features
features = [
    "Structure (City)", "Structure (Farm)", "Structure (Fortress)",
    "Structure is Player 0?", "Structure is Player 1?",
    "Terrain is Grasslands?", "Terrain is Hills?", "Terrain is Mountains?",
    "Terrain is Forest?", "Terrain is Water?",
    "Fog Level (Player 0) is 2", "Fog Level (Player 0) is 1", "Fog Level (Player 0) is 0",
    "Fog Level (Player 1) is 2", "Fog Level (Player 1) is 1", "Fog Level (Player 1) is 0",
    "Unit 1 is a Phalanx", "Unit 1 is a Cavalry", "Unit 1 is an Archer", "Unit 1 is a Garrison",
    "Unit 1 is owned by Player 0?", "Unit 1 is owned by Player 1?",
    "Unit 1 has four moves remaining?", "Unit 1 has three moves remaining?",
    "Unit 1 has two moves remaining?", "Unit 1 has one move remaining?",
    "Unit 1 has zero moves remaining", "Unit 2 is a Phalanx", "Unit 2 is a Cavalry", "Unit 2 is an Archer", "Unit 2 is a Garrison",
    "Unit 2 is owned by Player 0?", "Unit 2 is owned by Player 1?",
    "Unit 2 has four moves remaining?", "Unit 2 has three moves remaining?",
    "Unit 2 has two moves remaining?", "Unit 2 has one move remaining?",
    "Unit 2 has zero moves remaining", "Unit 3 is owned by Player 0?", "Unit 3 is owned by Player 1?",
    "Unit 3 has four moves remaining?", "Unit 3 has three moves remaining?",
    "Unit 3 has two moves remaining?", "Unit 3 has one move remaining?",
    "Unit 3 has zero moves remaining",  "Unit 4 is owned by Player 0?", "Unit 4 is owned by Player 1?",
    "Unit 4 has four moves remaining?", "Unit 4 has three moves remaining?",
    "Unit 4 has two moves remaining?", "Unit 4 has one move remaining?",
    "Unit 4 has zero moves remaining",  "Unit 5 is owned by Player 0?", "Unit 5 is owned by Player 1?",
    "Unit 5 has four moves remaining?", "Unit 5 has three moves remaining?",
    "Unit 5 has two moves remaining?", "Unit 5 has one move remaining?",
    "Unit 5 has zero moves remaining",  "Unit 6 is owned by Player 0?", "Unit 6 is owned by Player 1?",
    "Unit 6 has four moves remaining?", "Unit 6 has three moves remaining?",
    "Unit 6 has two moves remaining?", "Unit 6 has one move remaining?",
    "Unit 6 has zero moves remaining",  "Unit 7 is owned by Player 0?", "Unit 7 is owned by Player 1?",
    "Unit 7 has four moves remaining?", "Unit 7 has three moves remaining?",
    "Unit 7 has two moves remaining?", "Unit 7 has one move remaining?",
    "Unit 7 has zero moves remaining",  "Unit 8 is owned by Player 0?", "Unit 8 is owned by Player 1?",
    "Unit 8 has four moves remaining?", "Unit 8 has three moves remaining?",
    "Unit 8 has two moves remaining?", "Unit 8 has one move remaining?",
    "Unit 8 has zero moves remaining"
]

# Create the list of dictionaries with one-hot encoded features
encoded_data = []
for hex in data['hexes']:
    hex_dict = {feature: 0 for feature in features}
    # Encode structure
    if hex['structure_type'] != "None":
        structure, player = hex['structure_type'].split('|')
        if structure == "City":
            hex_dict["Structure (City)"] = 1
        elif structure == "Farm":
            hex_dict["Structure (Farm)"] = 1
        elif structure == "Fortress":
            hex_dict["Structure (Fortress)"] = 1
        if player == '0':
            hex_dict["Structure is Player 0?"] = 1
        else:
            hex_dict["Structure is Player 1?"] = 1

    # Encode terrain
    hex_dict[f"Terrain is {hex['terrain_type']}?"] = 1

    # Encode fog levels
    hex_dict[f"Fog Level (Player 0) is {hex['fog'][0]}"] = 1
    hex_dict[f"Fog Level (Player 1) is {hex['fog'][1]}"] = 1

    # Encode units
    if hex['units']:
        unit, player, moves = hex['units'][0].split('|')
        hex_dict[f"Unit 1 is a {unit}"] = 1
        if player == '0':
            hex_dict["Unit 1 is owned by Player 0?"] = 1
        else:
            hex_dict["Unit 1 is owned by Player 1?"] = 1
        hex_dict[f"Unit 1 has {moves} moves remaining?"] = 1

    encoded_data.append(hex_dict)

# Convert to DataFrame
df = pd.DataFrame(encoded_data)

# Save the DataFrame to a file
df.to_csv('Maps/EncodedMap.csv', index=False)