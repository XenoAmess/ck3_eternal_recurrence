#include "xar_bridge/ck3_12002_nonwar_mailbox.hpp"

#include <array>
#include <cassert>
#include <cstring>
#include <iostream>
#include <vector>

namespace {
using namespace xar::ck3_11906;

struct Result {
  int executor = 0;
  std::size_t calls = 0;
  MainThreadExecutionStampV1 stamp{};
};

template <int N>
bool Executor(void *opaque, const MainThreadExecutionStampV1 &stamp) noexcept {
  auto &result = *static_cast<Result *>(opaque);
  result.executor = N;
  ++result.calls;
  result.stamp = stamp;
  return true;
}

struct Slot {
  MainThreadQueryExecutorV1 callback = nullptr;
  int identity = 0;
};

void Check(MainThreadQueryExecutorV1 registered,
           MainThreadQueryExecutorV1 callback, bool enabled, int identity,
           std::vector<Slot> &selected) {
  assert(registered == (enabled ? callback : nullptr));
  if (registered != nullptr) { selected.push_back({registered, identity}); }
}

BOOL WINAPI PeekFixture(LPMSG, HWND, UINT, UINT, UINT) { return FALSE; }
struct Protection {
  void **slot = nullptr;
  DWORD protection = PAGE_READONLY;
};

bool QueryFixture(void *opaque, const void *address,
                  MEMORY_BASIC_INFORMATION &information) noexcept {
  auto &protection = *static_cast<Protection *>(opaque);
  if (address != protection.slot) { return false; }
  const auto page = reinterpret_cast<std::uintptr_t>(address) & ~std::uintptr_t{4095};
  information = {};
  information.BaseAddress = reinterpret_cast<void *>(page);
  information.AllocationBase = information.BaseAddress;
  information.AllocationProtect = PAGE_READONLY;
  information.RegionSize = 4096;
  information.State = MEM_COMMIT;
  information.Protect = protection.protection;
  information.Type = MEM_IMAGE;
  return true;
}

bool ProtectFixture(void *opaque, void *, std::size_t size, DWORD protection,
                    DWORD &old) noexcept {
  if (size != 4096) { return false; }
  auto &memory = *static_cast<Protection *>(opaque);
  old = memory.protection;
  memory.protection = protection;
  return true;
}

std::array<std::byte, 0x28> tls{};
void *__fastcall TlsFixture() noexcept { return tls.data(); }

void ExerciseMailbox(MainThreadQueryInstallEnvironmentV1 environment,
                     const std::vector<Slot> &selected) {
  const auto thread = GetCurrentThreadId();
  std::array<std::byte, 0x18> rng{};
  std::memcpy(rng.data() + 0x10, &thread, sizeof(thread));
  auto rng_pointer = reinterpret_cast<std::uintptr_t>(rng.data());
  auto rng_wrapper = reinterpret_cast<std::uintptr_t>(&rng_pointer);
  std::array<std::byte, 0x28> jomini{};
  jomini[0x20] = std::byte{1};
  auto jomini_pointer = reinterpret_cast<std::uintptr_t>(jomini.data());
  std::array<std::byte, 0x18> game{};
  constexpr std::int32_t date = 53169072;
  std::memcpy(game.data() + 0x08, &date, sizeof(date));
  auto game_pointer = reinterpret_cast<std::uintptr_t>(game.data());
  std::uint8_t initialized = 1;
  tls[0x20] = std::byte{1};
  void *iat = reinterpret_cast<void *>(&PeekFixture);
  Protection protection{&iat};
  environment.offline_fixture = true;
  environment.peek_message_iat_slot_override = &iat;
  environment.resolved_peek_message_override = &PeekFixture;
  environment.global_rng_wrapper_slot_override = reinterpret_cast<std::uintptr_t>(&rng_wrapper);
  environment.jomini_state_slot_override = reinterpret_cast<std::uintptr_t>(&jomini_pointer);
  environment.game_state_slot_override = reinterpret_cast<std::uintptr_t>(&game_pointer);
  environment.tls_initialized_flag_override = reinterpret_cast<std::uintptr_t>(&initialized);
  environment.tls_context_getter_override = &TlsFixture;
  environment.memory_protection_context = &protection;
  environment.memory_query_override = &QueryFixture;
  environment.memory_protect_override = &ProtectFixture;
  environment.system_page_size_override = 4096;
  MainThreadQueryMailboxV1 mailbox{};
  assert(InstallMainThreadQueryMailboxV1(mailbox, environment));
  assert(mailbox.permitted_executor_epidemic_treatment12002 ==
         environment.permitted_executor_epidemic_treatment12002);
  assert(mailbox.permitted_executor_epidemic_recovery12002 ==
         environment.permitted_executor_epidemic_recovery12002);
  assert(mailbox.permitted_executor_religion_conversion_reasons12002 ==
         environment.permitted_executor_religion_conversion_reasons12002);
  assert(mailbox.permitted_executor_sway_completion_execution12002 ==
         environment.permitted_executor_sway_completion_execution12002);
  assert(mailbox.permitted_executor_religion_reform12002 ==
         environment.permitted_executor_religion_reform12002);
  assert(mailbox.permitted_executor_religion_doctrine_catalogue12002 ==
         environment.permitted_executor_religion_doctrine_catalogue12002);
  assert(mailbox.permitted_executor_religion_conversion_outcome12002 ==
         environment.permitted_executor_religion_conversion_outcome12002);
  assert(mailbox.permitted_executor_religion_numeric_special_parameters12002 ==
         environment.permitted_executor_religion_numeric_special_parameters12002);
  assert(mailbox.permitted_executor_sway_completion_termination12002 ==
         environment.permitted_executor_sway_completion_termination12002);
  assert(mailbox.permitted_executor_religion_personal_parameters12002 ==
         environment.permitted_executor_religion_personal_parameters12002);
  assert(mailbox.permitted_executor_sway_completion_invalidation_reason12002 ==
         environment.permitted_executor_sway_completion_invalidation_reason12002);
  assert(mailbox.permitted_executor_religion_draft_groups12002 ==
         environment.permitted_executor_religion_draft_groups12002);
  assert(mailbox.permitted_executor_religion_draft_doctrine_choices12002 ==
         environment.permitted_executor_religion_draft_doctrine_choices12002);
  assert(mailbox.permitted_executor_religion_draft_tenet_choices12002 ==
         environment.permitted_executor_religion_draft_tenet_choices12002);
  assert(mailbox.permitted_executor_religion_draft_resource_costs12002 ==
         environment.permitted_executor_religion_draft_resource_costs12002);
  assert(iat == reinterpret_cast<void *>(&XarMainThreadPeekMessageWHookV1));
  const auto return_rva = environment.build_profile->pump_exact_return_rva;
  for (std::size_t i = 0; i < 3; ++i) {
    assert(!ObserveMainThreadPumpAndDrainV1(mailbox, return_rva, thread));
  }
  assert(ReadMainThreadQueryMailboxDiagnosticsV1(mailbox).ready);
  for (const auto &slot : selected) {
    Result result{};
    MainThreadQueryTicketV1 ticket{};
    // The production submit posts WM_NULL only to this fixture's own thread.
    assert(TrySubmitMainThreadQueryV1(mailbox, slot.callback, &result, ticket) ==
           MainThreadQuerySubmitResultV1::submitted);
    assert(ObserveMainThreadPumpAndDrainV1(mailbox, return_rva, thread));
    assert(WaitForMainThreadQueryV1(mailbox, ticket, 0) ==
           MainThreadQueryWaitResultV1::completed);
    assert(result.calls == 1 && result.executor == slot.identity);
    assert(result.stamp.thread_id == thread && result.stamp.paused);
    assert(result.stamp.date_raw == date);
    assert(ReclaimMainThreadQueryV1(mailbox, ticket) ==
           MainThreadQueryReclaimResultV1::reclaimed);
  }
  assert(UninstallMainThreadQueryMailboxV1(mailbox, 0) ==
         MainThreadQueryUninstallResultV1::uninstalled);
  assert(iat == reinterpret_cast<void *>(&PeekFixture));
}
} // namespace

