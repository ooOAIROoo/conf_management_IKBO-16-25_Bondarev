#pragma once

#include <string>

namespace emu {

/// Декодирует Base64 (RFC 4648, с padding '='). Бросает std::invalid_argument
/// при недопустимых символах или неверной длине.
std::string base64Decode(const std::string& input);

/// Кодирует произвольные байты в Base64 (используется в тестах и отладке).
std::string base64Encode(const std::string& input);

}  // namespace emu
