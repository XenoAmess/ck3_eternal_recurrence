#include "holy_order_loan_principal_12004.hpp"
#include "xar_bridge/ck3_12004_religion_context_addons.hpp"

#include <array>
#include <cstddef>
#include <cstring>

namespace xar::ck3_12004::religion::loan_principal {
namespace {
static_assert(sizeof(std::uintptr_t) == 8);

template <typename T> T Load(const void *p, std::size_t offset) noexcept {
  T result{};
  std::memcpy(&result, static_cast<const std::byte *>(p) + offset, sizeof(result));
  return result;
}
template <typename T> void Store(void *p, std::size_t offset, T value) noexcept {
  std::memcpy(static_cast<std::byte *>(p) + offset, &value, sizeof(value));
}

struct OwnedRead {
  alignas(16) std::array<std::byte, 0x170> root_storage{};
  alignas(16) std::array<std::byte, 0x3E0> scratch_storage{};
  alignas(16) std::array<std::byte, 0x30> context_storage{};
  alignas(16) std::array<std::byte, 0x20> source_storage{};
  const Bindings *bindings = nullptr;
  CoreSnapshotPrefix before{};
  void *character = nullptr, *database = nullptr;
  const void *definition = nullptr;
  std::uint32_t key_hash = 0;
  std::int64_t value_raw = 0;
  bool root_started = false, root_returned = false, root_owned = false;
  bool first_started = false, first_returned = false, first_owned = false;
  bool second_started = false, second_returned = false, second_owned = false;
  std::string_view reason = "source_unavailable";
};

// Each owned buffer is rounded to 16 bytes. The source-used root/scratch/context
// extents are 0x168/0x3D8/0x28; these are not native sizeof assertions.
using Callback = bool (*)(OwnedRead &) noexcept;
bool Guard(Callback callback, OwnedRead &read) noexcept {
#if defined(_WIN32) && defined(_MSC_VER)
  __try { return callback(read); }
  __except (1) { return false; }
#else
  return callback(read);
#endif
}

bool ExactDefinition(const OwnedRead &r, const void *definition) noexcept {
  const auto &b = r.bindings->named;
  if (!definition || Load<std::uintptr_t>(definition, 0) != b.named_primary_vtable ||
      Load<std::uintptr_t>(definition, 0x88) != b.named_secondary_vtable ||
      Load<std::uint32_t>(definition, 0x14) != r.key_hash ||
      Load<std::uint32_t>(definition, 0x38) != 0x4744624FU) return false;
  const auto *key = static_cast<const std::byte *>(definition) + 0x18;
  const auto length = Load<std::uint64_t>(key, 0x10);
  const auto capacity = Load<std::uint64_t>(key, 0x18);
  if (length != kValueKey.size() || length > capacity ||
      (capacity < 16 && capacity != 15)) return false;
  const auto *text = capacity < 16 ? reinterpret_cast<const char *>(key)
                                  : Load<const char *>(key, 0);
  return text && std::memcmp(text, kValueKey.data(), kValueKey.size()) == 0 &&
      text[kValueKey.size()] == 0;
}

bool PausedPlayer(const Bindings &b, CoreSnapshotPrefix &frame, void *&character) noexcept {
  if (!ck3_12004::ReadCoreSnapshot(b.core, frame) || !frame.map_ready ||
      !frame.has_played_character || !frame.played_character_alive ||
      !frame.clock.paused || frame.played_character_id <= 0) return false;
  character = ck3_12004::ResolveCoreCharacter(b.core, frame.played_character_id);
  return character != nullptr;
}

bool CaptureAndEvaluate(OwnedRead &r) noexcept {
  const auto &b = *r.bindings;
  const auto &n = b.named;
  if (!PausedPlayer(b, r.before, r.character)) {
    r.reason = "paused_player_unavailable"; return false;
  }
  r.database = n.named_database();
  if (!r.database) { r.reason = "named_database_unavailable"; return false; }
  r.key_hash = b.root.decision_hash(r.database, kValueKey.data(),
      static_cast<std::uint32_t>(kValueKey.size()));
  r.definition = n.lookup_named(r.database, r.key_hash);
  if (!ExactDefinition(r, r.definition)) {
    r.reason = "holy_order_value_definition_unavailable"; return false;
  }

  // Complete actual889F60 constructs this single root, actual87E0E0 owns its
  // eventual destruction. No interaction scope is accepted, cloned or reused.
  r.reason = "player_root_construction_failed";
  r.root_started = true;
  void *root = r.root_storage.data();
  const auto *constructed_root = b.root.root_construct(root);
  r.root_returned = r.root_owned = true;
  if (constructed_root != root) return false;
  Store(root, 0, std::uint16_t{4});
  Store(root, 8, static_cast<std::uint64_t>(
      static_cast<std::uint32_t>(r.before.played_character_id)));

  r.reason = "numeric_scratch_construction_failed";
  void *scratch = r.scratch_storage.data();
  r.first_started = true;
  const auto *first = n.construct_support_118(scratch);
  r.first_returned = r.first_owned = true;
  if (first != scratch) return false;
  r.second_started = true;
  const auto *second = n.construct_support_2a8(r.scratch_storage.data() + 0x128);
  r.second_returned = r.second_owned = true;
  if (second != r.scratch_storage.data() + 0x128) return false;

  // Actual3761680 supplies {root,NULL,root,scratch,loaded mode}; it is not
  // inferred from an interaction context. scratch+3D0 borrows this owned root.
  Store(scratch, 0x3D0, root);
  auto *context = r.context_storage.data();
  Store(context, 0, root);
  Store(context, 8, static_cast<void *>(nullptr));
  Store(context, 0x10, root);
  Store(context, 0x18, scratch);
  Store(context, 0x20, *n.evaluation_flag);

  r.reason = "named_source_descriptor_unavailable";
  alignas(16) std::array<std::byte, 0x10> key_view{};
  Store(key_view.data(), 0, kValueKey.data());
  Store(key_view.data(), 8, static_cast<std::uint32_t>(kValueKey.size()));
  void *intern_database = n.intern_database();
  const void *intern = intern_database ? n.intern_string(intern_database, key_view.data()) : nullptr;
  if (!intern) return false;
  // Source descriptor borrows the intern entry; it owns no string/vector.
  Store(r.source_storage.data(), 0, intern);
  Store(r.source_storage.data(), 0x14, std::uint8_t{1});
  Store(r.source_storage.data(), 0x18, std::int32_t{-1});

  r.reason = "native_principal_evaluation_failed";
  // Actual37542D0 chooses +70 provider or +7B/+68 constant itself. Do not
  // transplant the old .3 wrapper's +7C admission into this .4 call.
  return n.evaluate_fixed(r.definition, &r.value_raw, context, nullptr,
                          r.source_storage.data()) == &r.value_raw;
}

using Deallocate = void (*)(void *, void *, std::size_t);
bool ReleaseScratchVector(OwnedRead &r, std::size_t offset, bool clear_values) noexcept {
  auto *vector = r.scratch_storage.data() + offset;
  if (!Load<void *>(vector, 0)) return true;
  if (clear_values) r.bindings->named.destroy_support_rows(vector);
  else Store(vector, 0x0C, std::int32_t{0});
  // Actual3761680 reloads data after ClearValues, then calls allocator+10.
  void *data = Load<void *>(vector, 0);
  void *allocator = Load<void *>(vector, 0x10);
  if (!data || !allocator) return false;
  const auto vtable = Load<const void *>(allocator, 0);
  if (!vtable) return false;
  const auto release = Load<Deallocate>(vtable, 0x10);
  if (!release) return false;
  release(allocator, data, 8);
  Store(vector, 0, static_cast<void *>(nullptr));
  Store(vector, 8, std::int32_t{0});
  return true;
}
bool ReleaseSecond(OwnedRead &r) noexcept {
  if (!r.second_owned) return !r.second_started || r.second_returned;
  const bool released = ReleaseScratchVector(r, 0x128, true);
  if (released) r.second_owned = false;
  return released;
}
bool ReleaseFirst(OwnedRead &r) noexcept {
  if (!r.first_owned) return !r.first_started || r.first_returned;
  const bool released = ReleaseScratchVector(r, 0, false);
  if (released) r.first_owned = false;
  return released;
}
bool ReleaseRoot(OwnedRead &r) noexcept {
  if (!r.root_owned) return !r.root_started || r.root_returned;
  r.bindings->root.root_destroy(r.root_storage.data());
  r.root_owned = false;
  return true;
}
bool VerifyBookends(OwnedRead &r) noexcept {
  CoreSnapshotPrefix after{};
  void *character = nullptr;
  const auto &b = *r.bindings;
  return PausedPlayer(b, after, character) && character == r.character &&
      after.local_player_id == r.before.local_player_id &&
      after.played_character_id == r.before.played_character_id &&
      after.clock.date_raw == r.before.clock.date_raw &&
      b.named.named_database() == r.database &&
      b.named.lookup_named(r.database, r.key_hash) == r.definition &&
      ExactDefinition(r, r.definition);
}
} // namespace

Bindings BindHolyOrderLoanPrincipalImage12004(
    std::uintptr_t base, std::string_view sha) noexcept {
  Bindings b{};
  if (!base || sha != ck3_12004::kExecutableSha256) return b;
  b.image_base = base;
  b.core = ck3_12004::BindCoreImage(base, sha);
  b.root = BindReligionContextAddonsImage12004(base, sha).mystical_communion_bindings;
  b.named = BindPrisonerNamedImage12004(base, sha);
  const auto &n = b.named;
  b.enabled = b.core.enabled && b.root.enabled && n.enabled &&
      b.root.root_construct && b.root.root_destroy && b.root.decision_hash &&
      n.named_database && n.lookup_named && n.construct_support_118 &&
      n.construct_support_2a8 && n.intern_database && n.intern_string &&
      n.evaluate_fixed && n.destroy_support_rows && n.evaluation_flag &&
      n.named_primary_vtable && n.named_secondary_vtable;
  return b;
}

bool ReadPlayerHolyOrderLoanPrincipal12004(
    const Bindings &b, std::uint64_t epoch, Observation &out) noexcept {
  out = {};
  out.capture_epoch = epoch;
  if (!b.enabled || !epoch) return false;
  OwnedRead read{};
  read.bindings = &b;
  const bool evaluated = Guard(&CaptureAndEvaluate, read);
  // Every acquired temporary is attempted once in the native owner order,
  // including after an evaluation failure. No short-circuit skips an owner.
  const bool second_released = Guard(&ReleaseSecond, read);
  const bool first_released = Guard(&ReleaseFirst, read);
  const bool root_released = Guard(&ReleaseRoot, read);
  out.date_raw = read.before.clock.date_raw;
  out.played_character_id = read.before.played_character_id;
  out.owned_temporaries_released = second_released && first_released && root_released;
  if (!out.owned_temporaries_released) {
    out.unavailable_reason = "native_temporary_cleanup_unverified"; return false;
  }
  if (!evaluated) { out.unavailable_reason = read.reason; return false; }
  if (!Guard(&VerifyBookends, read)) {
    out.unavailable_reason = "principal_source_or_player_frame_changed"; return false;
  }
  out.prospective_principal_raw = read.value_raw;
  out.available = true;
  out.unavailable_reason = {};
  return true;
}

} // namespace xar::ck3_12004::religion::loan_principal
