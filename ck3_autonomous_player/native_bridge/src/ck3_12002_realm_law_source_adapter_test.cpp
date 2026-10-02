#include "xar_bridge/ck3_12002_realm_law_source_adapter.hpp"
#include "xar_bridge/ck3_12002_nonwar_realm.hpp"

#if defined(NDEBUG)
#undef NDEBUG
#endif

#include <cassert>
#include <cstring>
#include <iostream>
#include <map>
#include <memory>
#include <string>
#include <vector>

using namespace xar::bridge;
using namespace xar::ck3_12002;
namespace law = xar::ck3_12002::private_law;
namespace {
constexpr std::uintptr_t base = 0x140000000, actor = 0x71000000,
    land = 0x71100000, resource = 0x71200000, primary = 0x71300000,
    secondary = 0x71400000, char_storage = 0x71500000,
    char_slots = 0x71600000, title_storage = 0x71700000,
    title_slots = 0x71800000, law_db = 0x71900000,
    crown = 0x71A00000, succession = 0x71B00000;
constexpr std::int32_t actor_id = 0x01000001, first_id = 0x02000002,
    second_id = 0x03000003, primary_id = 0x04000005,
    secondary_id = 0x05000006;
constexpr std::string_view manifest =
    "1111111111111111111111111111111111111111111111111111111111111111";

// Exact UTF-8 bytes from Murchad's saved 1.20.0.3 final terms (actor 31853,
// date 53328360). Fixture object identities remain synthetic; no live mutation.
constexpr std::string_view murchad_ca0_reason = "\x15\x68\x69\x67\x68\x20\xe5\xbd\x93\xe5\x89\x8d\xe6\xb3\x95\xe5\xbe\x8b\x15\x21";
constexpr std::string_view murchad_ca2_reason = "\x15\x69\x6e\x64\x65\x6e\x74\x5f\x6e\x65\x77\x6c\x69\x6e\x65\x3a\x30\x20\x15\x21\x15\x69\x6e\x64\x65\x6e\x74\x5f\x6e\x65\x77\x6c"
    "\x69\x6e\x65\x3a\x36\x20\x16\x77\x61\x72\x6e\x69\x6e\x67\x5f\x69\x63\x6f\x6e\x21\x20\x15\x58\x20\xe4\xbd\xa0\x15\x62\x6f\x6c\x64"
    "\x20\xe6\xb2\xa1\x15\x21\xe6\x9c\x89\x15\x56\x3b\x20\x15\x54\x4f\x4f\x4c\x54\x49\x50\x3a\x4c\x41\x57\x2c\x63\x72\x6f\x77\x6e\x5f"
    "\x61\x75\x74\x68\x6f\x72\x69\x74\x79\x5f\x31\x20\x15\x4c\x3b\x20\xe6\x9c\x89\xe9\x99\x90\xe5\x90\x9b\xe6\x9d\x83\x15\x21\x15\x21"
    "\x15\x21\x15\x45\x3b\x20\x15\x54\x4f\x4f\x4c\x54\x49\x50\x3a\x47\x41\x4d\x45\x5f\x43\x4f\x4e\x43\x45\x50\x54\x2c\x6c\x61\x77\x20"
    "\xe6\xb3\x95\xe5\xbe\x8b\x15\x21\x15\x21\x15\x21\x15\x21\x15\x69\x6e\x64\x65\x6e\x74\x5f\x6e\x65\x77\x6c\x69\x6e\x65\x3a\x30\x20"
    "\x0a\x15\x21\x15\x69\x6e\x64\x65\x6e\x74\x5f\x6e\x65\x77\x6c\x69\x6e\x65\x3a\x36\x20\x16\x77\x61\x72\x6e\x69\x6e\x67\x5f\x69\x63"
    "\x6f\x6e\x21\x20\x15\x58\x20\x15\x4f\x4e\x43\x4c\x49\x43\x4b\x3a\x43\x55\x4c\x54\x55\x52\x45\x2c\x37\x35\x20\x15\x54\x4f\x4f\x4c"
    "\x54\x49\x50\x3a\x43\x55\x4c\x54\x55\x52\x45\x2c\x37\x35\x20\x15\x4c\x3b\x20\xe7\x88\xb1\xe5\xb0\x94\xe5\x85\xb0\x15\x21\x15\x21"
    "\x15\x21\x15\x45\x3b\x20\x15\x54\x4f\x4f\x4c\x54\x49\x50\x3a\x47\x41\x4d\x45\x5f\x43\x4f\x4e\x43\x45\x50\x54\x2c\x63\x75\x6c\x74"
    "\x75\x72\x65\x20\xe6\x96\x87\xe5\x8c\x96\x15\x21\x15\x21\x15\x62\x6f\x6c\x64\x20\xe6\xb2\xa1\xe6\x9c\x89\x15\x21\x15\x54\x4f\x4f"
    "\x4c\x54\x49\x50\x3a\x43\x55\x4c\x54\x55\x52\x45\x5f\x49\x4e\x4e\x4f\x56\x41\x54\x49\x4f\x4e\x2c\x37\x35\x2c\x32\x34\x20\x15\x4c"
    "\x3b\x20\xe5\xae\x97\xe5\xae\xa4\xe7\x89\xb9\xe6\x9d\x83\x15\x21\x15\x21\x15\x45\x3b\x20\x15\x54\x4f\x4f\x4c\x54\x49\x50\x3a\x47"
    "\x41\x4d\x45\x5f\x43\x4f\x4e\x43\x45\x50\x54\x2c\x69\x6e\x6e\x6f\x76\x61\x74\x69\x6f\x6e\x20\xe9\x9d\xa9\xe6\x96\xb0\x15\x21\x15"
    "\x21\x15\x21\x15\x21";
constexpr std::string_view murchad_ca3_reason = "\x15\x69\x6e\x64\x65\x6e\x74\x5f\x6e\x65\x77\x6c\x69\x6e\x65\x3a\x30\x20\x15\x21\x15\x69\x6e\x64\x65\x6e\x74\x5f\x6e\x65\x77\x6c"
    "\x69\x6e\x65\x3a\x36\x20\x16\x77\x61\x72\x6e\x69\x6e\x67\x5f\x69\x63\x6f\x6e\x21\x20\x15\x58\x20\xe4\xbd\xa0\x15\x62\x6f\x6c\x64"
    "\x20\xe6\xb2\xa1\x15\x21\xe6\x9c\x89\x15\x56\x3b\x20\x15\x54\x4f\x4f\x4c\x54\x49\x50\x3a\x4c\x41\x57\x2c\x63\x72\x6f\x77\x6e\x5f"
    "\x61\x75\x74\x68\x6f\x72\x69\x74\x79\x5f\x32\x20\x15\x4c\x3b\x20\xe9\xab\x98\xe5\x90\x9b\xe6\x9d\x83\x15\x21\x15\x21\x15\x21\x15"
    "\x45\x3b\x20\x15\x54\x4f\x4f\x4c\x54\x49\x50\x3a\x47\x41\x4d\x45\x5f\x43\x4f\x4e\x43\x45\x50\x54\x2c\x6c\x61\x77\x20\xe6\xb3\x95"
    "\xe5\xbe\x8b\x15\x21\x15\x21\x15\x21\x15\x21\x15\x69\x6e\x64\x65\x6e\x74\x5f\x6e\x65\x77\x6c\x69\x6e\x65\x3a\x30\x20\x0a\x15\x21"
    "\x15\x69\x6e\x64\x65\x6e\x74\x5f\x6e\x65\x77\x6c\x69\x6e\x65\x3a\x36\x20\x16\x77\x61\x72\x6e\x69\x6e\x67\x5f\x69\x63\x6f\x6e\x21"
    "\x20\x15\x58\x20\x15\x4f\x4e\x43\x4c\x49\x43\x4b\x3a\x43\x55\x4c\x54\x55\x52\x45\x2c\x37\x35\x20\x15\x54\x4f\x4f\x4c\x54\x49\x50"
    "\x3a\x43\x55\x4c\x54\x55\x52\x45\x2c\x37\x35\x20\x15\x4c\x3b\x20\xe7\x88\xb1\xe5\xb0\x94\xe5\x85\xb0\x15\x21\x15\x21\x15\x21\x15"
    "\x45\x3b\x20\x15\x54\x4f\x4f\x4c\x54\x49\x50\x3a\x47\x41\x4d\x45\x5f\x43\x4f\x4e\x43\x45\x50\x54\x2c\x63\x75\x6c\x74\x75\x72\x65"
    "\x20\xe6\x96\x87\xe5\x8c\x96\x15\x21\x15\x21\x15\x62\x6f\x6c\x64\x20\xe6\xb2\xa1\xe6\x9c\x89\x15\x21\x15\x54\x4f\x4f\x4c\x54\x49"
    "\x50\x3a\x43\x55\x4c\x54\x55\x52\x45\x5f\x49\x4e\x4e\x4f\x56\x41\x54\x49\x4f\x4e\x2c\x37\x35\x2c\x32\x34\x20\x15\x4c\x3b\x20\xe5"
    "\xae\x97\xe5\xae\xa4\xe7\x89\xb9\xe6\x9d\x83\x15\x21\x15\x21\x15\x45\x3b\x20\x15\x54\x4f\x4f\x4c\x54\x49\x50\x3a\x47\x41\x4d\x45"
    "\x5f\x43\x4f\x4e\x43\x45\x50\x54\x2c\x69\x6e\x6e\x6f\x76\x61\x74\x69\x6f\x6e\x20\xe9\x9d\xa9\xe6\x96\xb0\x15\x21\x15\x21\x15\x21"
    "\x15\x21";

struct Fixture;
Fixture *current = nullptr;
struct Fixture {
  std::map<std::uintptr_t, std::vector<unsigned char>> blocks;
  std::map<std::uintptr_t, int> laws;
  std::uintptr_t allocation = 0x73000000;
  std::uintptr_t active_slots = 0, primary_successors = 0;
  bool allowed = true;
  bool actual_murchad_reasons = false;
  std::array<std::string, 4> crown_reasons{};
  std::int64_t exotic_cost = 0;
  int queued = 0;
  RealmLawGovernanceFrameV1 frame{40, 40, 20, 53169072, true, true,
                                 actor_id, true, true};
  void Add(std::uintptr_t address, std::size_t size) { blocks[address].resize(size); }
  template <typename T> void Put(std::uintptr_t address, T value) {
    auto it = blocks.upper_bound(address); assert(it != blocks.begin()); --it;
    const auto offset = address - it->first;
    assert(offset + sizeof(value) <= it->second.size());
    std::memcpy(it->second.data() + offset, &value, sizeof(value));
  }
  std::uintptr_t Allocate(std::size_t size) {
    const auto address = allocation; allocation += 0x10000; Add(address, size); return address;
  }
  void Key(std::uintptr_t address, std::string_view key) {
    Put(address + 0x10, static_cast<std::uint64_t>(key.size()));
    Put(address + 0x18, std::uint64_t{key.size() <= 15 ? 15 : key.size()});
    auto bytes = key.size() <= 15 ? address : Allocate(key.size() + 1);
    if (key.size() > 15) Put(address, bytes);
    for (std::size_t i = 0; i < key.size(); ++i) Put(bytes + i, key[i]);
  }
  static bool Memory(void *opaque, std::uintptr_t address, void *out, std::size_t size) noexcept {
    auto &f = *static_cast<Fixture *>(opaque);
    auto it = f.blocks.upper_bound(address);
    if (it == f.blocks.begin()) return false;
    --it; const auto offset = address - it->first;
    if (offset + size > it->second.size()) return false;
    std::memcpy(out, it->second.data() + offset, size); return true;
  }
  static bool Frame(void *opaque, RealmLawGovernanceFrameV1 &out) noexcept {
    out = static_cast<Fixture *>(opaque)->frame; return true;
  }
  static bool Proof(void *opaque, RealmLawNativeRuntimeProofV1 &out) noexcept {
    const auto &f = *static_cast<Fixture *>(opaque); out = {};
    out.exact_build_admitted = true;
    AssignRealmLawNativeDigestV1(law::kRealmLawActiveCollectionExeSha25612002, out.executable_sha256);
    AssignRealmLawNativeDigestV1(manifest, out.signature_manifest_sha256);
    out.module_base = base; out.signatures_complete = true;
    out.signature_generation = 3; out.connection_generation = 4;
    out.proof_epoch = f.frame.proof_epoch;
    out.current_thread_id = out.application_main_thread_id = 5;
    out.paused = true; return true;
  }
  static void *Primary(void *character) { assert(character == reinterpret_cast<void *>(actor)); return reinterpret_cast<void *>(primary); }
  static bool Kind(const void *) { return true; }
  static bool Active(const void *, const void *definition) {
    const auto index = current->laws.at(reinterpret_cast<std::uintptr_t>(definition));
    std::uintptr_t first = 0;
    Memory(current, current->active_slots, &first, sizeof(first));
    return reinterpret_cast<std::uintptr_t>(definition) == first || index == 4;
  }
  static bool Final(const void *definition, const void *, void *) {
    if (current->actual_murchad_reasons) {
      return current->laws.at(reinterpret_cast<std::uintptr_t>(definition)) == 1;
    }
    return current->allowed;
  }
  static std::int64_t *Cost(std::int64_t *out, const void *block, std::uint32_t id) {
    assert(id == static_cast<std::uint32_t>(actor_id));
    std::fill_n(out, 10, std::int64_t{0});
    const auto index = current->laws.at(reinterpret_cast<std::uintptr_t>(block) - 0xC40);
    if (current->actual_murchad_reasons) {
      if (index == 1) out[1] = 14'600'000;
    } else if (index > 0 && index < 4) {
      out[1] = 20'000'000; out[3] = current->exotic_cost;
    }
    return out;
  }
  static bool Reason(const void *definition, const void *, void *sink) {
    const bool active = Active(nullptr, definition);
    const auto index = current->laws.at(reinterpret_cast<std::uintptr_t>(definition));
    const auto text = current->actual_murchad_reasons && index < 4
                            ? std::string_view(current->crown_reasons[index])
                            : active ? std::string_view("already_active")
                            : current->allowed ? std::string_view{}
                                               : std::string_view("engine_blocked");
    const auto size = static_cast<std::uint64_t>(text.size());
    const auto capacity = size <= 15 ? std::uint64_t{15} : size;
    if (capacity > 15) {
      const char *characters = text.data();
      std::memcpy(sink, &characters, sizeof(characters));
    } else {
      std::memcpy(sink, text.data(), text.size());
    }
    std::memcpy(static_cast<char *>(sink) + 0x10, &size, 8);
    std::memcpy(static_cast<char *>(sink) + 0x18, &capacity, 8);
    return !active && (current->actual_murchad_reasons ? index == 1 : current->allowed);
  }
  static void DestroyReason(void *) {}
  static void *Scope(void *out, const void *) { return out; }
  static bool Component(const void *, const void *) { return false; }
  static void DestroyScope(void *) {}
  static bool Validate(void *, const law::AddLawCommandV1 &) noexcept { return current->allowed; }
  static bool Clone(void *, const law::AddLawCommandV1 &command, void *&out) noexcept {
    out = new law::AddLawCommandV1(command); return true;
  }
  static bool Queue(void *opaque, std::uintptr_t, void *&owned, std::uint32_t flags) noexcept {
    assert(flags == 0x0E); ++static_cast<Fixture *>(opaque)->queued;
    delete static_cast<law::AddLawCommandV1 *>(owned); owned = nullptr; return true;
  }
  static void DestroyCommand(void *, void *owned) noexcept { delete static_cast<law::AddLawCommandV1 *>(owned); }