int main() {
  using namespace xar::ck3_12002;
  std::array<MainThreadQueryExecutorV1, 14> typed{};
  typed.fill(&Executor<1>);
  typed.back() = &Executor<14>;
  auto environment = BindThreadRuntimeImage(0x100000, kExecutableSha256, typed);
  const auto *profile = environment.build_profile;
  assert(profile != nullptr && profile == &ThreadRuntimeBuildProfile());
  environment.permitted_executor_quattuordenary = &Executor<114>;
  environment.permitted_executor_quintrigintary = &Executor<135>;
  NonwarMailboxExecutorsV1 callbacks{};
  callbacks.lifestyle = &Executor<43>;
  callbacks.construction = &Executor<42>;
  callbacks.ranked_marriage = &Executor<38>;
  callbacks.alliance_projection = &Executor<48>;
  callbacks.relationship = &Executor<68>;
  callbacks.marriage_submit = &Executor<69>;
  callbacks.council_candidates = &Executor<33>;
  callbacks.council = &Executor<41>;
  callbacks.faction_gift = &Executor<34>;
  callbacks.sway_state = &Executor<55>;
  callbacks.sway_action = &Executor<58>;
  callbacks.law_final_terms = &Executor<56>;
  callbacks.law_action = &Executor<37>;
  callbacks.feast_open = &Executor<57>;
  callbacks.feast_options = &Executor<59>;
  callbacks.feast_can_start = &Executor<60>;
  callbacks.feast_gold = &Executor<61>;
  callbacks.feast_full_costs = &Executor<62>;
  callbacks.feast_destination = &Executor<63>;
  callbacks.feast_stage2_confirm = &Executor<1200236>;
  callbacks.feast_start = &Executor<64>;
  callbacks.feast_guest = &Executor<65>;
  callbacks.feast_guest_rules = &Executor<66>;
  callbacks.feast_guest_opinion = &Executor<67>;
  callbacks.factions = &Executor<1200231>;
  callbacks.warcash = &Executor<1200232>;
  callbacks.family_obligations = &Executor<1200233>;
  callbacks.prewar = &Executor<1200234>;
  callbacks.government = &Executor<1200235>;
  callbacks.religion = &Executor<1200237>;
  callbacks.prisoner_collection = &Executor<53>;
  callbacks.prisoner_ransom = &Executor<54>;
  callbacks.rite_governance = &Executor<1200238>;
  callbacks.clergy = &Executor<1200239>;
  callbacks.religion_conversion = &Executor<1200240>;
  callbacks.religion_doctrines = &Executor<1200241>;
  callbacks.rite_members = &Executor<1200242>;
  callbacks.religion_conversion_choices = &Executor<1200243>;
  callbacks.religion_conversion_inputs = &Executor<1200244>;
  callbacks.sway_completion = &Executor<1200245>;
  callbacks.religion_hostility = &Executor<1200246>;
  callbacks.religion_doctrine_knowledge = &Executor<1200247>;
  callbacks.religion_tenets = &Executor<1200248>;
  callbacks.epidemic_treatment = &Executor<1200249>;
  callbacks.epidemic_recovery = &Executor<1200250>;
  callbacks.religion_conversion_reasons = &Executor<1200251>;
  callbacks.sway_completion_execution = &Executor<1200252>;
  callbacks.religion_reform = &Executor<1200253>;
  callbacks.religion_doctrine_catalogue = &Executor<1200254>;
  callbacks.religion_conversion_outcome = &Executor<1200255>;
  callbacks.religion_numeric_special_parameters = &Executor<1200256>;
  callbacks.sway_completion_termination = &Executor<1200257>;
  callbacks.religion_personal_parameters = &Executor<1200258>;
  callbacks.sway_completion_invalidation_reason = &Executor<1200259>;
  callbacks.religion_draft_groups = &Executor<1200260>;
  callbacks.religion_draft_doctrine_choices = &Executor<1200261>;
  callbacks.religion_draft_tenet_choices = &Executor<1200262>;
  callbacks.religion_draft_resource_costs = &Executor<1200263>;
  RegisterNonwarMailboxExecutorsV1(environment, callbacks);
  assert(environment.build_profile == profile);
  assert(environment.permitted_executor == &Executor<1>);
  assert(environment.permitted_executor_quattuordenary == &Executor<114>);
  assert(environment.permitted_executor_quintrigintary == &Executor<135>);
  assert(environment.permitted_executor_semantic12002 == &Executor<14>);
  std::vector<Slot> selected{{&Executor<1>, 1}, {&Executor<114>, 114},
                             {&Executor<135>, 135}, {&Executor<14>, 14}};
#if defined(XAR_CK3_ENABLE_G2_PLAYER_LIFESTYLE_FORMAL_WIRE_PRIVATE_V1)
  Check(environment.permitted_executor_trioquadragintary, callbacks.lifestyle, true, 43, selected);
#else
  Check(environment.permitted_executor_trioquadragintary, callbacks.lifestyle, false, 43, selected);
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_CONSTRUCTION_VIEW_PROBE_PRIVATE_V1)
  Check(environment.permitted_executor_duoquadragintary, callbacks.construction, true, 42, selected);
