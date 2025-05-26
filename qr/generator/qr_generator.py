import numpy as np
from PIL import Image

from .encoder import Encoder
from .error_correction import ErrorCorrection
from .version_selector import VersionSelector


class QRCodeGenerator:
    """
    Generates a QR code matrix and exports it as a PNG image.
    """

    # Finder pattern template (7×7)
    FINDER_PATTERN = np.array([
        [1, 1, 1, 1, 1, 1, 1],
        [1, 0, 0, 0, 0, 0, 1],
        [1, 0, 1, 1, 1, 0, 1],
        [1, 0, 1, 1, 1, 0, 1],
        [1, 0, 1, 1, 1, 0, 1],
        [1, 0, 0, 0, 0, 0, 1],
        [1, 1, 1, 1, 1, 1, 1]
    ])

    # Alignment pattern centers by version
    ALIGNMENT_PATTERN_LOCATIONS = {
        2: [18, 6], 3: [22, 6], 4: [26, 6], 5: [30, 6], 6: [34, 6],
        7: [38, 22, 6], 8: [42, 24, 6], 9: [46, 26, 6], 10: [50, 28, 6],
        11: [54, 30, 6], 12: [58, 32, 6], 13: [62, 34, 6], 14: [66, 46, 26, 6],
        15: [70, 48, 26, 6], 16: [74, 50, 26, 6], 17: [78, 54, 30, 6],
        18: [82, 56, 30, 6], 19: [86, 58, 30, 6], 20: [90, 62, 34, 6],
        21: [94, 72, 50, 28, 6], 22: [98, 74, 50, 26, 6], 23: [102, 78, 54, 30, 6],
        24: [106, 80, 54, 28, 6], 25: [110, 84, 58, 32, 6], 26: [114, 86, 58, 30, 6],
        27: [118, 90, 62, 34, 6], 28: [122, 98, 74, 50, 26, 6], 29: [126, 102, 78, 54, 30, 6],
        30: [130, 104, 78, 52, 26, 6], 31: [134, 108, 82, 56, 30, 6], 32: [138, 112, 86, 60, 34, 6],
        33: [142, 114, 86, 58, 30, 6], 34: [146, 118, 90, 62, 34, 6], 35: [150, 126, 102, 78, 54, 30, 6],
        36: [154, 128, 102, 76, 50, 24, 6], 37: [158, 132, 106, 80, 54, 28, 6],
        38: [162, 136, 110, 84, 58, 32, 6], 39: [166, 138, 110, 82, 54, 26, 6],
        40: [170, 142, 114, 86, 58, 30, 6]
    }

    def __init__(self):
        # Version selector instance
        self.version_selector = VersionSelector()
        # Keep alignment locations as instance attribute for compatibility
        self.alignment_pattern_locations = self.ALIGNMENT_PATTERN_LOCATIONS

    def generate(self, text, output_file):
        """
        Main entry point: encodes text, builds the QR matrix, applies masking,
        adds format/version info, and saves as PNG.
        Returns the final matrix (without quiet zone).
        """
        encoder = Encoder()
        ec = ErrorCorrection()

        mode = encoder.determine_encoding(text)
        version = self.version_selector.smallest_version(text, mode)
        # compute raw data + EC bits
        final_bits = ec.generate_error_correction_codewords(text, version)

        size = 21 + (version - 1) * 4
        matrix = np.zeros((size, size), dtype=int)

        self.place_finder_patterns(matrix)
        align_positions = self.place_alignment_patterns(matrix, version)
        self.place_timing_patterns(matrix)
        self.place_dark_module(matrix, version)
        self.place_data(matrix, final_bits, version, align_positions)

        masked, best_mask = self.apply_best_mask(matrix, version, align_positions)
        fmt_bits = self.generate_format_string(best_mask)
        self.place_format_information(masked, fmt_bits)

        ver_bits = self.generate_version_information(version)
        self.place_version_information(masked, ver_bits)

        final = self.add_quiet_zone(masked)
        self.export_to_png(final, output_file, scale=10, quiet_zone=False)
        return masked

    def place_finder_patterns(self, mat):
        """Place three 7×7 finder patterns in corners."""
        mat[0:7, 0:7] = self.FINDER_PATTERN
        mat[0:7, -7:] = self.FINDER_PATTERN
        mat[-7:, 0:7] = self.FINDER_PATTERN

    def place_alignment_patterns(self, mat, version):
        """
        Place alignment patterns at predefined centers, skipping overlaps
        with finder patterns. Returns list of placed centers.
        """
        if version == 1:
            return []

        centers = self.alignment_pattern_locations[version]
        size = mat.shape[0]
        placed = []
        for r in centers:
            for c in centers:
                if not self._overlaps_finder(r, c, size):
                    placed.append((r, c))
                    self._place_single_alignment(mat, r, c)
        return placed

    def _overlaps_finder(self, r, c, size):
        """Check if (r,c) would overlap any finder or separator area."""
        return ((r < 8 and c < 8) or
                (r < 8 and c > size - 9) or
                (r > size - 9 and c < 8))

    def _place_single_alignment(self, mat, r, c):
        """Draw one 5×5 alignment pattern centered at (r,c)."""
        for dr in range(-2, 3):
            for dc in range(-2, 3):
                if abs(dr) == 2 or abs(dc) == 2 or (dr == 0 and dc == 0):
                    mat[r + dr, c + dc] = 1
                else:
                    mat[r + dr, c + dc] = 0

    def place_timing_patterns(self, mat):
        """Place horizontal and vertical timing patterns at row/col 6."""
        size = mat.shape[0]
        for i in range(8, size - 8):
            mat[6, i] = i % 2 == 0
            mat[i, 6] = i % 2 == 0

    def place_dark_module(self, mat, version):
        """
        Place the fixed 'dark module' at (4*version+9, 8).
        """
        idx = 4 * version + 9
        mat[idx, 8] = 1

    def place_data(self, mat, bits, version, align_pos):
        """
        Fill data modules in zig-zag columns, skipping functional areas.
        """
        size = mat.shape[0]
        idx = 0
        upward = True

        for col in range(size - 1, 0, -2):
            c = col - 1 if col == 7 else col
            rows = range(size - 1, -1, -1) if upward else range(size)
            for r in rows:
                for cc in (c, c - 1):
                    if cc < 0:
                        continue
                    if self._is_data_module(mat, r, cc, version, align_pos):
                        mat[r, cc] = bits[idx]
                        idx += 1
                        if idx >= len(bits):
                            return
            upward = not upward

    def _is_data_module(self, mat, r, c, version, align_pos):
        """Return True if (r,c) can hold data (not part of functional patterns)."""
        size = mat.shape[0]
        # finder & separators
        if (r < 9 and c < 9) or (r < 9 and c > size - 9) or (r > size - 9 and c < 9):
            return False
        # timing
        if r == 6 or c == 6:
            return False
        # alignment
        for (ar, ac) in align_pos:
            if ar - 2 <= r <= ar + 2 and ac - 2 <= c <= ac + 2:
                return False
        # dark module
        if (r, c) == (4 * version + 9, 8):
            return False
        return True

    def apply_best_mask(self, mat, version, align_pos):
        """
        Try all 8 masks, score them, and return the matrix with best mask and its index.
        """
        best_score = float('inf')
        best_mask = 0
        best_mat = None
        for mask in range(8):
            trial = self._apply_mask(mat, mask, version, align_pos)
            score = self._evaluate_mask(trial)
            if score < best_score:
                best_score, best_mask, best_mat = score, mask, trial
        return best_mat, best_mask

    def _apply_mask(self, mat, mask, version, align_pos):
        """Toggle bits per mask function on data modules."""
        sz = mat.shape[0]
        masked = mat.copy()
        for r in range(sz):
            for c in range(sz):
                if self._is_data_module(masked, r, c, version, align_pos):
                    if self._mask_func(mask, r, c):
                        masked[r, c] ^= 1
        return masked

    def _mask_func(self, m, r, c):
        """Mask patterns as defined by QR spec."""
        if m == 0:
            return (r + c) % 2 == 0
        elif m == 1:
            return r % 2 == 0
        elif m == 2:
            return c % 3 == 0
        elif m == 3:
            return (r + c) % 3 == 0
        elif m == 4:
            return (r // 2 + c // 3) % 2 == 0
        elif m == 5:
            return (r * c) % 2 + (r * c) % 3 == 0
        elif m == 6:
            return ((r * c) % 2 + (r * c) % 3) % 2 == 0
        else:
            return ((r + c) % 2 + (r * c) % 3) % 2 == 0

    def _evaluate_mask(self, mat):
        """Sum penalties for all four conditions."""
        return (self._eval1(mat) + self._eval2(mat) +
                self._eval3(mat) + self._eval4(mat))

    def _eval1(self, mat):
        """Condition 1: rows/cols runs of same color."""
        penalty = 0
        sz = mat.shape[0]
        for line in range(sz):
            count = 1
            # rows
            for col in range(1, sz):
                if mat[line, col] == mat[line, col - 1]:
                    count += 1
                else:
                    if count >= 5:
                        penalty += 3 + (count - 5)
                    count = 1
            if count >= 5:
                penalty += 3 + (count - 5)
        for col in range(sz):
            count = 1
            # cols
            for row in range(1, sz):
                if mat[row, col] == mat[row - 1, col]:
                    count += 1
                else:
                    if count >= 5:
                        penalty += 3 + (count - 5)
                    count = 1
            if count >= 5:
                penalty += 3 + (count - 5)
        return penalty

    def _eval2(self, mat):
        """Condition 2: 2×2 blocks of same color."""
        penalty = 0
        sz = mat.shape[0]
        for r in range(sz - 1):
            for c in range(sz - 1):
                if mat[r, c] == mat[r, c + 1] == mat[r + 1, c] == mat[r + 1, c + 1]:
                    penalty += 3
        return penalty

    def _eval3(self, mat):
        """Condition 3: patterns similar to finder patterns in data."""
        penalty = 0
        sz = mat.shape[0]
        pat = np.array([1, 0, 1, 1, 1, 0, 1])
        for r in range(sz):
            for c in range(sz - 6):
                if np.array_equal(mat[r, c:c + 7], pat):
                    if (c >= 4 and np.all(mat[r, c - 4:c] == 0)) or (
                            c + 11 <= sz and np.all(mat[r, c + 7:c + 11] == 0)):
                        penalty += 40
        for c in range(sz):
            for r in range(sz - 6):
                if np.array_equal(mat[r:r + 7, c], pat):
                    if (r >= 4 and np.all(mat[r - 4:r, c] == 0)) or (
                            r + 11 <= sz and np.all(mat[r + 7:r + 11, c] == 0)):
                        penalty += 40
        return penalty

    def _eval4(self, mat):
        """Condition 4: balance of dark modules."""
        total = mat.size
        dark = mat.sum()
        pct = (dark / total) * 100
        dist = min(abs((pct // 5) * 5 - 50), abs(((pct // 5) + 1) * 5 - 50))
        return int(dist / 5) * 10

    def generate_format_string(self, mask_pattern):
        """
        Compute 15-bit format string: 5 bits (EC+mask) + 10 EC bits, then XOR mask.
        """
        ec_level = '00'
        mask_bits = f'{mask_pattern:03b}'
        bits = ec_level + mask_bits
        poly_g = 0b10100110111
        poly = int(bits + '0' * 10, 2)
        for _ in range(5):
            shift = poly.bit_length() - poly_g.bit_length()
            if shift >= 0:
                poly ^= poly_g << shift
        ec_bits = f'{poly:010b}'
        fmt = bits + ec_bits
        return f'{int(fmt, 2) ^ 0b101010000010010:015b}'

    def place_format_information(self, mat, fmt_str):
        """Overlay the 15 format bits around timing patterns and corners."""
        sz = mat.shape[0]
        # horizontal, vertical arms
        for i in range(6):
            mat[8, i] = int(fmt_str[i])
            mat[i, 8] = int(fmt_str[14 - i])
        mat[8, 7] = int(fmt_str[7])
        mat[7, 8] = int(fmt_str[6])
        # bottom-left and top-right replicas
        for i in range(8):
            mat[sz - 1 - i, 8] = int(fmt_str[i])
            mat[8, sz - 1 - i] = int(fmt_str[14 - i])

    def generate_version_information(self, version):
        """
        Return 18-bit version information (6 data + 12 EC bits) for version ≥7.
        """
        if version < 7:
            return None
        data = int(f'{version:06b}' + '0' * 12, 2)
        poly_g = 0b1111100100101
        for _ in range(6):
            shift = data.bit_length() - poly_g.bit_length()
            if shift >= 0:
                data ^= poly_g << shift
        ec_bits = f'{data:012b}'
        return f'{version:06b}' + ec_bits

    def place_version_information(self, mat, ver_bits):
        """
        Place version information in two 3×6 areas for version ≥7.
        """
        if ver_bits is None:
            return
        sz = mat.shape[0]
        # bottom-left
        for i in range(6):
            for j in range(3):
                mat[sz - 11 + j, i] = int(ver_bits[i * 3 + j])
        # top-right
        for i in range(6):
            for j in range(3):
                mat[i, sz - 11 + j] = int(ver_bits[i * 3 + j])

    def add_quiet_zone(self, mat):
        """Surround matrix with a 4-module white border."""
        sz = mat.shape[0]
        out = np.zeros((sz + 8, sz + 8), dtype=int)
        out[4:4 + sz, 4:4 + sz] = mat
        return out

    def export_to_png(self, mat, filename, scale=10, quiet_zone=True):
        """
        Render matrix to a PIL image, scaling each module, and save as PNG.
        """
        if quiet_zone:
            mat = self.add_quiet_zone(mat)
        h, w = mat.shape
        img = Image.new('RGB', (w * scale, h * scale), 'white')
        px = img.load()
        for y in range(h):
            for x in range(w):
                if mat[y, x]:
                    for dy in range(scale):
                        for dx in range(scale):
                            px[x * scale + dx, y * scale + dy] = (0, 0, 0)
        img.save(filename)
