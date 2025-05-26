from .version_selector import VersionSelector


class Encoder:
    """
    Encodes input text into a bit string suitable for QR code generation.
    It selects the encoding mode, adds mode and character count indicators,
    and applies terminator and padding to fill codeword blocks.
    """

    # Allowed characters in alphanumeric mode
    ALPHANUMERIC_CHARS = set('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ $%*+-./():')

    # Mode indicator bit patterns
    MODE_INDICATORS = {
        "NUMERIC": "0001",
        "ALPHANUMERIC": "0010",
        "BYTE": "0100",
        "KANJI": "1000"
    }

    # Alphanumeric character values for pairs encoding
    ALPHANUMERIC_VALUES = {
        **{str(i): i for i in range(10)},
        **{chr(ord('A') + i): 10 + i for i in range(26)},
        " ": 36, "$": 37, "%": 38, "*": 39,
        "+": 40, "-": 41, ".": 42, "/": 43, ":": 44
    }

    # QR block structure: [total CW, EC CW/block, #blocks type1, #blocks type2, data CW type1, data CW type2]
    BLOCK_INFO = {
        1: [16, 10, 1, 0, 16, 0],
        2: [28, 16, 1, 0, 28, 0],
        3: [44, 26, 1, 0, 44, 0],
        4: [64, 18, 2, 0, 32, 0],
        5: [86, 24, 2, 0, 43, 0],
        6: [108, 16, 4, 0, 27, 0],
        7: [124, 18, 4, 0, 31, 0],
        8: [154, 22, 2, 2, 38, 39],
        9: [182, 22, 3, 2, 36, 37],
        10: [216, 22, 4, 1, 43, 44],
        11: [254, 30, 1, 4, 50, 51],
        12: [290, 22, 6, 2, 36, 37],
        13: [334, 22, 8, 1, 37, 38],
        14: [365, 24, 4, 5, 40, 41],
        15: [415, 24, 5, 5, 41, 42],
        16: [453, 28, 7, 3, 45, 46],
        17: [507, 28, 10, 1, 46, 47],
        18: [563, 26, 9, 4, 43, 44],
        19: [627, 26, 3, 11, 44, 45],
        20: [669, 26, 3, 13, 41, 42],
        21: [714, 26, 17, 0, 42, 0],
        22: [782, 28, 17, 0, 46, 0],
        23: [860, 28, 4, 5, 121, 122],
        24: [914, 2, 6, 14, 45, 46],
        25: [1000, 28, 8, 13, 47, 48],
        26: [1062, 28, 19, 4, 46, 47],
        27: [1128, 28, 22, 3, 45, 46],
        28: [1193, 28, 3, 23, 45, 46],
        29: [1267, 28, 21, 7, 45, 46],
        30: [1373, 28, 19, 10, 47, 48],
        31: [1455, 28, 2, 29, 46, 47],
        32: [1541, 28, 10, 23, 46, 47],
        33: [1631, 28, 14, 21, 46, 47],
        34: [1725, 28, 14, 23, 46, 47],
        35: [1812, 28, 12, 26, 47, 48],
        36: [1914, 28, 6, 34, 47, 48],
        37: [1992, 28, 29, 14, 46, 47],
        38: [2102, 28, 13, 32, 46, 47],
        39: [2216, 28, 40, 7, 47, 48],
        40: [2334, 28, 18, 31, 47, 48]
    }

    # Character count indicator lengths by (max version, bit length)
    CHAR_COUNT_BITS = {
        "NUMERIC": [(9, 10), (26, 12), (40, 14)],
        "ALPHANUMERIC": [(9, 9), (26, 11), (40, 13)],
        "BYTE": [(9, 8), (40, 16)],
        "KANJI": [(9, 8), (26, 10), (40, 12)]
    }

    def __init__(self):
        # Version selector must remain as self.version for compatibility
        self.version = VersionSelector()
        # Preserve instance attributes for backward compatibility
        self.alphanum = self.ALPHANUMERIC_CHARS
        self.mode_indicators = self.MODE_INDICATORS
        self.alphanumeric_values = self.ALPHANUMERIC_VALUES
        self.block_info = self.BLOCK_INFO

    def determine_encoding(self, text):
        """
        Determine the best encoding mode for the given text.
        Returns one of 'NUMERIC', 'ALPHANUMERIC', 'BYTE', 'KANJI'.
        """
        if text.isnumeric():
            return "NUMERIC"
        if all(ch in self.alphanum for ch in text):
            return "ALPHANUMERIC"
        if self.is_iso8859_1(text):
            return "BYTE"
        if self.is_double_byte_jis(text):
            return "KANJI"
        # Fallback to byte mode
        return "BYTE"

    def encode(self, text):
        """
        Encode the input text into a bit string:
        1) Mode indicator
        2) Character count indicator
        3) Encoded data bits
        4) Terminator and alignment to 8 bits
        5) Pad bytes (0xEC, 0x11) to fill the QR data capacity
        """
        mode = self.determine_encoding(text)
        mode_bits = self.mode_indicators[mode]
        count_bits, version = self.get_char_count_indicator(text)
        data_bits = self.__get_encoded_data__(mode, text)

        bitstr = mode_bits + count_bits + data_bits
        bitstr = self.terminator_padding(version, bitstr)
        bitstr = self.pad_to_multiples_of_8(bitstr)
        bitstr = self.add_236_and_17(bitstr, version)

        return bitstr

    def is_iso8859_1(self, text):
        """Check if all characters can be encoded in ISO-8859-1."""
        try:
            text.encode('latin-1')
            return True
        except UnicodeError:
            return False

    def is_double_byte_jis(self, text):
        """
        Check if text can be encoded in Shift_JIS as valid double-byte characters
        (used for Kanji mode).
        """
        try:
            encoded = text.encode('shift_jis')
        except UnicodeEncodeError:
            return False
        if len(encoded) % 2 != 0:
            return False
        for i in range(0, len(encoded), 2):
            hb, lb = encoded[i], encoded[i + 1]
            if not ((0x81 <= hb <= 0x9F or 0xE0 <= hb <= 0xFC) and
                    (0x40 <= lb <= 0x7E or 0x80 <= lb <= 0xFC)):
                return False
        return True

    def get_char_count_indicator(self, text):
        """
        Compute the character count indicator bit string and select QR version.
        Returns (bit_string, version).
        """
        num_chars = len(text)
        mode = self.determine_encoding(text)
        version = self.version.smallest_version(text, mode)

        # Find appropriate bit length for this mode and version
        for max_v, bits in self.CHAR_COUNT_BITS[mode]:
            if version <= max_v:
                fmt = f'0{bits}b'
                return format(num_chars, fmt), version

        # Should never happen for version ≤ 40
        raise ValueError(f"Version {version} out of range for mode {mode}")

    def __get_encoded_data__(self, mode, text):
        """Dispatch to the specific encoding routine."""
        if mode == "NUMERIC":
            return self.numeric_encoding(text)
        if mode == "ALPHANUMERIC":
            return self.alphanumeric_encoding(text)
        if mode == "BYTE":
            return self.byte_encoding(text)
        # mode == "KANJI"
        return self.kanji_encoding(text)

    def terminator_padding(self, version, bitstr):
        """
        Append up to 4 zero bits or as many as remain to reach data capacity.
        """
        total_bits = self.block_info[version][0] * 8
        remaining = total_bits - len(bitstr)
        if remaining >= 4:
            return bitstr + '0000'
        return bitstr + '0' * remaining

    def pad_to_multiples_of_8(self, bitstr):
        """Pad with zero bits until length is a multiple of 8."""
        if len(bitstr) % 8:
            bitstr += '0' * (8 - len(bitstr) % 8)
        return bitstr

    def add_236_and_17(self, bitstr, version):
        """
        Add alternating pad bytes 0xEC and 0x11 until data capacity is filled.
        """
        total_bits = self.block_info[version][0] * 8
        pads = ['11101100', '00010001']
        idx = 0
        while len(bitstr) < total_bits:
            bitstr += pads[idx % 2]
            idx += 1
        return bitstr

    def numeric_encoding(self, text):
        """
        Encode numeric text in groups of up to 3 digits.
        Returns concatenated binary strings (no zero-fill).
        """
        parts = [text[i:i + 3] for i in range(0, len(text), 3)]
        return ''.join(bin(int(p))[2:] for p in parts)

    def alphanumeric_encoding(self, text):
        """
        Encode alphanumeric text in pairs. Two chars → 11 bits, one char → 6 bits.
        """
        pairs = [text[i:i + 2] for i in range(0, len(text), 2)]
        result = ""
        for grp in pairs:
            if len(grp) == 2:
                val = self.alphanumeric_values[grp[0]] * 45 + self.alphanumeric_values[grp[1]]
                result += format(val, '011b')
            else:
                val = self.alphanumeric_values[grp]
                result += format(val, '06b')
        return result

    def byte_encoding(self, text):
        """
        Encode text as bytes (ISO-8859-1 or UTF-8 fallback), each → 8 bits.
        """
        try:
            data = text.encode('iso-8859-1')
        except UnicodeError:
            data = text.encode('utf-8')
        return ''.join(format(b, '08b') for b in data)

    def kanji_encoding(self, text):
        """
        Encode Kanji text: two-byte Shift_JIS → 13-bit values per character.
        """
        data = text.encode('shift_jis')
        result = ""
        for i in range(0, len(data), 2):
            word = (data[i] << 8) | data[i + 1]
            if 0x8140 <= word <= 0x9FFC:
                offset = word - 0x8140
            else:
                offset = word - 0xC140
            val = ((offset >> 8) & 0xFF) * 0xC0 + (offset & 0xFF)
            result += format(val, '013b')
        return result
