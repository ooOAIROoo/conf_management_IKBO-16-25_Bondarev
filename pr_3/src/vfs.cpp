#include "emu/vfs.hpp"

#include <algorithm>
#include <cctype>
#include <fstream>
#include <vector>

#include "emu/base64.hpp"
#include "emu/csv.hpp"
#include "emu/path.hpp"

namespace emu {
namespace {

std::string toLower(std::string value) {
    std::transform(value.begin(), value.end(), value.begin(),
                   [](unsigned char c) { return static_cast<char>(std::tolower(c)); });
    return value;
}

bool looksLikeOctal(const std::string& mode) {
    if (mode.size() < 3 || mode.size() > 4) {
        return false;
    }
    return std::all_of(mode.begin(), mode.end(),
                       [](unsigned char c) { return c >= '0' && c <= '7'; });
}

void validateName(const std::string& name) {
    if (name.empty()) {
        throw VfsError("имя элемента VFS не может быть пустым");
    }
    if (name == "." || name == "..") {
        throw VfsError("имя \"" + name + "\" зарезервировано");
    }
    if (name.find('/') != std::string::npos ||
        name.find('\\') != std::string::npos) {
        throw VfsError("имя \"" + name + "\" не может содержать разделитель пути");
    }
    if (name.size() > 255) {
        throw VfsError("имя элемента VFS длиннее 255 символов");
    }
}

/// Имя VFS из пути, если в CSV нет директивы "# vfs:".
std::string nameFromFile(const std::string& csvPath) {
    const std::string base = path::basename(csvPath);
    const std::size_t dot = base.find_last_of('.');
    std::string name = (dot != std::string::npos && dot != 0) ? base.substr(0, dot)
                                                              : base;
    return name.empty() ? "vfs" : name;
}

}  // namespace

std::string Node::path() const {
    if (parent == nullptr) {
        return "/";
    }
    std::vector<const Node*> chain;
    const Node* current = this;
    while (current != nullptr && current->parent != nullptr) {
        chain.push_back(current);
        current = current->parent;
    }
    std::string result;
    for (auto it = chain.rbegin(); it != chain.rend(); ++it) {
        result += '/';
        result += (*it)->name;
    }
    return result.empty() ? "/" : result;
}

Vfs::Vfs() : root_(std::make_unique<Node>()) {
    root_->type = Node::Type::Directory;
    root_->name = "/";
    root_->mode = "0755";
}

Node* Vfs::findInternal(const std::string& absolutePath) {
    Node* current = root_.get();
    for (const std::string& part : path::components(absolutePath)) {
        if (!current->isDirectory()) {
            return nullptr;
        }
        const auto it = current->children.find(part);
        if (it == current->children.end()) {
            return nullptr;
        }
        current = it->second.get();
    }
    return current;
}

Node* Vfs::find(const std::string& absolutePath) {
    return findInternal(absolutePath);
}

const Node* Vfs::find(const std::string& absolutePath) const {
    return const_cast<Vfs*>(this)->findInternal(absolutePath);
}

Node& Vfs::createFile(Node& parent, const std::string& name,
                      const std::string& content, const std::string& mode) {
    if (!parent.isDirectory()) {
        throw VfsError("нельзя создать файл в не-каталоге " + parent.path());
    }
    validateName(name);
    if (parent.children.count(name) != 0) {
        throw VfsError("элемент уже существует: " + path::join(parent.path(), name));
    }
    auto node = std::make_unique<Node>();
    node->type = Node::Type::File;
    node->name = name;
    node->mode = mode.empty() ? "0644" : mode;
    node->content = content;
    node->parent = &parent;
    Node* raw = node.get();
    parent.children.emplace(name, std::move(node));
    return *raw;
}

Node& Vfs::createDirectory(Node& parent, const std::string& name,
                           const std::string& mode) {
    if (!parent.isDirectory()) {
        throw VfsError("нельзя создать каталог в не-каталоге " + parent.path());
    }
    validateName(name);
    if (parent.children.count(name) != 0) {
        throw VfsError("элемент уже существует: " + path::join(parent.path(), name));
    }
    auto node = std::make_unique<Node>();
    node->type = Node::Type::Directory;
    node->name = name;
    node->mode = mode.empty() ? "0755" : mode;
    node->parent = &parent;
    Node* raw = node.get();
    parent.children.emplace(name, std::move(node));
    return *raw;
}

void Vfs::remove(Node& node) {
    if (node.parent == nullptr) {
        throw VfsError("нельзя удалить корневой каталог");
    }
    node.parent->children.erase(node.name);
}

VfsStats Vfs::stats() const {
    VfsStats result;
    collectStats(*root_, result);
    return result;
}

void Vfs::collectStats(const Node& node, VfsStats& stats) {
    if (node.isDirectory()) {
        ++stats.directories;
        for (const auto& entry : node.children) {
            collectStats(*entry.second, stats);
        }
    } else {
        ++stats.files;
        stats.bytes += node.size();
    }
}

Vfs Vfs::loadFromCsv(const std::string& csvPath) {
    std::ifstream input(csvPath, std::ios::binary);
    if (!input) {
        throw VfsError("не удалось открыть CSV-файл VFS: " + csvPath);
    }

    Vfs vfs;
    bool nameSet = false;
    bool headerSeen = false;
    bool rootSeen = false;
    bool firstLine = true;
    std::size_t lineNumber = 0;
    std::string line;

    auto fail = [&](const std::string& message) {
        throw VfsError(csvPath + ':' + std::to_string(lineNumber) + ": " + message);
    };

    while (std::getline(input, line)) {
        ++lineNumber;
        if (firstLine && line.rfind("\xEF\xBB\xBF", 0) == 0) {
            line.erase(0, 3);
        }
        firstLine = false;
        if (!line.empty() && line.back() == '\r') {
            line.pop_back();
        }

        const std::string trimmed = trim(line);
        if (trimmed.empty()) {
            continue;
        }
        if (trimmed.front() == '#') {
            // Комментарии и директива с именем VFS.
            const std::string comment = trim(trimmed.substr(1));
            if (comment.rfind("vfs:", 0) == 0) {
                const std::string value = trim(comment.substr(4));
                if (!value.empty()) {
                    vfs.name_ = value;
                    nameSet = true;
                }
            }
            continue;
        }

        std::vector<std::string> fields;
        try {
            fields = parseCsvLine(line);
        } catch (const CsvError& error) {
            fail(error.what());
        }
        if (fields.size() < 4) {
            fail("ожидается не менее 4 полей: type,name,parent,mode[,content,encoding]");
        }

        if (!headerSeen) {
            const std::string first = toLower(trim(fields[0]));
            if (first != "type") {
                fail("первая строка данных должна быть заголовком "
                     "type,name,parent,mode,content,encoding");
            }
            headerSeen = true;
            continue;
        }

        const std::string type = toLower(trim(fields[0]));
        const std::string name = trim(fields[1]);
        const std::string parentPath = trim(fields[2]);
        std::string mode = fields.size() > 3 ? trim(fields[3]) : std::string();
        const std::string content = fields.size() > 4 ? fields[4] : std::string();
        const std::string encoding =
            fields.size() > 5 ? toLower(trim(fields[5])) : std::string("text");

        if (type != "dir" && type != "file") {
            fail("неизвестный тип элемента: \"" + type + "\" (ожидается dir или file)");
        }
        if (!mode.empty() && !looksLikeOctal(mode)) {
            fail("права доступа должны быть восьмеричным числом, например 0755");
        }
        if (mode.empty()) {
            mode = (type == "dir") ? "0755" : "0644";
        }

        std::string decoded;
        if (encoding == "base64") {
            try {
                decoded = base64Decode(content);
            } catch (const std::exception& error) {
                fail(std::string("ошибка Base64: ") + error.what());
            }
        } else if (encoding == "text" || encoding.empty()) {
            decoded = content;
        } else {
            fail("неизвестная кодировка содержимого: \"" + encoding +
                 "\" (ожидается text или base64)");
        }

        // Корневой каталог: имя "/", родитель пуст.
        if (name == "/") {
            if (type != "dir") {
                fail("корневой элемент должен быть каталогом");
            }
            if (rootSeen) {
                fail("корневой каталог объявлен повторно");
            }
            if (!parentPath.empty() && parentPath != "/") {
                fail("у корневого каталога не может быть родителя");
            }
            vfs.root_->mode = mode;
            rootSeen = true;
            continue;
        }

        if (type == "dir" && name.empty()) {
            fail("пустое имя каталога");
        }
        if (parentPath.empty()) {
            fail("для элемента \"" + name + "\" не указан родительский каталог");
        }

        const std::string normalizedParent = path::normalize(parentPath, "/");
        Node* parent = vfs.find(normalizedParent);
        if (parent == nullptr) {
            fail("родительский каталог не найден: " + normalizedParent);
        }
        if (!parent->isDirectory()) {
            fail("родитель не является каталогом: " + normalizedParent);
        }
        if (parent->children.count(name) != 0) {
            fail("элемент уже существует: " + path::join(normalizedParent, name));
        }

        try {
            if (type == "dir") {
                vfs.createDirectory(*parent, name, mode);
            } else {
                vfs.createFile(*parent, name, decoded, mode);
            }
        } catch (const VfsError& error) {
            fail(error.what());
        }
    }

    if (!headerSeen) {
        throw VfsError(csvPath + ": файл пуст или не содержит заголовка CSV");
    }
    if (!nameSet) {
        vfs.name_ = nameFromFile(csvPath);
    }
    return vfs;
}

}  // namespace emu
