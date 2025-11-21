import wcif
import math
# TODO: DELETE
import pprint

# TODO: explain
def get_scorecards_data(wcif_json: dict,
						options_dict: dict,
						) -> list:
	scorecards_list = []

	act_id_to_persons = wcif.get_activity_id_to_persons_list_dict(wcif_json)
	act_id_to_room = wcif.get_activity_id_to_room_dict(wcif_json)
	acts = wcif.get_activities_dict(wcif_json)
	round_id_to_round_dict = wcif.get_round_id_to_round_dict(wcif_json)

	### Multi-event scorecards
	### TODO: check options dict to make sure this is the desired behavior
	cumul_limits_list = []
	for event_dict in wcif_json['events']:
		# Get list of events with cumulative time limits
		for round_dict in event_dict['rounds']:
			if not round_dict['timeLimit']:
				# e.g. multiblind has no time limit in the WCIF
				continue

			cumul_round_ids = round_dict['timeLimit']['cumulativeRoundIds']

			# TODO: Don't hard-code 2.
			# TODO:  It is explicitly enforced here that we only support 2 events; I should 1) clearly document this and 2) enforce that both events must have 3-solve formats.
			if cumul_round_ids and len(cumul_round_ids) == 2:
				cumul_limits_list.append(cumul_round_ids)

		# Remove duplicates
		cumul_limits_set = {tuple(_list) for _list in cumul_limits_list}

	round_id_to_reg_id_dict = {}

	# TODO: there's likely a way to do this all in one loop, which would remove a lot of obnoxious duplicate code.
	for round_id_list in cumul_limits_set:
		next_scorecards_list = []
		round_dict_list = [round_id_to_round_dict[round_id] for round_id in round_id_list]
		round_num_list = [wcif.round_id_to_round_number(round_id) for round_id in round_id_list]
		format_list = [round_dict['format'] for round_dict in round_dict_list]
		event_id_list = [wcif.round_id_to_event_id(round_id) for round_id in round_id_list]
		event_list = [wcif.event_id_to_name(event_id) for event_id in event_id_list]
		round_list = [wcif.round_id_to_round_number(round_id) for round_id in round_id_list]

		act_ids = []
		for event_id, round_num in zip(event_id_list, round_num_list):
			act_ids.extend(wcif.get_activity_ids_for_event_round(wcif_json, event_id, round_num))

		# Dictionary that maps the round ID (e.g. 333-r1) to registrant ID if and only if
		# the registrant has a scorecard for that round.
		# Used for preventing duplicate scorecards.
		for round_id in round_id_list:
			if not round_id in round_id_to_reg_id_dict:
				round_id_to_reg_id_dict[round_id] = []

		# Construct list of scorecards, then remove duplicates by name.
		# TODO: add warnings/checks for errors. Removing duplicates by name has the potential for undesirable behaviors.
		for _id in act_ids:
			room_dict = act_id_to_room[_id]
			# TODO: fix the function and delete this try except block
			try:
				persons_list = act_id_to_persons[_id]
			except KeyError:
				# Sometimes, an activity (representing, perhaps, a group on a stage)
				# can have no competitors, leading to a KeyError.
				# For example, a group may have no assignments at all, or it may have
				# staff assigned but no competitors assigned (e.g. at WesternChampionship2024).
				continue

			# TODO: boo duplicate code
			room_abbr = options_dict[f'Abbreviation for {room_dict["name"]}'].value
			if room_abbr == None:
				room_abbr = ''

			# TODO: this assumes the competitor is in the same group for any events with a shared cumulative time limit... surely this should be the case if someone's using this feature!!!
			activity_code_list = acts[_id]['activityCode'].split('-')
			group_number = activity_code_list[2][1:]

			for person in persons_list:
				# Skip if we already have a scorecard for this person for this event.
				if any([
						person['registrantId'] in round_id_to_reg_id_dict[round_id]
	   					for round_id in round_id_list
					]):
					continue

				# Skip if this person isn't competing in all of the events with the cumulative time limit.
				# We'll make them a scorecard for one event later.
				# TODO: there's a better way to do this than manually checking if someone's in a list lol
				# TODO: also this will not work if we deepcopy a person, but surely we'd never do that
				if not all([
						person in wcif.event_round_to_persons_list(wcif_json, event_id, round_num)
						for event_id, round_num in zip(event_id_list, round_num_list)
					]):
					continue

				# TODO: surely there's a way to avoid duplicates that doesn't involve 3 nested loops
				for round_id in round_id_list:
					round_id_to_reg_id_dict[round_id].append(person['registrantId'])

				_dict = {}
				_dict['competition'] = wcif.get_comp_name(wcif_json)
				# Competitor-specific info
				_dict['name'] = person['name']
				_dict['wca_id'] = person['wcaId']
				_dict['id'] = person['registrantId']

				# Event-specific info
				_dict['multi_event'] = True
				# TODO: wrong
				_dict['event'] = event_list
				# TODO: need multiple formats
				_dict['format'] = format_list
				# TODO: nope, just don't even bother with cutoff. maybe print a warning if a cutoff is given
				#_dict['cutoff'] = wcif.cutoff_human_readable(round_dict['cutoff'])
				_dict['time_limit'] = wcif.time_limit_human_readable(round_dict_list[0]['timeLimit'], event_id_list[0], wcif_json['events'])

				# TODO: zip(event_list, round_list) can be used for getting the event/round pairs, but this is hacky
				# TODO: surely no one would ever have a cumulative time limit for Round 1 of one event and Round 2 of another event! Surely no one would do something like that! (this assumes that cumulative time limits apply to the same round)
				_dict['round'] = round_list[0]

				# TODO: not a fan of the int type conversion here
				# TODO: another ugly zip loop!
				_dict['round_text'] = []
				for event_id, round_num in zip(event_id_list, round_num_list):
					num_rounds = wcif.get_num_rounds(wcif_json['events'], event_id)
					_dict['round_text'].append(wcif.round_num_to_round_str(round_num, num_rounds))

				_dict['group'] = f'{room_abbr}{group_number}'

				# TODO: better way of doing this?
				_dict['pdf_group'] = '_'.join(event_list)

				next_scorecards_list.append(_dict)

		# Add multi-event blanks
		# TODO: integrate this with other blanks function
		# TODO: add options for this
		num_non_blank = len(next_scorecards_list)
		num_total = math.ceil(max(num_non_blank * 1.20, num_non_blank + 10) / 4) * 4
		num_blanks = num_total - num_non_blank
		for i in range(0, num_blanks):
			blank_dict = {}
			blank_dict['competition'] = wcif.get_comp_name(wcif_json)
			blank_dict['name'] = ''
			# TODO: this is a hack to avoid the "New Competitor" print. Make a new_competitor boolean instead.
			blank_dict['wca_id'] = ' '
			blank_dict['id'] = ''

			blank_dict['multi_event'] = True
			blank_dict['event'] = event_list
			blank_dict['format'] = format_list
			blank_dict['time_limit'] = wcif.time_limit_human_readable(round_dict_list[0]['timeLimit'], event_id_list[0], wcif_json['events'])

			blank_dict['round'] = round_list[0]
			# TODO: another ugly zip loop!
			blank_dict['round_text'] = []
			for event_id, round_num in zip(event_id_list, round_num_list):
				num_rounds = wcif.get_num_rounds(wcif_json['events'], event_id)
				blank_dict['round_text'].append(wcif.round_num_to_round_str(round_num, num_rounds))

			blank_dict['group'] = ''

			# TODO: better way of doing this?
			blank_dict['pdf_group'] = '_'.join(event_list)
			next_scorecards_list.append(blank_dict)

		scorecards_list.extend(next_scorecards_list)

	### Individual event scorecards
	for event_dict in wcif_json['events']:
		event_id = event_dict['id']
		act_ids = wcif.get_activity_ids_for_event(wcif_json, event_dict['id'])
		for _id in act_ids:
			# Collect group-specific data
			room_dict = act_id_to_room[_id]

			# TODO: fix the function and delete this try except block
			try:
				persons_list = act_id_to_persons[_id]
			except KeyError:
				# Sometimes, an activity (representing, perhaps, a group on a stage)
				# can have no competitors, leading to a KeyError.
				# For example, a group may have no assignments at all, or it may have
				# staff assigned but no competitors assigned (e.g. at WesternChampionship2024).
				continue

			activity_code_list = acts[_id]['activityCode'].split('-')
			round_id = f'{activity_code_list[0]}-{activity_code_list[1]}'
			round_dict = round_id_to_round_dict[round_id]

			# TODO: not a fan of hard-coding the option names like this...
			room_abbr = options_dict[f'Abbreviation for {room_dict["name"]}'].value
			if room_abbr == None:
				room_abbr = ''
			group_number = activity_code_list[2][1:]

			if not round_id in round_id_to_reg_id_dict:
				round_id_to_reg_id_dict[round_id] = []

			for person in persons_list:
				if person['registrantId'] in round_id_to_reg_id_dict[round_id]:
					continue

				round_id_to_reg_id_dict[round_id].append(person['registrantId'])

				_dict = {}
				_dict['competition'] = wcif.get_comp_name(wcif_json)
				# Competitor-specific info
				_dict['name'] = person['name']
				_dict['wca_id'] = person['wcaId']
				_dict['id'] = person['registrantId']

				# Event-specific info
				_dict['multi_event'] = False
				_dict['event'] = wcif.event_id_to_name(event_id)
				_dict['format'] = round_dict['format']
				_dict['cutoff'] = wcif.cutoff_human_readable(round_dict['cutoff'])
				_dict['time_limit'] = wcif.time_limit_human_readable(round_dict['timeLimit'], event_dict['id'], wcif_json['events'])

				_dict['round'] = activity_code_list[1][1:]

				_dict['round_text'] = wcif.round_num_to_round_str(int(_dict['round']), wcif.get_num_rounds(wcif_json['events'], event_id))
				_dict['group'] = f'{room_abbr}{group_number}'
				# TODO: better way of doing this?
				_dict['pdf_group'] = _dict['event']

				scorecards_list.append(_dict)

	# Add blanks
	for round_id in round_id_to_round_dict:
		round_dict = round_id_to_round_dict[round_id]

		# e.g. convert 333-r1 to 333
		event_id = round_dict['id'].split('-')[0]
		event_name = wcif.event_id_to_name(event_id)

		# e.g. convert 333-r1 to 1
		round_num = int(round_dict['id'].split('-')[1][1:])
		round_text = wcif.round_num_to_round_str(round_num, wcif.get_num_rounds(wcif_json['events'], event_id))

		blanks_option_name = f'Blanks: {event_name} {round_text}'

		num_blanks = int(options_dict[blanks_option_name].value)

		for i in range(0, num_blanks):
			blank_dict = {}
			blank_dict['competition'] = wcif.get_comp_name(wcif_json)
			blank_dict['name'] = ''
			# TODO: this is a hack to avoid the "New Competitor" print. Make a new_competitor boolean instead.
			blank_dict['wca_id'] = ' '
			blank_dict['id'] = ''

			blank_dict['multi_event'] = False
			blank_dict['event'] = event_name
			blank_dict['format'] = round_dict['format']
			blank_dict['cutoff'] = wcif.cutoff_human_readable(round_dict['cutoff'])
			blank_dict['time_limit'] = wcif.time_limit_human_readable(round_dict['timeLimit'], event_id, wcif_json['events'])

			blank_dict['round'] = str(round_num)
			blank_dict['round_text'] = round_text
			blank_dict['group'] = ''

			# TODO: better way of doing this?
			blank_dict['pdf_group'] = blank_dict['event']
			scorecards_list.append(blank_dict)

	return scorecards_list