  Fixture() {
    current = this;
    for (const auto [address, size] : std::vector<std::pair<std::uintptr_t, std::size_t>>{
        {actor, 0x300}, {land, 0x300}, {resource, 0x300}, {primary, 0x400},
        {secondary, 0x400}, {char_storage, 0x40}, {char_slots, 16 * 16},
        {title_storage, 0x40}, {title_slots, 16 * 16}, {law_db, 0x80},
        {crown, 0x100}, {succession, 0x100}}) Add(address, size);
    auto Global = [&](std::uintptr_t rva, std::uintptr_t value) { Add(base + rva, 8); Put(base + rva, value); };
    Global(kCampaignRootCharacterStorageSlotRva, char_storage);
    Global(kCampaignRootCharacterFallbackSlotRva, 0);
    Global(kCampaignRootLandedTitleStorageSlotRva, title_storage);
    Global(kCampaignRootLandedTitleFallbackSlotRva, 0);
    Global(law::kLawGroupDatabaseSingletonRva12002, law_db);
    Put(actor + 0x18, actor_id); Put(actor + 0x1C0, land); Put(actor + 0x1B0, resource);
    Put(resource + 0x130, std::int64_t{50'000'000});
    Put(resource + 0x100, std::int64_t{8'000'000});
    Put(resource + 0x110, std::int64_t{7'000'000});
    Put(char_storage + 0x20, char_slots); Put(char_storage + 0x2C, std::int32_t{16});
    Put(char_slots + (actor_id & 0xFFFFFF) * 16 + 8, actor);
    for (const auto id : {first_id, second_id}) {
      auto character = Allocate(0x30); Put(character + 0x18, id);
      Put(char_slots + (id & 0xFFFFFF) * 16 + 8, character);
    }
    Put(title_storage + 0x20, title_slots); Put(title_storage + 0x2C, std::int32_t{16});
    Put(title_slots + (primary_id & 0xFFFFFF) * 16 + 8, primary);
    Put(title_slots + (secondary_id & 0xFFFFFF) * 16 + 8, secondary);
    auto held = Allocate(8); Put(held, primary_id); Put(held + 4, secondary_id);
    Put(land + 0x1E0, held); Put(land + 0x1E8, std::int32_t{2}); Put(land + 0x1EC, std::int32_t{2});
    primary_successors = Allocate(8); Put(primary_successors, first_id); Put(primary_successors + 4, second_id);
    auto secondary_successors = Allocate(8); Put(secondary_successors, second_id); Put(secondary_successors + 4, first_id);
    for (const auto [title, id, successors] : std::vector<std::tuple<std::uintptr_t, std::int32_t, std::uintptr_t>>{
        {primary, primary_id, primary_successors}, {secondary, secondary_id, secondary_successors}}) {
      Put(title + 0x10, id); Put(title + 0x128, actor_id); Put(title + 0x150, successors);
      Put(title + 0x158, std::int32_t{2}); Put(title + 0x15C, std::int32_t{2});
    }
    Key(crown + 0x18, "crown_authority"); Key(succession + 0x18, "succession_order_laws");
    auto groups = Allocate(16); Put(groups, crown); Put(groups + 8, succession);
    Put(law_db + 0x50, groups); Put(law_db + 0x5C, std::int32_t{2});
    auto crown_candidates = Allocate(32), succession_candidates = Allocate(32);
    Put(crown + 0x58, crown_candidates); Put(crown + 0x64, std::int32_t{4});
    Put(succession + 0x58, succession_candidates); Put(succession + 0x64, std::int32_t{4});
    const std::array<std::string_view, 8> keys{"crown_authority_0", "crown_authority_1", "crown_authority_2", "crown_authority_3",
      "confederate_partition_succession_law", "partition_succession_law", "high_partition_succession_law", "single_heir_succession_law"};
    std::array<std::uintptr_t, 8> addresses{};
    for (std::size_t i = 0; i < keys.size(); ++i) {
      auto definition = Allocate(0xD00); addresses[i] = definition;
      laws[definition] = static_cast<int>(i); Key(definition + 0x18, keys[i]);
      if (i < 4) {
        Put(definition + 0xBD8, std::uint8_t{9});
        Put(definition + 0xBD9, std::uint8_t{3});
        Put(definition + 0xBDB, std::uint8_t{2});
        Put(definition + 0xBDC, std::uint8_t{2});
      }
      Put(definition + 0x40, i < 4 ? crown : succession);
      Put((i < 4 ? crown_candidates : succession_candidates) + (i % 4) * 8, definition);
    }
    active_slots = Allocate(16); Put(active_slots, addresses[0]); Put(active_slots + 8, addresses[4]);
    Put(land + 0x200, active_slots); Put(land + 0x208, std::int32_t{2}); Put(land + 0x20C, std::int32_t{2});
  }
};

struct Binding {
  Fixture fixture;
  RealmLawCrownSource12002 source;
  law::AddLawCommandOfflineCallsV1 command_calls{&fixture, Fixture::Validate, Fixture::Clone, Fixture::Queue, Fixture::DestroyCommand};
  std::unique_ptr<RealmLawNativeBinderStateV1> state = std::make_unique<RealmLawNativeBinderStateV1>();
  Binding() {
    source.module_base = base;
    source.admitted_executable_sha256 = law::kRealmLawActiveCollectionExeSha25612002;
    source.callback_context = &fixture; source.read_runtime_proof = Fixture::Proof;
    source.capture_frame = Fixture::Frame; source.read_memory = Fixture::Memory;
    source.final_operations = {{Fixture::Kind, Fixture::Active, Fixture::Final, Fixture::Cost}, Fixture::Reason, Fixture::DestroyReason};
    source.component_operations = {true, Fixture::Scope, Fixture::Component,
                                   Fixture::DestroyScope, Fixture::DestroyScope};
    source.primary_title = Fixture::Primary;
    source.command_access.module_base = base; source.command_access.submit_enabled = true;
    source.command_access.mutation_abi_proof.verified = true;
    source.command_access.offline_calls = &command_calls;
    assert(BindRealmLawCrownSource12002(source, manifest, *state, true));
  }
  RealmLawEnactActionRequestV1 Request() {
    RealmLawEnactActionRequestV1 request;
    request.request_id = "offline-selected-crown";
    AssignRealmLawGovernanceKeyV1("crown_authority", request.group_key);
    AssignRealmLawGovernanceKeyV1("crown_authority_1", request.law_key);
    request.expected_public_revision = fixture.frame.public_revision;
    request.expected_native_revision = fixture.frame.native_revision;
    request.expected_proof_epoch = fixture.frame.proof_epoch;
    request.expected_date_raw = fixture.frame.date_raw;
    request.expected_player_character_id = actor_id;
    request.budget_count = 1;
    AssignRealmLawGovernanceKeyV1("prestige", request.budgets[0].currency_key);
    request.budgets[0].maximum_spend_raw = 20'000'000;
    return request;
  }
};

void TestActualMurchadReasonsKeepLegalCandidateReadable() {
  auto binding = std::make_unique<Binding>();
  binding->fixture.actual_murchad_reasons = true;
  binding->fixture.frame.date_raw = 53'328'360;
  binding->fixture.crown_reasons = {
      std::string(murchad_ca0_reason), "", std::string(murchad_ca2_reason),
      std::string(murchad_ca3_reason)};
  assert(murchad_ca2_reason.size() == 453 && murchad_ca3_reason.size() == 450);
  const auto access = MakeRealmLawNativeActionAccessV1(*binding->state);
  auto observation = std::make_unique<RealmLawEnactActionObservationV1>();
  assert(access.capture_observation(access.context, *observation));
  assert(observation->available && observation->resources_complete);
  const auto &snapshot = observation->law_snapshot;
  assert(snapshot.status == RealmLawGovernanceSnapshotV1Status::available);
  assert(snapshot.date_raw == 53'328'360 && snapshot.group_count == 1);
  const auto &group = snapshot.groups[0];
  assert(RealmLawGovernanceKeyViewV1(group.active_law_key) == "crown_authority_0");
  assert(group.candidates_complete && group.candidate_count == 4);
  const auto &ca0 = group.candidates[0];
  assert(ca0.is_active && !ca0.can_enact);
  assert(RealmLawGovernanceReasonViewV1(ca0.blocked_reason) == murchad_ca0_reason);
  const auto &ca1 = group.candidates[1];
  assert(RealmLawGovernanceKeyViewV1(ca1.law_key) == "crown_authority_1");
  assert(ca1.engine_final_only && ca1.can_enact && !ca1.is_active);
  assert(ca1.costs_complete && ca1.cost_count == 1);
  assert(RealmLawGovernanceKeyViewV1(ca1.costs[0].currency_key) == "prestige");
  assert(ca1.costs[0].amount_raw == 14'600'000);
  for (const auto index : {2u, 3u}) {
    const auto &candidate = group.candidates[index];
    const auto expected = index == 2 ? murchad_ca2_reason : murchad_ca3_reason;
    assert(RealmLawGovernanceKeyViewV1(candidate.law_key) ==
           (index == 2 ? "crown_authority_2" : "crown_authority_3"));
    assert(candidate.evaluation_complete && candidate.engine_final_only);
    assert(!candidate.can_enact && !candidate.is_active);
    assert(candidate.costs_complete && candidate.cost_count == 0);
    assert(RealmLawGovernanceReasonViewV1(candidate.blocked_reason) == expected);
  }
  assert(binding->fixture.queued == 0 && !binding->state->submit_pending);
}
}

