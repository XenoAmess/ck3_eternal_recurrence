#include "xar_bridge/ck3_12004_council_runtime.hpp"
#include "xar_bridge/ck3_12004_council_task_owner_tax.hpp"

#include <algorithm>
#include <array>
#include <cstdlib>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <memory>
#include <vector>

namespace {
using namespace xar;
using namespace xar::ck3_12004;
using Operation = bridge::CouncilApplicationMainOperationV1;
using Completion = bridge::CouncilApplicationMainCompletionV1;

void Require(bool ok, const char *message) {
  if (!ok) { std::cerr << message << '\n'; std::exit(1); }
}
template<std::size_t N> struct Blob {
  std::array<std::byte, N> data{};
  void *Data() noexcept { return data.data(); }
  template<typename T> void Put(std::size_t at, T value) {
    std::memcpy(data.data() + at, &value, sizeof(value));
  }
};
struct Fixture;
Fixture *active = nullptr;
struct Fixture {
  static constexpr std::int32_t owner = 29829, incumbent = 32440,
      candidate = 32716, task_id = 6100;
  struct Slot { std::uintptr_t reserved = 0; void *object = nullptr; };
  std::array<Blob<0x200>, 3> characters{};
  Blob<0x300> extension{};
  Blob<0x80> task{}, type{}, position{};
  Blob<0x30> character_storage{}, task_storage{}, pending_manager{};
  std::vector<Slot> character_slots{40000}, task_slots{7000};
  void *character_storage_pointer = nullptr, *task_storage_pointer = nullptr;
  void *character_fallback = nullptr, *task_fallback = nullptr;
  std::int32_t owned_task_id = task_id, played_id = owner;
  std::string task_key = "collect_taxes", keyword = "domain_tax_mult";
  CouncilCandidatesFrameV1 frame{};
  CouncilMailboxContext12004 context{};
  ck3_11906::MainThreadExecutionStampV1 stamp{};
  std::int64_t raw = 24000;
  std::uint32_t build_calls = 0, numeric_calls = 0, cleanup_calls = 0,
      keyword_calls = 0, producer_calls = 0, release_calls = 0;
  void *owned_modifier = nullptr;

