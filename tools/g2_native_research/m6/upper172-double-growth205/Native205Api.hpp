#pragma once
#include <array>
#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <iosfwd>
#include <span>
#include <string>
#include <vector>
namespace upper172doublegrowth205 {
inline constexpr std::size_t UPPER_BYTES=172,RANGE_BYTES=424,ADD_BYTES=351;
struct Case { std::string id;bool source16HeaderAlias;std::int32_t count16,count4; };
struct Header { std::string base;std::int32_t capacity{},size{};std::string allocatorRvaHex; };
struct Call { std::string kind,target;std::vector<std::string> args; };
struct Row {
    std::string id;bool returnedDestination{};std::string vptrRvaHex,kindHex,tailHex,flagHex;
    Header header16,header4;bool release16SnapshotTaken{},release4SnapshotTaken{};
    Header beforeRelease16,beforeRelease4;std::string buffer16Hex,buffer4Hex;
    std::vector<Call> calls;
};
struct Run { std::vector<Row> rows;bool rawUnchanged{},protectionsFinal{},mappingReleased{},callbackGuard{},memoryGuard{},forbiddenTargetsUnmapped{}; };
Run executeOriginal(std::span<const std::uint8_t,UPPER_BYTES> upper,std::span<const std::uint8_t,RANGE_BYTES> range,std::span<const std::uint8_t,ADD_BYTES> add,std::span<const std::uint8_t,4> literal,std::span<const Case> cases);
std::array<std::uint8_t,UPPER_BYTES> readUpper(const std::filesystem::path& path);
std::array<std::uint8_t,RANGE_BYTES> readRange(const std::filesystem::path& path);
std::array<std::uint8_t,ADD_BYTES> readAdd(const std::filesystem::path& path);
std::array<std::uint8_t,4> readLiteral(const std::filesystem::path& path);
std::vector<Case> frozenCases();
void writeRun(std::ostream& out,const Run& result);
}
