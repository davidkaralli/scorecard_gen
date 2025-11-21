import os

import sys
sys.path.append('..')
import wcif

from collections import OrderedDict
import openpyxl
from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from abc import ABC # Abstract Base Class
import copy
import math


# TODO: Needed info:
# Upper limit on OTS reg

# {} is replaced with the competition ID, e.g. WesternChampionship2024
# TODO: inconsistent result depending on where the script is executed lol
OPTIONS_DIR = os.path.join('Options')
OPTIONS_FILE_STR_FORMAT = os.path.join(OPTIONS_DIR, 'Options_{}.xlsx')

# TODO: document check_value
class Option(ABC):
	init_from_xlsx_args = None

	def __init__(self,
				 name: str,
				 value,
				 description: str,
				 ):
		self.name = name
		self.value = value
		self.description = description

	@classmethod
	def check_value(cls, value):
		pass

class GroupByOption(Option):
	name = 'Group scorecards by'
	description = 'Within a round, are scorecards grouped together by group number ("group_number") or by the room\'s abbreviation ("room")?'

	@classmethod
	def init_default_option(cls,
							value='group_number',
							):
		return cls(cls.name, value, cls.description)

	@classmethod
	def init_from_xlsx(cls,
					   xlsx_value=None,
					   ):
		return cls(cls.name, xlsx_value, cls.description)

	def get_args_for_xlsx(self):
		return []

	def check_value(self):
		return isinstance(self.value, str) and self.value in ['group_number', 'room']

# TODO: can this be merged with the below class?
class NumBlanksForRoundOption(Option):
	name_format = 'Blanks: {}'
	description_format = 'Number of blank scorecards for {}.'

	def __init__(self,
				 name: str,
				 value,
				 description: str,
				 event_round_str: str,
				 ):
		self.event_round_str = event_round_str

		super().__init__(name, value, description)

	@classmethod
	def init_default_option(cls,
							event_round_str: str,
							num_people_in_round: int,
							only_blanks: bool=False,
							):
		name = cls.name_format.format(event_round_str)
		description = cls.description_format.format(event_round_str)

		# Add 20% of the number of non-blank scorecards, rounded to the next multiple of 4.
		total_num_scorecards = math.ceil((num_people_in_round * 1.20) / 4) * 4

		# Get the default number of blank scorecards
		if only_blanks:
			default_value = total_num_scorecards
		else:
			default_value = total_num_scorecards - num_people_in_round

		return cls(name, default_value, description, event_round_str)

	@classmethod
	def init_from_xlsx(cls,
					   event_round_str: str,
					   xlsx_value=None,
					   ):
		name = cls.name_format.format(event_round_str)
		description = cls.description_format.format(event_round_str)

		return cls(name, xlsx_value, description, event_round_str)

	def get_args_for_xlsx(self):
		return [self.event_round_str]

	def check_value(self):
		return isinstance(self.value, int) and self.value >= 0

# TODO: can this be merged with the above class?
class NumBlanksForFormatOption(Option):
	name_format = 'Blanks: {}'
	description_format = 'Number of blank scorecards for the {} format.'

	def __init__(self,
				 name: str,
				 value,
				 description: str,
				 format_str: str,
				 ):
		self.format_str = format_str
		self.format_name = wcif.format_dict[format_str]

		super().__init__(name, value, description)

	@classmethod
	def init_default_option(cls,
							format_str: str,
							num_blanks=52,
							):
		format_name = wcif.format_dict[format_str]

		name = cls.name_format.format(format_name)
		description = cls.description_format.format(format_name)

		return cls(name, num_blanks, description, format_str)

	@classmethod
	def init_from_xlsx(cls,
					   format_str: str,
					   xlsx_value=None,
					   ):
		format_name = wcif.format_dict[format_str]

		name = cls.name_format.format(format_name)
		description = cls.description_format.format(format_name)

		return cls(name, xlsx_value, description, format_str)

	def get_args_for_xlsx(self):
		return [self.format_str]

	def check_value(self):
		return isinstance(self.value, int) and self.value >= 0