#else
  Check(environment.permitted_executor_duoquadragintary, callbacks.construction, false, 42, selected);
#endif
#if defined(XAR_CK3_ENABLE_G2_M5_RANKED_MARRIAGE_PRIVATE_QUERY_V1)
  Check(environment.permitted_executor_octotrigintary, callbacks.ranked_marriage, true, 38, selected);
#else
  Check(environment.permitted_executor_octotrigintary, callbacks.ranked_marriage, false, 38, selected);
#endif
#if defined(XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1)
  Check(environment.permitted_executor_octoquadragintary, callbacks.alliance_projection, true, 48, selected);
#else
  Check(environment.permitted_executor_octoquadragintary, callbacks.alliance_projection, false, 48, selected);
#endif
#if defined(XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1)
  Check(environment.permitted_executor_octosexagintary, callbacks.relationship, true, 68, selected);
#else
  Check(environment.permitted_executor_octosexagintary, callbacks.relationship, false, 68, selected);
#endif
#if defined(XAR_CK3_ENABLE_G2_M5_HEIR_MARRIAGE_PRIVATE_ACTION_V1) && defined(XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1)
  Check(environment.permitted_executor_novemsexagintary, callbacks.marriage_submit, true, 69, selected);
#else
  Check(environment.permitted_executor_novemsexagintary, callbacks.marriage_submit, false, 69, selected);
