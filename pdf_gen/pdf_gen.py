import os
import EDITME

from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.platypus import Table, Paragraph
from reportlab.platypus.tables import TableStyle

from pathlib import Path
from io import BytesIO

from languages import language_list

PAGE_WIDTH = 8.5
PAGE_HEIGHT = 11

def gen_scorecards_pdf(competition_id: str,
					   scorecards_dict: dict,
					   ) -> None:

	directory = Path('Scorecards', competition_id)
	directory.mkdir(parents=True, exist_ok=True)

	# Generate scorecards for events with shared cumulative time limits, if requested.
	### TODO: confirm this is the desired behavior from the options ###
#	for event in scorecards_dict:

	# Generate remaining per-event scorecard PDFs
	for event in scorecards_dict:
		event_with_underscores = event.replace(' ', '_')
		file_name = f'{competition_id}_{event_with_underscores}.pdf'
		file_path = os.path.join(directory, file_name)
		gen_scorecards_pdf_for_event(file_path, scorecards_dict[event])

def gen_scorecards_pdf_for_event(file_path: str,
								 scorecards_dict: dict,
								 ) -> None:

	c = canvas.Canvas(file_path)
	c.setPageSize((PAGE_WIDTH*inch, PAGE_HEIGHT*inch))

	# This makes sure rounds are printed in the correct order
	rounds_sorted = [_round for _round in scorecards_dict]
	rounds_sorted = sorted(rounds_sorted)

	for _round in rounds_sorted:
		gen_scorecards_pages_for_round(c, scorecards_dict[_round])

	c.save()

def gen_scorecards_pages_for_round(c: canvas.Canvas,
								   scorecards_list: list,
								   ) -> None:

	for i in range(0, len(scorecards_list), 4):
		curr_scorecards = scorecards_list[i:i+4]
		gen_scorecards_page(c, curr_scorecards)


