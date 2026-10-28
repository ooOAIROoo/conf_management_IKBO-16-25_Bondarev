#pragma once

#include <stdexcept>
#include <string>
#include <vector>

namespace emu {

/// Ошибка разбора CSV-строки.
class CsvError : public std::runtime_error {
public:
    using std::runtime_error::runtime_error;
};

/// Разбирает одну строку CSV в поля.
///
/// Поддерживаются поля в двойных кавычках, запятые внутри кавычек и
/// экранирование кавычки удвоением (""). Строка не должна содержать
/// символа перевода строки (каждая запись VFS — одна строка файла).
std::vector<std::string> parseCsvLine(const std::string& line);

/// Убирает пробельные символы слева и справа.
std::string trim(const std::string& value);

}  // namespace emu
