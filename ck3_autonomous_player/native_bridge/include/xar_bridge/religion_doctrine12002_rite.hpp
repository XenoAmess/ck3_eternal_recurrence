#pragma once

#include "xar_bridge/religion_doctrine12002_intrinsic.hpp"

namespace xar::ck3_12002::religion::doctrine12002 {

inline constexpr std::size_t kRiteEffectiveDoctrineDataOffset = 0x7A0;
inline constexpr std::size_t kRiteEffectiveDoctrineCapacityOffset = 0x7A8;
inline constexpr std::size_t kRiteEffectiveDoctrineCountOffset = 0x7AC;

struct RiteDoctrineSnapshot {
  bool available = false;
  std::string unavailable_reason = "bindings_unavailable";
  std::uint64_t capture_epoch = 0;
  std::int32_t date_raw = 0;
  std::int32_t played_character_id = -1;
  std::optional<std::uint32_t> rite_id;
  std::optional<std::uint32_t> faith_id;
  std::vector<DoctrineRow> rows;
};

// The existing application-main paused owner supplies the context bindings.
// This reads the played actor's own Rite, never Faith.main_rite as a substitute.
bool ReadPlayedRiteDoctrines12002(const religion::Bindings &bindings,
                                std::uint64_t capture_epoch,
                                RiteDoctrineSnapshot &output) noexcept;
bool HasRiteDoctrineByStableKey12002(const RiteDoctrineSnapshot &snapshot,
                                   std::string_view key) noexcept;
std::string SerializeRiteDoctrines12002(const RiteDoctrineSnapshot &snapshot);

} // namespace xar::ck3_12002::religion::doctrine12002
