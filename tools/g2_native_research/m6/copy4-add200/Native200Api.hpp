#pragma once
#include <array>
#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <iosfwd>
#include <span>
#include <string>
#include <vector>
namespace copy4add200 {
inline constexpr std::size_t RAW_BYTES=351;
struct Case { std::string id;std::int32_t capacity,size,index,count;int mutation;bool emptyNull,oldNull; };
struct Call { std::string kind,target;std::vector<std::string> args; };
struct Row { std::string id;bool hasHeader;std::string base;std::int32_t capacity,size;std::string allocator;std::vector<Call> calls; };
struct Run { std::vector<Row> rows;bool rawUnchanged,protectionsFinal,mappingReleased,callbackGuard,memoryGuard; };
Run executeOriginal(std::span<const std::uint8_t,RAW_BYTES> raw,std::span<const std::uint8_t,4> literal,std::span<const Case> cases);
std::array<std::uint8_t,RAW_BYTES> readRaw(const std::filesystem::path& path);
std::array<std::uint8_t,4> readLiteral(const std::filesystem::path& path);
std::vector<Case> frozenCases();
void writeRun(std::ostream& output,const Run& result);
}