# TODO: explain
# TODO: more configuration from the user
def gen_format_blanks(wcif_json: dict,
					  options_dict: dict,
					  ) -> dict:
	blanks_dict = {}
	# TODO: there's probably a more elegant way to do this, but I'm in a rush.

	# Iterate through the options_dict looking for keys that specify blanks for formats
	for key in options_dict:
		_format = None
		if key.startswith("Blanks: "):
			pdf_suffix = key.removeprefix("Blanks: ")
			if pdf_suffix in wcif.format_dict.values():
				# ChatGPT's solution for getting a key from a value. i.e., get the WCIF _format specifier
				# from the long name of the format (e.g., get 'm' from 'Mean of 3').
				_format = next((k for k, v in wcif.format_dict.items() if v == pdf_suffix), None)

		if _format != None:
			if options_dict[key].value == 0:
				print(f'Warning: Specified 0 generic blanks for the {pdf_suffix.replace("_", " ")} format. Not generating blank scorecards for this format.')
				continue

			blanks_dict[pdf_suffix] = {'': []}

			for i in range(0, options_dict[key].value):
				_dict = {}

				_dict['competition'] = wcif.get_comp_name(wcif_json)
				_dict['name'] = ''
				_dict['wca_id'] = ' '
				_dict['id'] = ''

				_dict['multi_event'] = False
				_dict['event'] = ''
				_dict['format'] = _format
				_dict['cutoff'] = 'Cutoff:'
				_dict['time_limit'] = 'Time limit:'

				_dict['round'] = ''
				_dict['round_text'] = ''
				_dict['group'] = ''

				blanks_dict[pdf_suffix][''].append(_dict)

	return blanks_dict


