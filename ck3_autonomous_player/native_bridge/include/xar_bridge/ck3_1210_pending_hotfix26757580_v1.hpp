#pragma once
#include <array>
#include <cstddef>
#include <cstdint>
// bb3 hotfix only. Historical 2F2B constants remain in the original header.
// Static file evidence; caller still requires exact mapped pins + Actor owner.
namespace xar::ck3_1210::pending_hotfix26757580 {
inline constexpr char kExecutableSha256[] = "BB3FEF106240E95ECDB6F1532982E89E9432C92A99D33DB623521572F06E6F79";
inline constexpr std::uintptr_t kStorageSlotRva = 0x6A683C0;
inline constexpr std::uintptr_t kDatabaseVtableRva = 0x4E99220;
inline constexpr std::uintptr_t kObjectVtableRva = 0x4E779B8;
inline constexpr std::uintptr_t kPredicateRva = 0x14DECE0;
inline constexpr std::uintptr_t kValidatorRva = 0x2E50270;
inline constexpr std::uintptr_t kReplyPrimaryRva = 0x4AF5900;
inline constexpr std::uintptr_t kReplySecondaryRva = 0x4AF58C8;
inline constexpr std::uintptr_t kOwnerManagerVtableRva = 0x4E99280;
inline constexpr std::size_t kOwnerManagerDataOffset = 0x113C0;
inline constexpr std::array<std::uint8_t,32> kPredicateEntry32 = {
  0x48,0x83,0xEC,0x28,0x81,0x79,0x14,0x6E,0x49,0x68,0x43,0x75,0x1E,0x83,0x79,0x10,
  0xFF,0x74,0x18,0x44,0x8B,0x81,0xD0,0x05,0x00,0x00,0x45,0x85,0xC0,0x74,0x1E,0x41
};
inline constexpr std::array<std::uint8_t,32> kValidatorEntry32 = {
  0x48,0x89,0x5C,0x24,0x10,0x57,0x48,0x83,0xEC,0x20,0x48,0x8B,0xF9,0x83,0x79,0x24,
  0x04,0x0F,0x84,0xF5,0x00,0x00,0x00,0x48,0x8B,0x05,0x32,0x81,0xC1,0x03,0x48,0x85
};
} // namespace xar::ck3_1210::pending_hotfix26757580