#endif
#if defined(XAR_CK3_ENABLE_G2_COUNCIL_COMPOSITION_STEWARD_CANDIDATES_PRIVATE_PROBE_V1)
  Check(environment.permitted_executor_tritrigintary, callbacks.council_candidates, true, 33, selected);
#else
  Check(environment.permitted_executor_tritrigintary, callbacks.council_candidates, false, 33, selected);
#endif
#if defined(XAR_CK3_ENABLE_G2_COUNCIL_APPLICATION_MAIN_PRIVATE_ROUTE_V1)
  Check(environment.permitted_executor_unquadragintary, callbacks.council, true, 41, selected);
#else
  Check(environment.permitted_executor_unquadragintary, callbacks.council, false, 41, selected);
#endif
#if defined(XAR_CK3_ENABLE_G2_FACTION_GIFT_MITIGATION_ASYNC_PRIVATE_GLUE_V1)
  Check(environment.permitted_executor_quattuortrigintary, callbacks.faction_gift, true, 34, selected);
#else
  Check(environment.permitted_executor_quattuortrigintary, callbacks.faction_gift, false, 34, selected);
#endif
#if defined(XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_PRIVATE_CANDIDATE_V1)
  Check(environment.permitted_executor_quinquinquagintary, callbacks.sway_state, true, 55, selected);
#else
  Check(environment.permitted_executor_quinquinquagintary, callbacks.sway_state, false, 55, selected);
#endif
#if defined(XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_SWAY_FORMAL_PRIVATE_ACTION_V1)
  Check(environment.permitted_executor_octoquinquagintary, callbacks.sway_action, true, 58, selected);
#else
  Check(environment.permitted_executor_octoquinquagintary, callbacks.sway_action, false, 58, selected);
#endif
#if defined(XAR_CK3_ENABLE_G2_REALM_LAW_PAUSED_PRIVATE_QUERY_V1)
  Check(environment.permitted_executor_sexquinquagintary, callbacks.law_final_terms, true, 56, selected);
#else
  Check(environment.permitted_executor_sexquinquagintary, callbacks.law_final_terms, false, 56, selected);
#endif
#if defined(XAR_CK3_ENABLE_G2_REALM_LAW_ENACT_PRIVATE_V1)
  Check(environment.permitted_executor_septentrigintary, callbacks.law_action, true, 37, selected);
#else
  Check(environment.permitted_executor_septentrigintary, callbacks.law_action, false, 37, selected);
