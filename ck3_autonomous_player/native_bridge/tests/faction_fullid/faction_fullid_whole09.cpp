#define main RetainedAdoptedWholeMain09
#include "retained_adopted_whole09.cpp"
#undef main
#include <bit>
#include <limits>
#include <memory>
#include "faction_allocator_exec10.hpp"
#include "xar_bridge/ck3_12004_faction_mailbox.hpp"

namespace {
struct World09;
World09 *world09 = nullptr;
void *Liege09(void *character);
struct World09 {
  Fixture fixture;
  std::array<std::byte, 0x230> land{}, recipient_land{};
  std::array<std::int32_t, 3> targeting{};
  std::array<std::array<std::byte, 0x20>, 2> additional_members{};
  std::vector<std::int32_t> expected_factions;
  std::array<std::byte, 0x30> contracts{}, contract{};
  std::array<std::byte, 0x20> contract_slots{};
  std::array<std::int32_t, 1> contract_ids{0x06000001};
  void *contract_pointer = contracts.data();
  void *fallback = nullptr;
  game::PlayerFactionAlertsFrameV1 frame{};
  std::uint32_t source = 0;
  bool stale = false;
  std::unique_ptr<m1_allocator_exec10::FactionAllocatorImage> allocator;
  bool actual_allocator = false;
  bool mixed = false;
  int actual_alert_calls = 0;
  explicit World09(std::uint32_t raw, bool drift, bool mix) : source(raw), stale(drift), mixed(mix) {
    world09 = this;
    const auto signed_id = std::bit_cast<std::int32_t>(source);
    void *faction = fixture.faction.data();
    if ((source & 0x00FFFFFFU) == 0 && source != UINT32_MAX) {
      const auto assets = std::filesystem::path(__FILE__).parent_path() / "native-allocator-assets";
      allocator = std::make_unique<m1_allocator_exec10::FactionAllocatorImage>(assets.string());
      allocator->Reset(((source - 0x01000000U) & 0xFF000000U) | 0x00FFFFFFU);
      faction = allocator->Allocate(fixture.faction_type.data(),
          std::bit_cast<std::int32_t>(actor_id), 29);
      m1_allocator_exec10::Require(faction == allocator->FirstObject() &&
          Get<std::uint32_t>(faction, 0x10) == source, "actual allocator fullID");
      allocator->RequireOriginalCodeUnchanged();
      fixture.faction_store_pointer = allocator->Storage();
      fixture.faction_fallback = allocator->Fallback();
      fixture.factions.expected_faction_vtable = allocator->PrimaryVtable();
      actual_allocator = true;
      // Membership and discontent are authored later state, after the real
      // allocator installed type, target, update_day, fullID and slot pointer.
      Put(faction, 0x28, std::int64_t{7'000'000});
      Put(faction, 0x44, recipient_id);
      Put(faction, 0x48, fixture.faction_member.data());
      Put(faction, 0x54, std::int32_t{1});
    } else {
      Put(fixture.faction_slots.data(), 3 * 0x10 + 8, static_cast<void *>(nullptr));
      Put(fixture.faction_slots.data(), (source == UINT32_MAX ? 0 : source & 0x00FFFFFFU) * 0x10ULL + 8,
          faction);
      Put(faction, 0x10, signed_id);
    }
    if (stale) Put(faction, 0x10, source ^ 0x01000000U);
    Put(fixture.faction_member.data(), 0x0C, signed_id);
    targeting[0] = signed_id;
    expected_factions.push_back(signed_id);
    if (mixed) {
      m1_allocator_exec10::Require(actual_allocator && source == 0x80000000U && !stale,
          "mixed world uses distinct actual allocator slots");
      for (std::uint32_t i = 0; i < 2; ++i) {
        const std::uint32_t wanted = i == 0 ? 1U : 0xFF000002U;
        Put(allocator->FirstObject(), (i + 1U) * 0xD0U + 0x10U,
            ((wanted - 0x01000000U) & 0xFF000000U) | 0x00FFFFFFU);
        void *extra = allocator->Allocate(fixture.faction_type.data(),
            std::bit_cast<std::int32_t>(actor_id), 29);
        m1_allocator_exec10::Require(Get<std::uint32_t>(extra, 0x10) == wanted,
            "mixed allocator fullID");
        Put(extra, 0x28, std::int64_t{7'000'000});
        Put(extra, 0x44, recipient_id);
        Put(extra, 0x48, additional_members[i].data());
        Put(extra, 0x54, std::int32_t{1});
        Put(additional_members[i].data(), 8, recipient_id);
        Put(additional_members[i].data(), 0x0C, wanted);
        targeting[i + 1U] = std::bit_cast<std::int32_t>(wanted);
        expected_factions.push_back(targeting[i + 1U]);
      }
      allocator->RequireOriginalCodeUnchanged();
      std::sort(expected_factions.begin(), expected_factions.end());
    }
    Put(fixture.characters[0].data(), 0x1C0, land.data());
    Put(fixture.characters[1].data(), 0x1C0, recipient_land.data());
    Put(land.data(), 0x120, targeting.data());
    Put(land.data(), 0x12C, mixed ? std::int32_t{3} : std::int32_t{1});
    Put(land.data(), 0x218, contract_ids.data());
    Put(land.data(), 0x224, std::int32_t{1});
    Put(contracts.data(), 0x20, contract_slots.data());
    Put(contracts.data(), 0x2C, std::int32_t{2});
    Put(contract_slots.data(), 0x18, contract.data());
    Put(contract.data(), 8, contract_ids[0]);
    Put(contract.data(), 0x20, fixture.characters[1].data());
    fixture.factions.character_fallback_slot = &fallback;
    fixture.factions.vassal_contract_storage_slot = &contract_pointer;
    fixture.factions.vassal_contract_fallback_slot = &fallback;
    fixture.factions.immediate_liege = &Liege09;
  }
};
void *Liege09(void *character) {
  return character == world09->fixture.characters[1].data()
      ? world09->fixture.characters[0].data() : nullptr;
}
bool Frame09(void *opaque, game::PlayerFactionAlertsFrameV1 &out) noexcept {
  auto &w = *static_cast<World09 *>(opaque);
  CoreSnapshotPrefix core{};
  if (!ck3_12004::ReadCoreSnapshot(w.fixture.b.interaction.core, core)) return false;
  out = w.frame;
  out.date_raw = core.clock.date_raw;
  out.paused = core.clock.paused;
  out.map_ready = core.map_ready;
  out.has_played_character = core.has_played_character;
  out.played_character_alive = core.played_character_alive;
  out.played_character_id = core.played_character_id;
  return true;
}
bool Root09(void *opaque, const game::CampaignRootFrameV1 &frame,
            game::CampaignRootContextV1 &out) noexcept {
  // Core is real; the direct-vassal eligibility projection is authored and
  // agrees with the same owned contract graph traversed by the real alerts.
  return RootSource(&static_cast<World09 *>(opaque)->fixture, frame, out);
}
bool Alerts09(void *opaque, const game::PlayerFactionAlertsFrameV1 &frame,
              game::PlayerFactionAlertsV1 &out) noexcept {
  auto &w = *static_cast<World09 *>(opaque);
  ++w.actual_alert_calls;
  w.frame = frame;
  auto access = w.fixture.faction_access;
  access.context = &w;
  access.capture_frame = &Frame09;
  return ReadPlayerFactionAlerts12004(w.fixture.factions, access,
      {frame.snapshot_revision}, out) == game::ReadPlayerFactionAlertsResultV1::available;
}
std::string ReplaceSource09(std::string value, std::string_view replacement) {
  const auto start = value.find("\"source_faction_id\":") + 20;
  const auto end = value.find(',', start);
  value.replace(start, end - start, replacement);
  return value;
}
}

