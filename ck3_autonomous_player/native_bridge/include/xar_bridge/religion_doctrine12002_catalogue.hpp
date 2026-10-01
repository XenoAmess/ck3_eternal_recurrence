#pragma once

#include "xar_bridge/religion_doctrine12002_intrinsic.hpp"

namespace xar::ck3_12002::religion::doctrine12002 {

struct CatalogueBindings {
  bool enabled = false;
  CoreBindings core{};
  // Pointer to the already loaded native global. The lazy DB getter is never called.
  void **database_slot = nullptr;
};

struct DoctrineCatalogue {
  bool available = false;
  bool catalogue_complete = false;
  std::string unavailable_reason = "bindings_unavailable";
  std::uint64_t capture_epoch = 0;
  std::int32_t date_raw = 0;
  std::int32_t played_character_id = -1;
  std::string source = "loaded_doctrine_registry";
  std::vector<DoctrineRow> rows;
};

CatalogueBindings BindDoctrineCatalogueImage12002(std::uintptr_t module_base,
    std::string_view executable_sha256) noexcept;
bool ReadPlayedDoctrineCatalogue12002(const CatalogueBindings &bindings,
    std::uint64_t capture_epoch, DoctrineCatalogue &output) noexcept;
std::string SerializeDoctrineCatalogue12002(const DoctrineCatalogue &value);

// Internal exact-key lookup for current/selection queries. A successful complete
// lookup with no matching key returns true and definition=nullptr. The pointer
// never belongs in the wire DTO; it identifies a loaded native static definition.
bool ResolveDoctrineDefinitionByStableKey12002(const CatalogueBindings &bindings,
    std::string_view key, const void *&definition, std::string &failure) noexcept;

} // namespace xar::ck3_12002::religion::doctrine12002