#endif
#if defined(XAR_CK3_ENABLE_G2_ACTIVITY_FEAST_PLANNER_OPEN_PRIVATE_V1)
  Check(environment.permitted_executor_septenquinquagintary, callbacks.feast_open, true, 57, selected);
#else
  Check(environment.permitted_executor_septenquinquagintary, callbacks.feast_open, false, 57, selected);
#endif
#if defined(XAR_CK3_ENABLE_G2_ACTIVITY_STAGE1_OPTION_READ_PRIVATE_V1)
  Check(environment.permitted_executor_novemquinquagintary, callbacks.feast_options, true, 59, selected);
#else
  Check(environment.permitted_executor_novemquinquagintary, callbacks.feast_options, false, 59, selected);
#endif
#if defined(XAR_CK3_ENABLE_G2_ACTIVITY_STAGE5_CANSTART_PRIVATE_V1)
  Check(environment.permitted_executor_sexagintary, callbacks.feast_can_start, true, 60, selected);
#else
  Check(environment.permitted_executor_sexagintary, callbacks.feast_can_start, false, 60, selected);
#endif
#if defined(XAR_CK3_ENABLE_G2_ACTIVITY_STAGE5_GOLD_COST_PRIVATE_V1)
  Check(environment.permitted_executor_unsexagintary, callbacks.feast_gold, true, 61, selected);
#else
  Check(environment.permitted_executor_unsexagintary, callbacks.feast_gold, false, 61, selected);
#endif
#if defined(XAR_CK3_ENABLE_G2_ACTIVITY_STAGE5_FEAST_FULL_COST_PRIVATE_V1)
  Check(environment.permitted_executor_duosexagintary, callbacks.feast_full_costs, true, 62, selected);
#else
  Check(environment.permitted_executor_duosexagintary, callbacks.feast_full_costs, false, 62, selected);
#endif
#if defined(XAR_CK3_ENABLE_G2_ACTIVITY_STAGE2_DESTINATION_PRIVATE_V1)
  Check(environment.permitted_executor_trisexagintary, callbacks.feast_destination, true, 63, selected);
#else
  Check(environment.permitted_executor_trisexagintary, callbacks.feast_destination, false, 63, selected);
#endif
#if defined(XAR_CK3_ENABLE_G2_ACTIVITY_STAGE2_DESTINATION_PRIVATE_V1)
  Check(environment.permitted_executor_feast_stage2_confirm12002, callbacks.feast_stage2_confirm, true, 1200236, selected);
#else
  Check(environment.permitted_executor_feast_stage2_confirm12002, callbacks.feast_stage2_confirm, false, 1200236, selected);
#endif
#if defined(XAR_CK3_ENABLE_G2_ACTIVITY_FEAST_STAGE5_START_PRIVATE_V1)
  Check(environment.permitted_executor_quattuorsexagintary, callbacks.feast_start, true, 64, selected);
#else
  Check(environment.permitted_executor_quattuorsexagintary, callbacks.feast_start, false, 64, selected);
#endif
#if defined(XAR_CK3_ENABLE_G2_ACTIVITY_FEAST_GUEST_CANDIDATE_PRIVATE_V1)
  Check(environment.permitted_executor_quinsexagintary, callbacks.feast_guest, true, 65, selected);
#else
  Check(environment.permitted_executor_quinsexagintary, callbacks.feast_guest, false, 65, selected);
#endif
#if defined(XAR_CK3_ENABLE_G2_ACTIVITY_FEAST_GUEST_RULE_TOGGLE_PRIVATE_V1)
  Check(environment.permitted_executor_sexsexagintary, callbacks.feast_guest_rules, true, 66, selected);
#else
  Check(environment.permitted_executor_sexsexagintary, callbacks.feast_guest_rules, false, 66, selected);
#endif
#if defined(XAR_CK3_ENABLE_G2_ACTIVITY_FEAST_GUEST_OPINION_PRIVATE_V1)
  Check(environment.permitted_executor_septensexagintary, callbacks.feast_guest_opinion, true, 67, selected);
#else
  Check(environment.permitted_executor_septensexagintary, callbacks.feast_guest_opinion, false, 67, selected);
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_FACTION_ALERTS_PRIVATE_QUERY_V1)
  Check(environment.permitted_executor_factions12002, callbacks.factions, true, 1200231, selected);
