#include "emu/config.hpp"

#include <filesystem>
#include <ostream>

#include "emu/version.hpp"

namespace emu {
namespace {

/// Абсолютный путь для отладочного вывода; не требует существования файла.
std::string displayPath(const std::string& path) {
    std::error_code ec;
    const std::filesystem::path absolute = std::filesystem::absolute(path, ec);
    return ec ? path : absolute.lexically_normal().string();
}

std::string quoted(const std::optional<std::string>& value) {
    return value ? "\"" + *value + "\"" : "\"не задан\"";
}

}  // namespace

ConfigParseResult parseCommandLine(const std::vector<std::string>& args) {
    ConfigParseResult result;
    Config& config = result.config;

    for (std::size_t i = 0; i < args.size(); ++i) {
        const std::string& arg = args[i];

        auto takeValue = [&](const std::string& option) -> std::optional<std::string> {
            if (i + 1 >= args.size()) {
                result.error = "параметр " + option + " требует значения";
                return std::nullopt;
            }
            return args[++i];
        };

        if (arg == "--help" || arg == "-h") {
            config.help = true;
        } else if (arg == "--version" || arg == "-V") {
            config.version = true;
        } else if (arg == "--interactive" || arg == "-i") {
            config.interactiveAfterScript = true;
        } else if (arg == "--no-debug") {
            config.debugOutput = false;
        } else if (arg == "--debug") {
            config.debugOutput = true;
        } else if (arg == "--vfs") {
            const auto value = takeValue(arg);
            if (!value) {
                return result;
            }
            config.vfsPath = *value;
        } else if (arg.rfind("--vfs=", 0) == 0) {
            config.vfsPath = arg.substr(6);
            if (config.vfsPath->empty()) {
                result.error = "параметр --vfs требует значения";
                return result;
            }
        } else if (arg == "--script") {
            const auto value = takeValue(arg);
            if (!value) {
                return result;
            }
            config.scriptPath = *value;
        } else if (arg.rfind("--script=", 0) == 0) {
            config.scriptPath = arg.substr(9);
            if (config.scriptPath->empty()) {
                result.error = "параметр --script требует значения";
                return result;
            }
        } else if (!arg.empty() && arg.front() == '-') {
            result.error = "неизвестный параметр: " + arg;
            return result;
        } else {
            result.error = "неожиданный позиционный аргумент: \"" + arg +
                           "\" (используйте --vfs и --script)";
            return result;
        }
    }

    if (config.interactiveAfterScript && !config.scriptPath) {
        result.error = "параметр --interactive имеет смысл только вместе с --script";
    }
    return result;
}

std::string usageText() {
    return "Использование: emu [параметры]\n"
           "\n"
           "Параметры:\n"
           "  --vfs <путь>       путь к физическому расположению VFS (CSV-файл)\n"
           "  --script <путь>    стартовый скрипт с командами эмулятора\n"
           "  -i, --interactive  остаться в интерактивном режиме после скрипта\n"
           "  --debug            печатать параметры запуска (включено по умолчанию)\n"
           "  --no-debug         отключить отладочный вывод параметров\n"
           "  -h, --help         эта справка\n"
           "  -V, --version      версия эмулятора\n"
           "\n"
           "Стартовый скрипт поддерживает комментарии, начинающиеся с '#',\n"
           "и выполняется построчно с отображением ввода и вывода команд.\n";
}

void printConfig(const Config& config, std::ostream& out) {
    if (!config.debugOutput) {
        return;
    }
    out << "[config] отладочный вывод параметров запуска:\n";
    out << "[config]   путь к VFS:       " << quoted(config.vfsPath) << "\n";
    out << "[config]   стартовый скрипт: " << quoted(config.scriptPath) << "\n";
    out << "[config]   режим работы:     ";
    if (config.scriptPath) {
        out << (config.interactiveAfterScript ? "скрипт, затем интерактивный"
                                             : "пакетный (только скрипт)");
    } else {
        out << "интерактивный";
    }
    out << "\n";
    out << "[config]   отладочный вывод: "
        << (config.debugOutput ? "включён" : "выключен") << "\n";
    out << "[config]   версия:           " << kVersion << "\n";
    if (config.vfsPath) {
        out << "[config]   VFS (абс. путь):  "
            << displayPath(*config.vfsPath) << "\n";
    }
    if (config.scriptPath) {
        out << "[config]   скрипт (абс. путь): "
            << displayPath(*config.scriptPath) << "\n";
    }
    out << std::flush;
}

}  // namespace emu
