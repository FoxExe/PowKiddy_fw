

def print_hex(data: bytes, sep: str = "", limit: int = 32):
	return sep.join("{:02X}".format(c) for c in data[:limit])


def calc_checksum(data: bytes):
	result = 0
	for pos in range(0, len(data) >> 2):
		result += int.from_bytes(data[pos * 4: pos * 4 + 4], 'little', signed=False)
	return (result & 0xFFFFFFFF).to_bytes(4, 'little', signed=False)


def cfg_hash(data1: bytes, data2: bytes):
	result = 0
	for i in range(len(data2)):
		result = result * 0x1000193 ^ data2[i]
