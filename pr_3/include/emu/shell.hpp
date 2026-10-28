#pragma once

#include <string>
#include <vector>

namespace emu {

/// Оболочка: цикл «приглашение — ввод — разбор — выполнение».
///
/// На этапе 2 добавлены стартовые скрипты: строки читаются из файла,
/// комментарии ('#') игнорируются, ввод и вывод команд отображаются так же,
/// как при интерактивной работе. Ошибки скрипта сопровождаются именем файла
/// и номером строки.
class Shell {
public:
    explicit Shell(std::string vfsName);

    /// Интерактивный цикл до команды exit или конца ввода.
    /// Возвращает код завершения эмулятора.
    int runInteractive();

    /// Выполняет стартовый скрипт. Бросает std::runtime_error, если файл
    /// не удаётся открыть. Возвращает код завершения последней команды.
    int runScriptFile(const std::string& path);

    /// Текст приглашения, например "vfs:/$ ".
    std::string prompt() const;

private:
    /// Выполняет одну строку. Возвращает код завершения команды
    /// (0 — успех) и при необходимости выставляет running_ = false.
    int executeLine(const std::string& line, bool scriptMode);

    int handleExit(const std::vector<std::string>& args);
    void printStub(const std::string& command,
                   const std::vector<std::string>& args) const;
    void printHelp() const;

    std::string vfsName_;
    bool running_ = true;
    int exitCode_ = 0;
    int lastStatus_ = 0;
};

}  // namespace emu
