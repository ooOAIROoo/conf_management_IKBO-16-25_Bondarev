#pragma once

#include <cstddef>
#include <map>
#include <memory>
#include <stdexcept>
#include <string>

namespace emu {

/// Ошибка виртуальной файловой системы (загрузка CSV, операции с узлами).
class VfsError : public std::runtime_error {
public:
    using std::runtime_error::runtime_error;
};

/// Узел VFS: каталог или файл. Дерево целиком живёт в оперативной памяти.
struct Node {
    enum class Type { Directory, File };

    Type type = Type::Directory;
    std::string name;
    std::string mode;     ///< права в восьмеричном виде, например "0755"
    std::string content;  ///< содержимое файла (для каталога пусто)
    Node* parent = nullptr;
    std::map<std::string, std::unique_ptr<Node>> children;

    bool isDirectory() const { return type == Type::Directory; }
    bool isFile() const { return type == Type::File; }

    /// Абсолютный путь узла внутри VFS.
    std::string path() const;

    /// Размер содержимого в байтах.
    std::size_t size() const { return content.size(); }
};

/// Статистика загруженной VFS.
struct VfsStats {
    std::size_t directories = 0;
    std::size_t files = 0;
    std::size_t bytes = 0;
};

/// Виртуальная файловая система. Источник — CSV-файл, все изменения
/// выполняются только в памяти и никогда не пишутся на диск.
class Vfs {
public:
    /// Создаёт пустую VFS с корневым каталогом "/".
    Vfs();

    Vfs(const Vfs&) = delete;
    Vfs& operator=(const Vfs&) = delete;
    Vfs(Vfs&&) noexcept = default;
    Vfs& operator=(Vfs&&) noexcept = default;
    ~Vfs() = default;

    /// Загружает VFS из CSV-файла. Бросает VfsError с указанием строки.
    static Vfs loadFromCsv(const std::string& csvPath);

    const std::string& name() const { return name_; }
    void setName(std::string name) { name_ = std::move(name); }

    Node& root() { return *root_; }
    const Node& root() const { return *root_; }

    /// Находит узел по абсолютному нормализованному пути; nullptr, если нет.
    Node* find(const std::string& absolutePath);
    const Node* find(const std::string& absolutePath) const;

    /// Создаёт файл/каталог в указанном каталоге. Бросает VfsError при
    /// недопустимом имени или дубликате.
    Node& createFile(Node& parent, const std::string& name,
                     const std::string& content = {},
                     const std::string& mode = "0644");
    Node& createDirectory(Node& parent, const std::string& name,
                          const std::string& mode = "0755");

    /// Удаляет узел (для каталога — вместе со всем поддеревом).
    /// Корневой каталог удалить нельзя. Бросает VfsError.
    void remove(Node& node);

    /// Суммарная статистика по дереву.
    VfsStats stats() const;

private:
    Node* findInternal(const std::string& absolutePath);
    static void collectStats(const Node& node, VfsStats& stats);

    std::string name_ = "vfs";
    std::unique_ptr<Node> root_;
};

}  // namespace emu
