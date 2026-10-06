#include "xar_bridge/religion_reform12003_creation_terms.hpp"

#include <cstring>
#include <utility>

namespace xar::ck3_12002::religion_reform::creation_terms12003 {
namespace {
template <typename T> T Load(const void *object, std::size_t offset) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset,
              sizeof(value));
  return value;
}

bool Matches(const void *object, std::uint32_t id) noexcept {
  return id != religion::kAbsentReference && object &&
      Load<std::uint32_t>(object, religion::kReferenceIdentityOffset) == id;
}

// Same full-generation storage layout already used by the current draft Tenet
// source reader. The low 24 bits index a slot; object+8 verifies the full ID.
void *Resolve(void *const *global, std::uint32_t id) noexcept {
  if (!global || !*global || id == religion::kAbsentReference) return nullptr;
  const auto *storage = *global;
  const auto index = id & 0xFFFFFFU;
  if (index >= Load<std::uint32_t>(storage, 0x2C)) return nullptr;
  const auto *entries = Load<const void *>(storage, 0x20);
  if (!entries) return nullptr;
  auto *object = Load<void *>(entries, static_cast<std::size_t>(index) * 16 + 8);
  return Matches(object, id) ? object : nullptr;
}

bool Fail(DraftCreationTerms &out, const char *reason) {
  out.failure = reason;
  return false;
}

bool ReadOnce(const Bindings &b, const DraftWindowView &window,
    const void *actor_faith, std::uint32_t actor_faith_id,
    std::uint64_t epoch, DraftCreationTerms &out) {
  if (!window.available)
    return Fail(out, window.failure == DraftWindowFailure::none
        ? "current_window_unavailable" : DraftWindowFailureKey(window.failure));
  if (!window.present) return Fail(out, "current_window_absent");
  if (!window.visible) return Fail(out, "current_window_hidden");
  if (!window.window || !window.source_rite_id ||
      window.played_character_id == religion::kAbsentReference ||
      *window.source_rite_id == religion::kAbsentReference)
    return Fail(out, "draft_subject_unavailable");
  if (window.capture_epoch != epoch ||
      Load<std::uint32_t>(window.window, kDraftWindowActorIdOffset) !=
          window.played_character_id ||
      Load<std::uint32_t>(window.window, kDraftWindowRiteIdOffset) !=
          *window.source_rite_id)
    return Fail(out, "state_changed");

  auto *source_rite = Resolve(b.rite_storage_global, *window.source_rite_id);
  if (!source_rite) return Fail(out, "source_rite_unavailable");
  const auto source_faith_id =
      Load<std::uint32_t>(source_rite, religion::kRiteFaithIdOffset);
  auto *source_faith = Resolve(b.faith_storage_global, source_faith_id);
  if (!source_faith) return Fail(out, "source_faith_unavailable");
  const auto main_rite_id =
      Load<std::uint32_t>(source_faith, religion::kFaithMainRiteIdOffset);
  auto *main_rite = Resolve(b.rite_storage_global, main_rite_id);
  if (!main_rite) return Fail(out, "source_main_rite_unavailable");
  if (!Matches(actor_faith, actor_faith_id) ||
      Resolve(b.faith_storage_global, actor_faith_id) != actor_faith)
    return Fail(out, "actor_faith_unavailable");

  std::int64_t divergence{};
  if (b.draft_divergence(&divergence, window.window) != &divergence)
    return Fail(out, "draft_divergence_unavailable");
  const auto threshold = Load<std::int64_t>(b.creation_threshold_raw, 0);
  // 14FC93B/14FC941 compares signed int64 and includes equality. The native
  // 2BDCA90 predicate may additionally return true for actor Faith unreformed.
  const bool ui_creates_faith = divergence >= threshold;
  const bool native_creates_faith = b.native_create_faith_or_reform(
      actor_faith, static_cast<const std::byte *>(window.window) +
          kWindowPriceDraftOffset);

  if (Load<std::uint32_t>(window.window, kDraftWindowActorIdOffset) !=
          window.played_character_id ||
      Load<std::uint32_t>(window.window, kDraftWindowRiteIdOffset) !=
          *window.source_rite_id ||
      Resolve(b.rite_storage_global, *window.source_rite_id) != source_rite ||
      Load<std::uint32_t>(source_rite, religion::kRiteFaithIdOffset) != source_faith_id ||
      Resolve(b.faith_storage_global, source_faith_id) != source_faith ||
      Load<std::uint32_t>(source_faith, religion::kFaithMainRiteIdOffset) != main_rite_id ||
      Resolve(b.rite_storage_global, main_rite_id) != main_rite ||
      Resolve(b.faith_storage_global, actor_faith_id) != actor_faith)
    return Fail(out, "state_changed");

  out.source_rite_id = window.source_rite_id;
  out.source_faith_id = source_faith_id;
  out.source_main_rite_id = main_rite_id;
  out.actor_faith_id = actor_faith_id;
  out.draft_divergence_raw = divergence;
  out.faith_creation_threshold_raw = threshold;
  out.divergence_results_in_faith_creation = ui_creates_faith;
  out.native_create_faith_or_reform = native_creates_faith;
  out.available = true;
  out.failure = "none";
  return true;
}

