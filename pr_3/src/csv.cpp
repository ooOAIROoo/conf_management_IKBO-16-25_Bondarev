#include "emu/csv.hpp"

#include <cctype>

namespace emu {

std::string trim(const std::string& value) {
    std::size_t begin = 0;
    std::size_t end = value.size();
    while (begin < end && std::isspace(static_cast<unsigned char>(value[begin]))) {
        ++begin;
    }
    while (end > begin && std::isspace(static_cast<unsigned char>(value[end - 1]))) {
        --end;
    }
    return value.substr(begin, end - begin);
}

std::vector<std::string> parseCsvLine(const std::string& line) {
    std::vector<std::string> fields;
    std::string field;
    std::size_t i = 0;
    const std::size_t size = line.size();

    while (true) {
        field.clear();

        if (i < size && line[i] == '"') {
            // Поле в кавычках: запятые внутри не разделяют поля.
            ++i;
            bool closed = false;
            while (i < size) {
                if (line[i] == '"') {
                    if (i + 1 < size && line[i + 1] == '"') {
                        field.push_back('"');
                        i += 2;
                        continue;
                    }
                    ++i;
                    closed = true;
                    break;
                }
                field.push_back(line[i]);
                ++i;
            }
            if (!closed) {
                throw CsvError("не закрыта кавычка в поле CSV");
            }
            if (i < size && line[i] != ',') {
                throw CsvError(
                    "после закрывающей кавычки ожидается запятая или конец строки");
            }
        } else {
            // Поле без кавычек: читаем до запятой.
            while (i < size && line[i] != ',') {
                field.push_back(line[i]);
                ++i;
            }
        }

        fields.push_back(field);

        if (i >= size) {
            break;
        }
        ++i;  // пропускаем запятую
        if (i == size) {
            // Строка заканчивается запятой — последнее поле пустое.
            fields.emplace_back();
            break;
        }
    }

    return fields;
}

}  // namespace emu
