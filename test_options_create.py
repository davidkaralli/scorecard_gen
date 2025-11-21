#!/usr/bin/env python3

import wcif
import pprint
from options import OptionsXLSX

comp_id = 'WesternChampionship2024'
#comp_id = 'RocklinWinter2024'

file_name = "TestOptions.xlsx"

wcif_json = wcif.download_wcif(comp_id)

options = OptionsXLSX.init_from_wcif(wcif_json)

for key, item in options.options_dict.items():
	name = key
	value = item.value
	description = item.description

options.create_xlsx(file_name)
print(f'Created spreadsheet at {file_name}.')