  Fixture() {
    active = this;
    const std::int32_t ids[] = {owner, incumbent, candidate};
    for (std::size_t i = 0; i < characters.size(); ++i) {
      characters[i].Put(0x18, ids[i]);
      character_slots[static_cast<std::size_t>(ids[i])].object = characters[i].Data();
    }
    characters[0].Put(0x1C0, extension.Data());
    characters[1].Put(0xE0, std::int32_t{11});
    characters[2].Put(0xE0, std::int32_t{22});
    extension.Put(0x230, &owned_task_id);
    extension.Put(0x23C, std::int32_t{1});
    task.Put(0x10, task_id);
    task.Put(0x18, type.Data());
    task.Put(0x40, incumbent);
    task.Put(0x44, owner);
    // Borrowed native CString representation at TaskType+18.
    static_assert(sizeof(std::string) == 32);
    std::memcpy(type.data.data() + 0x18, &task_key, sizeof(task_key));
    type.Put(0x40, position.Data());
    task_slots[task_id].object = task.Data();
    character_storage.Put(0x20, character_slots.data());
    character_storage.Put(0x2C, static_cast<std::int32_t>(character_slots.size()));
    task_storage.Put(0x20, task_slots.data());
    task_storage.Put(0x2C, static_cast<std::int32_t>(task_slots.size()));
    character_storage_pointer = character_storage.Data();
    task_storage_pointer = task_storage.Data();
    const std::string_view snapshot = "native:7";
    std::copy(snapshot.begin(), snapshot.end(), frame.snapshot_id.begin());
    frame.public_revision = 7; frame.native_revision = 7; frame.date_raw = 53178264;
    frame.paused = frame.map_ready = frame.has_played_character = frame.played_character_alive = true;
    frame.played_character_id = owner;
    frame.played_character = reinterpret_cast<std::uintptr_t>(characters[0].Data());
    auto &env = context.candidates_environment;
    env = BindCouncilCandidates12004(0x140000000, kExecutableSha256);
    env.offline_fixture_function_overrides = true;
    env.character_storage_slot = &character_storage_pointer;
    env.character_fallback_slot = &character_fallback;
    env.active_task_storage_slot = &task_storage_pointer;
    env.active_task_fallback_slot = &task_fallback;
    env.task_owner_tax.build = Build;
    env.task_owner_tax.value = Value;
    env.task_owner_tax.destroy = Cleanup;
    env.task_owner_tax.keyword_name = Keyword;
    auto &access = context.candidates_access;
    access.context = this;
    access.capture_frame = Capture;
    access.is_main_thread = MainThread;
    access.read_memory = Memory;
    access.lookup_position = Lookup;
    access.initialize_vector = Initialize;
    access.invoke_producer = Produce;
    access.release_allocation = Release;
    context.query_request = {std::string_view(frame.snapshot_id.data()), 7, 7,
        frame.date_raw, owner, kCouncilCandidatesStewardPosition12004};
    auto &gates = context.gates_environment;
    gates.exact_build_admitted = true;
    gates.admitted_executable_sha256 = kExecutableSha256;
    gates.offline_fixture = true;
    gates.played_character_id_slot = &played_id;
    gates.read_context = this; gates.read_memory = Memory;
    gates.is_councillor = Predicate;
    gates.is_guest = Predicate;
    gates.pending_setup = PendingSetup;
    gates.has_pending = HasPending;
    gates.can_confirm = CanConfirm;
    pending_manager.Put(0x8, owner);
    stamp.thread_id = 7; stamp.paused = true; stamp.game_state = 1;
  }
  static bool Memory(void *, const void *at, void *out, std::size_t size) noexcept {
    if (!at || !out || !size) return false;
    std::memcpy(out, at, size); return true;
  }
  static bool Capture(void *raw, CouncilCandidatesFrameV1 &out) noexcept {
    out = static_cast<Fixture *>(raw)->frame; return true;
  }
  static bool MainThread(void *) noexcept { return true; }
  static bool Lookup(void *raw, const CouncilCandidatesEnvironmentV1 &,
      const void *character, std::string_view key, const void *&out) noexcept {
    auto &f = *static_cast<Fixture *>(raw);
    out = character == f.characters[0].Data() && key == kCouncilCandidatesStewardPosition12004
        ? f.task.Data() : nullptr;
    return out != nullptr;
  }
  static bool Initialize(void *, const CouncilCandidatesEnvironmentV1 &,
      void *allocator, std::size_t size, CouncilCandidatesNativeVectorV1 &out) noexcept {
    Require(size == 0x210, "native candidate allocator size");
    out.data_address = reinterpret_cast<std::uintptr_t>(allocator) + 8;
    out.capacity = 64; out.count = 0; out.allocator = allocator; return true;
  }
  static bool Produce(void *raw, const CouncilCandidatesEnvironmentV1 &,
      const void *character, const void *task, bool gui,
      CouncilCandidatesNativeVectorV1 &out) noexcept {
    auto &f = *static_cast<Fixture *>(raw);
    Require(character == f.characters[0].Data() && task == f.task.Data() && gui,
        "current native owner/task candidate inputs");
    ++f.producer_calls;
    const void *row = f.characters[2].Data();
    std::memcpy(reinterpret_cast<void *>(out.data_address), &row, sizeof(row));
    out.count = 1; return true;
  }
  static bool Release(void *raw, const CouncilCandidatesEnvironmentV1 &,
      CouncilCandidatesNativeVectorV1 &out) noexcept {
    ++static_cast<Fixture *>(raw)->release_calls; out = {}; return true;
  }
  static const std::string *Keyword(std::int32_t token) {
    Require(token == 11976, "captured actual4 keyword ID");
    ++active->keyword_calls; return &active->keyword;
  }
  static void *Build(const void *type, void *storage, const void *scopes) {
    Require(type == active->type.Data(), "current native TaskType receiver");
    Require(std::memcmp(scopes, active->task.data.data() + 0x40, 32) == 0,
        "original current incumbent/owner scopes");
    Require(reinterpret_cast<std::uintptr_t>(storage) % 8 == 0,
        "owned aggregate output alignment");
    ++active->build_calls; active->owned_modifier = storage;
    return storage;
  }
  static std::int64_t *Value(const void *whole, std::int64_t *output, std::uint16_t id) {
    Require(whole == active->owned_modifier && id == 162,
        "whole evaluated owner modifier receiver and exact uint16 ID");
    ++active->numeric_calls; *output = active->raw; return output;
  }
  static void Cleanup(void *whole) {
    Require(whole == active->owned_modifier, "same owned aggregate cleanup");
    ++active->cleanup_calls; active->owned_modifier = nullptr;
  }
  static bool Predicate(void *) { return false; }
  static void PendingSetup(void *window) {
    void *manager = active->pending_manager.Data();
    std::memcpy(static_cast<std::byte *>(window) + 0x5D8, &manager, sizeof(manager));
  }
  static bool HasPending(void *manager, std::int32_t id) {
    Require(manager == active->pending_manager.Data() && id == candidate,
        "native final-gate pending receiver"); return false;
  }
  static bool CanConfirm(void *confirmation) {
    std::int32_t old = -1, next = -1;
    std::memcpy(&old, static_cast<std::byte *>(confirmation) + 0x130, sizeof(old));
    std::memcpy(&next, static_cast<std::byte *>(confirmation) + 0x134, sizeof(next));
    Require(old == incumbent && next == candidate, "native replacement confirmation inputs");
    return true;
  }
  std::string Execute() {
    active = this;
    context.operation = Operation::query_final_gates;
    context.ticket.sequence = 1;
    Require(ExecuteCouncilMailbox12004(&context, stamp), "actual4 production mailbox executor");
    Require(context.active_stamp == nullptr && context.wire.completion == Completion::query_available,
        "available paused final-gates transaction");
    Require(context.wire.query_result.readiness.ready && context.wire.final_gate_row_count == 1 &&
        context.wire.final_gate_rows[0].incumbent_can_be_fired,
        "optional component must preserve candidate/final-gates availability");
    Require(producer_calls == 1 && release_calls == 1, "native candidate lifetime");
    return SerializeCouncilMailbox12004(context, "fixture:council-task-tax12004");
  }
};
} // namespace

