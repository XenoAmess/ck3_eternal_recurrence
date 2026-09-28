#include "realm_law_paused_private_transport_v1.hpp"

#include "xar_bridge/realm_law_enact_mutation_abi_v1.hpp"

#include <windows.h>

#include <cstring>

namespace xar::ck3_11906 {
namespace {

bool ReadMemory(void *, std::uintptr_t address, void *output,
                std::size_t size) noexcept {
  SIZE_T read = 0;
  return address != 0 && output != nullptr &&
         ReadProcessMemory(GetCurrentProcess(),
                           reinterpret_cast<const void *>(address), output,
                           size, &read) != 0 && read == size;
}

template <typename T>
bool ReadAt(std::uintptr_t address, T &output) noexcept {
  return ReadMemory(nullptr, address, &output, sizeof(output));
}

bool ReadAbiRva(void *opaque, std::uintptr_t rva, void *output,
                std::size_t size) noexcept {
  const auto base = *static_cast<const std::uintptr_t *>(opaque);
  return ReadMemory(nullptr, base + rva, output, size);
}

std::uintptr_t ResolvePlayedCharacter(const Bindings &bindings,
                                      std::int32_t full_id) noexcept {
  if (full_id <= 0 || bindings.character_storage_slot == nullptr) return 0;
  std::uintptr_t storage = 0;
  if (!ReadAt(reinterpret_cast<std::uintptr_t>(bindings.character_storage_slot),
              storage) || storage == 0) return 0;
  std::uintptr_t slots = 0;
  std::int32_t capacity = 0;
  if (!ReadAt(storage + 0x20, slots) || !ReadAt(storage + 0x2C, capacity) ||
      slots == 0 || capacity <= 0) return 0;
  const auto index = static_cast<std::uint32_t>(full_id) & 0x00FFFFFFu;
  if (index >= static_cast<std::uint32_t>(capacity)) return 0;
  std::uintptr_t actor = 0;
  std::int32_t observed_id = 0;
  if (!ReadAt(slots + static_cast<std::uintptr_t>(index) * 0x10 + 0x08,
              actor) || actor == 0 || !ReadAt(actor + 0x18, observed_id) ||
      observed_id != full_id) return 0;
  return actor;
}

using NativeValidator = bool (*)(const void *, const void *, void *);
using NativeStringDestructor = void (*)(void *);

bool ReadNativeReason(std::uintptr_t module_base, const void *law,
                      const void *actor, bool &can_enact,
                      std::string &out) {
  // MSVC's 32-byte string object is initialized in short-string mode. The
  // engine owns any allocation and its own destructor releases it below.
  alignas(8) std::array<std::byte, 32> sink{};
  const std::uint64_t inline_capacity = 15;
  std::memcpy(sink.data() + 0x18, &inline_capacity, sizeof(inline_capacity));
  const auto validator = reinterpret_cast<NativeValidator>(module_base +
                                                             0x2C7DAA0);
  const auto destroy = reinterpret_cast<NativeStringDestructor>(module_base +
                                                                  0x7E97D0);
  can_enact = validator(law, actor, sink.data());
  std::uint64_t size = 0;
  std::uint64_t capacity = 0;
  std::memcpy(&size, sink.data() + 0x10, sizeof(size));
  std::memcpy(&capacity, sink.data() + 0x18, sizeof(capacity));
  const char *data = capacity <= 15
                         ? reinterpret_cast<const char *>(sink.data())
                         : *reinterpret_cast<const char *const *>(sink.data());
  const bool valid = size <= 4096 && capacity >= size && data != nullptr;
  if (valid) out.assign(data, static_cast<std::size_t>(size));
  destroy(sink.data());
  return valid;
}

struct CaptureContext {
  RealmLawPausedPrivateQueryV1 *query = nullptr;
  std::uintptr_t module_base = 0;
  std::uintptr_t actor = 0;
  std::array<std::array<RealmLawPausedPrivateCandidateV1,
                        private_law::kRealmLawMaximumRelevantCandidates11906>, 2>
      *final = nullptr;
};

bool ObserveCandidate(
    void *opaque, std::size_t group, std::size_t index,
    std::uintptr_t native_law,
    const private_law::RealmLawCandidateCollectionRow11906 &row) noexcept {
  auto &context = *static_cast<CaptureContext *>(opaque);
  try {
    auto &result = (*context.final)[group][index];
    bridge::RealmLawFinalTerms11906Operations operations{};
    operations.candidate_kind_allowed =
        reinterpret_cast<decltype(operations.candidate_kind_allowed)>(
            context.module_base + 0x2C7E900);
    operations.is_active = reinterpret_cast<decltype(operations.is_active)>(
        context.module_base + 0x28BC040);
    operations.engine_final_can_enact =
        reinterpret_cast<decltype(operations.engine_final_can_enact)>(
            context.module_base + 0x2C7D930);
    operations.read_cost_q100000 =
        reinterpret_cast<decltype(operations.read_cost_q100000)>(
            context.module_base + 0x2C7E490);
    const auto &snapshot = context.query->expected_snapshot;
    result.terms = bridge::ReadRealmLawFinalTerms11906(
        {reinterpret_cast<const void *>(native_law),
         reinterpret_cast<const void *>(context.actor),
         static_cast<std::uint32_t>(snapshot.played_character_id)},
        operations);
    if (!result.terms.cost_available ||
        result.terms.status == bridge::RealmLawFinalTerms11906Status::unavailable ||
        (row.active != (result.terms.status ==
                        bridge::RealmLawFinalTerms11906Status::already_active))) {
      context.query->failure = "native_law_cost_or_active_red";
      return false;
    }
    bool validator_can_enact = false;
    if (!ReadNativeReason(context.module_base,
                          reinterpret_cast<const void *>(native_law),
                          reinterpret_cast<const void *>(context.actor),
                          validator_can_enact, result.native_reason) ||
        validator_can_enact !=
            (result.terms.status ==
             bridge::RealmLawFinalTerms11906Status::can_enact)) {
      context.query->failure = "native_law_validator_mismatch";
      return false;
    }
    return true;
  } catch (...) {
    context.query->failure = "native_law_reason_copy_red";
    return false;
  }
}

bool SameCapture(const RealmLawPausedPrivateQueryV1 &query,
                 const private_law::RealmLawCandidateCollection11906 &second,
                 const decltype(RealmLawPausedPrivateQueryV1::final) &final) {
  for (std::size_t g = 0; g < 2; ++g) {
    const auto &left = query.collection.groups[g];
    const auto &right = second.groups[g];
    if (left.key != right.key || left.active_found != right.active_found ||
        left.active_law_key != right.active_law_key ||
        left.candidate_count != right.candidate_count) return false;
    for (std::size_t i = 0; i < left.candidate_count; ++i) {
      const auto &a = query.final[g][i];
      const auto &b = final[g][i];
      if (left.candidates[i].key != right.candidates[i].key ||
          left.candidates[i].active != right.candidates[i].active ||
          a.terms.status != b.terms.status ||
          a.terms.cost_available != b.terms.cost_available ||
          a.terms.cost_raw != b.terms.cost_raw ||
          a.native_reason != b.native_reason) return false;
    }
  }
  return true;
}

void AppendJsonString(std::string &out, std::string_view value) {
  constexpr char hex[] = "0123456789abcdef";
  out += '"';
  for (const unsigned char c : value) {
    if (c == '"' || c == '\\') {
      out += '\\';
      out += static_cast<char>(c);
    } else if (c < 0x20) {
      out += "\\u00";
      out += hex[c >> 4];
      out += hex[c & 15];
    } else {
      out += static_cast<char>(c);
    }
  }
  out += '"';
}

std::string_view Key(const private_law::RealmLawActiveKey &key) noexcept {
  return {key.bytes.data(), key.size};
}

const char *Status(bridge::RealmLawFinalTerms11906Status status) noexcept {
  switch (status) {
  case bridge::RealmLawFinalTerms11906Status::candidate_kind_rejected:
    return "candidate_kind_rejected";
  case bridge::RealmLawFinalTerms11906Status::already_active:
    return "already_active";
  case bridge::RealmLawFinalTerms11906Status::engine_blocked:
    return "engine_blocked";
  case bridge::RealmLawFinalTerms11906Status::can_enact:
    return "can_enact";
  default:
    return "unavailable";
  }
}

} // namespace

bool ExecuteRealmLawPausedPrivateQueryV1(
    void *opaque, const MainThreadExecutionStampV1 &stamp) noexcept {
  auto *query = static_cast<RealmLawPausedPrivateQueryV1 *>(opaque);
  if (query == nullptr || query->mailbox == nullptr ||
      query->ticket.sequence == 0 || query->expected_revision == 0 ||
      query->invocations != 0 || stamp.pump_epoch == 0 || stamp.thread_id == 0 ||
      !stamp.paused || stamp.tls_initialized_flag_address == 0 ||
      stamp.tls_initialized != 1 || stamp.tls_context == 0 ||
      stamp.tls_main_thread_marker != 1 || stamp.jomini_state == 0 ||
      stamp.game_state == 0 || GetCurrentThreadId() != stamp.thread_id) return false;
  auto &mailbox = *query->mailbox;
  if (mailbox.state.load(std::memory_order_acquire) !=
          MainThreadQueryMailboxStateV1::executing ||
      mailbox.stop_requested.load(std::memory_order_acquire) ||
      mailbox.failure_flags.load(std::memory_order_acquire) != 0 ||
      mailbox.published_sequence.load(std::memory_order_acquire) !=
          query->ticket.sequence ||
      mailbox.owner_thread_id.load(std::memory_order_acquire) != stamp.thread_id ||
      mailbox.paused_owner_verified_pump_epochs.load(std::memory_order_acquire) <
          kMainThreadQueryMinimumPausedOwnerVerifiedPumpEpochs ||
      mailbox.executor != &ExecuteRealmLawPausedPrivateQueryV1 ||
      mailbox.executor_context != query) return false;
  try {
    ++query->invocations;
    game::Snapshot current{};
    if (!ReadSnapshot(query->bindings, current) ||
        current != query->expected_snapshot || !current.paused ||
        !current.map_ready || !current.has_played_character ||
        !current.played_character_alive || current.date_raw != stamp.date_raw) {
      query->frame_changed = true;
      query->failure = "published_frame_changed";
      query->completed = true;
      return true;
    }
    const auto module_base =
        reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr));
    const auto actor = ResolvePlayedCharacter(query->bindings,
                                              current.played_character_id);
    if (!query->bindings.enabled || module_base == 0 || actor == 0) {
      query->failure = "exact_actor_unavailable";
      query->completed = true;
      return true;
    }
    const private_law::RealmLawMutationAbiReaderV1 abi_reader{
        const_cast<std::uintptr_t *>(&module_base), &ReadAbiRva};
    if (!private_law::VerifyRealmLawEnactMutationAbiV1(
             abi_reader, module_base).verified) {
      query->failure = "native_law_abi_red";
      query->completed = true;
      return true;
    }
    private_law::RealmLawActiveCollectionAccess access{};
    access.admitted_executable_sha256 =
        private_law::kRealmLawActiveCollectionExeSha256;
    access.played_character_address = actor;
    access.read_memory = &ReadMemory;
    CaptureContext capture{query, module_base, actor, &query->final};
    if (!private_law::ReadRealmLawCandidateCollectionWithObserver11906(
            access, module_base, &capture, &ObserveCandidate,
            query->collection)) {
      if (query->failure.empty()) query->failure = "native_law_collection_red";
      query->completed = true;
      return true;
    }
    private_law::RealmLawCandidateCollection11906 second{};
    decltype(query->final) final_second{};
    capture.final = &final_second;
    if (!private_law::ReadRealmLawCandidateCollectionWithObserver11906(
            access, module_base, &capture, &ObserveCandidate, second) ||
        !SameCapture(*query, second, final_second)) {
      if (query->failure.empty()) query->failure = "native_law_samples_differ";
      query->completed = true;
      return true;
    }
    query->completed = true;
    return true;
  } catch (...) {
    query->failure = "native_law_query_exception";
    query->completed = true;
    return true;
  }
}

