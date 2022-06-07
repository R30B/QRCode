from PIL import Image, ImageOps
from itertools import product
import constants
import sys

image = Image.open("qrcode.png")


class QrDecoder:
    @staticmethod
    def convert_into_matrix(image):
        pixels = list(image.getdata())
        # print(pixels)
        width = image.width
        matrix = [pixels[j:width + j] for j in range(0, len(pixels), width)]

        for i, j in product(range(width), range(width)):
            if matrix[i][j] == 0:
                k = i
                break
        # print(k)
        while True:
            if matrix[i][j] == 255:
                break
            i += 1
            j += 1

        module_size = i - k
        # print(module_size)

        for i, j in product(range(width), range(width - 1, -1, -1)):
            if matrix[i][j] == 0:
                l = j
                break

        qrmatrix = []
        for i in range(k, l, module_size):
            rows = []
            for j in range(k, l, module_size):
                rows.append(matrix[i][j])
            qrmatrix.append(rows)
        # print(len(qrmatrix), len(qrmatrix[0]))
        return qrmatrix

    def __init__(self, image):
        self.matrix = QrDecoder.convert_into_matrix(image)
        self.height = len(self.matrix)
        self.width = len(self.matrix[0])
        self.version = self.get_version()
        self.error_type, self.mask_no = self.format_information()

    @staticmethod
    def char_count_indicator(encoding_type, version):
        k = int()
        if version <= 9:
            k = constants.character_count_indicator[1][encoding_type]
        elif version <= 26:
            k = constants.character_count_indicator[2][encoding_type]
        else:
            k = constants.character_count_indicator[3][encoding_type]
        return k

    def format_information(self):
        str1 = ""
        for i in range(0, 6):
            if self.matrix[8][i] == 255:
                str1 += "0"
            else:
                str1 += "1"

        str1 += "0" if self.matrix[8][7] == 255 else "1"
        str1 += "0" if self.matrix[8][8] == 255 else "1"
        str1 += "0" if self.matrix[7][8] == 255 else "1"

        for i in range(5, -1, -1):
            if self.matrix[i][8] == 255:
                str1 += "0"
            else:
                str1 += "1"

        format_info = f'{int(str1, base=2) ^ int(constants.format_mask, base=2):015b}'

        error_type = int(format_info[0:2], base=2)
        mask_no = int(format_info[2:5], base=2)

        if str1 == constants.format_pattern[constants.error_type[error_type]][mask_no]:
            return error_type, mask_no

        str2 = ""
        for i in range(-1, -8, -1):
            if self.matrix[i][8] == 255:
                str2 += "0"
            else:
                str2 += "1"

        for i in range(-8, 0):
            if self.matrix[8][i] == 255:
                str2 += "0"
            else:
                str2 += "1"

        format_info = f'{int(str2, base=2) ^ int(constants.format_mask, base=2):015b}'

        error_type = int(format_info[0:2], base=2)
        mask_no = int(format_info[2:5], base=2)

        if str2 == constants.format_pattern[constants.error_type[error_type]][mask_no]:
            return error_type, mask_no

        print("Error in format pattern", file=sys.stderr)
        exit(1)

    def get_version(self):
        version = (self.height - 21) // 4 + 1

        if version <= 6:
            return version

        str1 = ""
        for i in range(0, 6):
            for j in range(-11, -8):
                if self.matrix[i][j] == 255:
                    str1 = "0" + str1
                else:
                    str1 = "1" + str1

        if str1 == constants.version_pattern[version]:
            return version

        str2 = ""
        for i in range(0, 6):
            for j in range(-11, -8):
                if self.matrix[j][i] == 255:
                    str2 = "0" + str2
                else:
                    str2 = "1" + str2

        if str2 == constants.version_pattern[version]:
            return version

        print("Error in version pattern", file=sys.stderr)
        exit(1)

    def finding_pattern(self, i, j):
        for col in range(j, j + 7):
            self.matrix[i][col] = 128
            self.matrix[i + 6][col] = 128
        for row in range(i + 1, i + 6):
            self.matrix[row][j] = 128
            self.matrix[row][j + 6] = 128
        for col in range(j + 1, j + 6):
            self.matrix[i + 1][col] = 128
            self.matrix[i + 5][col] = 128
        for row in range(i + 2, i + 5):
            self.matrix[row][j + 1] = 128
            self.matrix[row][j + 5] = 128
        for row in range(i + 2, i + 5):
            for col in range(j + 2, j + 5):
                self.matrix[row][col] = 128

    def finding_position(self):
        self.finding_pattern(0, 0)
        self.finding_pattern(-7, 0)
        self.finding_pattern(0, -7)

        # for separators
        for i in range(0, 8):
            self.matrix[7][i] = 128
            self.matrix[i][7] = 128
            self.matrix[-8][i] = 128
            self.matrix[i][-8] = 128
            self.matrix[-i - 1][7] = 128
            self.matrix[7][-i - 1] = 128

    def alignment_pattern(self, i, j):
        for col in range(j, j + 5):
            self.matrix[i][col] = 128
            self.matrix[i + 4][col] = 128
        for row in range(i + 1, i + 4):
            self.matrix[row][j] = 128
            self.matrix[row][j + 4] = 128
        for col in range(j + 1, j + 4):
            self.matrix[i + 1][col] = 128
            self.matrix[i + 3][col] = 128
        for row in range(i + 2, i + 3):
            self.matrix[row][j + 1] = 128
            self.matrix[row][j + 3] = 128
        self.matrix[i + 2][j + 2] = 128

    def alignment_position(self):
        align_pos = constants.alignment_position[self.version]
        # for dark module
        self.matrix[(4 * self.version) + 9][8] = 128
        if not align_pos:
            return
        # print(align_pos)
        for j in range(1, len(align_pos) - 1):
            self.alignment_pattern(align_pos[0] - 2, align_pos[j] - 2)
        for i in range(1, len(align_pos) - 1):
            for j in range(0, len(align_pos)):
                self.alignment_pattern(align_pos[i] - 2, align_pos[j] - 2)
        for j in range(1, len(align_pos)):
            self.alignment_pattern(align_pos[-1] - 2, align_pos[j] - 2)

    def timing_position(self):
        size = self.width
        for i in range(8, size - 7):
            if i % 2 == 0:
                self.matrix[i][6] = 128
                self.matrix[6][i] = 128
            else:
                self.matrix[i][6] = 128
                self.matrix[6][i] = 128

    def format_position(self):
        for i in range(0, 6):
            self.matrix[8][i] = 128

        self.matrix[8][7] = 128
        self.matrix[8][8] = 128
        self.matrix[7][8] = 128

        for i in range(5, -1, -1):
            self.matrix[i][8] = 128

        for i in range(-1, -8, -1):
            self.matrix[i][8] = 128
        for i in range(-8, 0):
            self.matrix[8][i] = 128

    def version_position(self):
        if self.version < 7:
            return
        for i in range(0, 6):
            for j in range(-11, -8):
                self.matrix[i][j] = 128
                self.matrix[j][i] = 128

    def get_codeword(self):
        for i in range(0, self.height):
            for j in range(0, self.width):
                if constants.mask_patterns[self.mask_no](i, j):
                    self.matrix[i][j] = self.matrix[i][j] ^ 255

        self.finding_position()
        self.alignment_position()
        self.timing_position()
        self.format_position()
        self.version_position()
        up = True

        bits = []
        encoded_data = []
        bit_count = 0
        j = self.height - 1
        while j > 0:
            if j == 6:
                j -= 1
            for count in range(0, self.height):
                i = self.height - count - 1 if up else count
                for col in range(0, 2):

                    if self.matrix[i][j - col] != 128:
                        bit_count += 1
                        # print(i, j - col)
                        if self.matrix[i][j - col] == 255:
                            bits.append("0")
                        else:
                            bits.append("1")
                        if bit_count == 8:
                            bit_count = 0
                            encoded_data.append(int(''.join(bits), base=2))
                            bits = []
            up ^= True
            j -= 2
        return encoded_data

    def get_blocks(self):
        encoded_data = self.get_codeword()
        # print(encoded_data)
        error_data = constants.error_corr_table[self.version][constants.error_type[self.error_type]]
        data_codewords = ((error_data[1] * error_data[2]) + (
                error_data[3] * error_data[4]))
        error_codewords = (error_data[0] * (error_data[1] + error_data[3]))
        num_codewords = error_codewords + data_codewords

        if len(encoded_data) != num_codewords:
            print("Error number of codewords is not equal to it actual length", file=sys.stderr)
            exit(1)

        blocks = [list(range(error_data[2])) for i in range(error_data[1])]
        group_2_start = len(blocks)
        blocks.extend([list(range(error_data[4])) for i in range(error_data[3])])
        count = 0
        for j in range(error_data[2]):
            for i in range(len(blocks)):
                blocks[i][j] = encoded_data[count]
                count += 1
        for j in range(error_data[2], error_data[4]):
            for i in range(group_2_start, len(blocks)):
                blocks[i][j] = encoded_data[count]
                count += 1
        error_block_start = len(blocks)

        blocks.extend([list(range(error_data[0])) for i in range(error_data[1] + error_data[3])])

        for j in range(error_data[0]):
            for i in range(error_block_start, len(blocks)):
                blocks[i][j] = encoded_data[count]
                count += 1

        return blocks

    def byte_decoding(self, current_bit, bit_stream, char_count):
        text = bytearray()
        # print(char_count)
        while char_count > 0:
            char_count -= 1
            text.append(int(bit_stream[current_bit:current_bit + 8], base=2))
            current_bit += 8

        return current_bit, text.decode('utf-8')

    def decode(self):
        blocks = self.get_blocks()
        bit_stream = []
        for i in range(len(blocks) // 2):
            bit_stream.extend([f"{byte_val:08b}" for byte_val in blocks[i]])

        bit_stream = ''.join(bit_stream)
        text = ""
        current_bit = 0
        while True:
            if (len(bit_stream) - current_bit) < 4:
                mode = 0
            else:
                mode = int(bit_stream[current_bit:current_bit+4], base=2)
                current_bit += 4

            if mode == 0:
                break
            elif mode == 4:
                char_count_size = QrDecoder.char_count_indicator("bytes", self.version)
                char_count = int(bit_stream[current_bit:current_bit + char_count_size], base=2)
                current_bit += char_count_size
                current_bit, text = self.byte_decoding(current_bit, bit_stream, char_count)
            else:
                print("This mode may be incorrect or not supported")
                exit(1)
        return text


decoder = QrDecoder(image)


# def build_image(decoder):
#     size = (decoder.width, decoder.height)
#     pixels = []
#     for l in decoder.matrix:
#         pixels.extend(l)
#     # pixels = [j for i in decoder.matrix for j in i]
#
#     image = Image.new(mode='L', size=size)
#     image.putdata(pixels)
#     # image = ImageOps.expand(image, border=4, fill='white')
#     image = ImageOps.scale(image, factor=10, resample=Image.BOX)
#     return image


# print(decoder.matrix)

# decoder.get_codeword()

# decoder.get_version()
# print(decoder.get_codeword())
print(decoder.decode())
# image = build_image(decoder)
# image.show()