class RoomAbbrOption(Option):
	name_format = 'Abbreviation for {}'
	# TODO: fact check leaving blank
	description_format = 'Abbreviation for {}. This will appear at the start of the group on scorecards, e.g. W1 if the abbreviation is W. Leave blank if you do not want scorecards to include an abbreviation for this stage.'

	def __init__(self,
				 name: str,
				 value,
				 description: str,
				 room_name: str,
				 ):
		self.room_name = room_name

		super().__init__(name, value, description)

	@classmethod
	def init_default_option(cls,
							 room_name: str,
							 default_room_abbr=None,
							 ):
		name = cls.name_format.format(room_name)
		description = cls.description_format.format(room_name)

		if default_room_abbr == None:
			default_room_abbr = room_name[0]

		return cls(name, default_room_abbr, description, room_name)

	@classmethod
	def init_from_xlsx(cls,
					   room_name,
					   xlsx_value=None,
					   ):
		name = cls.name_format.format(room_name)
		description = cls.description_format.format(room_name)

		return cls(name, xlsx_value, description, room_name)

	def get_args_for_xlsx(self):
		return [self.room_name]

	def check_value(self):
		return isinstance(self.value, str)

class CumulativeScorecardOption(Option):
	name = 'Shared scorecards for cumulative time limits'
	# TODO: fact check leaving blank
	description = 'Type "Y" to create shared scorecards for events with cumulative time limits. WARNING: This is only guaranteed to look right for two Mo3 events with no cutoff.'

	@classmethod
	def init_default_option(cls,
							):
		return cls(cls.name, '', cls.description)

	@classmethod
	def init_from_xlsx(cls,
					   room_name,
					   xlsx_value=None,
					   ):
		return cls(cls.name, xlsx_value, cls.description)

	def get_args_for_xlsx(self):
		return []

	# TODO: maybe raise exception if something other than "Y" or "y" is typed
	def check_value(self):
		return True

# Mapping of class to ID.
# Avoid changing the order of classes (i.e., only append a class to the end of the list).
options_classes = [
	Option,
	GroupByOption,
	NumBlanksForRoundOption,
	NumBlanksForFormatOption,
	RoomAbbrOption,
]