std::string SerializeRealmLawPausedPrivateQueryV1(
    const RealmLawPausedPrivateQueryV1 &query) {
  if (!query.completed || !query.failure.empty() ||
      query.collection.failure !=
          private_law::RealmLawCandidateCollectionFailure::none) return {};
  std::string out = "{\"schema\":\"realm-law-final-terms-private-read-v1\","
                    "\"snapshot_revision\":" +
                    std::to_string(query.expected_revision) +
                    ",\"date_raw\":" +
                    std::to_string(query.expected_snapshot.date_raw) +
                    ",\"actor_character_id\":" +
                    std::to_string(query.expected_snapshot.played_character_id) +
                    ",\"cost_scale\":100000,\"cost_slots\":[\"gold\","
                    "\"prestige\",\"piety\",\"renown\",\"influence\",\"herd\","
                    "\"treasury\",\"treasury_or_gold\",\"merit\","
                    "\"barter_goods\"],\"groups\":[";
  for (std::size_t g = 0; g < 2; ++g) {
    if (g != 0) out += ',';
    const auto &group = query.collection.groups[g];
    out += "{\"group_key\":";
    AppendJsonString(out, Key(group.key));
    out += ",\"active_law_key\":";
    if (group.active_found) AppendJsonString(out, Key(group.active_law_key));
    else out += "null";
    out += ",\"candidates\":[";
    for (std::size_t i = 0; i < group.candidate_count; ++i) {
      if (i != 0) out += ',';
      const auto &row = group.candidates[i];
      const auto &final = query.final[g][i];
      out += "{\"law_key\":";
      AppendJsonString(out, Key(row.key));
      out += ",\"active\":";
      out += row.active ? "true" : "false";
      out += ",\"final_status\":";
      AppendJsonString(out, Status(final.terms.status));
      out += ",\"final_can_enact\":";
      out += final.terms.status == bridge::RealmLawFinalTerms11906Status::can_enact
                 ? "true" : "false";
      out += ",\"native_reason\":";
      AppendJsonString(out, final.native_reason);
      out += ",\"cost_raw\":[";
      for (std::size_t slot = 0; slot < final.terms.cost_raw.size(); ++slot) {
        if (slot != 0) out += ',';
        out += std::to_string(final.terms.cost_raw[slot]);
      }
      out += "]}";
    }
    out += "]}";
  }
  out += "]}";
  return out;
}

} // namespace xar::ck3_11906
