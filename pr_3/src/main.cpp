#include <exception>
#include <iostream>
#include <string>
#include <vector>

#include "emu/config.hpp"
#include "emu/shell.hpp"
#include "emu/vfs.hpp"
#include "emu/version.hpp"

#ifdef _WIN32
#include <windows.h>

#include <shellapi.h>
#endif

namespace {

#ifdef _WIN32
/// Преобразует аргументы Windows (UTF-16) в UTF-8, чтобы пути к данным
/// VFS и скриптам с кириллицей работали одинаково на обеих платформах.
std::vector<std::string> utf8Arguments() {
    int argc = 0;
    wchar_t** wargv = ::CommandLineToArgvW(::GetCommandLineW(), &argc);
    std::vector<std::string> args;
    if (wargv == nullptr) {
        return args;
    }
    for (int i = 0; i < argc; ++i) {
        const int size = ::WideCharToMultiByte(CP_UTF8, 0, wargv[i], -1, nullptr,
                                               0, nullptr, nullptr);
        std::string value(size > 1 ? static_cast<std::size_t>(size - 1) : 0, '\0');
        if (size > 1) {
            ::WideCharToMultiByte(CP_UTF8, 0, wargv[i], -1, value.data(), size,
                                  nullptr, nullptr);
        }
        args.push_back(value);
    }
    ::LocalFree(wargv);
    return args;
}

void setupConsole() {
    ::SetConsoleOutputCP(CP_UTF8);
    ::SetConsoleCP(CP_UTF8);
}
#else
void setupConsole() {}
#endif

std::vector<std::string> collectArguments(int argc, char** argv) {
    std::vector<std::string> args;
#ifdef _WIN32
    (void)argc;
    (void)argv;
    args = utf8Arguments();
#else
    for (int i = 0; i < argc; ++i) {
        args.emplace_back(argv[i]);
    }
#endif
    // Первый элемент — имя программы, параметрам он не нужен.
    if (!args.empty()) {
        args.erase(args.begin());
    }
    return args;
}

}  // namespace

int main(int argc, char** argv) {
    setupConsole();

    const std::vector<std::string> args = collectArguments(argc, argv);

    const emu::ConfigParseResult parsed = emu::parseCommandLine(args);
    if (!parsed.ok()) {
        std::cerr << "emu: " << parsed.error << "\n\n" << emu::usageText();
        return 2;
    }
    const emu::Config& config = parsed.config;

    if (config.help) {
        std::cout << emu::usageText();
        return 0;
    }
    if (config.version) {
        std::cout << "emu " << emu::kVersion << " (" << emu::kStageDescription
                  << ")\n";
        return 0;
    }

    emu::printConfig(config, std::cerr);

    try {
        emu::Vfs vfs;
        if (config.vfsPath) {
            vfs = emu::Vfs::loadFromCsv(*config.vfsPath);
            if (config.debugOutput) {
                const emu::VfsStats stats = vfs.stats();
                std::cerr << "[vfs] загружено из \"" << *config.vfsPath
                          << "\": имя \"" << vfs.name() << "\", каталогов "
                          << stats.directories << ", файлов " << stats.files
                          << ", объём " << stats.bytes << " Б\n";
            }
        } else if (config.debugOutput) {
            std::cerr << "[vfs] параметр --vfs не задан: используется пустая "
                         "встроенная VFS \"vfs\"\n";
        }

        emu::Shell shell(vfs);
        if (config.scriptPath) {
            const int scriptStatus = shell.runScriptFile(*config.scriptPath);
            if (!config.interactiveAfterScript) {
                return scriptStatus;
            }
        }
        return shell.runInteractive();
    } catch (const std::exception& error) {
        std::cerr << "emu: " << error.what() << "\n";
        return 1;
    }
}
