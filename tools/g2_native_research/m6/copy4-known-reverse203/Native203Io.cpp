#include "Native203Api.hpp"
#include <fstream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace copy4knownreverse203 {

static std::string readAll(const std::filesystem::path& path) {
    std::ifstream in(path, std::ios::binary);
    if (!in) throw std::runtime_error("cannot open file");
    std::ostringstream ss;
    ss << in.rdbuf();
    return ss.str();
}

std::array<std::uint8_t, UPPER_BYTES> readUpper(const std::filesystem::path& path) {
    std::string content = readAll(path);
    if (content.size() != UPPER_BYTES) throw std::runtime_error("upper size mismatch");
    std::array<std::uint8_t, UPPER_BYTES> out{};
    for (std::size_t i = 0; i < UPPER_BYTES; ++i) {
        out[i] = static_cast<std::uint8_t>(content[i]);
    }
    return out;
}

std::array<std::uint8_t, CALLER_BYTES> readCaller(const std::filesystem::path& path) {
    std::string content = readAll(path);
    if (content.size() != CALLER_BYTES) throw std::runtime_error("caller size mismatch");
    std::array<std::uint8_t, CALLER_BYTES> out{};
    for (std::size_t i = 0; i < CALLER_BYTES; ++i) {
        out[i] = static_cast<std::uint8_t>(content[i]);
    }
    return out;
}

std::array<std::uint8_t, REVERSE_BYTES> readReverse(const std::filesystem::path& path) {
    std::string content = readAll(path);
    if (content.size() != REVERSE_BYTES) throw std::runtime_error("reverse size mismatch");
    std::array<std::uint8_t, REVERSE_BYTES> out{};
    for (std::size_t i = 0; i < REVERSE_BYTES; ++i) {
        out[i] = static_cast<std::uint8_t>(content[i]);
    }
    return out;
}

std::array<std::uint8_t, 4> readLiteral(const std::filesystem::path& path) {
    std::string content = readAll(path);
    if (content.size() != 4) throw std::runtime_error("literal size mismatch");
    std::array<std::uint8_t, 4> out{};
    for (std::size_t i = 0; i < 4; ++i) {
        out[i] = static_cast<std::uint8_t>(content[i]);
    }
    return out;
}

std::vector<Case> frozenCases() {
    return {
        {"empty_unseeded_header", true, 0, 0, 0, 0, -1, 0, false, 0},
        {"middle_three", false, 5, 12, 2, 3, -1, 0, false, 0},
        {"append_no_reverse", false, 5, 12, 5, 3, -1, 0, false, 0},
        {"front_avx", false, 9, 20, 0, 9, -1, 0, true, 0x28},
        {"capacity_exact", false, 6, 9, 1, 3, -1, 0, false, 0},
        {"source_alias_old_words", false, 5, 10, 2, 3, 1, 0, false, 0},
        {"growth_passthrough", false, 4, 4, 2, 2, -1, 6, false, 0}
    };
}

void writeRun(std::ostream& output, const Run& result) {
    output << "{\n";
    output << "  \"rows\": [\n";
    for (std::size_t i = 0; i < result.rows.size(); ++i) {
        const Row& row = result.rows[i];
        output << "    {\n";
        output << "      \"id\": \"" << row.id << "\",\n";
        if (row.hasHeader) {
            output << "      \"headerAfter\": {\n";
            output << "        \"baseHex\": \"" << row.baseHex << "\",\n";
            output << "        \"capacityHex\": \"" << row.capacityHex << "\",\n";
            output << "        \"sizeHex\": \"" << row.sizeHex << "\",\n";
            output << "        \"allocatorHex\": \"" << row.allocatorHex << "\"\n";
            output << "      },\n";
        } else {
            output << "      \"headerAfter\": null,\n";
        }
        output << "      \"oldWordsHex\": [";
        for (std::size_t j = 0; j < row.oldWordsHex.size(); ++j) {
            if (j > 0) output << ", ";
            output << "\"" << row.oldWordsHex[j] << "\"";
        }
        output << "],\n";
        output << "      \"allocationWordsHex\": [";
        for (std::size_t j = 0; j < row.allocationWordsHex.size(); ++j) {
            if (j > 0) output << ", ";
            output << "\"" << row.allocationWordsHex[j] << "\"";
        }
        output << "],\n";
        output << "      \"sourceWordsHex\": [";
        for (std::size_t j = 0; j < row.sourceWordsHex.size(); ++j) {
            if (j > 0) output << ", ";
            output << "\"" << row.sourceWordsHex[j] << "\"";
        }
        output << "],\n";
        output << "      \"callbacks\": [";
        for (std::size_t j = 0; j < row.callbacks.size(); ++j) {
            if (j > 0) output << ", ";
            output << "\"" << row.callbacks[j] << "\"";
        }
        output << "]\n";
        output << "    }";
        if (i + 1 < result.rows.size()) output << ",\n";
        else output << "\n";
    }
    output << "  ],\n";
    output << "  \"skipped\": [";
    for (std::size_t i = 0; i < result.skipped.size(); ++i) {
        if (i > 0) output << ", ";
        output << "\"" << result.skipped[i] << "\"";
    }
    output << "],\n";
    output << "  \"avx2Eligible\": " << (result.avx2Eligible ? "true" : "false") << ",\n";
    output << "  \"rawUnchanged\": " << (result.rawUnchanged ? "true" : "false") << ",\n";
    output << "  \"protectionsFinal\": " << (result.protectionsFinal ? "true" : "false") << ",\n";
    output << "  \"mappingReleased\": " << (result.mappingReleased ? "true" : "false") << ",\n";
    output << "  \"callbackGuard\": " << (result.callbackGuard ? "true" : "false") << ",\n";
    output << "  \"memoryGuard\": " << (result.memoryGuard ? "true" : "false") << "\n";
    output << "}\n";
}

}