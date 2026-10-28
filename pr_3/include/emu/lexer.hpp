#pragma once

#include <cstddef>
#include <string>
#include <vector>

namespace emu {

/// Результат разбора одной строки командной строки.
struct TokenizeResult {
    std::vector<std::string> tokens;
    std::string error;            ///< Пустая строка, если разбор успешен.
    std::size_t errorColumn = 0;  ///< Позиция ошибки в строке (с 1).

    bool ok() const { return error.empty(); }
};

/// Разбирает строку на аргументы.
///
/// Поддерживаются:
///   * одинарные кавычки  — всё внутри них буквально (в т.ч. пробелы и '#');
///   * двойные кавычки    — пробелы буквальны, экранируются только \" и \\;
///   * обратный слэш вне кавычек экранирует следующий символ;
///   * в режиме scriptMode символ '#' в начале слова открывает комментарий
///     до конца строки (в интерактивном режиме '#' — обычный символ).
TokenizeResult tokenize(const std::string& line, bool scriptMode = false);

}  // namespace emu
