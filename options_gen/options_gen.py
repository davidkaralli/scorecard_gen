#!/usr/bin/env python3

import sys
sys.path.append('..')
sys.path.append('.')
import wcif
import options
import argparse
from pathlib import Path

# TODO: configure via argparse

comp_id = 'BASC67SanRamon2025'
# For Devanagari text
#comp_id = 'UCSDFall2024'

def parse_args():
	parser = argparse.ArgumentParser()

	parser.add_argument('comp_id', type=str, metavar='CompID',
						help='ID of the competition, e.g. RocklinWinter2024')

	return parser.parse_args()

def main():
	args = parse_args()

	wcif_json = wcif.download_wcif(args.comp_id)
	options_xlsx_obj = options.OptionsXLSX.init_from_wcif(wcif_json)

	Path(options.OPTIONS_DIR).mkdir(parents=True, exist_ok=True)

	file_name = options.OPTIONS_FILE_STR_FORMAT.format(args.comp_id)

	options_xlsx_obj.create_xlsx(file_name)

if __name__ == '__main__':
	main()
