#include "emu/base64.hpp"

#include <array>
#include <cctype>
#include <stdexcept>

namespace emu {
namespace {

constexpr char kAlphabet[] =
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";

std::array<int, 256> makeDecodeTable() {
    std::array<int, 256> table{};
    table.fill(-1);
    for (int i = 0; i < 64; ++i) {
        table[static_cast<unsigned char>(kAlphabet[i])] = i;
    }
    return table;
}

}  // namespace

std::string base64Decode(const std::string& input) {
    static const std::array<int, 256> table = makeDecodeTable();

    std::string cleaned;
    cleaned.reserve(input.size());
    for (const char c : input) {
        if (std::isspace(static_cast<unsigned char>(c))) {
            continue;
        }
        cleaned.push_back(c);
    }

    if (cleaned.empty()) {
        return {};
    }
    if (cleaned.size() % 4 != 0) {
        throw std::invalid_argument("длина Base64 должна быть кратна 4");
    }

    std::string output;
    output.reserve(cleaned.size() / 4 * 3);

    for (std::size_t i = 0; i < cleaned.size(); i += 4) {
        int values[4] = {0, 0, 0, 0};
        int padding = 0;

        for (int j = 0; j < 4; ++j) {
            const char c = cleaned[i + static_cast<std::size_t>(j)];
            if (c == '=') {
                // Padding допустим только в конце и только в двух последних
                // позициях группы.
                if (j < 2) {
                    throw std::invalid_argument("некорректный padding Base64");
                }
                ++padding;
                values[j] = 0;
            } else {
                if (padding != 0) {
                    throw std::invalid_argument(
                        "символ после padding в Base64");
                }
                const int value = table[static_cast<unsigned char>(c)];
                if (value < 0) {
                    throw std::invalid_argument(
                        std::string("недопустимый символ Base64: '") + c + "'");
                }
                values[j] = value;
            }
        }

        const unsigned int triple =
            (static_cast<unsigned int>(values[0]) << 18) |
            (static_cast<unsigned int>(values[1]) << 12) |
            (static_cast<unsigned int>(values[2]) << 6) |
            static_cast<unsigned int>(values[3]);

        output.push_back(static_cast<char>((triple >> 16) & 0xFF));
        if (padding < 2) {
            output.push_back(static_cast<char>((triple >> 8) & 0xFF));
        }
        if (padding < 1) {
            output.push_back(static_cast<char>(triple & 0xFF));
        }
    }

    return output;
}

std::string base64Encode(const std::string& input) {
    std::string output;
    output.reserve((input.size() + 2) / 3 * 4);

    std::size_t i = 0;
    while (i + 2 < input.size()) {
        const unsigned int triple =
            (static_cast<unsigned char>(input[i]) << 16) |
            (static_cast<unsigned char>(input[i + 1]) << 8) |
            static_cast<unsigned char>(input[i + 2]);
        output.push_back(kAlphabet[(triple >> 18) & 0x3F]);
        output.push_back(kAlphabet[(triple >> 12) & 0x3F]);
        output.push_back(kAlphabet[(triple >> 6) & 0x3F]);
        output.push_back(kAlphabet[triple & 0x3F]);
        i += 3;
    }

    const std::size_t rest = input.size() - i;
    if (rest == 1) {
        const unsigned int value = static_cast<unsigned char>(input[i]) << 16;
        output.push_back(kAlphabet[(value >> 18) & 0x3F]);
        output.push_back(kAlphabet[(value >> 12) & 0x3F]);
        output += "==";
    } else if (rest == 2) {
        const unsigned int value =
            (static_cast<unsigned char>(input[i]) << 16) |
            (static_cast<unsigned char>(input[i + 1]) << 8);
        output.push_back(kAlphabet[(value >> 18) & 0x3F]);
        output.push_back(kAlphabet[(value >> 12) & 0x3F]);
        output.push_back(kAlphabet[(value >> 6) & 0x3F]);
        output.push_back('=');
    }

    return output;
}

}  // namespace emu
