#include "xar_bridge/ck3_1210_battle_candidate_serializer_v1.hpp"
#include <iostream>
#include <string>
#include <utility>
#include <array>
#include <bit>
#include <cstdio>
#include <cstring>
#include <limits>
#include <span>
#include <vector>

namespace {
using namespace xar::ck3_1210;
struct Block {
  std::vector<std::byte> bytes;
  explicit Block(std::size_t n) : bytes(n) {}
  void *data() { return bytes.data(); }
  template<class T> void Put(std::size_t offset, T value) {
    std::memcpy(bytes.data() + offset, &value, sizeof value);
  }
};
struct Fixture {
  static constexpr auto unit_id = std::bit_cast<std::int32_t>(0x81000000U);
  static constexpr auto army_id = std::bit_cast<std::int32_t>(0x82000000U);
  static constexpr auto combat_id = std::bit_cast<std::int32_t>(0x83000000U);
  static constexpr auto actor_id = std::bit_cast<std::int32_t>(0x84000000U);
  Block units{0x30}, armies{0x30}, combats{0x30}, clone{0x30};
  Block unit_rows{0x10}, army_rows{0x10}, combat_rows{0x10};
  Block unit{0x17C}, army{0x12C}, combat{0x10};
  void *unit_root = nullptr, *army_root = nullptr, *combat_root = nullptr;
  BattleCandidateBindingsV1 bindings{};
  std::vector<std::span<const std::byte>> allowed;
  std::size_t copy_calls = 0, frame_calls = 0, fail_frame_call = 0;
  bool clone_combat_between_passes = false, mutate_generation = false;
  bool deny_combat_identity = false;
  Fixture() {
    unit_root = units.data(); army_root = armies.data(); combat_root = combats.data();
    bindings = {true, &unit_root, &army_root, &combat_root};
    units.Put(0x20, unit_rows.data()); units.Put(0x2C, std::int32_t{1});
    armies.Put(0x20, army_rows.data()); armies.Put(0x2C, std::int32_t{1});
    combats.Put(0x20, combat_rows.data()); combats.Put(0x2C, std::int32_t{1});
    clone.Put(0x20, combat_rows.data()); clone.Put(0x2C, std::int32_t{1});
    unit_rows.Put(8, unit.data()); army_rows.Put(8, army.data()); combat_rows.Put(8, combat.data());
    unit.Put(0x10, unit_id); unit.Put(0x14, std::uint32_t{0x556E6974U});
    unit.Put(0x174, actor_id); unit.Put(0x178, army_id);
    army.Put(0x10, army_id); army.Put(0x14, std::uint32_t{0x41726D79U});
    army.Put(0x124, unit_id); army.Put(0x128, combat_id);
    combat.Put(8, combat_id); combat.Put(0xC, std::uint32_t{0x436F6D62U});
    for (const auto *block : {&units,&armies,&combats,&clone,&unit_rows,&army_rows,&combat_rows,&unit,&army,&combat})
      allowed.emplace_back(block->bytes.data(), block->bytes.size());
    allowed.emplace_back(reinterpret_cast<const std::byte *>(&unit_root), sizeof unit_root);
    allowed.emplace_back(reinterpret_cast<const std::byte *>(&army_root), sizeof army_root);
    allowed.emplace_back(reinterpret_cast<const std::byte *>(&combat_root), sizeof combat_root);
  }
  static bool Copy(void *context, const void *source, void *dest, std::size_t size) noexcept {
    auto &f = *static_cast<Fixture *>(context); ++f.copy_calls;
    const auto address = reinterpret_cast<std::uintptr_t>(source);
    if (f.deny_combat_identity && address == reinterpret_cast<std::uintptr_t>(f.combat.data()) + 8) return false;
    for (const auto range : f.allowed) {
      const auto begin = reinterpret_cast<std::uintptr_t>(range.data());
      if (address >= begin && address - begin <= range.size() && size <= range.size() - (address - begin)) {
        std::memcpy(dest, source, size); return true;
      }
    }
    return false;
  }
  static bool Frame(void *context) noexcept {
    auto &f = *static_cast<Fixture *>(context); ++f.frame_calls;
    if (f.frame_calls == 2) {
      if (f.clone_combat_between_passes) f.combat_root = f.clone.data();
      if (f.mutate_generation) f.combat.Put(8, std::bit_cast<std::int32_t>(0x85000000U));
    }
    return f.frame_calls != f.fail_frame_call;
  }
  bool Read(BattleCandidateObservationV1 &out) {
    return ReadBattleCandidateV1(bindings, unit_id, actor_id, out, {this,Copy,Frame});
  }
};
int failed = 0;
void Check(bool condition, const char *name) {
  if (!condition) { std::fprintf(stderr, "FAIL: %s\n", name); ++failed; }
}

}
namespace {
struct ActualSourceFixture {
  std::size_t calls = 0;
  bool drift_epoch = false, drift_core = false, paused = true, tls = true, fail = false;
  static bool Capture(void *context, BattleCandidateActualSourceStampV1 &out) noexcept {
    auto &f = *static_cast<ActualSourceFixture *>(context); ++f.calls;
    out = {}; if (f.fail) return false;
    out.core.clock = {123456, f.drift_core && f.calls == 2 ? 3 : 2, f.paused};
    out.core.local_player_id = 4; out.core.map_ready = true;
    out.core.has_played_character = true; out.core.played_character_alive = true;
    out.core.played_character_id = Fixture::actor_id;
    auto &stamp = out.application_main;
    stamp.date_raw = 123456; stamp.paused = f.paused;
    stamp.pump_epoch = f.drift_epoch && f.calls == 2 ? 8 : 7;
    stamp.thread_id = 11; stamp.game_state = 0x1000; stamp.jomini_state = 0x2000;
    stamp.tls_initialized_flag_address = 0x3000; stamp.tls_initialized = 1;
    stamp.tls_context = 0x4000; stamp.tls_main_thread_marker = f.tls ? 1 : 0;
    return true;
  }
};
constexpr auto kUnavailable = "{\"candidate_status\":\"unavailable\"}";
bool Produce(Fixture &f, BattleCandidateProducedLeafV1 &out,
    BattleCandidateActualSourceAccessV1 stamp = {}) {
  return ReadBattleCandidateProducedLeafV1(f.bindings, Fixture::unit_id, Fixture::actor_id,
      out, {&f,Fixture::Copy,Fixture::Frame}, stamp);
}
void ProducedUnavailable(Fixture &f, ActualSourceFixture &stamp, const char *label) {
  BattleCandidateProducedLeafV1 out{};
  Check(!Produce(f, out, {&stamp,ActualSourceFixture::Capture}) &&
      SerializeBattleCandidateLeafV1(out) == kUnavailable && !out.actual_source_stamp, label);
}
}
int main() {
  using namespace xar::ck3_1210;
  std::vector<std::pair<std::string,std::string>> cases;
  { Fixture f; f.bindings = BindBattleCandidateImageV1(0x140000000ULL, "old");
    BattleCandidateProducedLeafV1 out{};
    Check(!Produce(f,out) && f.copy_calls == 0, "wrong SHA cannot produce a source leaf");
    const auto leaf = SerializeBattleCandidateLeafV1(out);
    Check(leaf == kUnavailable, "canonical unavailable has no IDs");
    cases.emplace_back("unavailable",leaf); }
  { Fixture f; f.army.Put(0x128,std::int32_t{-1}); f.combat_root = nullptr;
    BattleCandidateProducedLeafV1 out{};
    Check(Produce(f,out) && !out.actual_source_stamp, "optional actual stamp remains absent");
    const auto leaf = SerializeBattleCandidateLeafV1(out);
    Check(leaf == "{\"candidate_status\":\"not_referenced\",\"subject_public_cunit_id\":-2130706432,\"source_native_carmy_id\":-2113929216,\"candidate_combat_id\":null}",
        "native not-referenced formatter strict union");
    cases.emplace_back("not_referenced",leaf); }
  { Fixture f; f.unit.Put(0x10,std::int32_t{0}); f.unit.Put(0x174,std::int32_t{0});
    f.unit.Put(0x178,std::int32_t{0}); f.army.Put(0x10,std::int32_t{0});
    f.army.Put(0x124,std::int32_t{0}); f.army.Put(0x128,std::int32_t{0});
    f.combat.Put(8,std::int32_t{0}); BattleCandidateProducedLeafV1 out{};
    Check(ReadBattleCandidateProducedLeafV1(f.bindings,0,0,out,{&f,Fixture::Copy,Fixture::Frame}),
        "zero identities flow through real resolver");
    const auto leaf = SerializeBattleCandidateLeafV1(out);
    Check(leaf == "{\"candidate_status\":\"identity_candidate\",\"subject_public_cunit_id\":0,\"source_native_carmy_id\":0,\"candidate_combat_id\":0}", "zero identity formatter");
    cases.emplace_back("identity_zero",leaf); }
  { Fixture f; BattleCandidateProducedLeafV1 out{};
    Check(Produce(f,out), "highbit identities flow through real resolver");
    const auto leaf = SerializeBattleCandidateLeafV1(out);
    Check(leaf == "{\"candidate_status\":\"identity_candidate\",\"subject_public_cunit_id\":-2130706432,\"source_native_carmy_id\":-2113929216,\"candidate_combat_id\":-2097152000}", "signed identity formatter");
    cases.emplace_back("identity_highbit",leaf); }
  { Fixture f; ActualSourceFixture stamp; BattleCandidateProducedLeafV1 out{};
    Check(Produce(f,out,{&stamp,ActualSourceFixture::Capture}) && stamp.calls == 2 &&
        out.actual_source_stamp && out.actual_source_stamp->application_main.pump_epoch == 7,
        "actual stamp reserve captures callback values before and after");
    const auto leaf = SerializeBattleCandidateLeafV1(out);
    Check(leaf.find("\"stamp\":") == std::string::npos && leaf.find("\"date\":") == std::string::npos &&
        leaf.find("\"ready\":") == std::string::npos && leaf.find("\"available\"") == std::string::npos,
        "leaf never claims observed frame or action qualification"); }
  { Fixture f; ActualSourceFixture stamp; f.fail_frame_call = 1;
    ProducedUnavailable(f,stamp,"custody refused before source capture");
    Check(stamp.calls == 0 && f.copy_calls == 0,"no capture or read without custody"); }
  { Fixture f; ActualSourceFixture stamp; stamp.drift_epoch = true;
    ProducedUnavailable(f,stamp,"actual owner stamp drift invalidates source"); }
  { Fixture f; ActualSourceFixture stamp; stamp.drift_core = true;
    ProducedUnavailable(f,stamp,"actual Core prefix drift invalidates source"); }
  { Fixture f; ActualSourceFixture stamp; stamp.paused = false;
    ProducedUnavailable(f,stamp,"unpaused actual prefix rejected"); Check(f.copy_calls == 0,"no memory read before valid actual prefix"); }
  { Fixture f; ActualSourceFixture stamp; stamp.tls = false;
    ProducedUnavailable(f,stamp,"missing actual TLS marker rejected"); }
  { Fixture f; ActualSourceFixture stamp; stamp.fail = true;
    ProducedUnavailable(f,stamp,"failed actual stamp callback rejected"); }
  { Fixture f; f.combat.Put(8,std::bit_cast<std::int32_t>(0x85000000U));
    BattleCandidateProducedLeafV1 out{};
    Check(!Produce(f,out) && SerializeBattleCandidateLeafV1(out) == kUnavailable,
        "stale generation cannot become not-referenced or candidate"); }
  { Fixture f; BattleCandidateProducedLeafV1 out{}; Check(Produce(f,out),"malformed DTO fixture source");
    out.candidate.candidate_combat_id.reset();
    Check(SerializeBattleCandidateLeafV1(out) == kUnavailable,"identity needs CombatID");
    out.candidate.candidate_combat_id = -1;
    Check(SerializeBattleCandidateLeafV1(out) == kUnavailable,"identity excludes sentinel only");
    out.candidate.candidate_combat_id = 0; out.candidate.status = BattleCandidateStatusV1::not_referenced;
    Check(SerializeBattleCandidateLeafV1(out) == kUnavailable,"not-referenced forbids CombatID");
    out.candidate.candidate_combat_id.reset(); out.exact_source_admitted = false;
    Check(SerializeBattleCandidateLeafV1(out) == kUnavailable,"exact source gate cannot be discarded");
    out.exact_source_admitted = true; out.candidate.status = static_cast<BattleCandidateStatusV1>(99);
    Check(SerializeBattleCandidateLeafV1(out) == kUnavailable,"unknown C++ status fails closed"); }
  if (failed != 0) return 1;
  // This is fixture-only evidence. It can never be relabelled as actual/live.
  std::cout << "{\"schema\":\"xar.ck3.battle-identity-fixture.1210.v1\",\"actual\":false,\"executable_sha256\":\""
      << kExecutableSha256 << "\",\"cases\":[";
  for (std::size_t i = 0; i < cases.size(); ++i) {
    if (i != 0) std::cout << ',';
    std::cout << "{\"name\":\"" << cases[i].first << "\",\"candidate\":" << cases[i].second << '}';
  }
  std::cout << "]}\n";
  return 0;
}
