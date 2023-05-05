from PIL import Image
from io import BufferedReader

import argparse
import struct
import sys
import os

import lib.image_codecs as image_codecs
from lib.utils import calc_checksum, print_hex


RES_TYPES = {
	0x00: 'UNKNOWN 00',
	0x01: 'UNKNOWN 01',
	0x02: 'UNKNOWN 02',
	0x03: 'Localisation string, UTF8',
	0x04: 'UNKNOWN 04',
	0x05: 'RGB-565 Image',
	0x06: 'UNKNOWN 06',
	0x07: 'RGB-565 gzip image',
	0x08: 'RGBA-565 gzip image',
	0x09: 'UNKNOWN 09',
	0x0A: 'UNKNOWN 10',
	0x0B: 'RGB-8888 (RGBA) image',  # 11
}


parser = argparse.ArgumentParser(description='PowKiddy RESource unpacker')
parser.add_argument('files', nargs='+', type=argparse.FileType('rb'))
args = parser.parse_args()

if len(args.files) == 0:
	print("No file specified")
	exit(1)

src_file: BufferedReader
for src_file in args.files:
	src_name = os.path.basename(src_file.name)
	src_dir = os.path.dirname(src_file.name)

	if not src_file or not src_file.readable:
		print(src_name, "is not readable!")
		exit(2)

	dir = os.path.join(src_dir, src_name + "_DATA")
	os.makedirs(dir, exist_ok=True)

	# Read header info
	#          25 24      192     2
	#  52 45 53 19 18 00 00 c0 00 02 00 00 00 00 00 00
	#   R  E  S  .  .  .  .  A  .  .  .  .  .  .  .  .
	# |   MAGIC   |IC|             UNKNOWN            |

	f_type, res_version, items_count, unkn_byte_1, unkn_byte_2, unkn_byte_3, unk_str = struct.unpack(
		'<3sBBBBB8s', src_file.read(16))
	print(f'## {src_name}: {items_count} item(s):')
	print('  | FILE    | OFFSET   | SIZE | RESOURCE TYPE')
	#     ' - 123456789 1234567890 123456 12345678901234567890123456789012'
	if f_type.decode() != 'RES':
		print("ERROR: Not a resource")
		exit(3)

	resources = {}
	curr_offset = 16
	for i in range(items_count):
		src_file.seek(curr_offset)  # Go to last saved offset
		#  40 03 00 00 f3 00 08 50 49 43 31 00 00 00 00 00
		# |  << 832   | 243 | 8| P  I  C  1               |
		# |FILE OFFSET|SIZE |RT|         File name        |
		data_offset, data_lenght, res_type, file_name = struct.unpack('<LHB9s', src_file.read(16))
		curr_offset += 16

		file_name = file_name.decode().rstrip('\x00')
		print(
			f' - {file_name: <9} {data_offset: <10} {data_lenght: <6} {RES_TYPES[res_type]: <32}')

		src_file.seek(data_offset)  # Go to file start
		data = src_file.read(data_lenght)  # Read file

		if res_type in (3, 4):
			# Text string
			print(" >", data.decode()[:128])
			with open(f"{dir}/{file_name}.txt", "wb") as out:
				out.write(data[:-1])
			continue

		if res_type == 5:
			# Image
			width, height = struct.unpack('<HH', data[:4])
			size = width * height * 3

			if size != data_lenght:
				src_file.seek(data_offset)
				data = src_file.read(size + 4)  # Plus 4 bytes of width/height info

			# Save as png image
			img = Image.frombytes("RGBA", (width, height), data[4:], image_codecs.RES_PNG)
			img.save(f"{dir}/{file_name}.png")
			continue

		if res_type in (7, 8):
			# Animation/compressed image
			width, height, size = struct.unpack('<HHL', data[:8])

			img = Image.frombytes(
				"RGB" if res_type == 7 else "RGBA",
				(width, height),
				data[8:],
				image_codecs.RES_GZIP_PNG
			)

			img.save(f"{dir}/{file_name}.png")
			continue

		if res_type == 11:
			# Image, 32 bit, RGBA
			width, height = struct.unpack('<HH', data[:4])
			size = width * height * 4

			src_file.seek(data_offset + 4)

			img = Image.frombytes("RGBA", (width, height), src_file.read(size))
			img.save(f"{dir}/{file_name}.png")
			continue

		print("\tUNKNOWN DATA:", print_hex(data))
		with open(f"{dir}/{file_name}.bin", "wb") as out:
			out.write(data)

	src_file.close()