# TODO:
# OptionsXLSX needs:
# - List of options
# - A way to generate the XLSX
# - A way to retrieve options from the XLSX by name and check their values
#
# 2 ways to initialize an OptionsXLSX object:
# - From WCIF data? (this makes the most sense; read the WCIF data and generate it here)
# - From the actual XLSX file
class OptionsXLSX():
	def __init__(self,
				 options_dict: OrderedDict):
		self.options_dict = options_dict

	# TODO: finish
	@classmethod
	def init_from_xlsx(cls, file_name: str):
		workbook = openpyxl.load_workbook(file_name)
		data_worksheet = workbook.worksheets[0]
		metadata_worksheet = workbook.worksheets[1]

		options_dict = OrderedDict()

		for row_num, metadata_row in enumerate(metadata_worksheet.iter_rows(min_row=2), start=2):
			_class = options_classes[metadata_row[0].value]
			arg_count = metadata_row[1].value

			arg_list = []
			for i in range(0, arg_count):
				arg_list.append(metadata_row[2 + i].value)

			xlsx_value = data_worksheet[row_num][1].value

			option = _class.init_from_xlsx(*arg_list, xlsx_value=xlsx_value)

			cls.add_option(options_dict, option)

		return cls(options_dict)

	@classmethod
	def init_from_wcif(cls, wcif_json: dict):
		options_dict = OrderedDict()

		### Room abbreviations ###
		rooms_dict = wcif.get_rooms_dict(wcif_json)

		# Default: no abbreviation for one room
		if len(rooms_dict) == 1:
			cls.add_option(options_dict, RoomAbbrOption.init_default_option(rooms_dict[0]['name'], default_room_abbr=''))
		else:
			for room in rooms_dict:
				cls.add_option(options_dict, RoomAbbrOption.init_default_option(room['name']))


		### Group scorecards by (group number/room) ###
		cls.add_option(options_dict, GroupByOption.init_default_option())

		# TODO: is this needed?
		#activity_id_to_persons_list_dict = wcif.get_activity_id_to_persons_list_dict(wcif_json)

		### Blanks per round ###
		events_dict = wcif_json['events']
		for event_dict in events_dict:
			for round_dict in event_dict['rounds']:
				event_round_str = wcif.round_id_to_event_round_str(round_dict['id'], events_dict)

				event_id = event_dict['id']
				# e.g. 333-r1 -> 1
				round_num = round_dict['id'].split('-')[1][1:]


				# TODO: fix the function and delete this try except block
				try:
					persons_list = wcif.event_round_to_persons_list(wcif_json, event_id, round_num)
				except KeyError:
					persons_list = []

				num_persons = len(persons_list)

				# TODO: subsequent rounds; need to account for "advancementCondition"
				# TODO: error handling for a Round 1 with no competitors
				if num_persons == 0:
					try:
						num_persons = wcif.get_num_advancing_to_this_round(wcif_json, f'{event_id}-r{round_num}')
					except:
						print(f'Warning: No groups assigned for {wcif.event_id_to_name(event_id)} Round {round_num}.')
						num_persons = 0
					only_blanks = True
				else:
					only_blanks = False

				cls.add_option(options_dict, NumBlanksForRoundOption.init_default_option(event_round_str, num_persons, only_blanks=only_blanks))

		### Blanks per format ###
		formats_set = set()

		# Get all formats in the competition
		for event_dict in events_dict:
			for round_dict in event_dict['rounds']:
				formats_set.add(round_dict['format'])

		# TODO: maybe be a little smarter about determining the number of blanks
		for format_str in formats_set:
			cls.add_option(options_dict, NumBlanksForFormatOption.init_default_option(format_str))

		return cls(options_dict)

	@classmethod
	def add_option(cls,
				   options_dict: dict,
				   option: Option,
				   ):
		options_dict[option.name] = option

	def create_xlsx(self,
					file_name: str,
					):
		# Thanks ChatGPT!
		xlsx_data = []
		xlsx_data.append(['Name', 'Default value', 'Description'])

		# Data necessary to replicate the OptionsXLSX from the CSV file
		metadata = []

		start_of_header = ['class_id', 'arg_count']

		metadata.append(copy.deepcopy(start_of_header))

		# TODO: need to add number of columns corresponding to number of args
		for option in self.options_dict.values():
			xlsx_data.append([option.name, option.value, option.description])

			metadata_row = []
			class_id = options_classes.index(option.__class__)
			metadata_row.append(class_id)

			# TODO: add position of "Options" configurable argument in the list of initializer arguments
			# TODO: need to add support for this for every class
			arg_list = option.get_args_for_xlsx()
			arg_count = len(arg_list)

			metadata_row.append(arg_count)
			metadata_row += arg_list

			# Add any needed columns, i.e. arg0, arg1, arg2, etc.
			header_row = metadata[0]
			if len(header_row) < len(start_of_header) + len(arg_list):
				for i in range(len(header_row) - len(start_of_header), len(arg_list)):
					arg_id = i
					header_row.append(f'arg_{arg_id}')

			metadata.append(metadata_row)

		workbook = Workbook()

		worksheet = workbook.active
		worksheet.title = 'Options'

		for row in xlsx_data:
			worksheet.append(row)

		# Determine the width of each column
		for i, column in enumerate(zip(*xlsx_data), start=1):
			max_text_length = max(len(str(value)) for value in column)
			column_width = max_text_length + 3
			worksheet.column_dimensions[get_column_letter(i)].width = column_width

		worksheet = workbook.create_sheet('Metadata (DO NOT EDIT)')

		for row in metadata:
			worksheet.append(row)

		# Determine the width of each column
		for i, column in enumerate(zip(*metadata), start=1):
			max_text_length = max(len(str(value)) for value in column)
			column_width = max_text_length + 3
			worksheet.column_dimensions[get_column_letter(i)].width = column_width

		workbook.save(file_name)