int main(int argc, char **argv) {
  if (argc == 2 && std::string_view(argv[1]) == "--actual-murchad-reasons-only") {
    TestActualMurchadReasonsKeepLegalCandidateReadable();
    std::cout << "PASS: actual Murchad CA2/CA3 reasons 453/450 bytes preserved; CA0 active, CA1 legal prestige14600000; submit0\n";
    return 0;
  }
  {
    auto binding = std::make_unique<Binding>();
    auto source_result = std::make_unique<RealmLawGovernanceSourceResultV1>();
    assert(ObserveRealmLawGovernanceSourceV1(MakeRealmLawNativeSourceAccessV1(*binding->state), *source_result));
    assert(source_result->snapshot.group_count == 1);
    const auto &candidate = source_result->snapshot.groups[0].candidates[1];
    assert(candidate.engine_final_only && candidate.can_enact && !candidate.can_have && !candidate.can_pass);
    assert(source_result->snapshot.title_baseline.held_titles[1].successor_count == 2);
    auto ack = std::make_unique<RealmLawEnactActionAckV1>();
    assert(ExecuteBoundRealmLawNativeEnactV1(*binding->state, binding->Request(), *ack) == RealmLawEnactActionAckStatusV1::submitted_verification_pending);
    assert(binding->fixture.queued == 1);
    // Queue ACK does not enact a law; independent unchanged state must fail.
    auto receipt = std::make_unique<RealmLawEnactActionReceiptV1>();
    assert(VerifyBoundRealmLawNativeReceiptV1(*binding->state, *ack, *receipt) == RealmLawEnactActionReceiptStatusV1::failed);
    for (const auto &[address, index] : binding->fixture.laws)
      if (index == 1) binding->fixture.Put(binding->fixture.active_slots, address);
    binding->fixture.Put(resource + 0x130, std::int64_t{30'000'000});
    ++binding->fixture.frame.public_revision; ++binding->fixture.frame.native_revision; ++binding->fixture.frame.proof_epoch;
    assert(VerifyBoundRealmLawNativeReceiptV1(*binding->state, *ack, *receipt) == RealmLawEnactActionReceiptStatusV1::enacted);
    assert(receipt->effective_law_verified && receipt->resources_verified && receipt->succession_verified);
  }
  {
    auto binding = std::make_unique<Binding>(); binding->fixture.allowed = false;
    RealmLawEnactActionAckV1 ack;
    assert(ExecuteBoundRealmLawNativeEnactV1(*binding->state, binding->Request(), ack) == RealmLawEnactActionAckStatusV1::rejected_before_submit);
    assert(binding->fixture.queued == 0);
  }
  {
    auto binding = std::make_unique<Binding>(); binding->fixture.exotic_cost = 100'000;
    auto request = binding->Request(); request.budget_count = 2;
    AssignRealmLawGovernanceKeyV1("renown", request.budgets[1].currency_key);
    request.budgets[1].maximum_spend_raw = 100'000;
    RealmLawEnactActionAckV1 ack;
    assert(ExecuteBoundRealmLawNativeEnactV1(*binding->state, request, ack) == RealmLawEnactActionAckStatusV1::rejected_before_submit);
    assert(ack.failure == RealmLawEnactActionFailureV1::insufficient_resources && binding->fixture.queued == 0);
  }
  {
    auto binding = std::make_unique<Binding>();
    auto ack = std::make_unique<RealmLawEnactActionAckV1>();
    assert(ExecuteBoundRealmLawNativeEnactV1(*binding->state, binding->Request(), *ack) == RealmLawEnactActionAckStatusV1::submitted_verification_pending);
    for (const auto &[address, index] : binding->fixture.laws)
      if (index == 1) binding->fixture.Put(binding->fixture.active_slots, address);
    binding->fixture.Put(resource + 0x130, std::int64_t{30'000'000});
    binding->fixture.Put(binding->fixture.primary_successors + 4, first_id);
    ++binding->fixture.frame.public_revision; ++binding->fixture.frame.native_revision; ++binding->fixture.frame.proof_epoch;
    auto receipt = std::make_unique<RealmLawEnactActionReceiptV1>();
    assert(VerifyBoundRealmLawNativeReceiptV1(*binding->state, *ack, *receipt) == RealmLawEnactActionReceiptStatusV1::failed);
  }
  std::cout << "PASS: actual 1.20 source -> final-only LAW4 -> typed queue -> independent active/prestige/full-successor receipt; blocked and missing-resource no-op\n";
}