#else
  Check(environment.permitted_executor_factions12002, callbacks.factions, false, 1200231, selected);
#endif
#if defined(XAR_CK3_ENABLE_G2_M5_WAR_CASH_PRIVATE_QUERY_V1)
  Check(environment.permitted_executor_warcash12002, callbacks.warcash, true, 1200232, selected);
#else
  Check(environment.permitted_executor_warcash12002, callbacks.warcash, false, 1200232, selected);
#endif
#if defined(XAR_CK3_ENABLE_G2_M5_FAMILY_OBLIGATIONS_PRIVATE_QUERY_V1)
  Check(environment.permitted_executor_family_obligations12002, callbacks.family_obligations, true, 1200233, selected);
#else
  Check(environment.permitted_executor_family_obligations12002, callbacks.family_obligations, false, 1200233, selected);
#endif
#if defined(XAR_CK3_ENABLE_G2_M5_PREWAR_SOURCES_PRIVATE_QUERY_V1)
  Check(environment.permitted_executor_prewar12002, callbacks.prewar, true, 1200234, selected);
#else
  Check(environment.permitted_executor_prewar12002, callbacks.prewar, false, 1200234, selected);
#endif
#if defined(XAR_CK3_ENABLE_G2_GOVERNMENT_RUNTIME_PRIVATE_QUERY_V1)
  Check(environment.permitted_executor_government12002, callbacks.government, true, 1200235, selected);
#else
  Check(environment.permitted_executor_government12002, callbacks.government, false, 1200235, selected);
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_CONTEXT_PRIVATE_QUERY_V1)
  Check(environment.permitted_executor_religion12002, callbacks.religion, true, 1200237, selected);
#else
  Check(environment.permitted_executor_religion12002, callbacks.religion, false, 1200237, selected);
#endif
#if defined(XAR_CK3_ENABLE_G2_PRISONER_COLLECTION_PRIVATE_QUERY_V1)
  Check(environment.permitted_executor_triquinquagintary, callbacks.prisoner_collection, true, 53, selected);
#else
  Check(environment.permitted_executor_triquinquagintary, callbacks.prisoner_collection, false, 53, selected);
#endif
#if defined(XAR_CK3_ENABLE_G2_PRISONER_RANSOM_ACTION_PRIVATE_V1)
  Check(environment.permitted_executor_quattuorquinquagintary, callbacks.prisoner_ransom, true, 54, selected);
#else
  Check(environment.permitted_executor_quattuorquinquagintary, callbacks.prisoner_ransom, false, 54, selected);
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RITE_GOVERNANCE_PRIVATE_QUERY_V1)
  Check(environment.permitted_executor_rite_governance12002, callbacks.rite_governance, true, 1200238, selected);
#else
  Check(environment.permitted_executor_rite_governance12002, callbacks.rite_governance, false, 1200238, selected);
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_CLERGY_APPOINTMENT_PRIVATE_QUERY_V1)
  Check(environment.permitted_executor_clergy12002, callbacks.clergy, true, 1200239, selected);
#else
  Check(environment.permitted_executor_clergy12002, callbacks.clergy, false, 1200239, selected);
#endif
#if defined(XAR_CK3_ENABLE_G2_RELIGION_CONVERSION_PRIVATE_QUERY_V1)
  Check(environment.permitted_executor_religion_conversion12002, callbacks.religion_conversion, true, 1200240, selected);
#else
  Check(environment.permitted_executor_religion_conversion12002, callbacks.religion_conversion, false, 1200240, selected);
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DOCTRINES_PRIVATE_QUERY_V1)
  Check(environment.permitted_executor_religion_doctrines12002, callbacks.religion_doctrines, true, 1200241, selected);
#else
  Check(environment.permitted_executor_religion_doctrines12002, callbacks.religion_doctrines, false, 1200241, selected);
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RITE_MEMBERS_PRIVATE_QUERY_V1)
  Check(environment.permitted_executor_rite_members12002, callbacks.rite_members, true, 1200242, selected);
#else
  Check(environment.permitted_executor_rite_members12002, callbacks.rite_members, false, 1200242, selected);
#endif
#if defined(XAR_CK3_ENABLE_G2_RELIGION_CONVERSION_PRIVATE_QUERY_V1)
  Check(environment.permitted_executor_religion_conversion_choices12002, callbacks.religion_conversion_choices, true, 1200243, selected);
