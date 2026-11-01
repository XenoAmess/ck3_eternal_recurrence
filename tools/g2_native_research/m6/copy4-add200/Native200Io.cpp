#include "Native200Api.hpp"
#include <fstream>
#include <iomanip>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace copy4add200 {

std::array<std::uint8_t, RAW_BYTES> readRaw(const std::filesystem::path& path) {
    std::ifstream in(path, std::ios::binary);
    if (!in) {
        throw std::runtime_error("Failed to open raw file: " + path.string());
    }
    std::array<std::uint8_t, RAW_BYTES> data{};
    in.read(reinterpret_cast<char*>(data.data()), RAW_BYTES);
    if (!in) {
        throw std::runtime_error("Failed to read exact 351 bytes from raw file");
    }
    // Check for extra bytes
    in.seekg(0, std::ios::end);
    if (in.tellg() != static_cast<std::streampos>(RAW_BYTES)) {
        throw std::runtime_error("Raw file size mismatch: expected exactly 351 bytes");
    }
    return data;
}

std::array<std::uint8_t, 4> readLiteral(const std::filesystem::path& path) {
    std::ifstream in(path, std::ios::binary);
    if (!in) {
        throw std::runtime_error("Failed to open literal file: " + path.string());
    }
    std::array<std::uint8_t, 4> data{};
    in.read(reinterpret_cast<char*>(data.data()), 4);
    if (!in) {
        throw std::runtime_error("Failed to read exact 4 bytes from literal file");
    }
    // Check for extra bytes
    in.seekg(0, std::ios::end);
    if (in.tellg() != static_cast<std::streampos>(4)) {
        throw std::runtime_error("Literal file size mismatch: expected exactly 4 bytes");
    }
    // Verify content: 00 00 C0 3F
    if (data[0] != 0x00 || data[1] != 0x00 || data[2] != 0xC0 || data[3] != 0x3F) {
        throw std::runtime_error("Literal content mismatch: expected 00 00 C0 3F");
    }
    return data;
}

std::vector<Case> frozenCases() {
    return {
        {"empty_null", 0, 0, 0, 0, 0, true, false},
        {"within_fresh", 8, 2, 1, 2, 1, false, false},
        {"growth_null", 0, 0, 0, 2, 0, false, true},
        {"growth_tail", 2, 2, 1, 2, 0, false, false},
        {"growth_fresh", 2, 2, 1, 2, 2, false, false}
    };
}

static void writeJsonString(std::ostream& out, const std::string& s) {
    out << '"';
    for (char c : s) {
        if (c == '"') out << "\\\"";
        else if (c == '\\') out << "\\\\";
        else if (c == '\n') out << "\\n";
        else if (c == '\r') out << "\\r";
        else if (c == '\t') out << "\\t";
        else if (static_cast<unsigned char>(c) < 0x20) {
            std::ostringstream escaped;
            escaped << "\\u" << std::hex << std::setw(4) << std::setfill('0') << static_cast<int>(c);
            out << escaped.str();
        } else {
            out << c;
        }
    }
    out << '"';
}

void writeRun(std::ostream& output, const Run& result) {
    output << '{';
    output << "\"rows\":[";
    for (std::size_t i = 0; i < result.rows.size(); ++i) {
        if (i > 0) output << ',';
        const Row& r = result.rows[i];
        output << '{';
        output << "\"id\":";
        writeJsonString(output, r.id);
        output << ",\"header\":";
        if (r.hasHeader) {
            output << '{';
            output << "\"base\":";
            writeJsonString(output, r.base);
            output << ",\"capacity\":" << r.capacity;
            output << ",\"size\":" << r.size;
            output << ",\"allocator\":";
            writeJsonString(output, r.allocator);
            output << '}';
        } else {
            output << "null";
        }
        output << ",\"calls\":[";
        for (std::size_t j = 0; j < r.calls.size(); ++j) {
            if (j > 0) output << ',';
            const Call& c = r.calls[j];
            output << '{';
            output << "\"kind\":";
            writeJsonString(output, c.kind);
            output << ",\"target\":";
            writeJsonString(output, c.target);
            output << ",\"args\":[";
            for (std::size_t k = 0; k < c.args.size(); ++k) {
                if (k > 0) output << ',';
                writeJsonString(output, c.args[k]);
            }
            output << "]}";
        }
        output << "]}";
    }
    output << "]";
    output << ",\"rawUnchanged\":" << (result.rawUnchanged ? "true" : "false");
    output << ",\"protectionsFinal\":" << (result.protectionsFinal ? "true" : "false");
    output << ",\"mappingReleased\":" << (result.mappingReleased ? "true" : "false");
    output << ",\"callbackGuard\":" << (result.callbackGuard ? "true" : "false");
    output << ",\"memoryGuard\":" << (result.memoryGuard ? "true" : "false");
    output << '}';
}

}