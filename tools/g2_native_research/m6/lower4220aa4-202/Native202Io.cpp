#include "Native202Api.hpp"
#include <fstream>
#include <sstream>
#include <string>
#include <vector>
#include <cstdint>
#include <iomanip>
#include <stdexcept>

namespace reverse4220aa4_202 {
namespace {
std::string escaped(const std::string& text) {
    std::ostringstream out;
    for(unsigned char value:text) {
        if(value=='"')out << "\\\"";
        else if(value=='\\')out << "\\\\";
        else if(value<0x20)out << "\\u" << std::hex << std::setw(4) << std::setfill('0') << static_cast<unsigned>(value) << std::dec;
        else out << static_cast<char>(value);
    }
    return out.str();
}
}


std::array<std::uint8_t, REVERSE_BYTES> readReverse(const std::filesystem::path& path) {
    std::ifstream file(path, std::ios::binary);
    if (!file.is_open()) {
        throw std::runtime_error("Failed to open reverse file: " + path.string());
    }
    std::array<std::uint8_t, REVERSE_BYTES> data{};
    file.read(reinterpret_cast<char*>(data.data()), REVERSE_BYTES);
    if (!file.good() || file.gcount() != static_cast<std::streamsize>(REVERSE_BYTES)) {
        throw std::runtime_error("Reverse file size mismatch or read error");
    }
    // Reject trailing bytes
    file.seekg(0, std::ios::end);
    if (file.tellg() != static_cast<std::streampos>(REVERSE_BYTES)) {
        throw std::runtime_error("Reverse file has trailing bytes");
    }
    return data;
}

std::array<std::uint8_t, CALLER_BYTES> readCaller(const std::filesystem::path& path) {
    std::ifstream file(path, std::ios::binary);
    if (!file.is_open()) {
        throw std::runtime_error("Failed to open caller file: " + path.string());
    }
    std::array<std::uint8_t, CALLER_BYTES> data{};
    file.read(reinterpret_cast<char*>(data.data()), CALLER_BYTES);
    if (!file.good() || file.gcount() != static_cast<std::streamsize>(CALLER_BYTES)) {
        throw std::runtime_error("Caller file size mismatch or read error");
    }
    // Reject trailing bytes
    file.seekg(0, std::ios::end);
    if (file.tellg() != static_cast<std::streampos>(CALLER_BYTES)) {
        throw std::runtime_error("Caller file has trailing bytes");
    }
    return data;
}

std::vector<Case> frozenCases() {
    std::vector<Case> cases;
    // Direct cases (12)
    cases.push_back({"n0_short_unseeded", 0, 0, false, false, 0});
    cases.push_back({"n1_short_unseeded", 1, 0, false, false, 0});
    cases.push_back({"n2_short_unseeded", 2, 0, false, false, 0});
    cases.push_back({"n7_short_unseeded", 7, 0, false, false, 0});
    cases.push_back({"n8_short_unseeded", 8, 0, false, false, 0});
    cases.push_back({"n9_short_unseeded", 9, 0, false, false, 0});
    cases.push_back({"n10_short_unseeded", 10, 0, false, false, 0});
    cases.push_back({"n16_bit5_off_otherbit_on", 16, 0, false, true, 0x40000000});
    cases.push_back({"n16_bit5_on", 16, 0, false, true, 0x28});
    cases.push_back({"n17_bit5_on", 17, 0, false, true, 0x28});
    cases.push_back({"n18_bit5_on", 18, 0, false, true, 0x28});
    cases.push_back({"n24_bit5_on", 24, 0, false, true, 0x28});
    // Whole cases (2)
    cases.push_back({"whole8_split3", 8, 3, true, false, 0});
    cases.push_back({"whole24_split8", 24, 8, true, true, 0x28});
    return cases;
}

void writeRun(std::ostream& out, const Run& result) {
    out << "{\n";
    out << "  \"rows\": [\n";
    for (size_t i = 0; i < result.rows.size(); ++i) {
        const Row& row = result.rows[i];
        out << "    {\n";
        out << "      \"id\": \"" << escaped(row.id) << "\",\n";
        out << "      \"raxHex\": \"" << escaped(row.raxHex) << "\",\n";
        out << "      \"dataBaseHex\": \"" << escaped(row.dataBaseHex) << "\",\n";
        out << "      \"wordsHex\": [\n";
        for (size_t j = 0; j < row.wordsHex.size(); ++j) {
            out << "        \"" << escaped(row.wordsHex[j]) << "\"";
            if (j + 1 < row.wordsHex.size()) out << ",\n";
        }
        out << "      ]\n";
        out << "    }";
        if (i + 1 < result.rows.size()) out << ",\n";
    }
    out << "  ],\n";
    out << "  \"skipped\": [\n";
    for (size_t i = 0; i < result.skipped.size(); ++i) {
        out << "    \"" << escaped(result.skipped[i]) << "\"";
        if (i + 1 < result.skipped.size()) out << ",\n";
    }
    out << "  ],\n";
    out << "  \"avx2Eligible\": " << (result.avx2Eligible ? "true" : "false") << ",\n";
    out << "  \"rawUnchanged\": " << (result.rawUnchanged ? "true" : "false") << ",\n";
    out << "  \"protectionsFinal\": " << (result.protectionsFinal ? "true" : "false") << ",\n";
    out << "  \"mappingReleased\": " << (result.mappingReleased ? "true" : "false") << ",\n";
    out << "  \"memoryGuard\": " << (result.memoryGuard ? "true" : "false") << "\n";
    out << "}\n";
}

}