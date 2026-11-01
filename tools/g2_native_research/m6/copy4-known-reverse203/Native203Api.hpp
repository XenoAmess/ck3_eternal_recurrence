#pragma once
#include <array>
#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <iosfwd>
#include <span>
#include <string>
#include <vector>
namespace copy4knownreverse203 {
inline constexpr std::size_t UPPER_BYTES=351,CALLER_BYTES=126,REVERSE_BYTES=194;
struct Case { std::string id;bool empty;std::int32_t oldSize,capacity,index,sourceCount,aliasOffset,newCapacity;bool hasFeature;std::uint32_t featureWord; };
struct Row {
    std::string id;bool hasHeader;std::string baseHex,capacityHex,sizeHex,allocatorHex;
    std::vector<std::string> oldWordsHex,allocationWordsHex,sourceWordsHex,callbacks;
};
struct Run { std::vector<Row> rows;std::vector<std::string> skipped;bool avx2Eligible,rawUnchanged,protectionsFinal,mappingReleased,callbackGuard,memoryGuard; };
Run executeOriginal(std::span<const std::uint8_t,UPPER_BYTES> upper,std::span<const std::uint8_t,CALLER_BYTES> caller,std::span<const std::uint8_t,REVERSE_BYTES> reverse,std::span<const std::uint8_t,4> literal,std::span<const Case> cases);
std::array<std::uint8_t,UPPER_BYTES> readUpper(const std::filesystem::path& path);
std::array<std::uint8_t,CALLER_BYTES> readCaller(const std::filesystem::path& path);
std::array<std::uint8_t,REVERSE_BYTES> readReverse(const std::filesystem::path& path);
std::array<std::uint8_t,4> readLiteral(const std::filesystem::path& path);
std::vector<Case> frozenCases();
void writeRun(std::ostream& output,const Run& result);
}
