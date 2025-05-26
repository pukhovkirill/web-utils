class VersionSelector:
    """
    Selects the smallest QR code version that can encode a given input
    using error correction level M.
    """

    # Maximum input capacities for QR Code versions 1 to 40 at error correction level M.
    # Each list corresponds to capacities for [numeric, alphanumeric, byte, kanji] modes.
    VERSIONS_CAPACITY = {
        1: [34, 20, 14, 8],
        2: [63, 38, 26, 16],
        3: [101, 61, 42, 26],
        4: [149, 90, 62, 38],
        5: [202, 122, 84, 52],
        6: [255, 154, 106, 65],
        7: [293, 178, 122, 75],
        8: [365, 221, 152, 93],
        9: [432, 262, 180, 111],
        10: [513, 311, 213, 131],
        11: [604, 366, 251, 155],
        12: [691, 419, 287, 177],
        13: [796, 483, 331, 204],
        14: [871, 528, 362, 223],
        15: [991, 600, 412, 254],
        16: [1082, 656, 450, 277],
        17: [1212, 734, 504, 310],
        18: [1346, 816, 560, 345],
        19: [1500, 909, 624, 384],
        20: [1600, 970, 666, 410],
        21: [1708, 1035, 711, 438],
        22: [1872, 1134, 779, 480],
        23: [2059, 1248, 857, 528],
        24: [2188, 1326, 911, 561],
        25: [2395, 1451, 997, 614],
        26: [2544, 1542, 1059, 652],
        27: [2701, 1637, 1125, 692],
        28: [2857, 1732, 1190, 732],
        29: [3035, 1839, 1264, 778],
        30: [3289, 1994, 1370, 843],
        31: [3486, 2113, 1452, 894],
        32: [3693, 2238, 1538, 947],
        33: [3909, 2369, 1628, 1002],
        34: [4134, 2506, 1722, 1060],
        35: [4343, 2632, 1809, 1113],
        36: [4588, 2780, 1911, 1176],
        37: [4775, 2894, 1989, 1224],
        38: [5039, 3054, 2099, 1292],
        39: [5313, 3220, 2213, 1362],
        40: [5596, 3391, 2331, 1435]
    }

    # Mapping of encoding mode names to indices in the capacity lists.
    MODE_INDICES = {
        'NUMERIC': 0,
        'ALPHANUMERIC': 1,
        'BYTE': 2,
        'KANJI': 3
    }

    def get_versions_info(self, num_chars, encoding_index):
        """
        Return the smallest QR code version that can hold num_chars
        for the given encoding_index. Returns None if no version fits.
        """
        for version, capacities in self.VERSIONS_CAPACITY.items():
            if capacities[encoding_index] >= num_chars:
                return version
        return None

    def smallest_version(self, text, encoding_mode):
        """
        Determine the smallest QR code version for the provided text
        and encoding_mode ('NUMERIC', 'ALPHANUMERIC', 'BYTE', 'KANJI').
        Raises ValueError for unsupported modes.
        """
        try:
            index = self.MODE_INDICES[encoding_mode]
        except KeyError:
            raise ValueError(f"Unsupported encoding mode: {encoding_mode}")
        num_chars = len(text)
        return self.get_versions_info(num_chars, index)
