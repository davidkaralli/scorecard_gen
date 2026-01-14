#!/usr/bin/env python3

# Functions for downloading and parsing the WCIF (WCA Competition Interchange Format)

import requests
from datetime import datetime
import math


# Converts the WCIF format character to its full name
format_dict = {
	'a' : 'Average of 5',
	'm' : 'Mean of 3',
	'1' : 'Best of 1',
	'2' : 'Best of 2',
	'3' : 'Best of 3',
	'5' : 'Best of 5',
}

# Returns the WCIF JSON for a competition
#
# Arguments:
#     comp_id: The ID of the competition, e.g. DavisSummer2024
def download_wcif(comp_id: str) -> dict:
	url = f"https://www.worldcubeassociation.org/api/v0/competitions/{comp_id}/wcif/public"
	response = requests.get(url)

	if response.status_code != requests.codes.ok:
		response.raise_for_status()

	return response.json()


# Functions and structures for parsing events from the WCIF file

# Returns the competition name.
#
# Arguments:
#     wcif_json: The WCIF JSON for the competition.
#
# Returns:
#     String for the competition name.
def get_comp_name(wcif_json: dict) -> str:
	return wcif_json['name']


# Dictionary to translate the WCIF event ID to something human-readable
event_id_to_name_dict = {
	'333': '3x3x3 Cube',
	'222': '2x2x2 Cube',
	'444': '4x4x4 Cube',
	'555': '5x5x5 Cube',
	'666': '6x6x6 Cube',
	'777': '7x7x7 Cube',
	'333bf': '3x3x3 Blindfolded',
	'333fm': '3x3x3 Fewest Moves',
	'333oh': '3x3x3 One-Handed',
	'clock': 'Clock',
	'minx': 'Megaminx',
	'pyram': 'Pyraminx',
	'skewb': 'Skewb',
	'sq1': 'Square-1',
	'444bf': '4x4x4 Blindfolded',
	'555bf': '5x5x5 Blindfolded',
	'333mbf': '3x3x3 Multi-Blind',
}

# Return the human-readable name of the WCIF event
#
# Arguments:
#     event_id: WCIF event ID string, e.g. '333'
#
# Returns:
#     Event name, e.g. '3x3x3 Cube'
def event_id_to_name(event_id: str) -> str:
	return event_id_to_name_dict[event_id]

# Return the round number from the ID of the round.
#
# Arguments:
#     round_id: WCIF round ID string, e.g. '333-r4'
#
# Returns:
#     Integer round number, e.g. 4
def round_id_to_round_number(round_id: str) -> int:
	# Round ID format example: '333-r4'
	# We need to extract 4 in this example.

	# First, extract 'r4'.
	round_suffix = round_id.split('-')[1]

	# Now extract 4.
	round_number = int(round_suffix[1:])
	return round_number

# Return the event id from the ID of the round.
#
# Arguments:
#     round_id: WCIF round ID string, e.g. 'sq1-r3'
#
# Returns:
#     Event ID, e.g. sq1
def round_id_to_event_id(round_id: str) -> str:
	return round_id.split('-')[0]

# Return a human-readable version of the WCIF's time limit
#
# Arguments:
#     time_limit_dict: WCIF-formatted time limit dict, with entries for keys 'centiseconds' and 'cumulativeRoundIds'.
#     event_id: WCIF event ID, e.g. '333' or '333mbf'.
#     events_dict: The entire WCIF events dict... yes, we really do need this. (for cumulative time limits across multiple events)
def time_limit_human_readable(time_limit_dict: dict,
							  event_id: str,
							  events_dict: dict,
							  ) -> str:

	# Special handling for multi-blind and FMC
	if event_id == '333mbf':
		return 'Time limit per attempt: 10 minutes per cube, up to 1 hour'
	elif event_id == '333fm':
		return 'Time limit per attempt: 1 hour'

	# TODO: validate time limit dict
	centiseconds = time_limit_dict['centiseconds']
	cumulative_round_ids = time_limit_dict['cumulativeRoundIds']

	time_str = centiseconds_to_time_str(centiseconds)

	time_limit_type_str = cumulative_round_ids_to_time_limit_type_str(cumulative_round_ids, events_dict)

	return time_limit_type_str.format(time_str)

