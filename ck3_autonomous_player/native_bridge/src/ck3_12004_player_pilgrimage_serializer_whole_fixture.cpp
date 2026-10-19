#include "ck3_12004_player_pilgrimage_activities_private_v1.hpp"
#include "xar_bridge/activity_hosted_identity_v1.hpp"
#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/ck3_12004_activity_migration_v1.hpp"

#include <array>
#include <cstdio>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <map>
#include <stdexcept>
#include <string>

// Real generic reader and real production serializer, owned memory only.
// The command_result envelope is fixture-owned; router dispatch is tested by
// ck3_12002_activity_feast_router_test. No native game/executor is invoked.
namespace {
namespace b = xar::bridge;
namespace n = xar::ck3_12002;
namespace actual = xar::ck3_12004;
constexpr std::uintptr_t module = 0x140000000ULL, root = 0x200000000ULL;
constexpr std::uintptr_t world = 0x300000000ULL, chunks = 0x400000000ULL;
constexpr std::uintptr_t chunk = 0x410000000ULL, index_table = 0x420000000ULL;
constexpr std::uintptr_t storage = 0x430000000ULL, characters = 0x440000000ULL;
constexpr std::uintptr_t actor = 0x450000000ULL, manager = world + 0x22CB8;
constexpr std::int32_t actor_id = 29829;
constexpr std::uint64_t revision = 19;
constexpr std::int64_t date = 53220000;
void Require(bool value, const char *message) {
  if (!value) throw std::runtime_error(message);
}
struct Memory {
  std::map<std::uintptr_t, std::uint8_t> bytes;
  b::ActivityHostedIdentityFrameV1 frame{revision, date, actor_id, true, true, true, true};
  bool changed = false;
  int reads = 0;
  void PutBytes(std::uintptr_t at, const void *source, std::size_t size) {
    const auto *data = static_cast<const std::uint8_t *>(source);
    for (std::size_t i = 0; i < size; ++i) bytes[at + i] = data[i];
  }
  template<class T> void Put(std::uintptr_t at, const T &value) { PutBytes(at, &value, sizeof(value)); }
  static bool Read(void *opaque, std::uintptr_t at, void *out, std::size_t size) noexcept {
    auto &m = *static_cast<Memory *>(opaque);
    auto *data = static_cast<std::uint8_t *>(out);
    for (std::size_t i = 0; i < size; ++i) {
      const auto found = m.bytes.find(at + i);
      if (found == m.bytes.end()) return false;
      data[i] = found->second;
    }
    return true;
  }
  static bool Frame(void *opaque, b::ActivityHostedIdentityFrameV1 &out) noexcept {
    auto &m = *static_cast<Memory *>(opaque); out = m.frame;
    if (++m.reads >= 2 && m.changed) ++out.date_raw;
    return true;
  }
  b::ActivityHostedIdentityEnvironmentV1 Environment() {
    return {true, actual::kExecutableSha256, module, this, Read, Frame};
  }
  void Type(std::uint32_t slot, std::string_view key) {
    const auto type = 0x460000000ULL + slot * 0x100;
    const auto text = 0x470000000ULL + slot * 0x100;
    Put(chunk + slot * 0x628 + 0x3A0, type);
    Put(type, module + b::Activity12004RvaV1(actual::kExecutableSha256, 0x48BFE50));
    Put(type + 0x28, static_cast<std::uint64_t>(key.size()));
    Put(type + 0x30, std::uint64_t{63});
    Put(type + 0x18, text); PutBytes(text, key.data(), key.size());
  }
  Memory() {
    const std::array<std::pair<std::uintptr_t, std::array<std::uint8_t,7>>,3> code{{
      {0x2ADD8EE,{0x49,0x8D,0xBF,0xB8,0x2C,0x02,0x00}},
      {0x29C2E97,{0x48,0x81,0xC3,0x28,0x06,0x00,0x00}},
      {0x23F0195,{0x41,0x89,0x87,0xA8,0x03,0x00,0x00}}}};
    for (const auto &[rva, data] : code)
      PutBytes(module + b::Activity12004RvaV1(actual::kExecutableSha256, rva), data.data(), data.size());
    Put(module + 0x5C68C50, root); Put(root + 0xA0, world);
    Put(module + 0x5C67568, storage); Put(module + 0x5C67570, std::uintptr_t{0});
    Put(storage + 0x20, characters); Put(storage + 0x2C, std::uint32_t{30000});
    Put(characters + actor_id * 16 + 8, actor); Put(actor + 0x18, std::uint32_t{actor_id});
    Put(manager + 0x10, std::uint8_t{1}); Put(manager + 0x60, std::uint8_t{0});
    Put(manager + 0x61, std::uint8_t{0}); Put(manager + 0x20, chunks);
    Put(manager + 0x2C, std::uint32_t{1}); Put(manager + 0x38, index_table);
    Put(manager + 0x44, std::uint32_t{16}); Put(manager + 0x50, std::int32_t{9});
    Put(manager + 0x54, std::uint32_t{3}); Put(chunks, chunk);
    for (std::uint32_t i = 0; i <= 9; ++i) Put(index_table + i * 16 + 8, std::uintptr_t{0});
    for (const auto slot : {1U, 5U, 9U}) {
      const auto activity = chunk + slot * 0x628;
      Put(index_table + slot * 16 + 8, activity);
      Put(activity, module + b::Activity12004RvaV1(actual::kExecutableSha256, 0x472E130));
      Put(activity + 0x08, (slot == 1 ? 0x01000000U : slot == 5 ? 0x02000000U : 0x03000000U) | slot);
      Put(activity + 0x3A8, actor_id); Put(activity + 0x421, std::uint8_t{slot == 5});
      Put(activity + 0x422, std::uint8_t{slot == 9});
      Type(slot, slot == 1 ? "activity_feast" : "activity_pilgrimage");
    }
    // Slot 5 deliberately has no completion stamp. Slot 9 has observed zero.
    Put(chunk + 9 * 0x628 + 0x408, std::uint64_t{0});
  }
};
n::PlayerPilgrimageActivitiesPrivateQuery12004V1 Query(Memory &memory) {
  n::PlayerPilgrimageActivitiesPrivateQuery12004V1 q{};
  q.completed = true;
  q.executable_sha256 = actual::kExecutableSha256; q.expected_revision = revision;
  q.expected_snapshot.date_raw = date; q.expected_snapshot.played_character_id = actor_id;
  q.pilgrimage_identities = b::ReadActivityHostedIdentityV1(memory.Environment(), memory.frame);
  Require(q.pilgrimage_identities.status == b::ActivityHostedIdentityStatusV1::observed,
          "production generic reader rejected owned fixture");
  return q;
}
void Save(const std::filesystem::path &directory, const char *name,
          const n::PlayerPilgrimageActivitiesPrivateQuery12004V1 &q) {
  const auto native = n::SerializePlayerPilgrimageActivitiesPrivate12004V1(q);
  Require(!native.empty(), "production serializer returned empty for observed fixture");
  std::ofstream out(directory / (std::string(name) + ".json"));
  out << "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\"fixture-pilgrimage\",\"ok\":true,\"result\":{"
      "\"step\":\"query-player-pilgrimage-activities-v1-private\",\"accepted\":true,\"status\":\"available\","
      "\"private_build\":true,\"read_only\":true,\"advertised\":false,\"player_pilgrimage_activities\":"
      << native << ",\"backend_id\":\"native-headless\"}}\n";
  Require(bool(out), "could not write whole packet");
}
} // namespace
int main(int argc, char **argv) {
  try {
    Require(argc == 2, "usage: fixture <new-output-directory>");
    const std::filesystem::path directory(argv[1]);
    Require(!std::filesystem::exists(directory), "output directory must be new");
    std::filesystem::create_directories(directory);
    Memory mixed; auto q = Query(mixed); Save(directory, "mixed-stamp-availability", q);
    Require(q.pilgrimage_identities.hosted_count == 3, "generic reader must retain non-target type");
    Memory only_other; only_other.Type(5, "activity_feast"); only_other.Type(9, "activity_feast");
    Save(directory, "non-pilgrimage-filtered", Query(only_other));
    Memory empty; empty.Put(manager + 0x50, std::int32_t{-1}); empty.Put(manager + 0x54, std::uint32_t{0});
    Save(directory, "empty-hosted", Query(empty));
    Memory generation; generation.Put(chunk + 5 * 0x628 + 0x08, std::uint32_t{0xFE000005});
    Save(directory, "full-generation", Query(generation));
    auto invalid = q; invalid.executable_sha256 = "wrong-build";
    Require(n::SerializePlayerPilgrimageActivitiesPrivate12004V1(invalid).empty(), "serializer must reject non-.4");
    invalid = q; invalid.expected_snapshot.played_character_id++;
    Require(n::SerializePlayerPilgrimageActivitiesPrivate12004V1(invalid).empty(), "serializer must reject wrong host");
    invalid = q; invalid.completed = false;
    Require(n::SerializePlayerPilgrimageActivitiesPrivate12004V1(invalid).empty(), "serializer must reject incomplete");
    Memory malformed; malformed.Put(chunk + 5 * 0x628 + 0x421, std::uint8_t{2});
    Require(b::ReadActivityHostedIdentityV1(malformed.Environment(), malformed.frame).status ==
        b::ActivityHostedIdentityStatusV1::activity_identity_unavailable, "invalid terminal byte must be RED");
    Memory stale; stale.changed = true;
    Require(b::ReadActivityHostedIdentityV1(stale.Environment(), stale.frame).status ==
        b::ActivityHostedIdentityStatusV1::snapshot_changed, "changed reader frame must be RED");
    std::ofstream manifest(directory / "PROVENANCE.json");
    manifest << "{\"production_reader\":\"ReadActivityHostedIdentityV1\","
        "\"production_serializer\":\"SerializePlayerPilgrimageActivitiesPrivate12004V1\","
        "\"memory\":\"owned-synthetic-exact4-layout\",\"envelope\":\"fixture-owned\","
        "\"original_engine_executed\":false,\"live_qualified\":false,\"packet_count\":4}\n";
    Require(bool(manifest), "manifest write failed");
    std::puts("PASS: real generic reader and production pilgrimage serializer; four owned-memory whole packets; no CK3/live qualification");
    return 0;
  } catch (const std::exception &error) { std::cerr << error.what() << '\n'; return 1; }
}