bool ReadGuarded(const Bindings &b, const DraftWindowView &window,
    const void *actor_faith, std::uint32_t actor_faith_id,
    std::uint64_t epoch, DraftCreationTerms &out) {
#if defined(_WIN32) && defined(_MSC_VER)
  __try { return ReadOnce(b, window, actor_faith, actor_faith_id, epoch, out); }
  __except (1) { out.failure = "native_observation_unavailable"; return false; }
#else
  return ReadOnce(b, window, actor_faith, actor_faith_id, epoch, out);
#endif
}

std::string Quote(std::string_view value) {
  std::string out = "\"";
  constexpr char hex[] = "0123456789abcdef";
  for (const unsigned char c : value) {
    if (c == '\\' || c == '"') { out += '\\'; out += static_cast<char>(c); }
    else if (c < 32) { out += "\\u00"; out += hex[c >> 4]; out += hex[c & 15]; }
    else out += static_cast<char>(c);
  }
  return out + '"';
}
const char *Boolean(bool value) noexcept { return value ? "true" : "false"; }
template <typename T> std::string Number(const std::optional<T> &value) {
  return value ? std::to_string(*value) : "null";
}
std::string OptionalBoolean(const std::optional<bool> &value) {
  return value ? Boolean(*value) : "null";
}
} // namespace

Bindings BindDraftCreationTermsImage12003(std::uintptr_t base,
    std::string_view sha) noexcept {
  Bindings b{};
  if (!base || sha != ck3_12003::kExecutableSha256) return b;
  b.rite_storage_global = reinterpret_cast<void *const *>(base + kRiteStorageGlobalRva);
  b.faith_storage_global = reinterpret_cast<void *const *>(base + kFaithStorageGlobalRva);
  b.draft_divergence = reinterpret_cast<DraftDivergenceGetter>(base + kDraftDivergenceRva);
  b.creation_threshold_raw = reinterpret_cast<const std::int64_t *>(
      base + kFaithCreationThresholdRva);
  b.native_create_faith_or_reform = reinterpret_cast<NativeCreateFaithOrReform>(
      base + kNativeCreateFaithOrReformRva);
  b.enabled = true;
  return b;
}

bool ReadCurrentDraftCreationTerms12003(const Bindings &b,
    const DraftWindowView &window, const void *actor_faith,
    std::uint32_t actor_faith_id, std::uint64_t epoch,
    DraftCreationTerms &out) noexcept {
  out = {};
  out.capture_epoch = epoch;
  out.date_raw = window.date_raw;
  out.played_character_id = window.played_character_id;
  if (!b.enabled || !b.rite_storage_global || !b.faith_storage_global ||
      !b.draft_divergence || !b.creation_threshold_raw ||
      !b.native_create_faith_or_reform) return false;
  DraftCreationTerms candidate{};
  candidate.capture_epoch = epoch;
  candidate.date_raw = window.date_raw;
  candidate.played_character_id = window.played_character_id;
  if (!ReadGuarded(b, window, actor_faith, actor_faith_id, epoch, candidate)) {
    // Only owner-frame metadata survives unavailable/hidden/failed captures.
    out.failure = std::move(candidate.failure);
    return false;
  }
  out = std::move(candidate);
  return true;
}

std::string SerializeCurrentDraftCreationTerms12003(const DraftCreationTerms &v) {
  return "{\"schema\":\"ck3_12003_current_draft_creation_terms_v1\""
      ",\"game_version\":\"1.20.0.3\",\"executable_sha256\":" +
      Quote(ck3_12003::kExecutableSha256) +
      ",\"available\":" + Boolean(v.available) +
      ",\"unavailable_reason\":" + (v.available ? "null" : Quote(v.failure)) +
      ",\"capture_epoch\":" + std::to_string(v.capture_epoch) +
      ",\"date_raw\":" + std::to_string(v.date_raw) +
      ",\"played_character_id\":" + std::to_string(v.played_character_id) +
      ",\"source_rite_id\":" + Number(v.source_rite_id) +
      ",\"source_faith_id\":" + Number(v.source_faith_id) +
      ",\"source_main_rite_id\":" + Number(v.source_main_rite_id) +
      ",\"actor_faith_id\":" + Number(v.actor_faith_id) +
      ",\"draft_divergence_raw\":" + Number(v.draft_divergence_raw) +
      ",\"faith_creation_threshold_raw\":" + Number(v.faith_creation_threshold_raw) +
      ",\"divergence_results_in_faith_creation\":" +
      OptionalBoolean(v.divergence_results_in_faith_creation) +
      ",\"native_create_faith_or_reform\":" +
      OptionalBoolean(v.native_create_faith_or_reform) +
      ",\"raw_scale\":100000}";
}
} // namespace xar::ck3_12002::religion_reform::creation_terms12003
