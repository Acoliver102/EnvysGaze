import pandas as pd
from Levenshtein import distance
import re


# matches players with previous names
# used because players in this godforsaken game can't use one name
# fuzzy matching helps with OCR errors
def find_closest_match(target, list):
    best_distance = 2
    best_match = target
    for word in list:
        temp_dist = distance(target, word, score_cutoff=1)
        if temp_dist < best_distance:
            print(target + " matched with " + word)
            best_distance = temp_dist
            best_match = word
    return best_match, best_distance


# match in match usernames to known players
# used to keep running stats over a long time
def find_match(name, alias_file, player_pos=-1):
    name = re.sub('[^A-Za-z0-9]+', '', name.upper())

    alias_df = pd.read_csv(alias_file)
    alias_df = alias_df.set_index('name')

    if name in alias_df.index:
        return alias_df.loc[name, 'player']
    else:
        best_name, best_distance = find_closest_match(name, alias_df.index.values.tolist())
        if best_distance < 2 and len(best_name) > 3:
            return alias_df.loc[best_name, 'player']
        else:
            print("No match found for " + name)
            response = input("Create new alias? (y/n)")
            if response.upper() == "Y":
                response = input("To what player?").upper()
                if response in alias_df.index:
                    alias_df.loc[name] = response
                    alias_df.to_csv(alias_file)
                    return response
                else:
                    best_match, best_distance = find_closest_match(response, alias_df.index.values.tolist())
                    if best_distance < 2:
                        alias_df.loc[name] = best_match
                        alias_df.to_csv(alias_file)
                        return best_match
                    print("Could not find player.")
                    return name
            else:
                response = input("Create new profile? (y/n)").upper()
                if response == "Y":
                    print("Creating new profile.")
                    alias_df.loc[name] = name
                    alias_df.to_csv(alias_file)
                    return name
                else:
                    return "UNKNOWN"
        return best_name

