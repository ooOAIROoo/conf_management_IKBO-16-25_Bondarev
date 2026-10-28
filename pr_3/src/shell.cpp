#include "emu/shell.hpp"

#include <fstream>
#include <iostream>
#include <stdexcept>

#include "emu/lexer.hpp"
#include "emu/vfs.hpp"

namespace emu {

Shell::Shell(Vfs& vfs) : vfs_(vfs) {}

std::string Shell::prompt() const {
    // Приглашение содержит имя VFS и текущий каталог.
    return vfs_.name() + ":" + cwd_ + "$ ";
}

int Shell::runInteractive() {
    std::string line;
    while (running_) {
        std::cout << prompt() << std::flush;
        if (!std::getline(std::cin, line)) {
            // Конец ввода (Ctrl+D / Ctrl+Z) — штатное завершение.
            std::cout << "\n";
            break;
        }
        lastStatus_ = executeLine(line, /*scriptMode=*/false);
    }
    return running_ ? lastStatus_ : exitCode_;
}

int Shell::runScriptFile(const std::string& path) {
    std::ifstream input(path, std::ios::binary);
    if (!input) {
        throw std::runtime_error("не удалось открыть стартовый скрипт: " + path);
    }

    std::string line;
    std::size_t lineNumber = 0;
    while (std::getline(input, line)) {
        ++lineNumber;
        if (lineNumber == 1 && line.rfind("\xEF\xBB\xBF", 0) == 0) {
            line.erase(0, 3);  // BOM от редакторов Windows
        }
        if (!line.empty() && line.back() == '\r') {
            line.pop_back();  // перевод строки CRLF
        }

        // Предварительный разбор: пустые строки и комментарии не отображаем.
        const TokenizeResult parsed = tokenize(line, /*scriptMode=*/true);
        if (parsed.ok() && parsed.tokens.empty()) {
            continue;
        }

        // Имитация диалога: строка скрипта показывается вместе с приглашением.
        std::cout << prompt() << line << "\n";

        if (!parsed.ok()) {
            std::cerr << "[script] " << path << ':' << lineNumber
                      << ": ошибка разбора: " << parsed.error << " (позиция "
                      << parsed.errorColumn << ")\n";
            lastStatus_ = 2;
            continue;
        }

        lastStatus_ = executeLine(line, /*scriptMode=*/true);
        if (lastStatus_ != 0) {
            std::cerr << "[script] " << path << ':' << lineNumber
                      << ": команда завершилась с кодом " << lastStatus_
                      << "\n";
        }
        if (!running_) {
            break;
        }
    }

    if (!input.eof() && input.bad()) {
        throw std::runtime_error("ошибка чтения стартового скрипта: " + path);
    }
    return running_ ? lastStatus_ : exitCode_;
}

int Shell::executeLine(const std::string& line, bool scriptMode) {
    const TokenizeResult parsed = tokenize(line, scriptMode);
    if (!parsed.ok()) {
        std::cerr << "emu: ошибка разбора строки: " << parsed.error
                  << " (позиция " << parsed.errorColumn << ")\n";
        return 2;
    }
    if (parsed.tokens.empty()) {
        return 0;
    }

    const std::string& command = parsed.tokens.front();
    const std::vector<std::string> args(parsed.tokens.begin() + 1,
                                        parsed.tokens.end());

    if (command == "exit" || command == "quit") {
        return handleExit(args);
    }
    if (command == "ls") {
        return cmdLs(args);
    }
    if (command == "cd") {
        return cmdCd(args);
    }
    if (command == "who") {
        return cmdWho(args);
    }
    if (command == "uname") {
        return cmdUname(args);
    }
    if (command == "tree") {
        return cmdTree(args);
    }
    if (command == "touch") {
        return cmdTouch(args);
    }
    if (command == "rmdir") {
        return cmdRmdir(args);
    }
    if (command == "help") {
        printHelp();
        return 0;
    }

    std::cerr << "emu: команда не найдена: " << command
              << " (для списка команд введите help)\n";
    return 127;
}

int Shell::handleExit(const std::vector<std::string>& args) {
    if (args.size() > 1) {
        std::cerr << "exit: слишком много аргументов\n";
        return 2;
    }
    int code = 0;
    if (!args.empty()) {
        try {
            std::size_t consumed = 0;
            code = std::stoi(args.front(), &consumed);
            if (consumed != args.front().size() || code < 0 || code > 255) {
                throw std::invalid_argument("range");
            }
        } catch (const std::exception&) {
            std::cerr << "exit: неверный код завершения: " << args.front()
                      << " (ожидается целое число 0..255)\n";
            return 2;
        }
    }
    exitCode_ = code;
    running_ = false;
    return 0;
}

void Shell::printHelp() const {
    std::cout << "Эмулятор командной строки UNIX-подобной ОС (все этапы)\n"
                 "Доступные команды:\n"
                 "  ls [-l] [-a] [путь...]  — содержимое каталога\n"
                 "                            -l: подробный формат\n"
                 "                            -a: показывать . и ..\n"
                 "  cd [путь]               — переход в каталог\n"
                 "                            без аргумента или ~ — в /,\n"
                 "                            cd - — в предыдущий каталог\n"
                 "  who                     — пользователь текущего сеанса\n"
                 "  tree [путь]             — дерево каталогов\n"
                 "  uname [-snrvmoa]        — сведения о системе\n"
                 "  touch <файл...>         — создать файл (только в памяти)\n"
                 "  rmdir <каталог...>      — удалить пустой каталог\n"
                 "  exit [код]              — выход с кодом 0..255\n"
                 "  help                    — эта справка\n"
                 "\n"
                 "Строки поддерживают одинарные и двойные кавычки.\n"
                 "В стартовых скриптах '#' в начале слова начинает комментарий.\n";
}

}  // namespace emu
