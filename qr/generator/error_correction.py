from .encoder import Encoder
from .version_selector import VersionSelector
from bitarray import bitarray


class ErrorCorrection:
    """
    Handles Reed–Solomon error correction for QR codes using Galois Field arithmetic.
    """

    # Primitive polynomial for GF(256): x^8 + x^4 + x^3 + x^2 + 1
    PRIMITIVE_POLYNOMIAL = 0x11d
    GF_EXP_SIZE = 512
    GF_LOG_SIZE = 256

    # Number of remainder bits to append for each QR version (level M)
    REQUIRED_REMAINDER_BITS = {
        1: 0, 2: 7, 3: 7, 4: 7, 5: 7,
        6: 7, 7: 0, 8: 0, 9: 0, 10: 0,
        11: 0, 12: 0, 13: 0, 14: 3, 15: 3,
        16: 3, 17: 3, 18: 3, 19: 3, 20: 3,
        21: 4, 22: 4, 23: 4, 24: 4, 25: 4,
        26: 4, 27: 4, 28: 3, 29: 3, 30: 3,
        31: 3, 32: 3, 33: 3, 34: 3, 35: 0,
        36: 0, 37: 0, 38: 0, 39: 0, 40: 0
    }

    def __init__(self):
        # Encoder and version selector instances
        self.encoder = Encoder()
        self.version_selector = VersionSelector()

        # Galois Field tables
        self.gf_exp = [0] * self.GF_EXP_SIZE
        self.gf_log = [0] * self.GF_LOG_SIZE

        # Remainder bits map (with backward-compatible alias)
        self.required_remainder_bits = self.REQUIRED_REMAINDER_BITS
        self.requred_remainder_bits = self.required_remainder_bits  # backward compatibility

        # Initialize GF(256) tables
        self.init_galois_field()

    def init_galois_field(self):
        """
        Initialize exponent (gf_exp) and logarithm (gf_log) tables for GF(256) arithmetic.
        """
        x = 1
        for i in range(255):
            self.gf_exp[i] = x
            self.gf_log[x] = i
            x <<= 1
            if x & 0x100:
                x ^= self.PRIMITIVE_POLYNOMIAL
        # Extend gf_exp to support indices up to 511 for easy wrap-around
        for i in range(255, self.GF_EXP_SIZE):
            self.gf_exp[i] = self.gf_exp[i - 255]

    def gf_multiply(self, x, y):
        """
        Multiply two elements in GF(256). Returns 0 if either operand is 0.
        """
        if x == 0 or y == 0:
            return 0
        # Addition of exponents modulo 255
        return self.gf_exp[(self.gf_log[x] + self.gf_log[y]) % 255]

    def multiply_polynomials(self, p1, p2):
        """
        Multiply two polynomials over GF(256) and return the result.
        """
        result = [0] * (len(p1) + len(p2) - 1)
        for i, coeff1 in enumerate(p1):
            for j, coeff2 in enumerate(p2):
                if coeff1 and coeff2:
                    result[i + j] ^= self.gf_multiply(coeff1, coeff2)
        return result

    def construct_generator_polynomial(self, version):
        """
        Build the generator polynomial for the specified QR version.
        """
        # block_info[version][1] is the number of EC codewords for that version
        num_codewords = self.encoder.block_info[version][1]
        gen = [1]
        for i in range(num_codewords):
            gen = self.multiply_polynomials(gen, [1, self.gf_exp[i]])
        return gen

    def message_polynomial(self, text):
        """
        Encode the text, split the bitstring into 8-bit codewords,
        and return the list of integer coefficients.
        """
        bit_string = self.encoder.encode(text)
        coefficients = []
        for i in range(0, len(bit_string), 8):
            byte = bit_string[i:i+8]
            coefficients.append(int(byte, 2))
        return coefficients

    def div(self, message_poly, generator_poly):
        """
        Perform polynomial division of message_poly by generator_poly.
        Returns only the remainder coefficients.
        """
        remainder = message_poly[:] + [0] * (len(generator_poly) - 1)
        for i in range(len(message_poly)):
            coef = remainder[i]
            if coef != 0:
                log_factor = self.gf_log[coef]
                for j in range(1, len(generator_poly)):
                    if generator_poly[j]:
                        remainder[i + j] ^= self.gf_exp[(log_factor + self.gf_log[generator_poly[j]]) % 255]
        return remainder[-(len(generator_poly) - 1):]

    def split_into_blocks(self, message_poly, version):
        """
        Split the message polynomial into data blocks according to block_info.
        """
        binfo = self.encoder.block_info[version]
        num_g1, num_g2 = binfo[2], binfo[3]
        size_g1, size_g2 = binfo[4], binfo[5]
        blocks = []
        idx = 0
        for _ in range(num_g1):
            blocks.append(message_poly[idx:idx + size_g1])
            idx += size_g1
        for _ in range(num_g2):
            blocks.append(message_poly[idx:idx + size_g2])
            idx += size_g2
        return blocks

    def interleave_blocks(self, data_blocks, ec_blocks):
        """
        Interleave data and EC blocks as specified by the QR standard.
        """
        interleaved = []
        max_data = max(len(b) for b in data_blocks)
        for i in range(max_data):
            for block in data_blocks:
                if i < len(block):
                    interleaved.append(block[i])
        max_ec = max(len(b) for b in ec_blocks)
        for i in range(max_ec):
            for block in ec_blocks:
                if i < len(block):
                    interleaved.append(block[i])
        return interleaved

    def get_final_message(self, message, version):
        """
        Convert the combined codewords into a bitarray and append remainder bits.
        """
        bit_str = ''.join(format(cw, '08b') for cw in message)
        remainder_bits = self.required_remainder_bits.get(version, 0)
        bit_str += '0' * remainder_bits
        return bitarray(bit_str)

    def generate_error_correction_codewords(self, text, version):
        """
        Generate the final bitarray containing interleaved data and error correction codewords.
        """
        gen_poly = self.construct_generator_polynomial(version)
        msg_poly = self.message_polynomial(text)
        data_blocks = self.split_into_blocks(msg_poly, version)
        ec_blocks = [self.div(block, gen_poly) for block in data_blocks]
        combined = self.interleave_blocks(data_blocks, ec_blocks)
        return self.get_final_message(combined, version)
