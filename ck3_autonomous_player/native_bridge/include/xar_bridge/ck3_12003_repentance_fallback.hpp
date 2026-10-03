#pragma once

#include "xar_bridge/ck3_12003.hpp"

#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace xar::ck3_12003::religion::repentance_fallback {
inline constexpr std::string_view kSchema = "ck3_12003_repentance_fallback_sources_v1";
inline constexpr std::string_view kRealmSource = "realm_vassal_or_below";
inline constexpr std::string_view kDejureSource = "primary_title_dejure_clerical_region_holder";

struct alignas(8) Scope16 { std::uint32_t kind = 0, padding = 0; std::uint64_t id = 0; };
static_assert(sizeof(Scope16) == 16);
using ObjectGetter = void *(*)(void *);
using ClericalRegion = Scope16 *(*)(void *, Scope16 *, const Scope16 **);
using ReadMemory = bool (*)(void *, const void *, void *, std::size_t) noexcept;

struct Bindings {
  bool enabled = false;
  void **character_storage_slot = nullptr, **contract_storage_slot = nullptr;
  void **title_storage_slot = nullptr;
  ObjectGetter primary_title = nullptr;
  ClericalRegion clerical_region = nullptr;
  void *read_context = nullptr;
  ReadMemory read_memory = nullptr;
};
struct Row {
  std::int32_t character_id = -1;
  std::optional<std::int32_t> origin_title_id;
};
struct Collection {
  std::string source;
  bool available = false, traversal_complete = false;
  std::string reason = "bindings_unavailable";
  std::size_t visited_nodes = 0;
  std::vector<Row> rows;
};
struct Candidate {
  std::int32_t character_id = -1;
  std::vector<std::string> sources;
  std::vector<std::int32_t> origin_title_ids;
};
struct Context {
  bool available = false, complete_source_traversal = false;
  std::string unavailable_reason = "bindings_unavailable";
  std::uint64_t capture_epoch = 0;
  std::int32_t date_raw = 0, played_character_id = -1;
  std::optional<std::int32_t> primary_title_id;
  Collection realm_vassals, dejure_clerical_holders;
  std::vector<Candidate> candidates;
};

Bindings BindRepentanceFallbackImage12003(std::uintptr_t module_base,
    std::string_view executable_sha256) noexcept;
// Caller supplies the current application-main paused owner/frame. This leaf
// observes actual unfiltered realm/de-jure role sources only. It never runs the
// stock effect, selects the preferred cleric, or previews/submits an interaction.
bool ReadRepentanceFallback12003(const Bindings &, void *played_character,
    std::int32_t played_character_id, std::int32_t date_raw,
    std::uint64_t capture_epoch, Context &) noexcept;
std::string SerializeRepentanceFallback12003(const Context &);
} // namespace xar::ck3_12003::religion::repentance_fallback