int main(int argc, char **argv) {
  Require(argc == 2, "fresh native wire output directory required");
  const std::filesystem::path dir = argv[1];
  std::filesystem::create_directories(dir);
  const char *files[] = {"positive-gates.json", "zero-gates.json", "negative-gates.json", "keyword-mismatch-gates.json"};
  const std::int64_t values[] = {24000, 0, -5000, 24000};
  for (std::size_t i = 0; i < 4; ++i) {
    auto f = std::make_unique<Fixture>();
    f->raw = values[i];
    f->task.Put(0x39, static_cast<std::uint8_t>(i == 2));
    if (i == 3) f->keyword = "other_modifier";
    const auto wire = f->Execute();
    const auto &leaf = f->context.wire.query_result.current_task_owner_domain_tax_mult_v1;
    Require(leaf.has_value() && leaf->modifier_id == 162 && leaf->keyword_id == 11976 &&
        leaf->active_task_id == Fixture::task_id && leaf->frozen == (i == 2),
        "current task component provenance");
    if (i == 3) {
      Require(!leaf->raw.has_value() && leaf->unavailable_reason ==
          game::CouncilCurrentTaskDomainTaxFailureV1::keyword_mismatch && f->build_calls == 0,
          "runtime keyword mismatch stays optional unavailable");
    } else {
      Require(leaf->raw == values[i] && f->build_calls == 1 && f->numeric_calls == 1 &&
          f->cleanup_calls == 1 && f->owned_modifier == nullptr,
          "native signed component and owned aggregate lifetime");
    }
    Require(!wire.empty(), "actual4 production serializer");
    std::ofstream out(dir / files[i], std::ios::binary);
    out << wire << '\n'; Require(static_cast<bool>(out), "native wire artifact write");
  }
  std::cout << "GREEN current Council owner tax whole source chain: 4 cases\n";
  return 0;
}