#else
  Check(environment.permitted_executor_religion_conversion_choices12002, callbacks.religion_conversion_choices, false, 1200243, selected);
#endif
#if defined(XAR_CK3_ENABLE_G2_RELIGION_CONVERSION_PRIVATE_QUERY_V1)
  Check(environment.permitted_executor_religion_conversion_inputs12002, callbacks.religion_conversion_inputs, true, 1200244, selected);
#else
  Check(environment.permitted_executor_religion_conversion_inputs12002, callbacks.religion_conversion_inputs, false, 1200244, selected);
#endif
#if defined(XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_PRIVATE_CANDIDATE_V1)
  Check(environment.permitted_executor_sway_completion12002, callbacks.sway_completion, true, 1200245, selected);
#else
  Check(environment.permitted_executor_sway_completion12002, callbacks.sway_completion, false, 1200245, selected);
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_HOSTILITY_PRIVATE_QUERY_V1)
  Check(environment.permitted_executor_religion_hostility12002, callbacks.religion_hostility, true, 1200246, selected);
#else
  Check(environment.permitted_executor_religion_hostility12002, callbacks.religion_hostility, false, 1200246, selected);
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DOCTRINE_KNOWLEDGE_PRIVATE_QUERY_V1)
  Check(environment.permitted_executor_religion_doctrine_knowledge12002, callbacks.religion_doctrine_knowledge, true, 1200247, selected);
#else
  Check(environment.permitted_executor_religion_doctrine_knowledge12002, callbacks.religion_doctrine_knowledge, false, 1200247, selected);
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_TENETS_PRIVATE_QUERY_V1)
  Check(environment.permitted_executor_religion_tenets12002, callbacks.religion_tenets, true, 1200248, selected);
#else
  Check(environment.permitted_executor_religion_tenets12002, callbacks.religion_tenets, false, 1200248, selected);
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_EPIDEMIC_TREATMENT_PRIVATE_QUERY_V1)
  Check(environment.permitted_executor_epidemic_treatment12002, callbacks.epidemic_treatment, true, 1200249, selected);
#else
  Check(environment.permitted_executor_epidemic_treatment12002, callbacks.epidemic_treatment, false, 1200249, selected);
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_EPIDEMIC_RECOVERY_PRIVATE_QUERY_V1)
  Check(environment.permitted_executor_epidemic_recovery12002, callbacks.epidemic_recovery, true, 1200250, selected);
#else
  Check(environment.permitted_executor_epidemic_recovery12002, callbacks.epidemic_recovery, false, 1200250, selected);
#endif
#if defined(XAR_CK3_ENABLE_G2_RELIGION_CONVERSION_PRIVATE_QUERY_V1)
  Check(environment.permitted_executor_religion_conversion_reasons12002, callbacks.religion_conversion_reasons, true, 1200251, selected);
#else
  Check(environment.permitted_executor_religion_conversion_reasons12002, callbacks.religion_conversion_reasons, false, 1200251, selected);
#endif
#if defined(XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_PRIVATE_CANDIDATE_V1)
  Check(environment.permitted_executor_sway_completion_execution12002, callbacks.sway_completion_execution, true, 1200252, selected);
#else
  Check(environment.permitted_executor_sway_completion_execution12002, callbacks.sway_completion_execution, false, 1200252, selected);
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_REFORM_CONTEXT_PRIVATE_QUERY_V1)
  Check(environment.permitted_executor_religion_reform12002, callbacks.religion_reform, true, 1200253, selected);
#else
  Check(environment.permitted_executor_religion_reform12002, callbacks.religion_reform, false, 1200253, selected);
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DOCTRINE_CATALOGUE_PRIVATE_QUERY_V1)
  Check(environment.permitted_executor_religion_doctrine_catalogue12002, callbacks.religion_doctrine_catalogue, true, 1200254, selected);
#else
  Check(environment.permitted_executor_religion_doctrine_catalogue12002, callbacks.religion_doctrine_catalogue, false, 1200254, selected);
#endif
#if defined(XAR_CK3_ENABLE_G2_RELIGION_CONVERSION_PRIVATE_QUERY_V1)
  Check(environment.permitted_executor_religion_conversion_outcome12002, callbacks.religion_conversion_outcome, true, 1200255, selected);