# TODO: explain
# TODO: delete below
# example group_by: 'event'
# TODO: support multi-level grouping
# TODO: support groupings defined by functions
def group_scorecards_data(scorecards_list: list,
						 group_by: str,
						 ) -> dict:
	scorecards_dict = {}
	for scorecard in scorecards_list:
		# Add the scorecard to the correct group, accessed via a key in scorecards_dict.
		# The "setdefault" call here just creates the "group" (i.e. list) for the key if it's
		# not already created.
		scorecards_dict.setdefault(scorecard[group_by], []).append(scorecard)

	return scorecards_dict



# TODO: explain
# TODO: delete below
# example sort_by (after being grouped by "event"): ['round', 'group', get_stage, 'name']
# TODO: support multi-level grouping
def sort_scorecards_data(scorecards_dict: dict,
						 sort_by: list
						 ) -> dict:
	final_dict = scorecards_dict
	for key in scorecards_dict:
		final_dict[key] = scorecards_dict[key]
		for sorting in reversed(sort_by):
			# TODO: comment explaining how this works
			# TODO: verify that the function takes only one argument and that the argument is "scorecard"
			if callable(sorting):
				final_dict[key] = sorted(final_dict[key], key=sorting)
			elif isinstance(sorting, str):
				# The "key" here is a hack to make the blank string sorted last
				final_dict[key] = sorted(final_dict[key], key=lambda scorecard: (scorecard[sorting] == ' ', scorecard[sorting]))
			else:
				raise Exception(f"Invalid sort_by item {sorting}. Each item in sort_by must be a single-argument function or a string.")

	return final_dict

# TODO: explain
# TODO: consider the possibility of a multi-letter stage name
def get_group_stage(scorecard):
	# Sort blanks at the end
	if len(scorecard['group']) == 0:
		# [ supposedly comes after z
		return '['
	return scorecard['group'][0]

# TODO: explain
# TODO: consider the possibility of a multi-letter stage name
def get_group_num(scorecard):
	# Sort blanks at the end
	if len(scorecard['group']) == 0:
		# [ supposedly comes after z
		return '['
	return scorecard['group'][1:]