# Return a human-readable version of the WCIF's cutoff
#
# Arguments:
#     cutoff_dict: WCIF-formatted time limit dict, with entries for 'numberOfAttempts' and 'attemptResult'.
# TODO: multiblind and FMC cut-off handling... or just don't support these cutoffs to disincentivize them lol
def cutoff_human_readable(cutoff_dict: dict) -> str:
	# TODO: Validate cutoff dict
	if not cutoff_dict:
		# No cutoff
		return 'Cutoff: N/A'

	centiseconds = cutoff_dict['attemptResult']
	time_str = centiseconds_to_time_str(centiseconds)

	if cutoff_dict['numberOfAttempts'] == 1:
		return f'Cutoff: Continue if 1 < {time_str}'
	else: # cutoff_dict['numberOfAttempts'] == 2
		return f'Cutoff: Continue if 1 or 2 < {time_str}'

# Return a human-readable time from the number of centiseconds, e.g.:
#
# Arguments:
#     centiseconds: integer number of centiseconds, e.g. 60000.
#
# Returns:
#     String indicating the time limit. Examples:
#         '10:00.00'
#         '1:05:00.00'
#         '5:30.00'
#         '2:05.10'
#         '30.05'
#         '5.00'
#
# Note: If you have a time limit or cutoff under 1 second, you deserve whatever error comes up.
def centiseconds_to_time_str(centiseconds: int) -> str:
	seconds, remainder = divmod(centiseconds, 100)

	# Get each component of the time (thanks, ChatGPT!)
	time_obj = datetime.utcfromtimestamp(seconds)
	hours = time_obj.hour
	minutes = time_obj.minute
	seconds = time_obj.second
	centiseconds = remainder

	# Now figure out which format to use and return the string.

	string_list = []

	if hours > 0:
		# format: 5 hours
		s = '' if hours == 1 else 's'
		string_list.append(f'{hours} hour{s}')

	if minutes > 0:
		# format: 3 minutes
		s = '' if minutes == 1 else 's'
		string_list.append(f'{minutes} minute{s}')

	if seconds > 0 and centiseconds > 0:
		# format: 5.12 seconds
		string_list.append(f'{seconds}.{centiseconds:02d} seconds')
	elif seconds > 0:
		# format: 5 seconds
		s = '' if seconds == 1 else 's'
		string_list.append(f'{seconds} second{s}')

	if not string_list:
		# Ain't no way
		raise Exception("A sub-1 second time limit or cutoff? Either something's gone horribly wrong, or you deserve a stern lecture from WCAT.")

	return ' '.join(string_list)

# Return a time limit type string for the time limit of a round, e.g.:
# 'Time limit per solve: > {}'
#
# Arguments:
#     cumulative_round_ids: WCIF cumulativeRoundIds dict
#     events_dict: The entire WCIF events dict... yes, we really do need this. (for cumulative time limits across multiple events)
#
# Returns: String format for the time limit, e.g.:
#     'Time limit per solve: DNF if ≥ {}'
#     'Cumulative time limit: {}'
#     'Cumulative time limit: {} for 4x4x4 Blindfolded Final and 5x5x5 Blindfolded Final'
#     'Cumulative time limit: {} for 3x3x3 Blindfolded Final, 4x4x4 Blindfolded Final, and 5x5x5 Blindfolded Final'
def cumulative_round_ids_to_time_limit_type_str(cumulative_round_ids: dict,
												events_dict: dict,
												) -> str:
	if not cumulative_round_ids:
		# Per-solve time limit
		return 'Time limit per solve: DNF if ≥ {}'

	elif len(cumulative_round_ids) == 1:
		# Cumulative time limit for one event
		return 'Cumulative time limit: {}'

	elif len(cumulative_round_ids) == 2:
		# Cumulative time limit for 2 events, e.g.:
		# 'Cumulative time limit for 4x4x4 Blindfolded Final and 5x5x5 Blindfolded Final: {}'

		# Get the round string, e.g. '4x4x4 Blindfolded Final'
		event_round_0 = round_id_to_event_round_str(cumulative_round_ids[0], events_dict)
		event_round_1 = round_id_to_event_round_str(cumulative_round_ids[1], events_dict)
		return f'Cumulative time limit: {{}} for {event_round_0} and {event_round_1}'

	else: # len(cumulative_round_ids) > 2
		# Hoo boy
		# Cumulative time limit for over 2 events, e.g.:
		# 'Cumulative time limit for 3x3x3 Blindfolded Round 1, 4x4x4 Blindfolded Final, and 5x5x5 Blindfolded Final: {}'
		# (in this house, we use the Oxford comma)

		# Build the string containing the list of events
		event_round_str = ""
		for round_id in cumulative_round_ids[:-1]:
			curr_event_round = round_id_to_event_round_str(round_id, events_dict)
			event_round_str += f'{curr_event_round}, '

		last_round_id = cumulative_round_ids[-1]
		last_event_round = round_id_to_event_round_str(last_round_id, events_dict)
		event_round_str += f'and {last_event_round}'

		return f'Cumulative time limit: {{}} for {event_round_str}'

