import os
import math

from typing import Callable, Tuple

from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

import arabic_reshaper
from bidi.algorithm import get_display

from PIL import Image, ImageDraw, ImageFont, ImageColor
from io import BytesIO

# TODO: platform-dependent
font_dir = os.path.join('/', 'mnt', 'c', 'Windows', 'Fonts')

# Source for Unicode ranges: https://www.ling.upenn.edu/courses/Spring_2003/ling538/UnicodeRanges.html

# Check if character is within given Unicode ranges.
# Useful for checking if a character is within a script.
# TODO: variables; note that ranges is (inclusive, exclusive)
def is_char_in_ranges(char,
					  *ranges,
					  ) -> bool:
	for _range in ranges:
		if ord(char) in range(_range[0], _range[1]):
			return True

	return False

# TODO: comment explaining why this is needed
# TODO: multi-line text for long translations? (or just keep shrinking until it fits on one line)
def get_translation_image(text: str,
						  font_path: str,
						  font_size: int,
						  ) -> BytesIO:
	# TODO: delete unused stuff
	scale = 30

	font = ImageFont.truetype(font_path, font_size*scale)

	# Start with a comically large canvas, then size it up based on the size of the text
	# TODO: I had to increase the width from 5000 to 8000 for competitor 2025RAMM01. Find a good way to handle this dynamically.
	# TODO: also 5000 is probably too much
	image = Image.new("RGB", (8000, 5000), ImageColor.getrgb("white"))
	draw = ImageDraw.Draw(image)
	draw.fontmode = "L"

	text_bbox = draw.text((0, 0), text, fill=ImageColor.getrgb("black"), font=font, font_size=font_size*scale)
	text_bbox = draw.textbbox((0, 0), text, font=font, font_size=font_size*scale)

	cropped_image = image.crop(text_bbox)

	buffer = BytesIO()
	cropped_image.save(buffer, format="PNG")
	buffer.seek(0)
	return buffer


class Language():
	def __init__(self,
			  	 language: str,
			  	 font_name: str,
				 font_path: str,
				 is_char_in_language: Callable,
				 font_size=0,
				 process_text=None,
				 get_image=None,
				 ):
		self.language = language
		self.font_name = font_name
		self.font_path = font_path
		self.is_char_in_language = is_char_in_language

		try:
			# TODO: warn if font is already registered? (in theory, we could override the previously registered font)
			pdfmetrics.registerFont(TTFont(font_name, font_path))
		except NameError:
			# TODO: use logger
			print(f"Warning: Path {font_path} not found for font {font_name}. Translations for language {language} will not be supported.")
			return None

		if font_size < 0:
			raise ValueError(f"font_size must be greater than 0 (value is {font_size}).")

		self.font_size = font_size

		if process_text != None and get_image != None:
			raise ValueError("Language class does not support values for both process_text and get_image. Please use only one of these arguments.")

		self.process_text = process_text
		self.get_image = get_image

	def is_str_in_language(self,
						   text: str
						   ):
		for char in text:
			if not (char.isspace() or self.is_char_in_language(char)):
				return False

		return True

	def get_pdf_element(self,
						text: str,
						) -> BytesIO | Tuple[str, str, int]:
		if self.get_image:
			# TODO: draw image using pillow, and store in buffer
			return self.get_image(text, self.font_path, self.font_size)
		else:
			if self.process_text:
				return self.process_text(text), self.font_name, self.font_size
			else:
				return text, self.font_name, self.font_size

# TODO: option to init from json (or python file?), with a JSON for different platforms
# TODO: font might already be registered
# basically I just don't like defining language data in the middle of the Python file like this lol
class LanguageList():
	def __init__(self):
		self.language_list = []

		self.add_language("Arabic",
						  "Arial",
						  os.path.join(font_dir, 'arial.ttf'),
						  lambda char: is_char_in_ranges(char, (0x600, 0x6ff+1)),
						  font_size=16,
						  process_text=lambda text: get_display(arabic_reshaper.reshape(text)),
		)

		self.add_language("Cyrillic",
						  "Arial",
						  os.path.join(font_dir, 'arial.ttf'),
						  lambda char: is_char_in_ranges(char, (0x400, 0x52f+1)),
						  font_size=16,
		)

		self.add_language("Chinese/Japanese/Korean Unified Symbols",
						  "Microsoft YaHei",
						  os.path.join(font_dir, 'msyh.ttc'),
						  lambda char: is_char_in_ranges(char, (0x4e00, 0x9fff+1)),
						  font_size=16,
		)

		self.add_language("Korean",
						  "Malgun Gothic",
						  os.path.join(font_dir, 'malgun.ttf'),
						  lambda char: is_char_in_ranges(char, (0xac00, 0xd7af+1)),
						  font_size=16,
		)

		self.add_language("Thai",
						  "Tahoma",
						  os.path.join(font_dir, 'Tahoma.ttf'),
						  lambda char: is_char_in_ranges(char, (0xe00, 0xe7f+1)),
						  font_size=16,
		)

		# Reportlab doesn't render Devanagari text correctly.
		# Need to use PIL to render the text instead.
		self.add_language("Devanagari",
						  "Nirmala",
						  os.path.join(font_dir, 'Nirmala.ttc'),
						  lambda char: is_char_in_ranges(char, (0x900, 0x97f+1)),
						  font_size=16,
						  get_image=get_translation_image,
		)

		self.add_language("Tamil",
						  "Nirmala",
						  os.path.join(font_dir, 'Nirmala.ttc'),
						  lambda char: is_char_in_ranges(char, (0xb80, 0xbff+1)),
						  font_size=16,
						  get_image=get_translation_image,
		)

		self.add_language("Armenian",
						  "Arial",
						  os.path.join(font_dir, 'arial.ttf'),
						  lambda char: is_char_in_ranges(char, (0x530, 0x58f+1)),
						  font_size=16,
						  get_image=get_translation_image,
		)


	# Add a language, assuming its font is available on the system.
	# Arguments must match Language constructor arguments.
	def add_language(self,
				  	 *args,
					 **kwargs
					 ):
		language = Language(*args, **kwargs)

		if language != None:
			self.language_list.append(language)

	# TODO: warn if multiple matches
	def get_language_obj(self,
					 	 text: str,
					 	 ) -> Language | None:
		for language in self.language_list:
			if language.is_str_in_language(text):
				return language

		return None

	def get_pdf_element(self,
					 	text: str,
						) -> BytesIO | Tuple[str, str, int] | None:
		language = self.get_language_obj(text)

		if language == None:
			return None

		return language.get_pdf_element(text)

language_list = LanguageList()

# TODO: delete below
#
# TODO: Devanagari text rendering is wrong. Find a solution for this.
#	elif all_chars_in_range(text_no_whitespace, 0x900, 0x97f):
#		return 'Mangal', 16
