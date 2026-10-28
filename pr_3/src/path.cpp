#include "emu/path.hpp"

namespace emu::path {
namespace {

std::vector<std::string> split(const std::string& value) {
    std::vector<std::string> parts;
    std::string current;
    for (const char c : value) {
        if (c == '/' || c == '\\') {
            if (!current.empty()) {
                parts.push_back(current);
                current.clear();
            }
            continue;
        }
        current.push_back(c);
    }
    if (!current.empty()) {
        parts.push_back(current);
    }
    return parts;
}

std::string fromComponents(const std::vector<std::string>& parts) {
    if (parts.empty()) {
        return "/";
    }
    std::string result;
    for (const std::string& part : parts) {
        result += '/';
        result += part;
    }
    return result;
}

}  // namespace

std::string normalize(const std::string& input, const std::string& cwd) {
    std::vector<std::string> parts =
        (input.empty() || input.front() != '/') ? components(cwd) : std::vector<std::string>{};

    for (const std::string& part : split(input)) {
        if (part == ".") {
            continue;
        }
        if (part == "..") {
            if (!parts.empty()) {
                parts.pop_back();
            }
            continue;
        }
        parts.push_back(part);
    }
    return fromComponents(parts);
}

std::vector<std::string> components(const std::string& absolute) {
    return split(absolute);
}

std::string join(const std::string& base, const std::string& relative) {
    return normalize(relative, base);
}

std::string basename(const std::string& absolute) {
    const std::vector<std::string> parts = components(absolute);
    return parts.empty() ? "/" : parts.back();
}

std::string dirname(const std::string& absolute) {
    std::vector<std::string> parts = components(absolute);
    if (!parts.empty()) {
        parts.pop_back();
    }
    return fromComponents(parts);
}

}  // namespace emu::path