#include "character_public_cases14.hpp"

int FactionFullIdCharacterPublicMain14(int argc, char **argv) {
  return CharacterPublicCase14(argc, argv);
}

#include "surrender_cases15.hpp"

int FactionFullIdSurrenderMain15(int argc, char **argv) {
  return SurrenderCase15(argc, argv);
}

#ifndef XAR_CK3_FACTION_FULLID_ENTRY
#define XAR_CK3_FACTION_FULLID_ENTRY main
#endif
int XAR_CK3_FACTION_FULLID_ENTRY(int argc, char **argv) {
  if (argc < 4) return 90;
  const auto raw = static_cast<std::uint32_t>(std::stoull(argv[1]));
  const bool stale = std::string_view(argv[2]) == "stale";
  const std::filesystem::path out = argv[3];
  std::filesystem::create_directories(out);
  if ((raw & 0x00FFFFFFU) >= 8 && raw != UINT32_MAX) return 91;
  World09 w(raw, stale, std::string_view(argv[2]) == "mixed");
  RouterAdapter adapter;
  const game::PlayerFactionAlertsFrameV1 frame{1, 53175816, true, true, true, true,
      static_cast<std::int32_t>(actor_id)};
  CoreSnapshotPrefix core{};
  const bool core_ok = ck3_12004::ReadCoreSnapshot(w.fixture.b.interaction.core, core);
  game::PlayerFactionAlertsV1 alerts{};
  const bool alert_ok = Alerts09(&w, frame, alerts);
  const std::string alert_wire = SerializePlayerFactionAlerts12004(alerts);
  WriteWire(out, "public-alerts.json", alert_wire);
  const auto signed_id = std::bit_cast<std::int32_t>(raw);
  std::string expected_projection = "\"dangerous_faction_ids\":[";
  for (const auto id : w.expected_factions) {
    if (expected_projection.back() != '[') expected_projection += ',';
    expected_projection += std::to_string(id);
  }
  expected_projection += ']';
  const bool public_wire_ok = alert_ok && !alert_wire.empty() &&
      alert_wire.find("\"faction_id\":" + std::to_string(signed_id)) != std::string::npos &&
      alert_wire.find(expected_projection) != std::string::npos;
  bool title_zero_rejected = false, war_zero_rejected = false, faction_absent_rejected = false;
  if (alert_ok && !alerts.targeting_factions.empty()) {
    auto invalid = alerts;
    invalid.targeting_factions[0].special_title_id = 0;
    title_zero_rejected = SerializePlayerFactionAlerts12004(invalid).empty();
    invalid = alerts;
    invalid.targeting_factions[0].faction_at_war = true;
    invalid.targeting_factions[0].faction_war_id = 0;
    war_zero_rejected = SerializePlayerFactionAlerts12004(invalid).empty();
    invalid = alerts;
    invalid.targeting_factions[0].faction_id = -1;
    faction_absent_rejected = SerializePlayerFactionAlerts12004(invalid).empty();
  }
  game::PlayerTargetingFactionV1 entity{};
  const bool entity_ok = ReadFactionEntity12004(w.fixture.factions,
      w.fixture.faction_access, signed_id, entity) == ReadFactionEntityResult12004::available;
  std::uint32_t selected = UINT32_MAX, recipient = UINT32_MAX;
  const bool selected_ok = SelectFactionGiftPrivateCandidate12004(
      w.fixture.campaign, alerts, selected, recipient) && selected == raw && recipient == recipient_id;
  ck3_11906::MainThreadQueryMailboxV1 mailbox{};
  mailbox.offline_fixture = true;
  mailbox.permitted_executor_quattuortrigintary = &ExecuteFactionGiftPrivateMailbox12004;
  // The actual production serializer receives an authored public-query
  // sequence. Public Handle/mailbox dispatch is outside this narrow fixture.
  std::string public_whole = SerializePlayerFactionAlertsWhole12004(alerts, 1,
      "faction-fullid09-public-pre", adapter.descriptor());
  const bool whole_pre = !public_whole.empty();
  if (whole_pre) WriteWire(out, "public-alerts-whole.json", public_whole);
  FactionGiftPrivateFixtureBindings12004 bindings{};
  bindings.factions = w.fixture.factions;
  bindings.gift = w.fixture.b;
  bindings.context = &w;
  bindings.read_campaign = &Root09;
  bindings.read_alerts = &Alerts09;
  FactionGiftPrivateState12004 state;
  std::string wire, failure;
  const auto call = [&](std::string_view step, const std::string &payload,
                        std::uint64_t revision, std::string_view file) {
    const auto outer_id = std::string("faction-fullid09-") + std::string(file);
    const bool ok = HandleFactionGiftPrivate12004(adapter, mailbox, adapter.snapshot,
        revision, step, payload, outer_id, state,
        wire, failure, &bindings);
    if (ok) WriteWire(out, file, wire);
    else std::ofstream(out / (std::string(file) + ".failure")) << failure << '\n';
    return ok;
  };
  const bool preview = call(ck3_11906::kFactionGiftPrivateQueryStepV1,
      FramePayload(1) + "}", 1, "private-preview.json");
  const std::string submit = FramePayload(1) + ",\"source_faction_id\":" + std::to_string(raw) +
      ",\"recipient_character_id\":" + std::to_string(recipient_id) +
      ",\"membership_role\":\"leader\",\"definition_stable_hash\":" + std::to_string(definition_hash) +
      ",\"gold_cost_raw\":7500000,\"opinion_delta\":35,\"minimum_gold_reserve_raw\":5000000,\"expected_native_revision\":1}";
  bool malformed_ok = true;
  int malformed_count = 0;
  if (preview && state.last_query) {
    for (const std::string_view bad : {"-1", "4294967295", "4294967296", "true", "0.0", "\"0\"", "null", "-2147483648", "-16777216"}) {
      const auto before = queues;
      const bool accepted = call(ck3_11906::kFactionGiftPrivateSubmitStepV1,
          ReplaceSource09(submit, bad), 1, "private-malformed-" + std::to_string(malformed_count) + ".json");
      malformed_ok = malformed_ok && !accepted && queues == before;
      ++malformed_count;
    }
  }
  const bool submitted = preview && call(ck3_11906::kFactionGiftPrivateSubmitStepV1,
      submit, 1, "private-submit.json");
  const bool pending = state.pending_ack && state.action_may_have_submitted &&
      state.pending_ack->source_faction_id == raw;
  const int after_submit = queues;
  bool duplicate = false, receipt = false, verified = false, cold = false, cold_public = false;
  if (pending) {
    duplicate = !call(ck3_11906::kFactionGiftPrivateSubmitStepV1, submit, 1, "private-duplicate.json") && queues == after_submit;
    Put(w.fixture.player_extension.data(), 0x100, std::int64_t{12'500'000});
    gift_applied = true;
    Put(opinion_group.data(), 0x14, std::int32_t{1});
    receipt = call(ck3_11906::kFactionGiftPrivateReceiptStepV1,
        FramePayload(2) + "}", 2, "private-receipt.json");
    verified = state.verified_receipt && state.verified_receipt->postcondition_verified &&
        state.verified_receipt->source_faction_id == raw;
    game::PlayerFactionAlertsV1 post_alerts{};
    auto post_frame = frame;
    post_frame.snapshot_revision = 2;
    if (Alerts09(&w, post_frame, post_alerts))
      WriteWire(out, "public-alerts-post.json", SerializePlayerFactionAlerts12004(post_alerts));
    public_whole = SerializePlayerFactionAlertsWhole12004(post_alerts, 2,
        "faction-fullid09-public-post", adapter.descriptor());
    WriteWire(out, "public-alerts-post-whole.json", public_whole);
    state = {};
    cold = call(ck3_11906::kFactionGiftPrivateColdRecoveryStepV1,
        FramePayload(3) + ",\"source_faction_id\":" + std::to_string(raw) +
        ",\"recipient_character_id\":" + std::to_string(recipient_id) + "}", 3, "private-cold.json");
    game::PlayerFactionAlertsV1 cold_alerts{};
    auto cold_frame = frame;
    cold_frame.snapshot_revision = 3;
    cold_public = Alerts09(&w, cold_frame, cold_alerts);
    if (cold_public) {
      WriteWire(out, "public-alerts-cold.json", SerializePlayerFactionAlerts12004(cold_alerts));
      WriteWire(out, "public-alerts-cold-whole.json", SerializePlayerFactionAlertsWhole12004(
          cold_alerts, 3, "faction-fullid09-public-cold", adapter.descriptor()));
    }
  }
  const bool expected = !stale && raw != UINT32_MAX;
  const bool full_pass = core_ok && alert_ok && public_wire_ok && entity_ok && selected_ok &&
      whole_pre && preview && submitted && pending && duplicate && receipt && verified && cold && cold_public &&
      malformed_ok && malformed_count == 9 && queues == 1 && clones == 1;
  const bool domain_controls = title_zero_rejected && war_zero_rejected && faction_absent_rejected;
  const bool control_pass = !alert_ok && !selected_ok && !submitted && queues == 0;
  std::ofstream summary(out / "SUMMARY.json");
  summary << "{\"machine_id\":\"xenoamess-full-tower-eb9d2c1186\",\"software_fixture\":true,"
      "\"real_Core_and_alerts_reader\":true,\"campaign_eligibility_authored\":true,"
      "\"engine_callbacks_and_mailbox_substituted\":true,\"allocator_machinecode_executed_here\":"
      << (w.actual_allocator ? "true" : "false") << ",\"membership_state_authored_after_allocation\":true,"
      "\"public_whole_serializer_actual\":true,\"public_query_sequence_authored\":true,\"public_whole_Handle_executed\":false,"
      "\"source_raw\":" << raw << ",\"source_signed\":" << signed_id << ",\"stale\":" << (stale ? "true" : "false")
      << ",\"mixed_signed_factions\":" << (w.mixed ? "true" : "false")
      << ",\"Core\":" << core_ok << ",\"alerts\":" << alert_ok << ",\"wire\":" << public_wire_ok
      << ",\"whole_public_pre\":" << whole_pre
      << ",\"entity\":" << entity_ok << ",\"selector\":" << selected_ok << ",\"preview\":" << preview
      << ",\"submit\":" << submitted << ",\"pending\":" << pending << ",\"duplicate\":" << duplicate
      << ",\"receipt\":" << receipt << ",\"verified\":" << verified << ",\"cold\":" << cold
      << ",\"cold_public_same_frame\":" << cold_public
      << ",\"malformed_rejections\":" << malformed_count << ",\"malformed_ok\":" << malformed_ok
      << ",\"title_zero_rejected\":" << title_zero_rejected << ",\"war_zero_rejected\":" << war_zero_rejected
      << ",\"faction_absent_rejected\":" << faction_absent_rejected
      << ",\"queue_calls\":" << queues << ",\"actual_alert_calls\":" << w.actual_alert_calls
      << ",\"full_chain_pass\":" << full_pass << ",\"control_pass\":" << control_pass << "}\n";
  std::cout << "Faction raw=" << raw << " signed=" << signed_id << " core=" << core_ok
      << " alerts=" << alert_ok << " wire=" << public_wire_ok << " selector=" << selected_ok
      << " preview=" << preview << " submitted=" << submitted << " queues=" << queues << '\n';
  return (expected ? full_pass && domain_controls : control_pass) ? 0 : 1;
}
