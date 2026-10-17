#pragma once
#include "xar_bridge/ck3_12002_religion_context.hpp"
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace xar::ck3_12004::religion::holy_site_relic {
struct Bindings;
struct FixedModifierEntry {
  std::uint16_t key_raw_u16=0;
  std::int64_t definition_raw_q64=0;
  bool operator==(const FixedModifierEntry &)const=default;
};
struct FixedModifierBlock {
  std::string kind;
  bool available=false;
  std::optional<std::int32_t> count_raw;
  std::vector<FixedModifierEntry> entries;
  std::string unavailable_reason="site_type_fixed_pc_not_read";
};
struct AggregateModifierValue {
  std::uint16_t key_raw_u16=0;
  bool available=false;
  std::optional<std::int64_t> aggregate_raw_q64;
  std::string unavailable_reason="character_aggregate_key_not_read";
  bool operator==(const AggregateModifierValue &)const=default;
};
struct ModifierRecipient {
  std::uint32_t character_id=0xFFFFFFFFU;
  bool source_player=false,source_county_holder=false;
  std::optional<std::uint32_t> rite_id,faith_id;
  bool available=false,owned_aggregate_observed=false;
  std::vector<AggregateModifierValue> values;
  std::string unavailable_reason="character_aggregate_not_read";
  bool operator==(const ModifierRecipient &)const=default;
};
struct ModifierAggregateObservation {
  bool available=false,complete=false,source_arrays_stable=false;
  std::uint64_t capture_epoch=0;
  std::int32_t date_raw=0,played_character_id=-1;
  std::uint32_t holy_site_id=0xFFFFFFFFU;
  std::optional<std::uint32_t> county_holder_character_id;
  std::vector<FixedModifierBlock> definition_blocks;
  std::vector<ModifierRecipient> recipients;
  static constexpr std::uint32_t max_definition_entries_per_block=32,max_unique_keys=64,max_recipients=2;
  std::string unavailable_reason="site_type_modifier_aggregate_not_read";
};
// Pure guarded copies. Keys come only from this site's actual Type fixed PCs;
// recipients are only current player and this site's resolved county holder.
// No key-name guess, native getter/rebuild, default aggregate or attribution.
bool ReadHolySiteModifierAggregate12004(const Bindings &,
    const ck3_12002::religion::Context &,std::uint32_t holy_site_id,
    ModifierAggregateObservation &) noexcept;
std::string SerializeHolySiteModifierAggregate12004(const ModifierAggregateObservation &);
}
