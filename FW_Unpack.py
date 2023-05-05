#!/usr/bin/env python

import argparse
import struct
import sys
import os
from io import BufferedReader
from lib.utils import calc_checksum, print_hex


ENC_PATTERN = b'\x11\x22\x33\x44\x55\x66\x77\x88\x99\xAA\xBB\xCC\xDD\xEE\xFF\x75'
FW_PATTERN = 'SFDNABDWFTCA'

HEADER_SIZE = 64
F_INFO_SIZE = 64
FS_FILE_EXT = {
	'FW': 'bin',
	'FAT16': 'FAT16.img',
	'FAT32': 'FAT32.img',
	'EXT4': 'EXT4.img',
	'ZIP': 'zip',
}

parser = argparse.ArgumentParser(description='Actions PAD .fw unpacker')
parser.add_argument('fw', nargs='?', type=argparse.FileType('rb'))
args = parser.parse_args()

src_file: BufferedReader = args.fw

src_name = os.path.basename(src_file.name)
src_dir = os.path.dirname(src_file.name)
dir = os.path.join(src_dir, src_name + "_DATA")
os.makedirs(dir, exist_ok=True)

magic, header_size, items = struct.unpack('<16sL16xB27x', src_file.read(HEADER_SIZE))
magic = magic.decode().strip('\x00')

print("=" * 64)
print("  File:", src_name)
print(" Items:", items)
print(" Magic:", magic)
print("=" * 64)
print('|# | File name      | FS     | Offset     | Size       |')
#     ' 12 1234567890123456 12345678 123456789012 123456789012 '

next_offset = HEADER_SIZE
p_num = 0
for i in range(items):
	src_file.seek(next_offset)
	name, fs_type, offset, size = struct.unpack('<16s8sL4xL28x', src_file.read(F_INFO_SIZE))

	# Text cleanup
	name = name.decode().strip('\x00')
	fs_type = fs_type.decode().strip('\x00')

	next_offset += F_INFO_SIZE
	p_num += 1

	print(F' {p_num: <2} {name: <16} {fs_type: <8} {offset: <12} {size: <12}')

	# Decode data
	src_file.seek(offset)  # Go to begin of file

	if fs_type == "FW":
		p_magic, p_size = struct.unpack('<12sL', src_file.read(16))

		# Encrypted data
		magic, enc_data_size, enc_sector_size = struct.unpack('<16sLL', src_file.read(32))
		if magic != ENC_PATTERN:
			print("Sorry, but i support only encryption v4...")
			continue

		with open(f'{dir}/{p_num}.{name}.bin', 'wb') as f:
			f.write(src_file.read(p_size))

		# Hmm... there is disk image after encrypted partition
		with open(f'{dir}/{p_num}.{name}.img', 'wb') as f:
			f.write(src_file.read(size - p_size - 16))

	else:
		# Save data as file
		with open(f'{dir}/{p_num}.{name}.{FS_FILE_EXT[fs_type]}', 'wb') as f:
			f.write(src_file.read(size))
