#include "Native205Api.hpp"
#include <fstream>
#include <stdexcept>
#include <iomanip>
#include <sstream>
#include <string>
#include <vector>

namespace upper172doublegrowth205 {

static std::string escapeJson(const std::string& s) {
    std::string out;
    for (char c : s) {
        if (c == '"') out += "\\\"";
        else if (c == '\\') out += "\\\\";
        else if (c == '\n') out += "\\n";
        else if (c == '\r') out += "\\r";
        else if (c == '\t') out += "\\t";
        else out += c;
    }
    return out;
}

static void writeHeader(std::ostream& out, const Header& h) {
    out << "{\"base\":\"" << escapeJson(h.base) << "\",\"capacity\":" << h.capacity << ",\"size\":" << h.size << ",\"allocatorRvaHex\":\"" << escapeJson(h.allocatorRvaHex) << "\"}";
}

static void writeCall(std::ostream& out, const Call& c) {
    out << "{\"kind\":\"" << escapeJson(c.kind) << "\",\"target\":\"" << escapeJson(c.target) << "\",\"args\":[";
    for (size_t i = 0; i < c.args.size(); ++i) {
        if (i > 0) out << ",";
        out << "\"" << escapeJson(c.args[i]) << "\"";
    }
    out << "]}";
}

static void writeRow(std::ostream& out, const Row& r) {
    out << "{";
    out << "\"id\":\"" << escapeJson(r.id) << "\",";
    out << "\"returnedDestination\":" << (r.returnedDestination ? "true" : "false") << ",";
    out << "\"vptrRvaHex\":\"" << escapeJson(r.vptrRvaHex) << "\",";
    out << "\"kindHex\":\"" << escapeJson(r.kindHex) << "\",";
    out << "\"tailHex\":\"" << escapeJson(r.tailHex) << "\",";
    out << "\"flagHex\":\"" << escapeJson(r.flagHex) << "\",";
    out << "\"header16\":";
    writeHeader(out, r.header16);
    out << ",\"header4\":";
    writeHeader(out, r.header4);
    out << ",\"release16SnapshotTaken\":" << (r.release16SnapshotTaken ? "true" : "false") << ",";
    if (r.release16SnapshotTaken) {
        out << "\"beforeRelease16\":";
        writeHeader(out, r.beforeRelease16);
    } else {
        out << "\"beforeRelease16\":null";
    }
    out << ",\"release4SnapshotTaken\":" << (r.release4SnapshotTaken ? "true" : "false") << ",";
    if (r.release4SnapshotTaken) {
        out << "\"beforeRelease4\":";
        writeHeader(out, r.beforeRelease4);
    } else {
        out << "\"beforeRelease4\":null";
    }
    out << ",\"buffer16Hex\":\"" << escapeJson(r.buffer16Hex) << "\",";
    out << "\"buffer4Hex\":\"" << escapeJson(r.buffer4Hex) << "\",";
    out << "\"calls\":[";
    for (size_t i = 0; i < r.calls.size(); ++i) {
        if (i > 0) out << ",";
        writeCall(out, r.calls[i]);
    }
    out << "]}";
}

void writeRun(std::ostream& out, const Run& result) {
    out << "{";
    out << "\"rows\":[";
    for (size_t i = 0; i < result.rows.size(); ++i) {
        if (i > 0) out << ",";
        writeRow(out, result.rows[i]);
    }
    out << "],";
    out << "\"rawUnchanged\":" << (result.rawUnchanged ? "true" : "false") << ",";
    out << "\"protectionsFinal\":" << (result.protectionsFinal ? "true" : "false") << ",";
    out << "\"mappingReleased\":" << (result.mappingReleased ? "true" : "false") << ",";
    out << "\"callbackGuard\":" << (result.callbackGuard ? "true" : "false") << ",";
    out << "\"memoryGuard\":" << (result.memoryGuard ? "true" : "false") << ",";
    out << "\"forbiddenTargetsUnmapped\":" << (result.forbiddenTargetsUnmapped ? "true" : "false");
    out << "}";
}

template<std::size_t Size> static std::array<std::uint8_t,Size> readExact(const std::filesystem::path& path) {
    std::ifstream input(path,std::ios::binary);if(!input)throw std::runtime_error("Cannot open raw file");
    std::array<std::uint8_t,Size> bytes{};input.read(reinterpret_cast<char*>(bytes.data()),static_cast<std::streamsize>(Size));
    if(input.gcount()!=static_cast<std::streamsize>(Size) || input.bad())throw std::runtime_error("Raw file short/read failure");
    char extra=0;if(input.get(extra))throw std::runtime_error("Raw file too long");
    if(!input.eof())throw std::runtime_error("Raw trailing check failed");return bytes;
}

std::array<std::uint8_t,UPPER_BYTES> readUpper(const std::filesystem::path& path) { return readExact<UPPER_BYTES>(path); }
std::array<std::uint8_t,RANGE_BYTES> readRange(const std::filesystem::path& path) { return readExact<RANGE_BYTES>(path); }
std::array<std::uint8_t,ADD_BYTES> readAdd(const std::filesystem::path& path) { return readExact<ADD_BYTES>(path); }
std::array<std::uint8_t,4> readLiteral(const std::filesystem::path& path) { return readExact<4>(path); }

std::vector<Case> frozenCases() {
    return {
        {"separate_double_growth", false, 2, 2},
        {"source16_header_alias_double_growth", true, 1, 1}
    };
}

}