#!/usr/bin/env python3

import wcif
import pprint
from options import OptionsXLSX

options = OptionsXLSX.init_from_xlsx("TestOptions.xlsx")

for key, item in options.options_dict.items():
	name = key
	value = item.value
	description = item.description

	print(f"{name}, {value}, {description}")
	print()
