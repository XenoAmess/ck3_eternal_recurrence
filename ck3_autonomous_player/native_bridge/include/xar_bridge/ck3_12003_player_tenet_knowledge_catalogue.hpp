#pragma once

#include "xar_bridge/ck3_12002_religion_context.hpp"
#include "xar_bridge/religion_reform12002_tenet_sources.hpp"

#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace xar::ck3_12003::religion::tenet_knowledge {

inline constexpr char kSchema[] = "ck3_12003_player_tenet_knowledge_catalogue_v1";

// Supplied by the existing reviewed image factory. This leaf has no binder.
struct Bindings {
  ck3_12002::religion::Bindings context{};
  void *const *tenet_database_global{};
  void *const *perk_database_global{};
  ck3_12002::religion_reform::TenetSourcesCollection actor_extra_collection{};
  ck3_12002::religion_reform::TenetSourcesCollection actor_perks_collection{};
  ck3_12002::religion_reform::TenetSourcesContains contains{};
};

enum class Failure {
  none,
  bindings_unavailable,
  played_character_unavailable,
  frame_not_paused,
  tenet_database_unavailable,
  tenet_definition_collection_unavailable,
  tenet_definition_key_unavailable,
  actor_extra_collection_unavailable,
  extra_tenet_definition_key_unavailable,
  prophet_definition_unavailable,
  actor_perks_collection_unavailable,
  state_changed,
  knowledge_native_read_unavailable,
};

enum class ExtraCollectionSource {
  character_extension_c8,
  native_default_collection,
};

struct Row {
  std::uint32_t source_index{};
  std::string tenet_key;
  bool native_extra_knowledge{};
  bool knowledge{};
  bool operator==(const Row &) const = default;
};

struct Catalogue {
  bool available{};
  Failure failure{Failure::bindings_unavailable};
  std::uint64_t capture_epoch{};
  std::int32_t date_raw{};
  std::uint32_t played_character_id{0xFFFFFFFFU};
  std::optional<bool> has_character_extension;
  std::optional<ExtraCollectionSource> extra_collection_source;
  bool extra_collection_complete{};
  std::optional<std::vector<std::string>> extra_tenet_keys;
  bool loaded_registry_complete{};
  std::optional<std::uint32_t> loaded_definition_count;
  std::optional<bool> native_has_prophet;
  bool knowledge_inputs_complete{};
  std::optional<std::vector<Row>> rows;
};

// Actual played character in a paused application-main frame. This reports
// knowledge inputs, independently of Rite status and draft final legality.
bool ReadPlayedTenetKnowledgeCatalogue12003(const Bindings &bindings,
    std::uint64_t capture_epoch, Catalogue &output) noexcept;
std::string SerializePlayedTenetKnowledgeCatalogue12003(const Catalogue &value);
const char *TenetKnowledgeCatalogueFailureKey(Failure failure) noexcept;

} // namespace xar::ck3_12003::religion::tenet_knowledge
