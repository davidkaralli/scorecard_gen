#!/usr/bin/env python3
import sys
import os

import wcif
import scorecards

sys.path.append('pdf_gen')
import pdf_gen

sys.path.append('options_gen')
import options
import argparse

# use this comp for a long cumulative time limit
#comp_id = 'HDCIMalovPark2022'
#comp_id = 'BASC67SanRamon2025'
#comp_id = 'UCSDFall2024'
#comp_id = 'EverythinginEvanstonB2023'
#comp_id = 'DavisFall2024'

# TODO: add description

def parse_args():
	parser = argparse.ArgumentParser()

	parser.add_argument('comp_id', type=str, metavar='CompId',
						 help='ID of the competition, e.g. RocklinWinter2024')

	return parser.parse_args()

def main():
	args = parse_args()

	wcif_json = wcif.download_wcif(args.comp_id)

	options_file_path = options.OPTIONS_FILE_STR_FORMAT.format(args.comp_id)
	options_xlsx_obj = options.OptionsXLSX.init_from_xlsx(options_file_path)

	scorecards_list = scorecards.get_scorecards_data(wcif_json, options_xlsx_obj.options_dict)
	grouped_scorecards_data = scorecards.group_scorecards_data(scorecards_list, 'pdf_group')
	sorted_scorecards_data = scorecards.sort_scorecards_data(grouped_scorecards_data, ['round', scorecards.get_group_num, scorecards.get_group_stage, 'name'])
	for event in sorted_scorecards_data:
		sorted_scorecards_data[event] = scorecards.group_scorecards_data(sorted_scorecards_data[event], 'round')

	format_blanks = scorecards.gen_format_blanks(wcif_json, options_xlsx_obj.options_dict)

	sorted_scorecards_data.update(format_blanks)

	#scorecards_grouped_by_pdf = scorecards.group_scorecards_data(scorecards_list, 'event')
	pdf_gen.gen_scorecards_pdf(args.comp_id, sorted_scorecards_data)

if __name__ == '__main__':
	main()

#wcif_json = wcif.download_wcif(comp_id)

#comp_name = wcif.get_comp_name(wcif_json)
#scorecards_list = scorecards.get_scorecards_data(wcif_json)
#for event in sorted_scorecards_data:
#	sorted_scorecards_data[event] = scorecards.group_scorecards_data(sorted_scorecards_data[event], 'round')

#pprint.pprint(sorted_scorecards_data)
#pdf_gen.gen_scorecards_pdf(comp_id, sorted_scorecards_data)