# TODO: check for only 4 in the list?
def gen_scorecards_page(c: canvas.Canvas,
					   scorecards_list: list
					   ):

	draw_dashed_lines(c)

	# Origins
	x_origin_list = [0*inch, (PAGE_WIDTH/2)*inch, 0*inch, (PAGE_WIDTH/2)*inch]
	y_origin_list = [PAGE_HEIGHT*inch, PAGE_HEIGHT*inch, (PAGE_HEIGHT/2)*inch, (PAGE_HEIGHT/2)*inch]
	# TODO: need to check for length (i.e., can't be greater than 4)

	for i in range(0, len(scorecards_list)):
		scorecard = scorecards_list[i]

		c.saveState()
		c.translate(x_origin_list[i], y_origin_list[i])

		# TODO: cleaner handling of multiple events
		multi_event = scorecard['multi_event']

		y_pos = print_header_table(c, scorecard['competition'], scorecard['id'], scorecard['event'], scorecard['round_text'], scorecard['group'])

		name_split = scorecard['name'].split(' (')

		competitor_name = name_split[0]

		translation_pdf_element = None

		if len(name_split) > 1:
			competitor_translation = name_split[1].replace(')','')
			translation_pdf_element = language_list.get_pdf_element(competitor_translation)

			if not translation_pdf_element:
				print(f'Warning: Language not supported for the translation of {competitor_name}. Translation will not be printed. (Byte representation: {competitor_translation.encode()})')
		else:
			competitor_translation = ''
			translation_font, translation_size = None, None

		if scorecard['wca_id']:
			wca_id = scorecard['wca_id']
		else:
			wca_id = 'New Competitor'

		# TODO: add image drawing
		if translation_pdf_element != None:
			# Competitor name
			y_pos = print_center_text(c, competitor_name, size=21, y_offset=y_pos, top_padding=0.04*inch, bottom_padding=0.04*inch)

			# Translation
			if isinstance(translation_pdf_element, tuple):
				# Text
				competitor_translation, translation_font, translation_size = translation_pdf_element
				y_pos = print_center_text(c, competitor_translation, font=translation_font, size=translation_size, y_offset=y_pos, top_padding=0, bottom_padding=0.05*inch)
			elif isinstance(translation_pdf_element, BytesIO):
				# Image
				y_pos = draw_center_image(c, translation_pdf_element, y_offset=y_pos, top_padding=0.04*inch, bottom_padding=0.04*inch)
			else:
				raise TypeError(f'Invalid type for translation_pdf_element ({type(translation_pdf_element)})')

			# WCA ID
			y_pos = print_center_text(c, wca_id, size=12, y_offset=y_pos, bottom_padding=0.08*inch)
		else:
			# Make the name and WCA ID larger if there's no translation (or the translation language is unsupported)
			y_pos = print_center_text(c, competitor_name, size=26, y_offset=y_pos, top_padding = 0.08*inch, bottom_padding=0.095*inch)
			y_pos = print_center_text(c, wca_id, size=16, y_offset=y_pos, bottom_padding=0.095*inch)


		colon = ':' if ':' in scorecard['time_limit'] else ''

		first_colon_pos = scorecard['time_limit'].find(':')
		time_limit_pre_colon = scorecard['time_limit'][0:first_colon_pos] + colon
		time_limit_post_colon = scorecard['time_limit'][(first_colon_pos + 1):]

		y_pos = print_bold_then_reg(c, time_limit_pre_colon, time_limit_post_colon, size=10, y_offset=y_pos)

		y_pos = print_bold_then_reg(c, 'Penalty example', '4.25 + 2 = 6.25', size=10, y_offset=y_pos)

		pre_cutoff_rows = 0
		post_cutoff_rows = 0

		if scorecard['format'] == 'a':
			# Average of 5
			pre_cutoff_rows = 2
			post_cutoff_rows = 3
		elif scorecard['format'] == 'm':
			# Mean of 3
			# TODO: does FMC/MBLD support a Bo2 with Mo3 cutoff?
			# (Not asking because I want to support it, asking because I want to know if I need to explicitly not support it)
			pre_cutoff_rows = 1
			post_cutoff_rows = 2
		elif scorecard['format'] == '3':
			# Best of 3
			pre_cutoff_rows = 3
			post_cutoff_rows = 0
		elif scorecard['format'] == '2':
			# Best of 2
			pre_cutoff_rows = 1
			post_cutoff_rows = 1
		elif scorecard['format'] == '1':
			# Best of 1
			pre_cutoff_rows = 1
			post_cutoff_rows = 0
		# TODO: cleaner way of doing this
		elif scorecard['multi_event']:
			# TODO: not necessarily 6 lol. just integrate this more cleanly with single scorecards.
			pre_cutoff_rows = 6
			post_cutoff_rows = 0
		else:
			raise Exception(f"Format {scorecard['format']} not recognized. Must be 'a', 'm', '3', '2', or '1'.")

		y_pos = print_pre_cutoff_table(c, pre_cutoff_rows, multi_event, y_offset=y_pos - 0.05*inch)

		if post_cutoff_rows > 0:
			colon = ':' if ':' in scorecard['cutoff'] else ''
			first_colon_pos = scorecard['cutoff'].find(':')
			cutoff_pre_colon = scorecard['cutoff'][0:first_colon_pos] + colon
			cutoff_post_colon = scorecard['cutoff'][(first_colon_pos + 1):]
			y_pos = print_bold_then_reg(c, cutoff_pre_colon, cutoff_post_colon, size=10, y_offset=y_pos - 0.03*inch)

			y_pos = print_post_cutoff_table(c, pre_cutoff_rows + 1, pre_cutoff_rows + post_cutoff_rows, y_offset=y_pos - 0.03*inch)

		y_pos = print_bold(c, "Extras", size=10, y_offset=y_pos - 0.03*inch)

		num_extras = 1 if multi_event else 2
		print_extra_table(c, num_extras, multi_event, y_offset=y_pos - 0.03*inch)

		c.restoreState()

	c.showPage()

