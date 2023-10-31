from lib.StaticVars import *
from lib.utils import DataReader, size_human

FIRMWARE = 'firmware.fw'


class FirmwareException(BaseException):
	pass


fw = DataReader(FIRMWARE)

magic = fw.read_string(16)
header_size = fw.read_int(4)
unknw_1 = fw.read_int(16)
items_count = fw.read_int(4)
unknw_2 = fw.read_int(24)

print(f"{fw.file_name} ({size_human(fw.file_size)}), {items_count} items:")
print('-' * 50)

if magic != FWU_MAGIC_WF:
	raise FirmwareException("Wrong magic string in file!")

items = []
for i in range(0, items_count):
	name = fw.read_string(16)
	filesystem = fw.read_string(8)
	offset = fw.read_int(8)
	size = fw.read_int(8)
	reserved = fw.read_bytes(24)
	print(f"{(name + '.' +filesystem):<24} {offset:>12} {size:>12} ({size_human(size):>9})")
	items.append((name, filesystem, offset, size))

if fw.get_pos() != header_size:
	raise FirmwareException("Wrong header size!")

print('-' * 50)

for item in items:
	name, fs, offset, size = item
	print(f"Unpacking {name:<16}", end=" ")

	# Go tofile start position
	fw.set_pos(offset)

	try:
		with open(f"{fw.file_name}.{name}.{fs}.bin", "wb") as f:
			f.write(fw.read_bytes(size))
	except FirmwareException as e:
		print('ERROR', e)
	else:
		print('[DONE]')
