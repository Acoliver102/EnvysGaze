from pathlib import Path

import pandas as pd
import shutil
import datetime

from nameCleanup import *
from kdaFromScoreboard import *

root_name = "gigantic"


# process for maintaining a set of stat files
def add_new_sb(sb_file):
    # convert file to fata
    data_new = image_to_dataframe(sb_file)

    # read in old data
    master_kda = pd.read_csv(f'statsheets/{root_name}_kda_master.csv')
    master_kda = master_kda.set_index('player')

    master_stats = pd.read_csv(f'statsheets/{root_name}_stats_master.csv', index_col=[0])

    # match new player names to old ones
    data_new['player'] = data_new.apply(lambda row: find_match(row['player'], 'aliases.csv'), axis=1)

    # update lifetime stats
    for index, row in data_new.iterrows():
        if not row['player'] in master_kda.index:
            master_kda.loc[row['player']] = 0

        master_kda.loc[row['player'], 'kills'] += row['kills']
        master_kda.loc[row['player'], 'deaths'] += row['deaths']
        master_kda.loc[row['player'], 'assists'] += row['assists']
        master_kda.loc[row['player'], 'games'] += 1

    # add scoreboard data
    master_stats = pd.concat([master_stats, data_new], ignore_index=True)
    master_stats.to_csv(f'statsheets/{root_name}_stats_master.csv')

    master_kda.to_csv(f'statsheets/{root_name}_kda_master.csv')

    print("Finished adding scoreboard: " + sb_file)


# get all unprocessed images
directory = f"{root_name}Unprocessed"

files = Path(directory).glob('*')

# timestamp batch to avoid writing over old files
batch_time = datetime.datetime.now()
batch_tag = str(batch_time.year) + "-" + str(batch_time.month) + "-" + str(batch_time.day) + "-" + str(
    batch_time.hour) + "-" + str(batch_time.minute)

# move processed files to long term storage
for file in files:
    add_new_sb(file.as_posix())
    shutil.move(file.as_posix(), f'{root_name}Processed/' + batch_tag + file.name)
