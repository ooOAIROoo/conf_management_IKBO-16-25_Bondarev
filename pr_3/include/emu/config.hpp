#pragma once

#include <iosfwd>
#include <optional>
#include <string>
#include <vector>

namespace emu {

/// Параметры командной строки эмулятора.
struct Config {
    std::optional<std::string> vfsPath;     ///< путь к физическому расположению VFS
    std::optional<std::string> scriptPath;  ///< путь к стартовому скрипту
    bool interactiveAfterScript = false;    ///< остаться в REPL после скрипта
    bool debugOutput = true;                ///< печатать параметры при запуске
    bool help = false;
    bool version = false;
};

struct ConfigParseResult {
    Config config;
    std::string error;  ///< пусто, если разбор успешен
    bool ok() const { return error.empty(); }
};

/// Разбирает argv (без имени программы) в Config.
ConfigParseResult parseCommandLine(const std::vector<std::string>& args);

/// Текст справки по параметрам командной строки.
std::string usageText();

/// Отладочный вывод всех заданных параметров при запуске.
void printConfig(const Config& config, std::ostream& out);

}  // namespace emu
