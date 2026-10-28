#include <algorithm>
#include <ctime>
#include <iostream>
#include <string>
#include <utility>
#include <vector>

#include "emu/path.hpp"
#include "emu/shell.hpp"
#include "emu/vfs.hpp"
#include "emu/version.hpp"

namespace emu {
namespace {

/// Символьное представление прав доступа, например "drwxr-xr-x".
std::string modeString(const std::string& rawMode, bool isDirectory) {
    std::string octal = rawMode;
    if (octal.size() == 3) {
        octal.insert(octal.begin(), '0');
    }
    if (octal.size() != 4 ||
        !std::all_of(octal.begin(), octal.end(),
                     [](unsigned char c) { return c >= '0' && c <= '7'; })) {
        octal = "0755";
    }

    const int special = octal[0] - '0';
    const int user = octal[1] - '0';
    const int group = octal[2] - '0';
    const int other = octal[3] - '0';

    auto bit = [](int value, int mask, char symbol) {
        return (value & mask) != 0 ? symbol : '-';
    };

    std::string result;
    result += isDirectory ? 'd' : '-';

    result += bit(user, 4, 'r');
    result += bit(user, 2, 'w');
    char userExecute = bit(user, 1, 'x');
    if ((special & 4) != 0) {
        userExecute = (user & 1) != 0 ? 's' : 'S';
    }
    result += userExecute;

    result += bit(group, 4, 'r');
    result += bit(group, 2, 'w');
    char groupExecute = bit(group, 1, 'x');
    if ((special & 2) != 0) {
        groupExecute = (group & 1) != 0 ? 's' : 'S';
    }
    result += groupExecute;

    result += bit(other, 4, 'r');
    result += bit(other, 2, 'w');
    char otherExecute = bit(other, 1, 'x');
    if ((special & 1) != 0) {
        otherExecute = (other & 1) != 0 ? 't' : 'T';
    }
    result += otherExecute;

    return result;
}

std::string sizeOf(const Node& node) {
    if (node.isDirectory()) {
        return "4096";
    }
    return std::to_string(node.size());
}

void printLongEntry(const Node& node, const std::string& displayName,
                    std::size_t sizeWidth) {
    const std::string size = sizeOf(node);
    std::cout << modeString(node.mode, node.isDirectory()) << ' '
              << std::string(sizeWidth > size.size() ? sizeWidth - size.size() : 0,
                             ' ')
              << size << "  " << displayName << "\n";
}

/// Раскрывает "~" и "~/..." в корень VFS (домашний каталог эмулятора).
std::string expandTilde(const std::string& value) {
    if (value == "~") {
        return "/";
    }
    if (value.rfind("~/", 0) == 0) {
        return value.substr(1);
    }
    return value;
}

std::string currentTimeString() {
    const std::time_t now = std::time(nullptr);
    std::tm local{};
#ifdef _WIN32
    localtime_s(&local, &now);
#else
    localtime_r(&now, &local);
#endif
    char buffer[32] = {};
    std::strftime(buffer, sizeof(buffer), "%Y-%m-%d %H:%M", &local);
    return buffer;
}

std::string architecture() {
#if defined(_M_X64) || defined(__x86_64__)
    return "x86_64";
#elif defined(_M_ARM64) || defined(__aarch64__)
    return "aarch64";
#elif defined(_M_IX86) || defined(__i386__)
    return "i686";
#else
    return "unknown";
#endif
}

}  // namespace

int Shell::cmdLs(const std::vector<std::string>& args) {
    bool longFormat = false;
    bool showAll = false;
    bool optionsEnded = false;
    std::vector<std::string> operands;

    for (const std::string& arg : args) {
        if (!optionsEnded && arg == "--") {
            optionsEnded = true;
            continue;
        }
        if (!optionsEnded && arg.size() > 1 && arg.front() == '-') {
            for (std::size_t i = 1; i < arg.size(); ++i) {
                switch (arg[i]) {
                    case 'l':
                        longFormat = true;
                        break;
                    case 'a':
                        showAll = true;
                        break;
                    case '1':
                        // Одноколоночный вывод — у нас он и так такой.
                        break;
                    default:
                        std::cerr << "ls: недопустимая опция -- '" << arg[i]
                                  << "'\n";
                        return 2;
                }
            }
            continue;
        }
        operands.push_back(arg);
    }

    if (operands.empty()) {
        operands.emplace_back(".");
    }

    const bool multiple = operands.size() > 1;
    int status = 0;
    bool printedAny = false;

    for (const std::string& operand : operands) {
        const std::string absolute = path::normalize(expandTilde(operand), cwd_);
        const Node* node = vfs_.find(absolute);
        if (node == nullptr) {
            std::cerr << "ls: " << operand
                      << ": нет такого файла или каталога\n";
            status = 1;
            continue;
        }

        if (multiple) {
            if (printedAny) {
                std::cout << "\n";
            }
            std::cout << operand << ":\n";
        }

        if (node->isFile()) {
            if (longFormat) {
                printLongEntry(*node, operand, 1);
            } else {
                std::cout << operand << "\n";
            }
            printedAny = true;
            continue;
        }

        // Каталог: собираем элементы, при -a добавляем "." и "..".
        struct Entry {
            const Node* node;
            std::string name;
        };
        std::vector<Entry> entries;
        if (showAll) {
            entries.push_back({node, "."});
            entries.push_back({node->parent != nullptr ? node->parent : node, ".."});
        }
        for (const auto& child : node->children) {
            entries.push_back({child.second.get(), child.first});
        }

        if (longFormat) {
            std::size_t width = 1;
            for (const Entry& entry : entries) {
                width = std::max(width, sizeOf(*entry.node).size());
            }
            for (const Entry& entry : entries) {
                printLongEntry(*entry.node, entry.name, width);
            }
        } else {
            for (std::size_t i = 0; i < entries.size(); ++i) {
                if (i != 0) {
                    std::cout << "  ";
                }
                std::cout << entries[i].name;
            }
            if (!entries.empty()) {
                std::cout << "\n";
            }
        }
        printedAny = true;
    }

    return status;
}

int Shell::cmdCd(const std::vector<std::string>& args) {
    if (args.size() > 1) {
        std::cerr << "cd: слишком много аргументов\n";
        return 2;
    }

    // Без аргумента — в корень VFS; "~" — тоже корень; "-" — предыдущий.
    const std::string spec = args.empty() ? "/" : args.front();
    if (spec == "-") {
        std::swap(cwd_, previousCwd_);
        std::cout << cwd_ << "\n";
        return 0;
    }

    const std::string absolute = path::normalize(expandTilde(spec), cwd_);
    const Node* node = vfs_.find(absolute);
    if (node == nullptr) {
        std::cerr << "cd: " << spec << ": нет такого каталога\n";
        return 1;
    }
    if (!node->isDirectory()) {
        std::cerr << "cd: " << spec << ": не каталог\n";
        return 1;
    }

    previousCwd_ = cwd_;
    cwd_ = absolute;
    return 0;
}

int Shell::cmdWho(const std::vector<std::string>& args) {
    if (!args.empty()) {
        std::cerr << "who: слишком много аргументов\n";
        return 2;
    }
    std::cout << "emu      tty0     " << currentTimeString() << "\n";
    return 0;
}

int Shell::cmdUname(const std::vector<std::string>& args) {
    bool sysname = false;
    bool nodename = false;
    bool release = false;
    bool version = false;
    bool machine = false;
    bool os = false;

    if (args.empty()) {
        sysname = true;
    }

    for (const std::string& arg : args) {
        if (arg.size() < 2 || arg.front() != '-') {
            std::cerr << "uname: недопустимый параметр: " << arg << "\n";
            return 2;
        }
        for (std::size_t i = 1; i < arg.size(); ++i) {
            switch (arg[i]) {
                case 's':
                    sysname = true;
                    break;
                case 'n':
                    nodename = true;
                    break;
                case 'r':
                    release = true;
                    break;
                case 'v':
                    version = true;
                    break;
                case 'm':
                    machine = true;
                    break;
                case 'o':
                    os = true;
                    break;
                case 'a':
                    sysname = nodename = release = version = machine = os = true;
                    break;
                default:
                    std::cerr << "uname: недопустимая опция -- '" << arg[i]
                              << "'\n";
                    return 2;
            }
        }
    }

    std::vector<std::string> fields;
    if (sysname) {
        fields.emplace_back("EmuVFS");
    }
    if (nodename) {
        fields.push_back(vfs_.name());
    }
    if (release) {
        fields.emplace_back("1.0.0");
    }
    if (version) {
        fields.push_back(std::string("#1 SMP emu ") + kVersion);
    }
    if (machine) {
        fields.push_back(architecture());
    }
    if (os) {
        fields.emplace_back("EmuOS");
    }

    for (std::size_t i = 0; i < fields.size(); ++i) {
        if (i != 0) {
            std::cout << ' ';
        }
        std::cout << fields[i];
    }
    std::cout << "\n";
    return 0;
}

void Shell::printTreeChildren(const Node& directory,
                              const std::string& prefix) const {
    std::size_t index = 0;
    for (const auto& child : directory.children) {
        const bool last = (index + 1 == directory.children.size());
        ++index;
        std::cout << prefix << (last ? "└── " : "├── ") << child.first << "\n";
        if (child.second->isDirectory()) {
            printTreeChildren(*child.second,
                              prefix + (last ? "    " : "│   "));
        }
    }
}

void Shell::countTree(const Node& directory, std::size_t& directories,
                      std::size_t& files) {
    for (const auto& child : directory.children) {
        if (child.second->isDirectory()) {
            ++directories;
            countTree(*child.second, directories, files);
        } else {
            ++files;
        }
    }
}

int Shell::cmdTree(const std::vector<std::string>& args) {
    if (args.size() > 1) {
        std::cerr << "tree: на этом этапе поддерживается только один путь\n";
        return 2;
    }

    const std::string spec = args.empty() ? "." : args.front();
    const std::string absolute = path::normalize(expandTilde(spec), cwd_);
    const Node* node = vfs_.find(absolute);
    if (node == nullptr) {
        std::cerr << "tree: " << spec << ": нет такого файла или каталога\n";
        return 1;
    }

    std::cout << absolute << "\n";
    if (node->isFile()) {
        std::cout << "каталогов: 0, файлов: 1\n";
        return 0;
    }

    printTreeChildren(*node, "");
    std::size_t directories = 0;
    std::size_t files = 0;
    countTree(*node, directories, files);
    std::cout << "\nкаталогов: " << directories << ", файлов: " << files
              << "\n";
    return 0;
}

int Shell::cmdTouch(const std::vector<std::string>& args) {
    bool optionsEnded = false;
    std::vector<std::string> operands;

    for (const std::string& arg : args) {
        if (!optionsEnded && arg == "--") {
            optionsEnded = true;
            continue;
        }
        if (!optionsEnded && arg.size() > 1 && arg.front() == '-') {
            std::cerr << "touch: недопустимая опция: " << arg << "\n";
            return 2;
        }
        operands.push_back(arg);
    }

    if (operands.empty()) {
        std::cerr << "touch: не указан операнд (имя файла)\n";
        return 2;
    }

    int status = 0;
    for (const std::string& operand : operands) {
        const std::string absolute = path::normalize(expandTilde(operand), cwd_);
        Node* node = vfs_.find(absolute);
        if (node != nullptr) {
            // Файл уже существует: в реальной ОС touch обновляет время
            // изменения. В модели VFS время не хранится, поэтому обновление
            // является успешной операцией-пустышкой.
            continue;
        }

        const std::string parentPath = path::dirname(absolute);
        const std::string name = path::basename(absolute);
        Node* parent = vfs_.find(parentPath);
        if (parent == nullptr) {
            std::cerr << "touch: " << operand
                      << ": нет такого файла или каталога\n";
            status = 1;
            continue;
        }
        if (!parent->isDirectory()) {
            std::cerr << "touch: " << operand
                      << ": родительский путь не является каталогом\n";
            status = 1;
            continue;
        }

        try {
            vfs_.createFile(*parent, name);
        } catch (const VfsError& error) {
            std::cerr << "touch: " << operand << ": " << error.what() << "\n";
            status = 1;
        }
    }
    return status;
}

int Shell::cmdRmdir(const std::vector<std::string>& args) {
    bool optionsEnded = false;
    std::vector<std::string> operands;

    for (const std::string& arg : args) {
        if (!optionsEnded && arg == "--") {
            optionsEnded = true;
            continue;
        }
        if (!optionsEnded && arg.size() > 1 && arg.front() == '-') {
            std::cerr << "rmdir: недопустимая опция: " << arg << "\n";
            return 2;
        }
        operands.push_back(arg);
    }

    if (operands.empty()) {
        std::cerr << "rmdir: не указан операнд (имя каталога)\n";
        return 2;
    }

    int status = 0;
    for (const std::string& operand : operands) {
        const std::string absolute = path::normalize(expandTilde(operand), cwd_);
        Node* node = vfs_.find(absolute);
        if (node == nullptr) {
            std::cerr << "rmdir: " << operand << ": нет такого каталога\n";
            status = 1;
            continue;
        }
        if (!node->isDirectory()) {
            std::cerr << "rmdir: " << operand << ": не каталог\n";
            status = 1;
            continue;
        }
        if (node == &vfs_.root()) {
            std::cerr << "rmdir: " << operand
                      << ": нельзя удалить корневой каталог\n";
            status = 1;
            continue;
        }
        if (!node->children.empty()) {
            std::cerr << "rmdir: " << operand << ": каталог не пуст\n";
            status = 1;
            continue;
        }

        try {
            vfs_.remove(*node);
        } catch (const VfsError& error) {
            std::cerr << "rmdir: " << operand << ": " << error.what() << "\n";
            status = 1;
        }
    }
    return status;
}

}  // namespace emu

