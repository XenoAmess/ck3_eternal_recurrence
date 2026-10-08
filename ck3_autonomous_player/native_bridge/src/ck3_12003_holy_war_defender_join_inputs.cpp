#include "xar_bridge/ck3_12003_holy_war_defender_join_inputs.hpp"
#include "xar_bridge/ordinary_holy_war_cb_cost_v1.hpp"

#include <cstring>
#include <sstream>
#if defined(_MSC_VER)
#include <Windows.h>
#endif

namespace xar::ck3_12002::religion::holy_war_defender_join {
namespace {
inline constexpr std::size_t kCharacterIdentityOffset = 0x18;

template <typename T> T Load(const void *object, std::size_t offset) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset, sizeof(value));
  return value;
}

template <typename Fn, typename... Args>
bool Call(Fn fn, Args... args) noexcept {
  if (!fn) return false;
#if defined(_MSC_VER)
  __try {
#endif
    fn(args...);
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
}

template <typename Fn, typename Result, typename... Args>
bool CallResult(Fn fn, Result &result, Args... args) noexcept {
  if (!fn) return false;
#if defined(_MSC_VER)
  __try {
#endif
    result = fn(args...);
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
}

void FreeNativeRows(void *allocator, void *rows, std::size_t element_size) {
  const auto *vtable = Load<const void *>(allocator, 0);
  const auto release = Load<FreeRows>(vtable, 0x10);
  release(allocator, rows, element_size);
}

class VectorOwner {
 public:
  explicit VectorOwner(const Bindings &bindings) noexcept : bindings_(bindings) {
    value.allocator = bindings.engine_allocator;
  }
  ~VectorOwner() {
    if (value.rows)
      (void)Call(bindings_.free_rows ? bindings_.free_rows : &FreeNativeRows,
                 value.allocator, static_cast<void *>(value.rows), std::size_t{8});
  }
  NativeCharacterVector value{};
 private:
  const Bindings &bindings_;
};

bool Matches(const void *object, std::uint32_t reference) noexcept {
  return object && Load<std::uint32_t>(object, kReferenceIdentityOffset) == reference;
}

bool ActualCharacter(const CoreBindings &core, void *character,
                     std::uint32_t reference) noexcept {
  return character && reference != kAbsentReference &&
      Load<std::uint32_t>(character, kCharacterIdentityOffset) == reference &&
      ResolveCoreCharacter(core, static_cast<std::int32_t>(reference)) == character;
}

FaithFailure ReadFaith(const religion::Bindings &b, void *character,
                       std::optional<std::uint32_t> &rite_id,
                       std::optional<std::uint32_t> &faith_id,
                       void *&faith) noexcept {
  if (!character) return FaithFailure::character_unavailable;
  const auto rite_ref = Load<std::uint32_t>(character, kCharacterRiteIdOffset);
  if (rite_ref == kAbsentReference) return FaithFailure::rite_unavailable;
  rite_id = rite_ref;
  void *rite = nullptr;
  if (!CallResult(b.character_rite, rite, character) || !Matches(rite, rite_ref))
    return FaithFailure::rite_unavailable;
  const auto faith_ref = Load<std::uint32_t>(rite, kRiteFaithIdOffset);
  if (faith_ref == kAbsentReference) return FaithFailure::faith_unavailable;
  faith_id = faith_ref;
  void *character_faith = nullptr;
  if (!CallResult(b.rite_faith, faith, rite) || !Matches(faith, faith_ref) ||
      !CallResult(b.character_faith, character_faith, character) ||
      character_faith != faith)
    return FaithFailure::faith_unavailable;
  return FaithFailure::none;
}

bool SameFrame(const CoreSnapshotPrefix &frame, const Context &c) noexcept {
  return frame.map_ready && frame.has_played_character &&
      frame.played_character_alive && frame.clock.paused &&
      frame.clock.date_raw == c.date_raw &&
      frame.played_character_id == c.played_character_id;
}

bool Fail(Context &out, Failure failure) noexcept {
  out.available = false;
  out.failure = failure;
  out.native_joiner_set_observed = false;
  out.joiners.clear();
  return false;
}

void Quote(std::ostream &out, std::string_view value) {
  constexpr char hex[] = "0123456789abcdef";
  out << '"';
  for (const unsigned char c : value) {
    if (c == '"' || c == '\\') out << '\\' << static_cast<char>(c);
    else if (c < 0x20) out << "\\u00" << hex[c >> 4] << hex[c & 15];
    else out << static_cast<char>(c);
  }
  out << '"';
}

template <typename T>
void Optional(std::ostream &out, const std::optional<T> &value) {
  if (value) out << *value;
  else out << "null";
}
} // namespace

Bindings BindHolyWarDefenderJoinInputsImage12003(
    std::uintptr_t base, std::string_view sha,
    const religion::Bindings &actual_existing_faith) noexcept {
  Bindings b{};
  if (!base || sha != kOrdinaryHolyWarExactSha12003) return b;
  b.enabled = true;
  b.faith = actual_existing_faith;
  b.collector = reinterpret_cast<Collector>(base + kCollectorRva12003);
  b.engine_allocator = reinterpret_cast<void *>(base + kEngineAllocatorRva12003);
  b.free_rows = &FreeNativeRows;
  return b;
}

bool ReadSelectedHolyWarDefenderJoinInputs12003(
    const Bindings &b, void *cb, void *attacker, void *defender,
    const OrdinaryHolyWarDeclarationContextV1 &finalized, Context &out) noexcept {
  out = {};
  out.capture_epoch = finalized.capture_epoch;
  out.native_revision = finalized.native_revision;
  out.public_revision = finalized.public_revision;
  out.date_raw = finalized.date_raw;
  out.played_character_id = finalized.played_character_id;
  out.declaration_id = finalized.declaration_id;
  out.selected = finalized.selected;
  if (finalized.context_additional_role_character_id)
    out.primary_attacker_character_id =
        static_cast<std::uint32_t>(*finalized.context_additional_role_character_id);
  if (finalized.context_recipient_character_id)
    out.primary_defender_character_id =
        static_cast<std::uint32_t>(*finalized.context_recipient_character_id);

  if (!finalized.available)
    return Fail(out, Failure::declaration_context_unavailable);
  if (!b.enabled || !b.faith.core.enabled || !b.collector ||
      !b.engine_allocator || !cb)
    return Fail(out, Failure::bindings_unavailable);

  CoreSnapshotPrefix frame{};
  if (!ReadCoreSnapshot(b.faith.core, frame))
    return Fail(out, Failure::frame_mismatch);
  if (!frame.clock.paused) return Fail(out, Failure::frame_not_paused);
  if (!SameFrame(frame, out)) return Fail(out, Failure::frame_mismatch);
  if (finalized.additional_role_uses_native_fallback ||
      finalized.recipient_uses_native_fallback)
    return Fail(out, Failure::native_role_fallback);
  if (!out.primary_attacker_character_id ||
      !ActualCharacter(b.faith.core, attacker, *out.primary_attacker_character_id))
    return Fail(out, Failure::primary_attacker_unavailable);
  if (!out.primary_defender_character_id ||
      !ActualCharacter(b.faith.core, defender, *out.primary_defender_character_id))
    return Fail(out, Failure::primary_defender_unavailable);

  void *defender_faith = nullptr;
  out.primary_defender_faith_failure =
      ReadFaith(b.faith, defender, out.primary_defender_rite_id,
                out.primary_defender_faith_id, defender_faith);
  out.primary_defender_faith_available =
      out.primary_defender_faith_failure == FaithFailure::none;
  out.cb_flags_raw = Load<std::uint32_t>(cb, kDeclarationsCbFlagsOffset);
  out.defender_faith_can_join = ((*out.cb_flags_raw >> 15) & 1U) != 0;

  if (*out.defender_faith_can_join) {
    VectorOwner native(b);
    if (!Call(b.collector, cb, attacker, defender, &native.value))
      return Fail(out, Failure::native_collection_unavailable);
    if (native.value.count < 0 || native.value.capacity < native.value.count ||
        (native.value.count != 0 && !native.value.rows))
      return Fail(out, Failure::native_vector_invalid);

    out.joiners.reserve(static_cast<std::size_t>(native.value.count));
    for (std::int32_t i = 0; i < native.value.count; ++i) {
      auto *character = native.value.rows[i];
      Joiner row{};
      if (character)
        row.character_id = Load<std::uint32_t>(character, kCharacterIdentityOffset);
      if (!ActualCharacter(b.faith.core, character, row.character_id)) {
        row.failure = FaithFailure::character_unavailable;
        out.joiners.push_back(row);
        continue;
      }

      void *faith = nullptr;
      row.failure = ReadFaith(b.faith, character, row.rite_id, row.faith_id, faith);
      row.row_faith_available = row.failure == FaithFailure::none;
      if (row.row_faith_available && out.primary_defender_faith_available &&
          row.faith_id && out.primary_defender_faith_id)
        row.matches_primary_defender_faith =
            *row.faith_id == *out.primary_defender_faith_id;
      if (row.row_faith_available) {
        if (row.matches_primary_defender_faith &&
            !*row.matches_primary_defender_faith) {
          row.failure = FaithFailure::faith_domain_mismatch;
        } else {
          std::int64_t fervor = 0;
          std::int64_t *result = nullptr;
          if (CallResult(b.faith.faith_fervor, result, faith, &fervor) &&
              result == &fervor) {
            row.faith_fervor_raw = fervor;
            row.row_fervor_available = true;
          } else {
            row.failure = FaithFailure::fervor_unavailable;
          }
        }
      }
      out.joiners.push_back(row);
    }
  }

  CoreSnapshotPrefix after{};
  if (!ReadCoreSnapshot(b.faith.core, after) || !SameFrame(after, out) ||
      !ActualCharacter(b.faith.core, attacker, *out.primary_attacker_character_id) ||
      !ActualCharacter(b.faith.core, defender, *out.primary_defender_character_id) ||
      Load<std::uint32_t>(cb, kDeclarationsCbFlagsOffset) != *out.cb_flags_raw)
    return Fail(out, Failure::state_changed);

  // Empty output and an observed raw fervor of zero remain available. This is
  // the native accepted set, not a reconstructed score or a war-join command.
  out.native_joiner_set_observed = true;
  out.available = true;
  out.failure = Failure::none;
  return true;
}

const char *HolyWarDefenderJoinInputsFailureKey(Failure failure) noexcept {
  switch (failure) {
  case Failure::none: return "none";
  case Failure::bindings_unavailable: return "bindings_unavailable";
  case Failure::declaration_context_unavailable: return "declaration_context_unavailable";
  case Failure::frame_not_paused: return "frame_not_paused";
  case Failure::frame_mismatch: return "frame_mismatch";
  case Failure::native_role_fallback: return "native_role_fallback";
  case Failure::primary_attacker_unavailable: return "primary_attacker_unavailable";
  case Failure::primary_defender_unavailable: return "primary_defender_unavailable";
  case Failure::native_collection_unavailable: return "native_collection_unavailable";
  case Failure::native_vector_invalid: return "native_vector_invalid";
  case Failure::state_changed: return "state_changed";
  }
  return "bindings_unavailable";
}

const char *HolyWarDefenderJoinFaithFailureKey(FaithFailure failure) noexcept {
  switch (failure) {
  case FaithFailure::none: return "none";
  case FaithFailure::character_unavailable: return "character_unavailable";
  case FaithFailure::rite_unavailable: return "rite_unavailable";
  case FaithFailure::faith_unavailable: return "faith_unavailable";
  case FaithFailure::faith_domain_mismatch: return "faith_domain_mismatch";
  case FaithFailure::fervor_unavailable: return "fervor_unavailable";
  }
  return "faith_unavailable";
}

std::string SerializeHolyWarDefenderJoinInputs12003(const Context &c) {
  std::ostringstream out;
  out << std::boolalpha << "{\"schema\":";
  Quote(out, kSchema12003);
  out << ",\"read_only\":true,\"available\":" << c.available
      << ",\"unavailable_reason\":";
  if (c.available) out << "null";
  else Quote(out, HolyWarDefenderJoinInputsFailureKey(c.failure));
  out << ",\"capture_epoch\":" << c.capture_epoch
      << ",\"native_revision\":" << c.native_revision
      << ",\"public_revision\":" << c.public_revision
      << ",\"date_raw\":" << c.date_raw
      << ",\"played_character_id\":" << c.played_character_id
      << ",\"declaration_id\":";
  Quote(out, c.declaration_id);
  out << ",\"selected_declaration\":"
      << SerializeOrdinaryHolyWarSelectedDeclarationV1(c.selected)
      << ",\"primary_attacker_character_id\":";
  Optional(out, c.primary_attacker_character_id);
  out << ",\"primary_defender_character_id\":";
  Optional(out, c.primary_defender_character_id);
  out << ",\"primary_defender_faith_available\":"
      << c.primary_defender_faith_available
      << ",\"primary_defender_faith_unavailable_reason\":";
  if (c.primary_defender_faith_available) out << "null";
  else Quote(out, HolyWarDefenderJoinFaithFailureKey(c.primary_defender_faith_failure));
  out << ",\"primary_defender_rite_id\":";
  Optional(out, c.primary_defender_rite_id);
  out << ",\"primary_defender_faith_id\":";
  Optional(out, c.primary_defender_faith_id);
  out << ",\"cb_flags_raw\":";
  Optional(out, c.cb_flags_raw);
  out << ",\"defender_faith_can_join\":";
  Optional(out, c.defender_faith_can_join);
  out << ",\"native_joiner_set_observed\":" << c.native_joiner_set_observed
      << ",\"joiner_count\":" << c.joiners.size() << ",\"joiners\":[";
  for (std::size_t i = 0; i < c.joiners.size(); ++i) {
    if (i) out << ',';
    const auto &row = c.joiners[i];
    out << "{\"character_id\":" << row.character_id
        << ",\"row_faith_available\":" << row.row_faith_available
        << ",\"row_fervor_available\":" << row.row_fervor_available
        << ",\"unavailable_reason\":";
    if (row.failure == FaithFailure::none) out << "null";
    else Quote(out, HolyWarDefenderJoinFaithFailureKey(row.failure));
    out << ",\"rite_id\":";
    Optional(out, row.rite_id);
    out << ",\"faith_id\":";
    Optional(out, row.faith_id);
    out << ",\"faith_fervor_raw\":";
    Optional(out, row.faith_fervor_raw);
    out << ",\"matches_primary_defender_faith\":";
    Optional(out, row.matches_primary_defender_faith);
    out << '}';
  }
  out << "],\"raw_scale\":100000,\"unit\":\"fervor_points\","
         "\"is_final_join_score\":false}";
  return out.str();
}

} // namespace xar::ck3_12002::religion::holy_war_defender_join
