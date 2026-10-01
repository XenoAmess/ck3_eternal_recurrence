#pragma once

#include "xar_bridge/ck3_12002_religion_context.hpp"

#include <string>
#include <vector>

namespace xar::ck3_12002::religion::doctrine12002 {

// Faith HasDoctrine/GetDoctrines observes its current main Rite. The frozen
// authored Faith intrinsic seed is not an independent current native list.
inline constexpr std::size_t kMainRiteDoctrineArrayOffset = 0x7A0;
inline constexpr std::size_t kMainRiteDoctrineCountOffset = 0x7AC;
inline constexpr std::size_t kDoctrineStableKeyOffset = 0x18;
inline constexpr std::size_t kDoctrineGroupPointerOffset = 0xB08;
inline constexpr std::size_t kDoctrineGroupStableKeyOffset = 0x18;
inline constexpr std::uintptr_t kDoctrineDatabaseGetterRva = 0x8FC740;
inline constexpr std::uintptr_t kDoctrineDatabasePointerRva = 0x5C67198;
inline constexpr std::size_t kDoctrineDatabaseArrayOffset = 0x50;
inline constexpr std::size_t kDoctrineDatabaseCountOffset = 0x5C;

struct DoctrineRow {
  std::string doctrine_key;
  std::string group_key;
  std::string source = "faith_main_rite";
  bool operator==(const DoctrineRow &other) const {
    return doctrine_key == other.doctrine_key && group_key == other.group_key &&
        source == other.source;
  }
};

struct FaithMainRiteDoctrines {
  bool available = false;
  std::string unavailable_reason = "bindings_unavailable";
  std::uint64_t capture_epoch = 0;
  std::int32_t date_raw = 0;
  std::int32_t played_character_id = -1;
  std::optional<std::uint32_t> rite_id;
  std::optional<std::uint32_t> faith_id;
  std::optional<std::uint32_t> main_rite_id;
  std::vector<DoctrineRow> rows;
};

// Existing paused application-main context only; no command or process access.
bool ReadPlayedFaithMainRiteDoctrines12002(const religion::Bindings &bindings,
    std::uint64_t capture_epoch, FaithMainRiteDoctrines &output) noexcept;
// Reusable definition copy for the sibling actual actor-Rite reader. These
// static definitions have stable authored keys; they are not full entity refs.
bool CopyDoctrineDefinition12002(const void *definition, DoctrineRow &output);
std::string SerializeFaithMainRiteDoctrines12002(const FaithMainRiteDoctrines &value);

} // namespace xar::ck3_12002::religion::doctrine12002