def draw_dashed_lines(c):
	c.setDash(5, 6)
	c.line(8.5/2*inch, 0*inch, 8.5/2*inch, 11*inch)
	c.line(0, 11/2*inch, 8.5*inch, 11/2*inch)

	# Disable dashed line
	c.setDash(1, 0)

def print_header_table(c, comp_name, person_id, event, _round, group):
	# TODO: ugly. also this assumes all shared cumulative limits are the same round.
	if isinstance(event, list):
		strings = [f'{_event} {__round}' for _event, __round in zip(event, _round)]
		event_round_string = '\n'.join(strings)
		s = 's'
		third_row_height = 34
	else:
		event_round_string = f'{event} {_round}'
		s = ''
		third_row_height = 21

	data = [[comp_name],
			['ID', f'Event{s}', 'Group'],
			[person_id, event_round_string, group]]
	t = Table(data,
			colWidths=[0.6*inch, 2.5*inch, 0.6*inch],
			rowHeights=[19.5, 18, third_row_height])
	t.setStyle(TableStyle(
		[('ALIGN', (0,0), (-1,-1), 'CENTRE'),
		('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
		('GRID', (0,0), (-1,-1), 0.7, colors.black),

		# First two rows are gray and bold
		('BACKGROUND', (0,0), (2,1), colors.lightgrey),
		('FONT', (0,0), (2,1), 'ArialBd'),

		# Last row is not bold
		('FONT', (0,2), (2,2), 'Arial'),

		# First row should be one column
		('SPAN', (0,0), (2,0)),

		# First row size
		('FONTSIZE', (0,0), (0,0), 10.5),

		# Second row size
		('FONTSIZE', (0,1), (-1,1), 10),

		# Third row size
		('FONTSIZE', (0,2), (-1,2), 12),
	]))

	width, height = t.wrapOn(c, 0, 0)
	x_pos = ((8.5/2 * inch) - width) / 2
	#y_pos = ((11/4 * inch) - height) / 2
	#t.wrapOn(c, 0, 0)
	#t.drawOn(c, 8.5/4*inch, -0.5*inch)
	y_pos = -0.3*inch - height
	t.drawOn(c, x_pos, y_pos)

	# Return next spot for drawing
	return y_pos

# Return True if all characters in 'text' are between 'lower' and 'upper'
# (inclusive). Otherwise, return False.
# lower and upper are inclusive
def all_chars_in_range(text, lower, upper):
	for char in text:
		if ord(char) < lower or ord(char) > upper:
			return False

	return True

# Note: string positions are calculated from the bottom of the text
def print_center_text(c, string, font='Arial', size=11, y_offset=0, top_padding=0, bottom_padding=0):
	final_size = size
	max_width = ((PAGE_WIDTH/2) - 0.55) * inch

	while final_size > 0:
		width = c.stringWidth(string, font, final_size)
		if width < max_width:
			break
		else:
			final_size -= 0.1
	else:
		raise Exception("Reached font size of 0. String is too long.")

	c.setFont(font, final_size)
	face = pdfmetrics.getFont(font).face
	box_height = (face.ascent - face.descent) / 1000 * size
	string_height = (face.ascent - face.descent) / 1000 * final_size
	c.drawCentredString((PAGE_WIDTH/4)*inch, y_offset - top_padding - (box_height + string_height) / 2 , string)

	return y_offset - box_height - (top_padding + bottom_padding)

def draw_center_image(c, image_buffer: BytesIO, y_offset=0, top_padding=0, bottom_padding=0):
	image = ImageReader(image_buffer)
	image_width, image_height = image.getSize() # "boo camel case" - WCAT
	# TODO: get from languages.py
	scale = 30

	# TODO: center it and position it correctly
	c.drawImage(ImageReader(image_buffer), ((PAGE_WIDTH/2)*inch - image_width/scale)/2,
				y_offset - top_padding - image_height/scale,
				width=image_width/scale, height=image_height/scale)

	return y_offset - image_height/scale - (top_padding + bottom_padding)

# Print str_bi in bold-italics, then a colon, then str_reg in the regular (non-bold, non-italicized) font.
def print_bold_then_reg(c, str_bold, str_reg, size=11, y_offset=0):
	p_style = ParagraphStyle('Normal',
		fontName='Arial',
		fontSize=size,
		alignment=TA_CENTER,
	)
	p = Paragraph(f'<b>{str_bold}</b> {str_reg}', p_style)

	#width, height = p.wrapOn(c, 8.5/2*inch, size)
	width, height = p.wrapOn(c, (PAGE_WIDTH/2 - 0.55)*inch, 0)
	x_pos = ((PAGE_WIDTH/2 * inch) - width) / 2
	y_pos = y_offset - height
	p.drawOn(c, x_pos, y_pos)

	return y_pos

def print_pre_cutoff_table(c, num_solves, multi_event, y_offset=0):
	if multi_event:
		col_1 = 'Event'
		col_1_width = 0.65*inch
		results_col_width = 2.0*inch
		col_1_entry = lambda x: ''
	else:
		col_1 = '#'
		col_1_width = 0.35*inch
		results_col_width = 2.3*inch
		col_1_entry = lambda x: str(x)

	data = [[col_1, 'S', 'Result', 'J', 'C']]
	for i in range(1, num_solves + 1):
		data.append([col_1_entry(i), '', '', '', ''])

	t = Table(data,
			colWidths=[col_1_width, 0.35*inch, results_col_width, 0.35*inch, 0.35*inch],
			rowHeights=[0.3*inch] * (num_solves + 1)
	)

	table_style = [
		('ALIGN', (0,0), (-1,-1), 'CENTRE'),
		('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
		('GRID', (0,0), (-1,-1), 0.7, colors.black),

		# First row is gray and bold
		('BACKGROUND', (0,0), (-1, 0), colors.lightgrey),
		('FONT', (0,0), (-1, 0), 'ArialBd'),

		# Subsequent rows are not bold
		('FONT', (1,1), (-1,-1), 'Arial'),

		# Font size for all rows
		('FONTSIZE', (0,0), (-1,-1), 10)
	]

	table_style.append(('FONT', (0,1), (0,-1), 'ArialBd'))

	t.setStyle(TableStyle(table_style))

	width, height = t.wrapOn(c, 0, 0)
	x_pos = ((PAGE_WIDTH/2 * inch) - width) / 2
	#y_pos = ((11/4 * inch) - height) / 2
	#t.wrapOn(c, 0, 0)
	#t.drawOn(c, PAGE_WIDTH/4*inch, -0.5*inch)
	y_pos = y_offset - height
	t.drawOn(c, x_pos, y_pos)

	# Return next spot for drawing
	#return [y_pos - (height/2)]
	#return [y_pos - height/2]
	return y_pos

def print_post_cutoff_table(c, first_solve, last_solve, y_offset=0):
	num_solves = last_solve - first_solve + 1
	data = []
	for i in range(first_solve, last_solve + 1):
		data.append([str(i), '', '', '', ''])

	t = Table(data,
			colWidths=[0.35*inch, 0.35*inch, 2.3*inch, 0.35*inch, 0.35*inch],
			rowHeights=[0.3*inch] * (num_solves)
	)

	table_style = [
		('ALIGN', (0,0), (-1,-1), 'CENTRE'),
		('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
		('GRID', (0,0), (-1,-1), 0.7, colors.black),

		('FONT', (1,1), (-1,-1), 'Arial'),

		('FONTSIZE', (0,0), (-1,-1), 10)
	]

	# Solve number is bold
	# TODO: integrate with table_style
	table_style.append(('FONT', (0,0), (0,-1), 'ArialBd'))

	t.setStyle(TableStyle(table_style))

	width, height = t.wrapOn(c, 0, 0)
	x_pos = ((PAGE_WIDTH/2 * inch) - width) / 2
	y_pos = y_offset - height
	t.drawOn(c, x_pos, y_pos)

	return y_pos

def print_bold(c, string, size=11, y_offset=0):
	c.setFont('ArialBd', size)
	face = pdfmetrics.getFont('ArialBd').face
	string_height = (face.ascent - face.descent) / 1000 * size
	c.drawCentredString(PAGE_WIDTH/4*inch, y_offset - string_height , string)

	return y_offset - string_height

def print_extra_table(c, num_solves, multi_event, y_offset=0):
	if multi_event:
		col_1_width = 0.65*inch
		results_col_width = 1.65*inch
		col_1_entry = lambda x: ''
	else:
		col_1_width = 0.35*inch
		results_col_width = 1.95*inch
		col_1_entry = lambda x: f'E{x}'

	data = []
	for i in range(1, num_solves + 1):
		data.append([col_1_entry(i), '', '', 'D', '', ''])

	t = Table(data,
			colWidths=[col_1_width, 0.35*inch, results_col_width, 0.35*inch, 0.35*inch, 0.35*inch],
			rowHeights=[0.3*inch] * (num_solves)
	)

	table_style = [
		('ALIGN', (0,0), (-1,-1), 'CENTRE'),
		('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
		('GRID', (0,0), (-1,-1), 0.7, colors.black),

		# Solve number is bold
		('FONT', (0,0), (0,-1), 'ArialBd'),
		('FONTSIZE', (0,0), (-1,-1), 10),

		# Delegate signature is large, bold, and light gray
		('FONT', (3,0), (3,-1), 'ArialBd'),
		('FONTSIZE', (3,0), (3,-1), 12),
		('TEXTCOLOR', (3,0), (3,-1), colors.lightgrey),
	]

	t.setStyle(TableStyle(table_style))

	width, height = t.wrapOn(c, 0, 0)
	x_pos = ((PAGE_WIDTH/2 * inch) - width) / 2
	y_pos = y_offset - height
	t.drawOn(c, x_pos, y_pos)

	return y_pos

# TODO: delete below
# TODO: need to add &nbsp; and non-breaking hyphen (idk what this character is lol) for event names for cumulative time limits
scorecard_0 = {
	'name' : 'David Karalli (ﺩﺍﻭﺩ ﻕﺭﺎﻌﻠﻳ)',
	'id' : '15',
	'wca_id': '2020KARA01',
	'competition' : 'Rocklin Winter 2024',
	'event' : '3x3x3 Blindfolded',
	'round' : 'Round 2',
	'group' : '1',
	'format': '3',
	'time_limit': 'Cumulative time limit: 2 hr for 3x3x3&nbsp;Blindfolded, 4x4x4&nbsp;Blindfolded, and 5x5x5&nbsp;Blindfolded',
}

scorecard_1 = {
	'name' : 'Tinker Tailor Soldier Sailor Rich Man Poor Man Beggar Man Thief',
	'id' : '225',
	'wca_id': '2016YORK09',
	'competition' : 'A Moon Shaped Pool 2024',
	'event' : '3x3x3 One-Handed',
	'round' : 'Round 1',
	'format' : '5',
	'group' : 'R4',
	'cutoff' : 'Cutoff: Continue if 1 or 2 < 45 sec',
	'time_limit' : 'Time limit: DNF if > 6 min 25 sec',
}

scorecard_blank = {
	'name' : '',
	'id' : '',
	'wca_id' : '',
	'competition' : 'Rocklin Winter 2024',
	'event' : '',
	'round' : '',
	'format' : '5',
	'group' : '',
	'cutoff' : 'Cutoff:' + "&nbsp;" * 30,
	'time_limit' : 'Time limit:' + "&nbsp;" * 30,
}

scorecard_list = [scorecard_0, scorecard_1, scorecard_0, scorecard_1,
	scorecard_1, scorecard_1, scorecard_0, scorecard_0,
	scorecard_1, scorecard_0, scorecard_1, scorecard_blank]
