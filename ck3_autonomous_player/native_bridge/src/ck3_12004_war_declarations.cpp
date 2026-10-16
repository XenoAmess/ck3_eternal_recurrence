#include "xar_bridge/ck3_12004_war_declarations.hpp"

#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/ck3_12004_holy_war.hpp"
#include "xar_bridge/ck3_12004_declaration_candidates.hpp"

#include <array>
#include <cstdlib>
#include <cstring>

#if defined(_MSC_VER)
#include <windows.h>
#endif

namespace xar::ck3_12004 {
namespace {
template <class T> T CandidateField(const void *object, std::size_t offset) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset, sizeof(value));
  return value;
}

// Current118B 28BFC50 SHA7f713bce578456413e82347434024b5a390a28bd40d17a4779f6eb3c4c7f6da4.
// The original getter covers both ruler lieges and landless court owners. Only
// a valid other character is evidence against being an independent ruler.
// Null/self/fallback/unreadable facts stay unknown and cannot exclude anyone.
bool ReadCandidateFacts12004(std::uintptr_t base, void *character,
                            ck3_12002::DeclarationsCandidateFactsV1 &out) noexcept {
  out = {};
  if (!base || !character) return false;
#if defined(_MSC_VER)
  __try {
#endif
    using Getter = void *(*)(void *);
    auto *liege = reinterpret_cast<Getter>(base + 0x28BFC50)(character);
    auto *fallback = *reinterpret_cast<void **>(base + 0x5C67570);
    if (!liege || liege == fallback || liege == character) return true;
    auto *storage = *reinterpret_cast<void **>(base + kCharacterStorageSlotRva);
    if (!storage) return true;
    const auto id = CandidateField<std::int32_t>(liege, 0x18);
    const auto index = static_cast<std::uint32_t>(id) & 0xFFFFFFU;
    const auto count = CandidateField<std::int32_t>(storage, 0x2C);
    const auto *slots = CandidateField<const std::byte *>(storage, 0x20);
    if (!slots || count <= 0 || count > 1'000'000 ||
        index >= static_cast<std::uint32_t>(count) ||
        CandidateField<void *>(slots, index * 0x10ULL + 8) != liege) return true;
    out.independent = ck3_12002::DeclarationsCandidateFactV1::no;
    // No guessed primary-title/is_landed equivalence. Landed stays unknown
    // until its original predicate or a stronger necessary chain is qualified.
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { out = {}; return false; }
#endif
}

bool CandidateBytes(const void *source, void *destination, std::size_t size) noexcept {
  if (size == 0) return true;
  if (!source || !destination) return false;
#if defined(_MSC_VER)
  __try {
#endif
    std::memcpy(destination, source, size);
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
}

// Stock31EFBC0 modes1..4 ->31EF2F0 requires defender pointer membership
// in this exact union before generating any target title. This is the actor's
// realm cache at+1C8, not the AI context at+1B0/+278 or strategy+A8.
bool ReadCandidateRealm12004(std::uintptr_t, void *actor,
                            std::vector<void *> &out) noexcept {
  return ReadDeclarationRealmCandidates12004(actor, &CandidateBytes, out);
}

// Source AST inventory ROOT-CB-HARD-DEFENDER-CONDITIONS.json. Runtime admission
// additionally proves that the prepared playset/DLC sources do not override
// these definitions; a matching EXE or this inventory hash alone is not proof.
constexpr std::string_view kCandidateRuleInventorySha256 =
    "b7cf0d40a5b049c3e9a1187244276edcccb5e31eab0fddfbffcdd8579d492b27";
using Rule = ck3_12002::DeclarationsCandidateRuleV1;
constexpr std::array<Rule, 15> kCandidateRules{{
    {"make_tributary_cb", "087d6151be86546d4b1fcb600230534cb14c6a57ec2762e4efdb3ae98f9227c9", 3},
    {"fp3_install_loyalist_cb", "deb77511b6835aae514fa15c3f4037bad5029092c02052400e5a5e044adac1e0", 1},
    {"fp3_seljuk_invasion_cb", "deb77511b6835aae514fa15c3f4037bad5029092c02052400e5a5e044adac1e0", 1},
    {"ep3_roman_empire_border_war", "ec5f8d964b2a5c76db9a96f12b0d81521246648c963437af62151e3bc4a18027", 1},
    {"humiliation_cb", "39a1bf3466a767c9a71d4d8a019def5fa3a80e0da0ca29b7a31b07d8831f85bd", 1},
    {"sovereignty_cb", "39a1bf3466a767c9a71d4d8a019def5fa3a80e0da0ca29b7a31b07d8831f85bd", 1},
    {"mpo_great_war_of_defiance_cb", "39a1bf3466a767c9a71d4d8a019def5fa3a80e0da0ca29b7a31b07d8831f85bd", 1},
    {"japan_install_bloc_member_cb", "c4f77b37d01d5dfd5cf59312a125b1f4937a30b4f765937c08ad73237dba5f16", 1},
    {"japan_soryo_conquest_county_landless_cb", "c4f77b37d01d5dfd5cf59312a125b1f4937a30b4f765937c08ad73237dba5f16", 1},
    {"japan_demand_administrative_cb", "c4f77b37d01d5dfd5cf59312a125b1f4937a30b4f765937c08ad73237dba5f16", 1},
    {"eradicate_house_cb", "c4f77b37d01d5dfd5cf59312a125b1f4937a30b4f765937c08ad73237dba5f16", 1},
    {"pam_humiliation_cb", "69aed3b778c12d4a7ba8cf6c18a9a9accef84fae619021f83478f4ca14f9d23b", 1},
    {"pam_challenge_hof_cb", "69aed3b778c12d4a7ba8cf6c18a9a9accef84fae619021f83478f4ca14f9d23b", 1},
    {"pam_investiture_conflict_cb", "69aed3b778c12d4a7ba8cf6c18a9a9accef84fae619021f83478f4ca14f9d23b", 1},
    {"mandala_raze_capital_structure_cb", "e172a89deb2dc4606f782195155f5ce49da8e660a2c03cd1301603d65f5d7ab4", 1},
}};

void BindCandidateVariant12004(ck3_12002::DeclarationsBindings &bindings,
                               std::uintptr_t base) noexcept {
#if defined(_MSC_VER)
#pragma warning(push)
#pragma warning(disable : 4996)
#endif
  const auto *variant = std::getenv("XAR_CK3_DECLARATIONS_CANDIDATE_VARIANT");
  const auto *rules = std::getenv("XAR_CK3_DECLARATIONS_CANDIDATE_RULES_SHA256");
  const auto *sources = std::getenv("XAR_CK3_DECLARATIONS_CANDIDATE_SOURCE_MANIFEST_SHA256");
  const auto *policy = std::getenv("XAR_CK3_DECLARATIONS_CANDIDATE_POLICY_FILE");
#if defined(_MSC_VER)
#pragma warning(pop)
#endif
  using Variant = ck3_12002::DeclarationsCandidateVariantV1;
  if (variant && std::string_view(variant) == "shadow-v1") bindings.candidate_options.variant = Variant::shadow;
  else if (variant && std::string_view(variant) == "cb-first-v1") bindings.candidate_options.variant = Variant::cb_first;
  else if (!policy || !*policy) return;
  bindings.candidate_provider_image_base = base;
  bindings.read_candidate_facts = &ReadCandidateFacts12004;
  bindings.read_candidate_realm = &ReadCandidateRealm12004;
  bindings.candidate_target_titles_mode_offset = 0x6C8;
  if (policy) bindings.candidate_options.runtime_policy_path = policy;
  if (rules && std::string_view(rules) == kCandidateRuleInventorySha256 && sources) {
    bindings.candidate_options.qualified_rules = kCandidateRules;
    bindings.candidate_options.qualified_source_manifest_sha256 = sources;
  }
}
} // namespace

ck3_12002::DeclarationsBindings BindDeclarationsImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256,
    const ck3_12002::CommandBindings &actual_commands) noexcept {
  if (image_base == 0 || executable_sha256 != kExecutableSha256) return {};
  auto bindings = BindOrdinaryHolyWarDeclarationsImage12004(
      image_base, executable_sha256);
  if (!bindings.enabled) return bindings;
  bindings.commands = actual_commands;
  // diplomacy-map/first01/construct_send_interaction_command-DETAIL.json:
  // full 164 B match and actual RIP-selected primary/secondary native tables.
  bindings.construct_send =
      reinterpret_cast<ck3_12002::DeclarationsConstructSend>(
          image_base + 0x2968150);
  bindings.send_primary_vtable = image_base + 0x448BCF0;
  bindings.send_secondary_vtable = image_base + 0x448BCC0;
  BindCandidateVariant12004(bindings, image_base);
  return bindings;
}

} // namespace xar::ck3_12004