# Returns the event round string from the WCIF round id, e.g. '3x3x3 Cube Round 1'
#
# Arguments:
#     round_id: The WCIF round_id, e.g. '333-r1'
#     events_dict: The entire WCIF events dict... yes, we really do need this. (for cumulative time limits across multiple events)
#
# Returns:
#     The event round string. Examples:
#         '3x3x3 Cube Round 1'
#         '3x3x3 Cube Round 2'
#         '3x3x3 Cube Semi Final'
#         '3x3x3 Cube Final'
def round_id_to_event_round_str(round_id: str,
								events_dict: dict,
								) -> str:
	# Split e.g. '333-r1' into '333' and 'r1'
	event_id, round_id_suffix = round_id.split('-')


	# Get some info about the event and the round
	event_name = event_id_to_name(event_id)
	round_number = round_id_to_round_number(round_id)
	num_rounds = get_num_rounds(events_dict, event_id)

	return event_name + ' ' + round_num_to_round_str(round_number, num_rounds)

# TODO: comment
def get_num_rounds(events_dict: dict,
				   event_id: str,
				   ) -> int:

	rounds_dict = None

	for _dict in events_dict:
		if _dict['id'] == event_id:
			rounds_dict = _dict['rounds']

	return len(rounds_dict)


# TODO: comment
def round_num_to_round_str(round_num: int,
						   total_num_rounds: int,
						   ) -> str:

	# Final round
	if round_num == total_num_rounds:
		return 'Final'

	# All other cases
	if round_num == 1:
		return 'Round 1'
	elif round_num == 2:
		return 'Round 2'
	elif round_num == 3:
		return 'Semi Final'

# TODO comment
# TODO finish
# TODO: add support for multiple venues? (currently, we only support one venue)
def get_rooms_dict(wcif_json: dict) -> list:
	venue = wcif_json['schedule']['venues'][0]
	return venue['rooms']

# Returns a dict of activity dicts, with each dict corresponding to a group of a round.
#
# Arguments:
#     wcif_json: The WCIF JSON for the competition.
#
# Returns:
#     A dict, where the key is the activity ID (int) and the value is the activity dict as formatted in the WCIF.
def get_activities_dict(wcif_json: dict) -> dict:
	venue = wcif_json['schedule']['venues'][0]
	activities_dict = {}
	for room in venue['rooms']:
		for activity in room['activities']:
			# TODO: this doesn't support FMC. also not sure if it supports 1-group rounds?
			for child_activity in activity['childActivities']:
				child_activity_id = child_activity['id']
				activities_dict[child_activity_id] = child_activity

	return activities_dict

# Returns a dict that maps an activity ID (int) to a room's dict.
#
# Arguments:
#     wcif_json: The WCIF JSON for the competition.
def get_activity_id_to_room_dict(wcif_json: dict) -> dict:
	venue = wcif_json['schedule']['venues'][0]
	activity_id_to_room_dict = {}
	for room in venue['rooms']:
		for activity in room['activities']:
			for child_activity in activity['childActivities']:
				child_activity_id = child_activity['id']
				activity_id_to_room_dict[child_activity_id] = room

	return activity_id_to_room_dict

# TODO: desc
#
# Arguments:
#     wcif_json: The WCIF JSON for the competition.
#
# TODO: at multiple locations, we need to a "try, except" block
# due to groups with zero assigned competitors... let's just go through all of the activities (and
# their child activities) and give them a value of an empty list in the dict.
def get_activity_id_to_persons_list_dict(wcif_json: dict) -> dict:
	_dict = {}
	persons_list = wcif_json['persons']
	for person in persons_list:
		for assignment in person['assignments']:
			if assignment['assignmentCode'] == 'competitor':
				activity_id = assignment['activityId']
				if not activity_id in _dict:
					_dict[activity_id] = []
				_dict[activity_id].append(person)

	# TODO: DELETE
	# Some activities have no competitor assignments.
	# Examples: groups with no assignments at all (common for final rounds),
	# groups with staff assignments and no competitor assignments (this happened at WesternChampionship2024).
	# We need to find all the activities and add any competitorless activities to the dictionary.
	# (In this case, the person_list is an empty list.)

	# Depth-first search to get all child activities
	#activities_stack = []
	#for venue in wcif_json['schedule']['venues']:
	#	for room in venue['rooms']:
	#		for activity in room['activities']:
	#			while activity['childActivities']:
	#				activities_stack.push()

	return _dict

