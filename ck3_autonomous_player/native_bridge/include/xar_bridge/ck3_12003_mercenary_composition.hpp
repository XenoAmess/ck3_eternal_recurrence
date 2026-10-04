#pragma once

#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace xar::ck3_12003::mercenary {

inline constexpr std::string_view kCompositionExecutableSha256 =
    "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6";

using CompanyHolder = void *(*)(void *company);
struct CompositionBindings {
  bool enabled = false;
  void **persistent_regiment_storage_slot = nullptr;
  void **persistent_regiment_fallback_slot = nullptr;
  CompanyHolder company_holder = nullptr;
};

struct CompanyRegimentComposition {
  std::uint32_t ordinal = 0;
  std::uint32_t persistent_regiment_id = UINT32_MAX;
  std::string type_status = "not_maa";
  std::optional<std::string> maa_type_key;
  std::optional<std::int32_t> siege_tier_raw;
  std::int32_t current_soldiers = 0;
  std::int32_t maximum_soldiers = 0;
};

struct CompanyComposition {
  bool available = false;
  std::string unavailable_reason = "not_sampled";
  std::uint32_t company_id = UINT32_MAX;
  bool holder_available = false;
  std::string holder_unavailable_reason = "not_sampled";
  std::optional<std::uint32_t> holder_character_id;
  std::optional<std::uint32_t> regiment_count;
  std::uint32_t covered_regiment_count = 0;
  std::optional<std::int64_t> current_regiment_soldiers;
  std::optional<std::int64_t> maximum_regiment_soldiers;
  // Inventory maximum initialized to0. This is not the actual province K.
  std::optional<std::int32_t> maximum_siege_tier_raw;
  std::optional<std::int64_t> positive_siege_tier_current_soldiers;
  std::vector<CompanyRegimentComposition> regiments;
};

CompositionBindings BindMercenaryCompositionImage12003(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;

// Owner-thread paused-frame read of copied company inventory only. Regi is the
// persistent object: type+118; +18 is its chunk array, not an ArRg type pointer.
bool ReadMercenaryComposition12003(const CompositionBindings &, void *company,
    std::uint32_t expected_company_id, CompanyComposition &) noexcept;

std::string SerializeMercenaryComposition12003(const CompanyComposition &);

} // namespace xar::ck3_12003::mercenary
