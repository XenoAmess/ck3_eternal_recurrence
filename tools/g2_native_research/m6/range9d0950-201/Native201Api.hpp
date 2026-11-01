#pragma once
#include <array>
#include <cstdint>
#include <filesystem>
#include <iosfwd>
#include <span>
#include <string>
#include <vector>
namespace range9d201 {
inline constexpr std::size_t RAW_BYTES=126;
struct Case { std::string id; std::uint64_t begin,middle,end,entryR9; };
struct Row { std::string id,rax,events; };
struct Run { std::vector<Row> rows; bool rawUnchanged,protectionsFinal,mappingReleased,callbackGuard; };
Run executeOriginal(std::span<const std::uint8_t,RAW_BYTES> raw,std::span<const Case> cases);
std::array<std::uint8_t,RAW_BYTES> readRaw(const std::filesystem::path& path);
std::vector<Case> frozenCases();
void writeRun(std::ostream& out,const Run& result);
}
