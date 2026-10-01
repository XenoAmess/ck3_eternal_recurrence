#pragma once

#include "xar_bridge/religion_doctrine12002_intrinsic.hpp"

namespace xar::ck3_12002::religion::doctrine12002 {

inline constexpr std::uintptr_t kCharacterKnowsDoctrineRva = 0x28B0C00;
inline constexpr std::size_t kCharacterKnowledgeExtensionOffset = 0x1C8;
inline constexpr std::size_t kLearnedDoctrineArrayOffset = 0xE0;
inline constexpr std::size_t kLearnedDoctrineCountOffset = 0xEC;
inline constexpr std::size_t kDefinitionRegistryArrayOffset = 0x50;
inline constexpr std::size_t kDefinitionRegistryCountOffset = 0x5C;

using NativeKnowsDoctrine = bool (*)(void *, const void *);

struct KnowledgeBindings {
  religion::Bindings context{};
  NativeKnowsDoctrine knows_doctrine = nullptr;
  // Reads an already initialized registry. The native database getter can
  // initialize the registry when its global is null, so it is not invoked.
  void *const *definition_database_global = nullptr;
};

struct KnownDoctrineRow {
  DoctrineRow definition{};
  bool native_knows_doctrine = false;
  bool operator==(const KnownDoctrineRow &) const = default;
};

struct PlayedDoctrineKnowledge {
  bool available = false;
  std::string unavailable_reason = "bindings_unavailable";
  std::uint64_t capture_epoch = 0;
  std::int32_t date_raw = 0;
  std::int32_t played_character_id = -1;
  std::optional<std::uint32_t> rite_id;
  std::string knowledge_source;
  std::vector<KnownDoctrineRow> learned_rows;
};

struct PlayedDoctrineKnowledgeLookup {
  bool available = false;
  std::string unavailable_reason = "bindings_unavailable";
  std::uint64_t capture_epoch = 0;
  std::int32_t date_raw = 0;
  std::int32_t played_character_id = -1;
  std::string requested_doctrine_key;
  std::optional<DoctrineRow> definition;
  std::optional<bool> native_knows_doctrine;
};

KnowledgeBindings BindDoctrineKnowledgeImage12002(std::uintptr_t module_base,
    std::string_view executable_sha256) noexcept;
// Existing paused owner only, subject is the actual played Character.
// Knowledge is one input to the UI gate; these are not future choices or
// CanPick/Prophet-perk/final creation/reform legality results.
bool ReadPlayedDoctrineKnowledge12002(const KnowledgeBindings &bindings,
    std::uint64_t capture_epoch, PlayedDoctrineKnowledge &output) noexcept;
bool ReadPlayedDoctrineKnowledgeByKey12002(const KnowledgeBindings &bindings,
    std::string_view doctrine_key, std::uint64_t capture_epoch,
    PlayedDoctrineKnowledgeLookup &output) noexcept;
std::string SerializePlayedDoctrineKnowledge12002(const PlayedDoctrineKnowledge &value);
std::string SerializePlayedDoctrineKnowledgeLookup12002(const PlayedDoctrineKnowledgeLookup &value);

} // namespace xar::ck3_12002::religion::doctrine12002
