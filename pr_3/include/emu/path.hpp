#pragma once

#include <string>
#include <vector>

namespace emu::path {

/// Приводит путь к абсолютному виду внутри VFS: убирает ".", обрабатывает
/// "..", схлопывает повторяющиеся разделители. Пустой путь трактуется как cwd.
/// Разделителем считается и '/', и '\' (удобство для Windows).
std::string normalize(const std::string& input, const std::string& cwd);

/// Делит абсолютный путь на компоненты (для "/" — пустой вектор).
std::vector<std::string> components(const std::string& absolute);

/// Собирает абсолютный путь из базового и относительного.
std::string join(const std::string& base, const std::string& relative);

/// Последний компонент пути ("/" -> "/").
std::string basename(const std::string& absolute);

/// Родительский путь ("/" -> "/").
std::string dirname(const std::string& absolute);

}  // namespace emu::path
