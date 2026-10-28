#include "emu/lexer.hpp"

namespace emu {
namespace {

enum class QuoteState { None, Single, Double };

}  // namespace

TokenizeResult tokenize(const std::string& line, bool scriptMode) {
    TokenizeResult result;

    std::string current;
    bool inToken = false;
    bool escaping = false;
    QuoteState quote = QuoteState::None;
    std::size_t quoteColumn = 0;

    auto flush = [&]() {
        if (inToken) {
            result.tokens.push_back(current);
            current.clear();
            inToken = false;
        }
    };

    for (std::size_t i = 0; i < line.size(); ++i) {
        const char c = line[i];

        if (escaping) {
            current.push_back(c);
            inToken = true;
            escaping = false;
            continue;
        }

        if (quote == QuoteState::Single) {
            if (c == '\'') {
                quote = QuoteState::None;
            } else {
                current.push_back(c);
            }
            continue;
        }

        if (quote == QuoteState::Double) {
            if (c == '"') {
                quote = QuoteState::None;
            } else if (c == '\\' && i + 1 < line.size() &&
                       (line[i + 1] == '"' || line[i + 1] == '\\')) {
                current.push_back(line[++i]);
            } else {
                current.push_back(c);
            }
            continue;
        }

        // Вне кавычек: комментарий в скрипте начинается с '#' в начале слова.
        if (scriptMode && c == '#' && !inToken) {
            break;
        }

        if (c == ' ' || c == '\t' || c == '\r' || c == '\n') {
            flush();
            continue;
        }

        if (c == '\'' || c == '"') {
            quote = (c == '\'') ? QuoteState::Single : QuoteState::Double;
            quoteColumn = i + 1;
            inToken = true;
            continue;
        }

        if (c == '\\') {
            if (i + 1 >= line.size()) {
                result.error = "обратный слэш в конце строки не экранирует символ";
                result.errorColumn = i + 1;
                return result;
            }
            escaping = true;
            inToken = true;
            continue;
        }

        current.push_back(c);
        inToken = true;
    }

    if (quote != QuoteState::None) {
        result.error = (quote == QuoteState::Single)
                           ? "не закрыта одинарная кавычка"
                           : "не закрыта двойная кавычка";
        result.errorColumn = quoteColumn;
        return result;
    }
    if (escaping) {
        result.error = "незавершённая escape-последовательность";
        result.errorColumn = line.size();
        return result;
    }

    flush();
    return result;
}

}  // namespace emu