# TODO: comment
# TODO: might not be needed
def get_activity_ids_for_event(wcif_json: dict,
							   event_name: str,
							   ) -> list:
	id_list = []
	venue = wcif_json['schedule']['venues'][0]

	for room in venue['rooms']:
		for activity in room['activities']:
			for child_activity in activity['childActivities']:
				# e.g. 333-r1-g2 -> 333
				child_activity_event = child_activity['activityCode'].split('-')[0]
				if child_activity_event == event_name:
					id_list.append(child_activity['id'])

	return id_list

# TODO: comment
# TODO: might not be needed
# TODO: apparently this wasn't working at all before... check where it's used? make sure I didn't break everything?
def get_activity_ids_for_event_round(wcif_json: dict,
							   		 event_id: str,
									 round_num: int,
							   		 ) -> list:
	id_list = []
	venue = wcif_json['schedule']['venues'][0]

	for room in venue['rooms']:
		for activity in room['activities']:
			for child_activity in activity['childActivities']:
				# e.g. 333-r1-g2 -> 333
				child_activity_event = child_activity['activityCode'].split('-')[0]
				# e.g. 333-r1-g2 -> 1
				child_activity_round = int(child_activity['activityCode'].split('-')[1][1:])
				if child_activity_event == event_id and int(child_activity_round) == int(round_num):
					id_list.append(child_activity['id'])

	return id_list

# TODO: comment
def event_round_to_persons_list(wcif_json: dict,
								event_id: str,
								round_num: int,
								) -> list:
	activity_id_to_persons = get_activity_id_to_persons_list_dict(wcif_json)
	activity_ids = get_activity_ids_for_event_round(wcif_json, event_id, round_num)

	persons_list = []

	for _id in activity_ids:
		try:
			to_add = activity_id_to_persons[_id]
		except KeyError:
			continue
		persons_list += to_add

	return persons_list



# TODO: comment
# TODO: consistent name scheme for functions
def get_round_id_to_round_dict(wcif_json: dict) -> dict:
	# Generate a mapping of round ID (e.g. '333-r1') to round dict
	round_id_to_round_dict = {}
	for event in wcif_json['events']:
		for _round in event['rounds']:
			round_id = _round['id']
			round_id_to_round_dict[round_id] = _round

	return round_id_to_round_dict

# TODO: more detailed comment
# Get the WCIF advancement criteria dict for the given round
# (specifying the number of people advancing from the given round to the next one).
def round_id_to_advancement_dict(events_dict: dict,
								 round_id: str,
								 ) -> dict:
	for event in events_dict:
		for _round in event['rounds']:
			if _round['id'] == round_id:
				return _round['advancementCondition']


# TODO: more detailed comment
# TODO: clean this up
# TODO: this needs more thorough testing
# Get the number of competitors advancing to this round
# (i.e. for round_id=333-r2, we'd want the number of people advancing *from* Round 1 *to* Round 2).
def get_num_advancing_to_this_round(wcif_json: dict,
								    round_id: str,
									recursive_call: bool = False,
									) -> int:
	event_id = round_id_to_event_id(round_id)
	curr_round = round_id_to_round_number(round_id)

	if curr_round < 2 and not recursive_call:
		raise ValueError("Cannot call get_num_advancing_to_this_round on round 1")
	elif curr_round == 1 and recursive_call:
		return len(event_round_to_persons_list(wcif_json, event_id, curr_round))
	# TODO: throw errors in other cases?

	prev_round = curr_round - 1
	prev_round_id = f'{event_id}-r{prev_round}'

	events_dict = wcif_json['events']
	advancement_dict = round_id_to_advancement_dict(events_dict, prev_round_id)

	if advancement_dict['type'] == 'ranking':
		return advancement_dict['level']
	elif advancement_dict['type'] == 'percent':
		num_people_in_prev_round = get_num_advancing_to_this_round(wcif_json, prev_round_id, recursive_call=True)
		fraction = advancement_dict['level'] / 100
		return math.floor(num_people_in_prev_round * fraction)
	elif advancement_dict['type'] == None:
		# TODO: technically this might be wrong lol
		raise Exception('No advancement condition specified for the previous round.')
	else:
		raise Exception('Unrecognized advancement condition.')