#else
  Check(environment.permitted_executor_religion_conversion_outcome12002, callbacks.religion_conversion_outcome, false, 1200255, selected);
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_NUMERIC_SPECIAL_PARAMETERS_PRIVATE_QUERY_V1)
  Check(environment.permitted_executor_religion_numeric_special_parameters12002, callbacks.religion_numeric_special_parameters, true, 1200256, selected);
#else
  Check(environment.permitted_executor_religion_numeric_special_parameters12002, callbacks.religion_numeric_special_parameters, false, 1200256, selected);
#endif
#if defined(XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_PRIVATE_CANDIDATE_V1)
  Check(environment.permitted_executor_sway_completion_termination12002, callbacks.sway_completion_termination, true, 1200257, selected);
#else
  Check(environment.permitted_executor_sway_completion_termination12002, callbacks.sway_completion_termination, false, 1200257, selected);
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_PERSONAL_PARAMETERS_PRIVATE_QUERY_V1)
  Check(environment.permitted_executor_religion_personal_parameters12002, callbacks.religion_personal_parameters, true, 1200258, selected);
#else
  Check(environment.permitted_executor_religion_personal_parameters12002, callbacks.religion_personal_parameters, false, 1200258, selected);
#endif
#if defined(XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_PRIVATE_CANDIDATE_V1)
  Check(environment.permitted_executor_sway_completion_invalidation_reason12002, callbacks.sway_completion_invalidation_reason, true, 1200259, selected);
#else
  Check(environment.permitted_executor_sway_completion_invalidation_reason12002, callbacks.sway_completion_invalidation_reason, false, 1200259, selected);
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DRAFT_GROUPS_PRIVATE_QUERY_V1)
  Check(environment.permitted_executor_religion_draft_groups12002, callbacks.religion_draft_groups, true, 1200260, selected);
#else
  Check(environment.permitted_executor_religion_draft_groups12002, callbacks.religion_draft_groups, false, 1200260, selected);
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DRAFT_DOCTRINE_CHOICES_PRIVATE_QUERY_V1)
  Check(environment.permitted_executor_religion_draft_doctrine_choices12002, callbacks.religion_draft_doctrine_choices, true, 1200261, selected);
#else
  Check(environment.permitted_executor_religion_draft_doctrine_choices12002, callbacks.religion_draft_doctrine_choices, false, 1200261, selected);
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DRAFT_TENET_CHOICES_PRIVATE_QUERY_V1)
  Check(environment.permitted_executor_religion_draft_tenet_choices12002, callbacks.religion_draft_tenet_choices, true, 1200262, selected);
#else
  Check(environment.permitted_executor_religion_draft_tenet_choices12002, callbacks.religion_draft_tenet_choices, false, 1200262, selected);
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DRAFT_RESOURCE_COSTS_PRIVATE_QUERY_V1)
  Check(environment.permitted_executor_religion_draft_resource_costs12002, callbacks.religion_draft_resource_costs, true, 1200263, selected);
#else
  Check(environment.permitted_executor_religion_draft_resource_costs12002, callbacks.religion_draft_resource_costs, false, 1200263, selected);
#endif
  // The frozen R7 baseline carries the prior callback proofs. This delta
  // retains their registration shape and executes only the three new slots.
  std::vector<Slot> delta;
  if (environment.permitted_executor_religion_draft_doctrine_choices12002 != nullptr) {
    delta.push_back({environment.permitted_executor_religion_draft_doctrine_choices12002, 1200261});
  }
  if (environment.permitted_executor_religion_draft_tenet_choices12002 != nullptr) {
    delta.push_back({environment.permitted_executor_religion_draft_tenet_choices12002, 1200262});
  }
  if (environment.permitted_executor_religion_draft_resource_costs12002 != nullptr) {
    delta.push_back({environment.permitted_executor_religion_draft_resource_costs12002, 1200263});
  }
  ExerciseMailbox(environment, delta);
  const auto wrong = BindThreadRuntimeImage(0x100000, "unsupported", typed);
  assert(wrong.build_profile == nullptr);
  std::cout << "PASS: all58 private slot mappings, " << selected.size()
            << " registered callbacks, " << delta.size()
            << " new callbacks submit/drain, prior R7 callbacks shape-only, retained14/35/semantic identities, exact12002 profile; no CK3 access\n";
}
