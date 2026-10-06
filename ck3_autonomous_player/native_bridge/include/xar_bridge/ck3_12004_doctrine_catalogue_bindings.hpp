#pragma once

#include "xar_bridge/religion_doctrine12002_catalogue.hpp"

namespace xar::ck3_12004::religion::doctrine_catalogue {

// These aliases retain the owned software DTO and reader contract. The image
// factory below supplies only actual .4 Core addresses and the proved DB slot.
using CatalogueBindings = ck3_12002::religion::doctrine12002::CatalogueBindings;
using DoctrineCatalogue = ck3_12002::religion::doctrine12002::DoctrineCatalogue;

CatalogueBindings BindDoctrineCatalogueImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;
bool ReadPlayedDoctrineCatalogue12004(const CatalogueBindings &bindings,
    std::uint64_t capture_epoch, DoctrineCatalogue &out) noexcept;

} // namespace xar::ck3_12004::religion::doctrine_catalogue
