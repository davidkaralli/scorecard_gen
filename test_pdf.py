#!/usr/bin/env python3

import wcif
import pprint
import scorecards
import pdf_gen

# use this comp for a long cumulative time limit
#comp_id = 'HDCIMalovPark2022'
comp_id = 'WesternChampionship2024'
#comp_id = 'EverythinginEvanstonB2023'

wcif_json = wcif.download_wcif(comp_id)

comp_name = wcif.get_comp_name(wcif_json)
print(comp_name)
print()

"""
for event_dict in wcif_json['events']:
	event_name = wcif.event_id_to_name(event_dict['id'])
	print(f'Event: {event_name}')
	print()
	for round_dict in event_dict['rounds']:
		round_number = wcif.round_id_to_round_number(round_dict['id'])
		print(f'Round: {round_number}')

		round_name = wcif.round_id_to_event_round_str(round_dict['id'], wcif_json['events'])
		print(f'Round name: {round_name}')

		format_short_name = wcif.format_id_to_short_name(round_dict['format'])
		print(f'Format: {format_short_name}')

		if '333fm' not in event_dict['id'] and '333mbf' not in event_dict['id']:
			cutoff = wcif.cutoff_human_readable(round_dict['cutoff'])
			print(f'Cutoff: {cutoff}')

		time_limit = wcif.time_limit_human_readable(round_dict['timeLimit'], event_dict['id'], wcif_json['events'])
		print(time_limit)
		print()
	print('-------')
	print()
"""

scorecards_list = scorecards.get_scorecards_data(wcif_json)
grouped_scorecards_data = scorecards.group_scorecards_data(scorecards_list, 'event')
sorted_scorecards_data = scorecards.sort_scorecards_data(grouped_scorecards_data, ['round', scorecards.get_group_num, scorecards.get_group_stage, 'name'])
for event in sorted_scorecards_data:
	sorted_scorecards_data[event] = scorecards.group_scorecards_data(sorted_scorecards_data[event], 'round')

#pprint.pprint(sorted_scorecards_data)
pdf_gen.gen_scorecards_pdf(comp_id, sorted_scorecards_data)
