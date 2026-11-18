// SOURCE_PREPARED / NOTRUN. Owned-memory producer -> actual serializer cases.
#include "xar_bridge/ck3_1210_siege_read_only_partial_v1.hpp"
#include <array>
#include <cstddef>
#include <cstring>
#include <functional>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <vector>

namespace {
namespace p = xar::ck3_1210::siege_read_only_partial_v1;
constexpr std::uintptr_t kBase = 0x140000000ULL;
constexpr auto kActor = static_cast<std::int32_t>(0xFE000001U);
constexpr auto kSiege = static_cast<std::int32_t>(0x81000001U);
void Need(bool value, const char *message) { if (!value) throw std::runtime_error(message); }
template <class B> std::uintptr_t Address(B &b) { return reinterpret_cast<std::uintptr_t>(b.data()); }
template <class B, class T> void Put(B &b, std::size_t off, T v) {
  Need(off <= b.size() && sizeof v <= b.size() - off, "owned byte bound");
  std::memcpy(b.data() + off, &v, sizeof v);
}
struct Region { std::uintptr_t address; const std::byte *data; std::size_t size; };
struct Fixture {
  std::array<std::byte, 0xA8> game{};
  std::array<std::byte, 0x28> jomini{};
  std::array<std::byte, 0x1D8> actor{};
  std::array<std::byte, 0x30> character_store{};
  std::array<std::byte, 0x20> character_slots{}, provinces{}, siege_slots{};
  std::array<std::byte, 0xB28> province{};
  std::array<std::byte, 0x470> siege{};
  std::array<std::byte, 0x58> registry{}, registry_replacement{};
  std::vector<std::byte> data = std::vector<std::byte>(0x3F160);
  std::array<std::array<std::byte, 8>, 4> globals{};
  std::vector<Region> regions;
  p::Bindings bindings = p::BindImage(kBase, p::kExecutableSha256);
  p::Request request{{(std::numeric_limits<std::uint64_t>::max)(), 53177016,
      9007199254740993ULL, kActor}, 1};
  p::FrameEvidence frame{};
  std::size_t copies = 0, frame_reads = 0;
  std::function<void(Fixture &)> before_second;
  template <class B> void Add(B &b) { regions.push_back({Address(b), b.data(), b.size()}); }
  Fixture() {
    Put(globals[0], 0, Address(game)); Put(globals[1], 0, Address(jomini));
    Put(globals[2], 0, Address(character_store)); Put(globals[3], 0, Address(registry));
    Put(game, 8, request.frame.game_date_raw); Put(game, 0x70, std::int32_t{1});
    Put(game, 0xA0, Address(data)); Put(jomini, 0x20, std::uint8_t{1});
    Put(character_store, 0x20, Address(character_slots)); Put(character_store, 0x2C, std::int32_t{2});
    Put(character_slots, 0x18, Address(actor)); Put(actor, 0x18, kActor);
    Put(actor, 0x1C, std::uint32_t{0x43686172});
    Put(data, 0x4140, Address(provinces)); Put(data, 0x414C, std::int32_t{2});
    Put(data, 0x3F130, kBase + 0x4E4B000); Put(data, 0x3F158, Address(registry));
    Put(provinces, 8, Address(province)); Put(province, 0x10, std::int32_t{1});
    Put(province, 0xB24, std::uint32_t{0x50726F76}); Put(province, 0xA20, kSiege);
    Put(registry, 0, kBase + 0x4E4AE18); Put(registry, 0x20, Address(siege_slots));
    Put(registry, 0x2C, std::int32_t{2}); Put(siege_slots, 0x18, Address(siege));
    Put(siege, 0, kBase + 0x4E4AF40); Put(siege, 8, kSiege);
    Put(siege, 0xC, std::uint32_t{0x53696765}); Put(siege, 0x210, Address(province));
    Put(siege, 0x3F0, (std::numeric_limits<std::int64_t>::max)());
    registry_replacement = registry;
    Add(game); Add(jomini); Add(actor); Add(character_store); Add(character_slots);
    Add(data); Add(provinces); Add(province); Add(registry); Add(registry_replacement);
    Add(siege_slots); Add(siege);
    constexpr std::array<std::uintptr_t, 4> offsets{0x68B1D58, 0x68B3800, 0x68A8628, 0x6A67198};
    for (std::size_t i = 0; i < offsets.size(); ++i)
      regions.push_back({kBase + offsets[i], globals[i].data(), globals[i].size()});
    frame = {request.frame, 7, Address(game), Address(jomini), Address(actor), 0, true, true, true, true};
  }
  static bool Copy(void *context, const void *from, void *to, std::size_t n) noexcept {
    auto &f = *static_cast<Fixture *>(context); ++f.copies;
    const auto raw = reinterpret_cast<std::uintptr_t>(from);
    for (const auto &r : f.regions) {
      if (raw >= r.address && raw - r.address <= r.size && n <= r.size - (raw - r.address)) {
        std::memcpy(to, r.data + (raw - r.address), n); return true;
      }
    }
    return false;
  }
  static bool Frame(void *context, p::FrameEvidence &out) noexcept {
    auto &f = *static_cast<Fixture *>(context);
    try {
      if (++f.frame_reads == 3 && f.before_second) f.before_second(f);
      out = f.frame; return true;
    } catch (...) { return false; }
  }
  bool Read(p::Captured &out) { return p::CopyTarget(bindings, request, out, {this, Copy, Frame}); }
};
void Unknown(Fixture &f) {
  p::Captured out; Need(f.Read(out), "valid source for UNKNOWN was rejected");
  Need(out.source_frame_verified && std::holds_alternative<p::UnknownTarget>(out.target),
      "target failure leaked values");
  std::string json; Need(p::AppendJson(out, json), "verified-source UNKNOWN did not serialize");
  Need(json.find("\"target\":{\"state\":\"UNKNOWN\"}") != std::string::npos, "UNKNOWN packet lost state");
}
std::string IdentityPacket() {
  Fixture f; p::Captured out; Need(f.Read(out), "identity capture failed");
  const auto *target = std::get_if<p::IdentityOnlyTarget>(&out.target);
  Need(target && target->province.validated_province_count == 2 && target->siege_full_id == kSiege,
      "identity/count/full generation changed");
  std::string json; Need(p::AppendJson(out, json), "identity serializer failed");
  const std::string expected =
      "{\"schema\":\"ck3.1210.siege_read_only_partial.v1\",\"source_frame\":{\"game_version\":\"1.21.0\","
      "\"steam_build_id\":\"26622941\",\"executable_sha256\":\"2F2B236A16223891C2DA8B167F5F3738D2AE3E6D69DE1B4FBE190A5402998ACC\","
      "\"native_revision\":\"18446744073709551615\",\"game_date_raw\":53177016,\"query_sequence\":\"9007199254740993\","
      "\"played_character_id\":-33554431},\"requested_province_id\":1,\"partial\":true,\"full_snapshot_available\":false,"
      "\"live_qualified\":false,\"target\":{\"state\":\"IDENTITY_ONLY\",\"province_id\":1,\"validated_province_count\":2,"
      "\"siege_full_id\":-2130706431,\"current_work_raw\":\"9223372036854775807\"},"
      "\"holder\":{\"state\":\"UNAVAILABLE\",\"reason\":\"holder_getter_unclosed\"},"
      "\"subrealm\":{\"state\":\"UNAVAILABLE\",\"reason\":\"subrealm_getter_unclosed\"},"
      "\"progress\":{\"state\":\"UNAVAILABLE\",\"reason\":\"progress_dependency_graph_unclosed\"}}";
  Need(json == expected, "exact serializer packet differs");
  return json;
}
void NoLeaf(Fixture &f) {
  p::Captured out; Need(!f.Read(out), "invalid source/custody was admitted");
  Need(!out.source_frame_verified && std::holds_alternative<p::UnknownTarget>(out.target),
      "source failure leaked target or source qualification");
  std::string json = "preserve";
  Need(!p::AppendJson(out, json) && json == "preserve", "invalid source emitted leaf or partial output");
}
void Cases() {
  { Fixture f; Put(f.province, 0xA20, std::int32_t{-1}); p::Captured out;
    Need(f.Read(out) && std::holds_alternative<p::AbsentTarget>(out.target), "-1 absence lost"); }
  { Fixture f; Put(f.siege, 0x3F0, std::int64_t{0}); p::Captured out;
    Need(f.Read(out), "zero work lost"); std::string json; Need(p::AppendJson(out, json), "zero serializer");
    Need(json.find("\"current_work_raw\":\"0\"") != std::string::npos &&
        json.find("\"progress\":{\"state\":\"UNAVAILABLE\"") != std::string::npos,
        "zero work promoted progress"); }
  { Fixture f; Put(f.siege, 8, std::int32_t{0x02000001}); Unknown(f); }
  { Fixture f; Put(f.siege, 0xC, std::uint32_t{0x446C7464}); Unknown(f); }
  { Fixture f; Put(f.siege_slots, 0x18, std::uintptr_t{0}); Unknown(f); }
  { Fixture f; Put(f.siege, 0x210, Address(f.game)); Unknown(f); }
  { Fixture f; Put(f.data, 0x3F130, std::uintptr_t{0}); Unknown(f); }
  { Fixture f; Put(f.globals[3], 0, Address(f.registry_replacement)); Unknown(f); }
  { Fixture f; Put(f.registry, 0, std::uintptr_t{0}); Unknown(f); }
  { Fixture f; Put(f.data, 0x414C, std::int32_t{1}); Unknown(f); }
  { Fixture f; Put(f.data, 0x414C, p::kProvinceTableBound + 1); Unknown(f); }
  { Fixture f; Put(f.province, 0x10, std::int32_t{2}); Unknown(f); }
  { Fixture f; Put(f.province, 0xB24, std::uint32_t{0}); Unknown(f); }
  { Fixture f; Put(f.siege, 0x3F0, std::int64_t{-1}); Unknown(f); }
  { Fixture f; Put(f.actor, 0x18, std::int32_t{1}); NoLeaf(f); }
  { Fixture f; Put(f.actor, 0x1C, std::uint32_t{0}); NoLeaf(f); }
  { Fixture f; Put(f.actor, 0x1D0, Address(f.siege)); NoLeaf(f); }
  { Fixture f; Put(f.character_slots, 0x18, std::uintptr_t{0}); NoLeaf(f); }
  { Fixture f; Put(f.game, 8, std::int32_t{53177040}); NoLeaf(f); }
  { Fixture f; Put(f.jomini, 0x20, std::uint8_t{0}); NoLeaf(f); }
  { Fixture f; f.frame.main_scope_held = false; NoLeaf(f); Need(f.copies == 0, "unheld scope read"); }
  { Fixture f; f.frame.map_ready = false; NoLeaf(f); }
  { Fixture f; f.frame.scope_epoch = 0; NoLeaf(f); }
  { Fixture f; ++f.frame.source.query_sequence; NoLeaf(f); }
  { Fixture f; ++f.frame.source.native_revision; NoLeaf(f); }
  { Fixture f; f.frame.source.played_character_id = 1; NoLeaf(f); }
  { Fixture f; f.request.frame.native_revision = 0; NoLeaf(f); }
  { Fixture f; f.request.frame.played_character_id = -1; NoLeaf(f); }
  { Fixture f; f.bindings = p::BindImage(kBase, "wrong"); NoLeaf(f);
    Need(f.copies == 0 && f.frame_reads == 0, "wrong build read"); }
  { Fixture f; f.bindings = p::BindImage((std::numeric_limits<std::uintptr_t>::max)(), p::kExecutableSha256);
    NoLeaf(f); Need(f.copies == 0, "overflow read"); }
  { Fixture f; f.before_second = [](Fixture &v) { ++v.frame.scope_epoch; }; NoLeaf(f); }
  { Fixture f; f.before_second = [](Fixture &v) {
      Put(v.data, 0x3F158, Address(v.registry_replacement));
      Put(v.globals[3], 0, Address(v.registry_replacement)); }; NoLeaf(f); }
  { Fixture f; f.before_second = [](Fixture &v) { Put(v.siege, 0x3F0, std::int64_t{1}); }; NoLeaf(f); }
  { Fixture f; f.before_second = [](Fixture &v) { Put(v.province, 0xA20, std::int32_t{-1}); }; NoLeaf(f); }
  { Fixture f; f.before_second = [](Fixture &v) { Put(v.actor, 0x18, std::int32_t{1}); }; NoLeaf(f); }
  { Fixture f; p::Captured out; out.request = f.request;
    Need(p::CopyTarget(f.bindings, out.request, out, {&f, Fixture::Copy, Fixture::Frame}),
        "input/output request alias lost original frame"); }
  { Fixture f; p::Captured out; Need(f.Read(out), "serializer guard setup");
    out.target = p::IdentityOnlyTarget{{1, 2}, -1, 0}; std::string json = "preserve";
    Need(!p::AppendJson(out, json) && json == "preserve", "serialized sentinel active target");
    out.target = p::IdentityOnlyTarget{{1, 1}, kSiege, 0};
    Need(!p::AppendJson(out, json) && json == "preserve", "serialized invalid dynamic count");
    out.target = p::IdentityOnlyTarget{{2, 3}, kSiege, 0};
    Need(!p::AppendJson(out, json) && json == "preserve", "serialized substituted Province");
    out.target = p::IdentityOnlyTarget{{1, 2}, kSiege, -1};
    Need(!p::AppendJson(out, json) && json == "preserve", "serialized negative work"); }
}
std::string AbsentPacket() {
  Fixture f; Put(f.province, 0xA20, std::int32_t{-1}); p::Captured out;
  Need(f.Read(out), "absent capture failed"); std::string json;
  Need(p::AppendJson(out, json), "absent serializer failed"); return json;
}
std::string UnknownPacket() {
  Fixture f; Put(f.siege, 8, std::int32_t{0x02000001}); p::Captured out;
  Need(f.Read(out), "UNKNOWN source capture failed"); std::string json;
  Need(p::AppendJson(out, json), "UNKNOWN serializer failed"); return json;
}
} // namespace
int main() {
  try {
    Cases();
    // Future Native-owner execution may redirect these actual serializer bytes
    // for Java's strict codec. No artifact is claimed before that execution.
    std::cout << IdentityPacket() << '\n' << AbsentPacket() << '\n' << UnknownPacket() << '\n';
    return 0;
  } catch (const std::exception &e) { std::cerr << e.what() << '\n'; return 1; }
}
