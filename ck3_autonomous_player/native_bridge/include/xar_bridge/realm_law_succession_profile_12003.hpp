#pragma once

#include "xar_bridge/ck3_12003.hpp"
#include "xar_bridge/ck3_12002_realm_law_active_collection.hpp"
#include "xar_bridge/ck3_12002_realm_law_components.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <string>
#include <string_view>

namespace xar::ck3_12003::private_law {

inline constexpr std::size_t kRealmLawSuccessionPolicyBytes12003 = 0x68;
inline constexpr std::size_t kRealmLawCreatePrimaryTierTitlesOffset12003 = 6;
inline constexpr std::int64_t kRealmLawSuccessionShareScale12003 = 100'000;

enum class RealmLawSuccessionProfile12003Status : std::uint8_t {
  unavailable,
  absent,
  available,
};

// Only copied values leave the existing paused candidate observer. The shape
// mapping remains the reviewed .2 mapping, whose exact .3 equivalence is frozen.
struct RealmLawSuccessionProfile12003 {
  RealmLawSuccessionProfile12003Status status =
      RealmLawSuccessionProfile12003Status::unavailable;
  bridge::RealmLawGovernanceSuccessionShapeV1 shape{};
  bool create_primary_tier_titles = false;
};

// No native call is added. Copy the same CLaw policy while its lifetime is
// already held by the candidate observer, then reuse the existing shape reader.
// Token 0x336f -> policy +6 -> native bool parser is exact-.3 confirmed; its
// registry name was closed by the root-owned 59-byte metadata receipt.
inline RealmLawSuccessionProfile12003 ReadRealmLawSuccessionProfile12003(
    const ck3_12002::private_law::RealmLawActiveCollectionAccess &access,
    std::uintptr_t native_law,
    std::string_view actual_executable_sha256) noexcept {
  RealmLawSuccessionProfile12003 output{};
  if (actual_executable_sha256 != ck3_12003::kExecutableSha256 ||
      native_law == 0 || access.read_memory == nullptr) return output;

  constexpr auto policy_offset =
      ck3_12002::private_law::kRealmLawSuccessionPolicyOffset;
  std::array<std::byte, policy_offset + kRealmLawSuccessionPolicyBytes12003>
      copied_law{};
  auto *copied_policy = copied_law.data() + policy_offset;
  if (!access.read_memory(access.context, native_law + policy_offset,
                          copied_policy, kRealmLawSuccessionPolicyBytes12003) ||
      !ck3_12002::private_law::ReadRealmLawSuccessionShape12002(
          copied_law.data(), output.shape)) return output;

  output.create_primary_tier_titles =
      std::to_integer<std::uint8_t>(copied_policy[
          kRealmLawCreatePrimaryTierTitlesOffset12003]) != 0;
  output.status =
      output.shape.presence == bridge::RealmLawGovernancePresenceV1::absent &&
              !output.create_primary_tier_titles
          ? RealmLawSuccessionProfile12003Status::absent
          : RealmLawSuccessionProfile12003Status::available;
  return output;
}

namespace detail_realm_law_succession_profile_12003 {
inline void AppendKey(std::string &out,
                      const bridge::RealmLawGovernanceKeyV1 &key) {
  if (key.size == 0) { out += "null"; return; }
  // Every key is copied from the existing canonical selector mapping.
  out += '"'; out.append(key.bytes.data(), key.size); out += '"';
}
inline void AppendOptionalKey(
    std::string &out, const bridge::RealmLawGovernanceOptionalKeyV1 &key) {
  if (key.presence == bridge::RealmLawGovernancePresenceV1::present)
    AppendKey(out, key.value);
  else
    out += "null";
}
} // namespace detail_realm_law_succession_profile_12003

// Appends the two candidate fields only; the existing serializer decides which
// exact-build group receives them. Existing final legality, reasons and costs
// retain their meanings even when this additional profile is unavailable.
inline void AppendRealmLawSuccessionProfileFields12003(
    std::string &out, const RealmLawSuccessionProfile12003 &profile) {
  using Status = RealmLawSuccessionProfile12003Status;
  out += ",\"succession_profile_status\":\"";
  switch (profile.status) {
  case Status::available: out += "available"; break;
  case Status::absent: out += "absent"; break;
  default: out += "unavailable"; break;
  }
  out += "\",\"succession_profile\":";
  if (profile.status != Status::available) { out += "null"; return; }

  using namespace detail_realm_law_succession_profile_12003;
  out += "{\"order\":";
  AppendKey(out, profile.shape.order_of_succession);
  out += ",\"traversal\":";
  AppendOptionalKey(out, profile.shape.traversal_order);
  out += ",\"rank\":";
  AppendOptionalKey(out, profile.shape.rank);
  out += ",\"division\":";
  AppendOptionalKey(out, profile.shape.title_division);
  out += ",\"primary_heir_minimum_share_raw\":";
  out += std::to_string(profile.shape.primary_heir_minimum_share.value_raw);
  out += ",\"primary_heir_minimum_share_scale\":";
  out += std::to_string(kRealmLawSuccessionShareScale12003);
  out += ",\"create_primary_tier_titles\":";
  out += profile.create_primary_tier_titles ? "true" : "false";
  out += '}';
}

} // namespace xar::ck3_12003::private_law
