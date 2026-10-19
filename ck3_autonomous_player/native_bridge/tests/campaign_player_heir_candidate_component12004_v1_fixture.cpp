// Reuse the sealed provider's fixture-owned Core/Family storage and getter.
// Its old suite/export is linked but NOT invoked; this suite tests attachment.
#include "ck3_12004_player_heir_candidate_v1_fixture.cpp"
#include "xar_bridge/campaign_player_heir_candidate_component12004_v1.hpp"

// Only the original root serializers are stubbed in the exact production
// ResultFrame fragment fixture. Their root validation is not claimed here.
namespace xar::ck3_11906 {
std::string SerializeCampaignRootContextV1(const game::CampaignRootContextV1 &) {
  return "{\"status\":\"available\",\"snapshot_revision\":77}";
}
}
namespace xar::ck3_12002 {
std::string SerializeCampaignRootContextV1(const game::CampaignRootContextV1 &) {
  return "{\"status\":\"available\",\"snapshot_revision\":77}";
}
}
namespace xar::ck3_12004 {
std::string SerializeCampaignRootContextV1(const game::CampaignRootContextV1 &) {
  return "{\"status\":\"available\",\"snapshot_revision\":77}";
}
}

namespace a = xar::ck3_12004::campaign_player_heir_candidate_v1;
namespace {
void AppendJsonString(std::string &out, std::string_view text) {
  out += '"';
  for (char c : text) {
    if (c == '"' || c == '\\') out += '\\';
    out += c;
  }
  out += '"';
}
std::string Number(std::uint64_t value) { return std::to_string(value); }
// Generated from the exact pinned source span by this fixture's producer.
#include "bridge_frame_fragment.hpp"

xar::game::CampaignRootContextV1 Parent(std::int32_t actor = Fixture::actor_id) {
  xar::game::CampaignRootContextV1 p{};
  p.status = xar::game::CampaignRootContextStatusV1::available;
  p.snapshot_revision = 77;
  p.date_raw = 53186880;
  p.local_player_id = 7;
  p.player_character_id = actor;
  p.player_character_alive = true;
  p.readiness.same_frame_ready = true;
  return p;
}
constexpr std::string_view base_payload =
    "{\"status\":\"available\",\"snapshot_revision\":77}";
std::string Attach(const xar::game::CampaignRootContextV1 &p,
                   const std::optional<a::Component> &c) {
  return a::AppendToCanonicalRoot(std::string(base_payload), p, c ? &*c : nullptr);
}
std::string ResultFrame(const xar::game::CampaignRootContextV1 &p,
                        const std::optional<a::Component> &c) {
  (void)c;
  return CampaignRootContextResultFrame("fixture-request", 19, p, true, true
#if defined(XAR_CK3_ENABLE_CAMPAIGN_ROOT_PLAYER_HEIR_CANDIDATE12004_V1)
      , c ? &*c : nullptr
#endif
      );
}
#if defined(XAR_CK3_ENABLE_CAMPAIGN_ROOT_PLAYER_HEIR_CANDIDATE12004_V1)
void NoFacts(const a::Component &c) {
  Check(!c.parent_frame_bound && !c.observation.available &&
        !c.observation.candidate_present &&
        c.observation.candidate_character_id == -1 &&
        !c.observation.lineage_available,
        "unbound attachment must not publish positive candidate facts");
}
#endif

void RunAttachmentCases() {
  cases = unused_break_binder_calls = 0;
  Case([](Fixture &f) {
    const auto p = Parent();
    const auto c = a::ReadForCampaignRoot(f.b, p, 77);
#if defined(XAR_CK3_ENABLE_CAMPAIGN_ROOT_PLAYER_HEIR_CANDIDATE12004_V1)
    Check(c && c->parent_frame_bound && c->observation.available &&
          c->observation.candidate_character_id == Fixture::heir_id &&
          c->observation.source_fixture && !c->observation.original_getter_source_bound &&
          c->observation.lineage_available && f.getter_calls == 1,
          "one getter/actual Core+Lineage binds parent with signed full IDs");
    Check(Attach(p, c).find("\"candidate_character_id\":-1845493758") != std::string::npos,
          "wire must preserve signed32 generation bits");
#else
    Check(!c && f.getter_calls == 0 && f.core_calls == 0 &&
          Attach(p, c) == base_payload,
          "default-off must omit material, preserve root bytes and do zero reads");
#endif
    Check(p == Parent(), "optional read must not modify root status/readiness/facts");
  });
  Case([](Fixture &f) {
    const auto p = Parent();
    Check(a::AppendToCanonicalRoot(std::string(base_payload), p, nullptr) == base_payload &&
          f.getter_calls == 0, "legacy missing material preserves exact root bytes");
    Check(CampaignRootContextResultFrame("fixture-request", 19, p) ==
          CampaignRootContextResultFrame("fixture-request", 19, p, true, true),
          "all legacy ResultFrame calls omit optional component identically");
  });
  Case([](Fixture &f) {
    const auto p = Parent();
    const auto c = a::ReadForCampaignRoot(f.b, p, 77);
    const auto json = ResultFrame(p, c);
    Check(json.find("\"query_sequence\":19") != std::string::npos &&
          json.find("\"backend_id\":\"native-headless\"") != std::string::npos,
          "exact production ResultFrame keeps its existing outer fields");
#if defined(XAR_CK3_ENABLE_CAMPAIGN_ROOT_PLAYER_HEIR_CANDIDATE12004_V1)
    Check(json.find("\"player_heir_candidate_v1\":") != std::string::npos,
          "actual ResultFrame must attach the enabled component inside root");
#else
    Check(json.find("player_heir_candidate_v1") == std::string::npos && f.getter_calls == 0,
          "actual default-off ResultFrame must omit component");
#endif
  });
#if defined(XAR_CK3_ENABLE_CAMPAIGN_ROOT_PLAYER_HEIR_CANDIDATE12004_V1)
  Case([](Fixture &f) {
    auto p = Parent(); p.status = xar::game::CampaignRootContextStatusV1::unavailable;
    const auto before = p;
    const auto c = a::ReadForCampaignRoot(f.b, p, 77);
    Check(c && f.getter_calls == 0 && f.core_calls == 0 && p == before,
          "unavailable root must block getter without changing parent"); NoFacts(*c);
  });
  Case([](Fixture &f) {
    const auto c = a::ReadForCampaignRoot(f.b, Parent(), 78);
    Check(c && f.getter_calls == 0 && f.core_calls == 0,
          "stale native revision must block getter"); NoFacts(*c);
  });
  Case([](Fixture &f) {
    auto p = Parent(); p.readiness.same_frame_ready = false;
    const auto c = a::ReadForCampaignRoot(f.b, p, 77);
    Check(c && f.getter_calls == 0, "partial root must block getter"); NoFacts(*c);
  });
  Case([](Fixture &f) {
    auto p = Parent(); p.local_player_id.reset();
    const auto c = a::ReadForCampaignRoot(f.b, p, 77);
    Check(c && f.getter_calls == 0, "missing parent identity blocks getter"); NoFacts(*c);
  });
  for (int field = 0; field != 3; ++field) Case([field](Fixture &f) {
    auto p = Parent();
    if (field == 0) ++p.date_raw;
    if (field == 1) p.player_character_id = 3;
    if (field == 2) p.local_player_id = 8;
    const auto before = p;
    const auto c = a::ReadForCampaignRoot(f.b, p, 77);
    Check(c && f.getter_calls == 1 && p == before &&
          c->observation.unavailable_reason == "parent_root_frame_changed",
          "parent date/actor/local-player mismatch must downgrade optional result");
    NoFacts(*c);
  });
  Case([](Fixture &f) {
    f.returned = nullptr;
    const auto c = a::ReadForCampaignRoot(f.b, Parent(), 77);
    Check(c && c->parent_frame_bound && c->observation.available &&
          c->observation.getter_observed && !c->observation.candidate_present &&
          c->observation.candidate_character_id == -1 && f.getter_calls == 1,
          "observed null is coherent, not a qualified heir or backup proof");
  });
  Case([](Fixture &f) {
    Put(f.heir, n::kCharacterDeathDataOffset, static_cast<void *>(f.house.data()));
    const auto c = a::ReadForCampaignRoot(f.b, Parent(), 77);
    Check(c && c->parent_frame_bound && c->observation.candidate_present &&
          !c->observation.candidate_alive && f.getter_calls == 1,
          "coherent dead return cannot become living qualification");
  });
  Case([](Fixture &f) {
    Put(f.dynasty, 0x10, std::int32_t{123});
    const auto c = a::ReadForCampaignRoot(f.b, Parent(), 77);
    Check(c && c->parent_frame_bound && c->observation.available &&
          !c->observation.lineage_available &&
          c->observation.candidate_lineage == fv::Lineage{} && f.getter_calls == 1,
          "lineage unavailable preserves unknown, not known-none");
  });
  Case([](Fixture &f) {
    Put(f.heir, fv::kCharacterHouseOffset, std::int32_t{-1});
    const auto c = a::ReadForCampaignRoot(f.b, Parent(), 77);
    Check(c && c->parent_frame_bound && c->observation.lineage_available &&
          c->observation.candidate_lineage == fv::Lineage{} && f.getter_calls == 1,
          "known-none lineage remains distinct from missing input");
  });
  Case([](Fixture &f) {
    f.mutation = Mutation::date_in_getter;
    const auto p = Parent();
    const auto c = a::ReadForCampaignRoot(f.b, p, 77);
    Check(c && f.getter_calls == 1 && !c->parent_frame_bound &&
          !c->observation.available && Attach(p, c).find(
              "\"candidate_character_id\":-1") != std::string::npos,
          "provider race remains unknown; no second getter or changed root status");
  });
  Case([](Fixture &f) {
    f.throw_getter = true;
    const auto c = a::ReadForCampaignRoot(f.b, Parent(), 77);
    Check(c && !c->parent_frame_bound && !c->observation.available && f.getter_calls == 1,
          "getter exception only affects optional material");
  });
  Case([](Fixture &f) {
    auto p = Parent();
    const auto c = a::ReadForCampaignRoot(f.b, p, 77);
    ++p.snapshot_revision;
    const auto json = ResultFrame(p, c);
    Check(json.find("serialized_parent_frame_changed") != std::string::npos &&
          json.find("\"candidate_character_id\":-1") != std::string::npos &&
          json.find("\"parent_frame_bound\":false") != std::string::npos &&
          f.getter_calls == 1, "late parent mismatch must strip copied positive facts");
  });
  Case([](Fixture &f) {
    auto c = a::ReadForCampaignRoot(f.b, Parent(), 77);
    Check(c.has_value(), "enabled component required");
    c->parent_frame_bound = c->observation.available = false;
    c->observation.unavailable_reason = "quote\" slash\\ newline\n tab\t";
    const auto json = Attach(Parent(), c);
    Check(json.find("quote\\\" slash\\\\ newline\\u000a tab\\u0009") != std::string::npos,
          "JSON reasons must escape quotes, slashes and control bytes");
  });
#endif
  Check(unused_break_binder_calls == 0, "unused fixture Break binder must have zero calls");
  ++cases;
}
} // namespace

