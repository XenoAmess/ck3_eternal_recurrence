#pragma once
#include <array>
#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <iosfwd>
#include <span>
#include <string>
#include <vector>
namespace reverse4220aa4_202 {
inline constexpr std::size_t REVERSE_BYTES=194, CALLER_BYTES=126;
struct Case { std::string id; unsigned words,splitWords; bool whole,hasFeature; std::uint32_t featureWord; };
struct Row { std::string id,raxHex,dataBaseHex; std::vector<std::string> wordsHex; };
struct Run { std::vector<Row> rows; std::vector<std::string> skipped; bool avx2Eligible,rawUnchanged,protectionsFinal,mappingReleased,memoryGuard; };
Run executeOriginal(std::span<const std::uint8_t,REVERSE_BYTES> reverse,std::span<const std::uint8_t,CALLER_BYTES> caller,std::span<const Case> cases);
std::array<std::uint8_t,REVERSE_BYTES> readReverse(const std::filesystem::path& path);
std::array<std::uint8_t,CALLER_BYTES> readCaller(const std::filesystem::path& path);
std::vector<Case> frozenCases();
void writeRun(std::ostream& out,const Run& result);
}
