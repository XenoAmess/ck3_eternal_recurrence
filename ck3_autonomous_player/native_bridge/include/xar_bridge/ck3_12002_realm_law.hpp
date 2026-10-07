#pragma once

#include "xar_bridge/ck3_12002.hpp"
#include "xar_bridge/crown_authority_cooldown_observer_12004.hpp"
#include "xar_bridge/ck3_12002_realm_law_candidate_collection.hpp"
#include "xar_bridge/ck3_12002_realm_law_final_terms.hpp"
#include "xar_bridge/realm_law_succession_profile_12003.hpp"
#include "xar_bridge/ck3_12002_query_mailbox.hpp"

#include <array>
#include <cstdint>
#include <string>

namespace xar::ck3_12002 {

inline constexpr std::string_view kRealmLawPausedPrivateQueryStep12002 =
    "query-realm-law-final-terms-v1-private";

struct RealmLawReadbackFrame12002 {
  std::uint64_t snapshot_revision = 0;
  std::int64_t date_raw = 0;
  std::int32_t actor_character_id = -1;
};

struct RealmLawReadback12002 {
  RealmLawReadbackFrame12002 frame{};
  private_law::RealmLawCandidateCollection11906 collection{};
  std::array<std::array<private_law::RealmLawFinalTerms12002Result,
      ck3_11906::private_law::kRealmLawMaximumRelevantCandidates11906>, 2> final{};
  // The copied profile DTO is shared by exact .3 and mapped .4 readers.
  bool succession_profiles_12003_observed = false;
  std::array<ck3_12003::private_law::RealmLawSuccessionProfile12003,
      ck3_11906::private_law::kRealmLawMaximumRelevantCandidates11906>
      succession_profiles_12003{};
  bool crown_authority_cooldown_observed = false;
  ck3_12004::crown_cooldown::Observation crown_authority_cooldown{};
  bool available = false;
  std::string failure{};
};

// The normal query keeps native image bindings and null overrides. Whole
// fixtures can supply their copied memory/access/operations while exercising
// this same executor, frame envelope, domain capture and serializer.
struct RealmLawReadbackQuery12002 {
  QueryMailboxEnvelope envelope{};
  CoreBindings bindings{};
  std::uintptr_t module_base = 0;
  std::string_view actual_executable_sha256{};
  RealmLawReadback12002 readback{};
  const private_law::RealmLawActiveCollectionAccess *collection_access_override = nullptr;
  const private_law::RealmLawFinalTerms12002Operations *final_operations_override = nullptr;
  const ck3_12004::crown_cooldown::Bindings *cooldown_bindings_override = nullptr;
};

// Actual collection and final native calls share the same caller-owned frame.
// Returned data contains stable keys and copied values, never engine pointers.
bool CaptureRealmLawReadback12002(
    const private_law::RealmLawActiveCollectionAccess &access,
    std::uintptr_t module_base, const RealmLawReadbackFrame12002 &frame,
    const private_law::RealmLawFinalTerms12002Operations &operations,
    RealmLawReadback12002 &output,
    std::string_view actual_executable_sha256 = {},
    const ck3_12004::crown_cooldown::Bindings *cooldown_bindings_override = nullptr) noexcept;
std::string SerializeRealmLawReadback12002(const RealmLawReadback12002 &readback);
// Same command-result wrapper used by the registered production law route.
std::string SerializeRealmLawReadbackCommandResult12002(
    std::string_view request_id, std::string_view native_readback,
    std::uint64_t revision);

bool ExecuteRealmLawPausedPrivateQuery12002(
    void *opaque, const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept;

bool ReadRealmLawOnApplicationMain12002(
    const game::GameAdapter &adapter,
    ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const game::Snapshot &published, std::uint64_t revision,
    std::string &serialized, std::string &failure) noexcept;

} // namespace xar::ck3_12002