FIXTURE_EXPORT int RunPlayerHeirCampaignAttachmentFixtures(
    char *output, std::size_t capacity) noexcept {
  try {
    RunAttachmentCases();
    std::snprintf(output, capacity,
      "{\"status\":\"PASS\",\"synthetic_cases\":%d,\"getter_calls_per_read_max\":1,"
      "\"unused_break_binder_calls\":%d,\"Game_RPC_process_access\":0,\"actual_H_credit\":false}",
      cases, unused_break_binder_calls);
    return 0;
  } catch (const std::exception &e) {
    std::snprintf(output, capacity, "FAIL after%d cases: %s", cases, e.what());
    return 1;
  }
}

FIXTURE_EXPORT int GetPlayerHeirCampaignAttachmentWire(
    char *output, std::size_t capacity) noexcept {
  try {
    auto f = std::make_unique<Fixture>();
    // Positive current actor accepted by the existing root schema; the heir
    // retains its complete negative signed32 generation bits on the wire.
    Put(f->actor, n::kCharacterFullIdOffset, std::int32_t{1});
    Put(f->entry, n::kPlayerEntryCharacterIdOffset, std::int32_t{1});
    const auto p = Parent(1);
    const auto c = a::ReadForCampaignRoot(f->b, p, 77);
    const auto json = ResultFrame(p, c);
    if (json.size() + 1 > capacity) return 2;
    std::memcpy(output, json.c_str(), json.size() + 1);
    active = nullptr;
    return 0;
  } catch (...) { active = nullptr; return 1; }
}
