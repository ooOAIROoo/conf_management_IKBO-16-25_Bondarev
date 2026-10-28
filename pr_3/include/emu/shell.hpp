#pragma once

#include <cstddef>
#include <string>
#include <vector>

namespace emu {

class Vfs;
struct Node;

/// Оболочка: цикл «приглашение — ввод — разбор — выполнение».
///
/// Этап 3: команды работают с виртуальной файловой системой в памяти,
/// приглашение содержит имя VFS и текущий каталог.
/// Этап 4: полноценные ls и cd, а также команды who, tree и uname.
/// Этап 5: команды touch и rmdir изменяют VFS только в памяти.
class Shell {
public:
    explicit Shell(Vfs& vfs);

    /// Интерактивный цикл до команды exit или конца ввода.
    /// Возвращает код завершения эмулятора.
    int runInteractive();

    /// Выполняет стартовый скрипт. Бросает std::runtime_error, если файл
    /// не удаётся открыть. Возвращает код завершения последней команды.
    int runScriptFile(const std::string& path);

    /// Текст приглашения, например "demo:/home/user$ ".
    std::string prompt() const;

private:
    /// Выполняет одну строку. Возвращает код завершения команды
    /// (0 — успех) и при необходимости выставляет running_ = false.
    int executeLine(const std::string& line, bool scriptMode);

    int handleExit(const std::vector<std::string>& args);

    int cmdLs(const std::vector<std::string>& args);
    int cmdCd(const std::vector<std::string>& args);
    int cmdWho(const std::vector<std::string>& args);
    int cmdUname(const std::vector<std::string>& args);
    int cmdTree(const std::vector<std::string>& args);
    int cmdTouch(const std::vector<std::string>& args);
    int cmdRmdir(const std::vector<std::string>& args);

    void printTreeChildren(const Node& directory, const std::string& prefix) const;
    static void countTree(const Node& directory, std::size_t& directories,
                          std::size_t& files);

    void printHelp() const;

    Vfs& vfs_;
    std::string cwd_ = "/";
    std::string previousCwd_ = "/";
    bool running_ = true;
    int exitCode_ = 0;
    int lastStatus_ = 0;
};

}  // namespace emu
