#include "Native201Api.hpp"
#include <fstream>
#include <stdexcept>
#include <sstream>
#include <iomanip>
#include <string>
#include <vector>
#include <cstdint>
#include <filesystem>
#include <iosfwd>

namespace range9d201 {

std::array<std::uint8_t, RAW_BYTES> readRaw(const std::filesystem::path& path) {
    std::ifstream in(path, std::ios::binary);
    if (!in) {
        throw std::runtime_error("Failed to open raw file");
    }
    std::array<std::uint8_t, RAW_BYTES> data{};
    in.read(reinterpret_cast<char*>(data.data()), RAW_BYTES);
    if (!in || in.gcount() != static_cast<std::streamsize>(RAW_BYTES)) {
        throw std::runtime_error("Failed to read exact 126 bytes");
    }
    if (in.peek() != std::char_traits<char>::eof()) throw std::runtime_error("Raw file exceeds126 bytes");
    return data;
}

std::vector<Case> frozenCases() {
    return {
        {"equal_begin_middle", 0x1000, 0x1000, 0x1020, 0x9000},
        {"equal_middle_end", 0x1000, 0x1020, 0x1020, 0x9000},
        {"aligned", 0x1000, 0x1010, 0x1020, 0x9000},
        {"software_misaligned", 0x1001, 0x1012, 0x1039, 0x9000},
        {"software_negative", 0x8000, 0x1013, 0x1000, 0x9000},
        {"software_wrap", 0xfffffffffffffff8, 0x7ffffffffffffffc, 0x8000000000000004, 0x9000}
    };
}

static std::string escapeJsonString(const std::string& s) {
    std::string out;
    for (char c : s) {
        if (c == '"') out += "\\\"";
        else if (c == '\\') out += "\\\\";
        else if (c == '\n') out += "\\n";
        else if (c == '\r') out += "\\r";
        else if (c == '\t') out += "\\t";
        else if (static_cast<unsigned char>(c)<0x20) {
            std::ostringstream encoded;
            encoded << "\\u" << std::hex << std::setw(4) << std::setfill('0')
                    << static_cast<unsigned>(static_cast<unsigned char>(c));
            out += encoded.str();
        } else out += c;
    }
    return out;
}

void writeRun(std::ostream& out, const Run& result) {
    out << "{\n";
    out << "  \"rows\": [\n";
    for (size_t i = 0; i < result.rows.size(); ++i) {
        const Row& r = result.rows[i];
        out << "    {\n";
        out << "      \"id\": \"" << escapeJsonString(r.id) << "\",\n";
        out << "      \"rax\": \"" << escapeJsonString(r.rax) << "\",\n";
        out << "      \"events\": \"" << escapeJsonString(r.events) << "\"\n";
        out << "    }";
        if (i + 1 < result.rows.size()) out << ",\n";
        else out << "\n";
    }
    out << "  ],\n";
    out << "  \"rawUnchanged\": " << (result.rawUnchanged ? "true" : "false") << ",\n";
    out << "  \"protectionsFinal\": " << (result.protectionsFinal ? "true" : "false") << ",\n";
    out << "  \"mappingReleased\": " << (result.mappingReleased ? "true" : "false") << ",\n";
    out << "  \"callbackGuard\": " << (result.callbackGuard ? "true" : "false") << "\n";
    out << "}\n";
}

}
