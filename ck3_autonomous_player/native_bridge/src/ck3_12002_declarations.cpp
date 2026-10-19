#include "xar_bridge/ck3_12002_declarations.hpp"

#if defined(XAR_CK3_ENABLE_ORDINARY_HOLY_WAR_DECLARATION_CONTEXT_PRIVATE_V1)
#include "xar_bridge/ordinary_holy_war_cb_cost_v1.hpp"
#include "xar_bridge/ck3_12003_holy_war_defender_join_inputs.hpp"
#endif

#include <array>
#include <algorithm>
#include <chrono>
#include <cstdlib>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <utility>
#include <tuple>
#include <unordered_map>
#include <unordered_set>

namespace xar::ck3_12002 {
namespace {

template <class T> T Load(const void *p, std::size_t offset) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(p) + offset, sizeof(T));
  return value;
}
template <class T> void Store(void *p, std::size_t offset, T value) noexcept {
  std::memcpy(static_cast<std::byte *>(p) + offset, &value, sizeof(T));
}

void *ResolveCharacter(const CoreBindings &b, std::int32_t id) noexcept {
  if (!b.character_storage_slot || id == -1) return nullptr;
  void *storage = *b.character_storage_slot;
  if (!storage) return nullptr;
  const auto index = static_cast<std::uint32_t>(id) & 0xFFFFFFU;
  const auto count = Load<std::int32_t>(storage, 0x2C);
  void *slots = Load<void *>(storage, 0x20);
  if (!slots || count <= 0 || count > 1'000'000 ||
      index >= static_cast<std::uint32_t>(count)) return nullptr;
  void *character = Load<void *>(slots, index * 0x10ULL + 8);
  return character && Load<std::int32_t>(character, 0x18) == id
             ? character : nullptr;
}

bool Ready(const DeclarationsBindings &b) noexcept {
  return b.enabled && b.configuration_scratch && b.get_cb_database &&
         b.evaluate_cb && b.destroy_configuration;
}
bool Database(const DeclarationsBindings &b, void *&types,
              std::int32_t &count) noexcept {
  void *db = b.get_cb_database();
  if (!db) return false;
  types = Load<void *>(db, kDeclarationsCbArrayOffset);
  count = Load<std::int32_t>(db, kDeclarationsCbCountOffset);
  return count >= 0 && count <= 10'000 && (!count || types);
}
bool EnabledType(const void *type) noexcept {
  if (!type) return false;
  void *rule = Load<void *>(type, kDeclarationsCbRuleOffset);
  return rule && !Load<std::uint8_t>(rule, kDeclarationsCbDisabledOffset);
}
bool Scratch(const DeclarationsBindings &b, void *&data,
             std::int32_t &count) noexcept {
  data = Load<void *>(b.configuration_scratch, 0);
  const auto capacity = Load<std::int32_t>(b.configuration_scratch, 8);
  count = Load<std::int32_t>(b.configuration_scratch, 12);
  return capacity >= 0 && count >= 0 && count <= capacity && count <= 10'000 &&
         (!count || data);
}
bool Clear(const DeclarationsBindings &b) noexcept {
  void *data{};
  std::int32_t count{};
  if (!Scratch(b, data, count)) return false;
  for (std::int32_t i = 0; i < count; ++i)
    b.destroy_configuration(static_cast<std::byte *>(data) +
                            i * kDeclarationsConfigurationSize);
  Store(b.configuration_scratch, 12, std::int32_t{0});
  return true;
}
bool IntArray(const void *array, std::vector<std::int32_t> &out) noexcept {
  const auto cap = Load<std::int32_t>(array, 8);
  const auto count = Load<std::int32_t>(array, 12);
  const auto data = Load<const std::int32_t *>(array, 0);
  if (cap < 0 || count < 0 || count > cap || count > 1'000'000 ||
      (count && !data)) return false;
  out.clear();
  if (count) out.assign(data, data + count);
  return true;
}
bool TypeKey(const void *type, std::string &out) noexcept {
  const auto storage = static_cast<const std::byte *>(type) + 0x18;
  const auto size = Load<std::size_t>(storage, 0x10);
  const auto cap = Load<std::size_t>(storage, 0x18);
  if (size > cap || size > 4096) return false;
  const char *data = cap <= 15 ? reinterpret_cast<const char *>(storage)
                              : Load<const char *>(storage, 0);
  if (size && !data) return false;
  out.assign(data ? data : "", size);
  return true;
}
bool Choices(const DeclarationsBindings &b, void *type, std::int32_t target,
             std::int32_t cb_index,
             std::vector<game::DeclarableWarSnapshot> &out) noexcept {
  std::string key;
  void *data{};
  std::int32_t count{};
  if (!TypeKey(type, key) || !Scratch(b, data, count)) return false;
  const bool combined = !count ||
      (Load<std::uint32_t>(type, kDeclarationsCbFlagsOffset) & (1U << 20));
  game::DeclarableWarSnapshot merged{target, cb_index, key, -1, -1, {}};
  for (std::int32_t i = 0; i < count; ++i) {
    auto *configuration = static_cast<std::byte *>(data) +
                          i * kDeclarationsConfigurationSize;
    game::DeclarableWarSnapshot row{target, cb_index, key, i,
                                    Load<std::int32_t>(configuration, 0), {}};
    if (!IntArray(configuration + 8, row.target_title_ids)) return false;
    if (combined) {
      merged.target_title_ids.insert(merged.target_title_ids.end(),
                                    row.target_title_ids.begin(),
                                    row.target_title_ids.end());
    } else if (!row.target_title_ids.empty()) out.push_back(std::move(row));
  }
  if (combined) out.push_back(std::move(merged));
  return true;
}
bool Target(const DeclarationsBindings &b, void *types, std::int32_t count,
            void *actor, void *target, std::int32_t target_id,
            std::vector<game::DeclarableWarSnapshot> &out) noexcept {
  for (std::int32_t i = 0; i < count; ++i) {
    void *type = Load<void *>(types, i * sizeof(void *));
    if (!EnabledType(type)) continue;
    if (!Clear(b)) return false;
    const bool available = b.evaluate_cb(type, actor, target,
                                        b.configuration_scratch,
                                        false, false, nullptr);
    const bool materialized = !available || Choices(b, type, target_id, i, out);
    const bool cleared = Clear(b);
    if (!materialized || !cleared) return false;
  }
  return true;
}

// Definition records are immutable while this paused main-thread query runs.
// Keep their original database ordinals and target-major evaluator order.
struct EnabledCb {
  void *type;
  std::int32_t ordinal;
  std::uint64_t evaluations = 0, available = 0, rows = 0;
  std::uint64_t evaluate_ns = 0, materialize_and_clear_ns = 0;
};

using ProfileClock = std::chrono::steady_clock;
std::uint64_t ElapsedNs(ProfileClock::time_point start) noexcept {
  return static_cast<std::uint64_t>(std::chrono::duration_cast<
      std::chrono::nanoseconds>(ProfileClock::now() - start).count());
}

void JsonString(std::ostream &stream, std::string_view value) {
  constexpr char hex[] = "0123456789abcdef";
  stream << '"';
  for (const unsigned char c : value) {
    if (c == '"' || c == '\\') stream << '\\' << static_cast<char>(c);
    else if (c < 0x20) stream << "\\u00" << hex[c >> 4] << hex[c & 15];
    else stream << static_cast<char>(c);
  }
  stream << '"';
}

// One opt-in record per complete query, never per target/evaluation. Logging
// failure cannot change a native query's result. The default path has no clock
// reads, file writes or per-CB counter updates. All CBs and target order remain.
auto ProfilePath() noexcept {
#if defined(_WIN32)
#if defined(_MSC_VER)
  // This owning-thread query reads the launch environment without mutating it.
#pragma warning(push)
#pragma warning(disable : 4996)
#endif
  const auto path = _wgetenv(L"XAR_CK3_DECLARATIONS_PROFILE_JSONL");
#if defined(_MSC_VER)
#pragma warning(pop)
#endif
  return path;
#else
  return std::getenv("XAR_CK3_DECLARATIONS_PROFILE_JSONL");
#endif
}
struct QueryProfile {
  decltype(ProfilePath()) path = ProfilePath();
  const CoreSnapshotPrefix &frame;
  const std::vector<EnabledCb> &enabled;
  ProfileClock::time_point start{};
  std::uint64_t targets = 0, result_rows = 0;
  bool success = false;
  DeclarationsCandidateVariantV1 variant = DeclarationsCandidateVariantV1::full;
  const DeclarationsCandidateDiagnosticV1 *candidate_diagnostic = nullptr;
  bool active() const noexcept { return path && *path; }
  QueryProfile(const CoreSnapshotPrefix &current,
               const std::vector<EnabledCb> &definitions) noexcept
      : frame(current), enabled(definitions) {
    if (active()) start = ProfileClock::now();
  }
  ~QueryProfile() noexcept {
    if (!active()) return;
    const auto total_ns = ElapsedNs(start);
    try {
      std::ofstream stream(std::filesystem::path(path),
                           std::ios::binary | std::ios::app);
      if (!stream) return;
      const auto unix_ns = std::chrono::duration_cast<std::chrono::nanoseconds>(
          std::chrono::system_clock::now().time_since_epoch()).count();
      stream << "{\"schema\":\"ck3-declarable-query-profile-v1\","
             << "\"recorded_unix_ns\":" << unix_ns
             << ",\"actor_character_id\":" << frame.played_character_id
             << ",\"date_raw\":" << frame.clock.date_raw
             << ",\"success\":" << (success ? "true" : "false")
             << ",\"total_ns\":" << total_ns
             << ",\"targets\":" << targets
             << ",\"result_rows\":" << result_rows
             << ",\"enabled_cb_count\":" << enabled.size() << ",\"casus_belli\":[";
      bool first = true;
      for (const auto &cb : enabled) {
        if (!first) stream << ',';
        first = false;
        std::string key;
        const bool key_read = TypeKey(cb.type, key);
        stream << "{\"ordinal\":" << cb.ordinal << ",\"key\":";
        if (key_read) JsonString(stream, key);
        else stream << "null";
        stream << ",\"evaluations\":" << cb.evaluations
               << ",\"available\":" << cb.available
               << ",\"rows\":" << cb.rows
               << ",\"evaluate_ns\":" << cb.evaluate_ns
               << ",\"materialize_and_clear_ns\":" << cb.materialize_and_clear_ns << '}';
      }
      stream << ']';
      if (candidate_diagnostic) {
        const auto &d = *candidate_diagnostic;
        stream << ",\"candidate_variant\":\""
               << (variant == DeclarationsCandidateVariantV1::shadow ? "shadow-v1" : "cb-first-v1")
               << "\",\"candidate_source_qualified\":" << (d.source_qualified ? "true" : "false")
               << ",\"baseline_compared\":" << (d.baseline_compared ? "true" : "false")
               << ",\"same_frame\":" << (d.same_frame ? "true" : "false")
               << ",\"tuple_sets_equal\":" << (d.tuple_sets_equal ? "true" : "false")
               << ",\"qualified_source_manifest_sha256\":";
        JsonString(stream, d.qualified_source_manifest_sha256);
        stream << ",\"candidate_casus_belli\":[";
        bool first_candidate = true;
        for (const auto &cb : d.casus_belli) {
          if (!first_candidate) stream << ',';
          first_candidate = false;
          stream << "{\"ordinal\":" << cb.ordinal << ",\"key\":";
          JsonString(stream, cb.key);
          stream << ",\"full_targets\":" << cb.full_targets
                 << ",\"candidates\":" << cb.candidates
                 << ",\"evaluations\":" << cb.evaluations
                 << ",\"baseline_evaluations\":" << cb.baseline_evaluations
                 << ",\"candidate_rows\":" << cb.candidate_rows
                 << ",\"baseline_rows\":" << cb.baseline_rows
                 << ",\"missing_tuples\":" << cb.missing_tuples
                 << ",\"extra_tuples\":" << cb.extra_tuples
                 << ",\"necessary_conditions\":" << cb.necessary_conditions
                 << ",\"native_target_titles_mode\":" << cb.native_target_titles_mode
                 << ",\"native_realm_index_used\":" << (cb.native_realm_index_used ? "true" : "false")
                 << ",\"projected_candidate_evaluations\":" << cb.projected_candidate_evaluations
                 << ",\"actor_precheck_qualified\":" << (cb.actor_precheck_qualified ? "true" : "false")
                 << ",\"actor_precheck\":\""
                 << (cb.actor_precheck == DeclarationsCandidateFactV1::no ? "no" :
                     cb.actor_precheck == DeclarationsCandidateFactV1::yes ? "yes" : "unknown")
                 << "\",\"actor_precheck_ns\":" << cb.actor_precheck_ns
                 << ",\"definition_source_sha256\":";
          JsonString(stream, cb.definition_source_sha256);
          stream << '}';
        }
        stream << ']';
        stream << ",\"native_realm_index_complete\":" << (d.native_realm_index_complete ? "true" : "false")
               << ",\"native_realm_index_entries\":" << d.native_realm_index_entries;
        stream << ",\"qualified_actor_source_manifest_sha256\":";
        JsonString(stream, d.qualified_actor_source_manifest_sha256);
      }
      stream << "}\n";
    } catch (...) { /* Diagnostic output is independent of gameplay. */ }
  }
};

bool CachedEvaluation(const DeclarationsBindings &b, EnabledCb &cb,
                  void *actor, void *target, std::int32_t target_id,
                  std::vector<game::DeclarableWarSnapshot> &out,
                  bool &scratch_is_clear, bool profile) noexcept {
    // The preceding evaluation already validated and cleared this scratch.
    // There is no native call between that clear and the next evaluation.
    if (!scratch_is_clear && !Clear(b)) return false;
    const auto evaluation_start = profile ? ProfileClock::now() : ProfileClock::time_point{};
    const bool available = b.evaluate_cb(cb.type, actor, target,
                                        b.configuration_scratch,
                                        false, false, nullptr);
    if (profile) {
      cb.evaluate_ns += ElapsedNs(evaluation_start);
      ++cb.evaluations;
      if (available) ++cb.available;
    }
    const auto materialize_start = profile ? ProfileClock::now() : ProfileClock::time_point{};
    const auto previous_rows = out.size();
    const bool materialized =
        !available || Choices(b, cb.type, target_id, cb.ordinal, out);
    scratch_is_clear = Clear(b);
    if (profile) {
      cb.materialize_and_clear_ns += ElapsedNs(materialize_start);
      cb.rows += out.size() - previous_rows;
    }
    if (!materialized || !scratch_is_clear) return false;
  return true;
}

bool CachedTarget(const DeclarationsBindings &b, std::vector<EnabledCb> &enabled,
                  void *actor, void *target, std::int32_t target_id,
                  std::vector<game::DeclarableWarSnapshot> &out,
                  bool &scratch_is_clear, bool profile) noexcept {
  for (auto &cb : enabled)
    if (!CachedEvaluation(b, cb, actor, target, target_id, out,
                          scratch_is_clear, profile)) return false;
  return true;
}

bool Sha256Text(std::string_view value) noexcept {
  return value.size() == 64 && std::all_of(value.begin(), value.end(), [](char c) {
    return (c >= '0' && c <= '9') || (c >= 'a' && c <= 'f') || (c >= 'A' && c <= 'F');
  });
}

std::uint32_t CandidateConditions(const DeclarationsCandidateOptionsV1 &options,
                                  std::string_view key) noexcept {
  if (!Sha256Text(options.qualified_source_manifest_sha256)) return 0;
  const DeclarationsCandidateRuleV1 *found = nullptr;
  for (const auto &rule : options.qualified_rules) {
    if (rule.key != key) continue;
    if (found || !Sha256Text(rule.definition_source_sha256) ||
        (rule.necessary_conditions & ~std::uint32_t{3})) return 0;
    found = &rule;
  }
  return found ? found->necessary_conditions : 0;
}

bool ActorCandidateQualified(const DeclarationsCandidateOptionsV1 &options,
                             std::string_view key) noexcept {
  if (!Sha256Text(options.qualified_actor_source_manifest_sha256)) return false;
  const DeclarationsCandidateActorRuleV1 *found = nullptr;
  for (const auto &rule : options.qualified_actor_rules) {
    if (rule.key != key) continue;
    if (found || !Sha256Text(rule.definition_source_sha256) ||
        !Sha256Text(rule.actor_trigger_closure_sha256)) return false;
    found = &rule;
  }
  return found != nullptr;
}

bool TupleLess(const game::DeclarableWarSnapshot &a,
               const game::DeclarableWarSnapshot &b) noexcept {
  return std::tie(a.target_character_id, a.casus_belli_index, a.casus_belli_key,
                  a.configuration_index, a.claimant_character_id, a.target_title_ids) <
         std::tie(b.target_character_id, b.casus_belli_index, b.casus_belli_key,
                  b.configuration_index, b.claimant_character_id, b.target_title_ids);
}

void CompareCandidateTuples(const std::vector<game::DeclarableWarSnapshot> &baseline,
                            const std::vector<game::DeclarableWarSnapshot> &candidate,
                            DeclarationsCandidateDiagnosticV1 &diagnostic) {
  for (auto &cb : diagnostic.casus_belli) {
    std::vector<game::DeclarableWarSnapshot> full, selected;
    for (const auto &row : baseline) if (row.casus_belli_index == cb.ordinal) full.push_back(row);
    for (const auto &row : candidate) if (row.casus_belli_index == cb.ordinal) selected.push_back(row);
    cb.baseline_rows = full.size(); cb.candidate_rows = selected.size();
    std::sort(full.begin(), full.end(), TupleLess);
    std::sort(selected.begin(), selected.end(), TupleLess);
    std::size_t f = 0, s = 0;
    while (f < full.size() && s < selected.size()) {
      if (TupleLess(full[f], selected[s])) { ++cb.missing_tuples; ++f; }
      else if (TupleLess(selected[s], full[f])) { ++cb.extra_tuples; ++s; }
      else { ++f; ++s; }
    }
    cb.missing_tuples += full.size() - f;
    cb.extra_tuples += selected.size() - s;
  }
  diagnostic.tuple_sets_equal = std::all_of(diagnostic.casus_belli.begin(),
      diagnostic.casus_belli.end(), [](const auto &cb) {
        return cb.missing_tuples == 0 && cb.extra_tuples == 0;
      });
}

struct alignas(8) ContextStorage { std::array<std::byte, kDeclarationsContextSize> bytes{}; };
struct alignas(8) SendStorage { std::array<std::byte, kDeclarationsSendSize> bytes{}; };
static_assert(sizeof(ContextStorage) == 0x338);
static_assert(sizeof(SendStorage) == 0x368);

} // namespace

DeclarationsBindings BindDeclarationsImage(std::uintptr_t base,
                                            std::string_view sha) noexcept {
  DeclarationsBindings b{};
  if (!base || sha != kExecutableSha256) return b;
  b.core = BindCoreImage(base, sha);
  b.commands = BindCommandImage(base, sha);
  b.configuration_scratch = reinterpret_cast<void *>(base + kDeclarationsScratchRva);
  b.get_cb_database = reinterpret_cast<DeclarationsDatabaseGetter>(base + kDeclarationsCbDatabaseGetterRva);
  b.get_interaction_database = reinterpret_cast<DeclarationsDatabaseGetter>(base + kDeclarationsInteractionDatabaseGetterRva);
  b.evaluate_cb = reinterpret_cast<DeclarationsEvaluateCb>(base + kDeclarationsEvaluateCbRva);
  b.destroy_configuration = reinterpret_cast<DeclarationsDestroy>(base + kDeclarationsDestroyConfigurationRva);
  b.construct_context = reinterpret_cast<DeclarationsConstructContext>(base + kDeclarationsConstructContextRva);
  b.refresh_context = reinterpret_cast<DeclarationsRefreshContext>(base + kDeclarationsRefreshContextRva);
  b.finalize_context = reinterpret_cast<DeclarationsDestroy>(base + kDeclarationsFinalizeContextRva);
  b.validate_context = reinterpret_cast<DeclarationsValidateContext>(base + kDeclarationsValidateContextRva);
  b.destroy_context = reinterpret_cast<DeclarationsDestroy>(base + kDeclarationsDestroyContextRva);
  b.construct_send = reinterpret_cast<DeclarationsConstructSend>(base + kDeclarationsConstructSendRva);
  b.copy_int_array = reinterpret_cast<DeclarationsCopyIntArray>(base + kDeclarationsCopyIntArrayRva);
  b.append_int_array = reinterpret_cast<DeclarationsAppendIntArray>(base + kDeclarationsAppendIntArrayRva);
  b.war_declaration_vtable = base + kDeclarationsWarVtableRva;
  b.send_primary_vtable = base + kDeclarationsSendPrimaryVtableRva;
  b.send_secondary_vtable = base + kDeclarationsSendSecondaryVtableRva;
  b.enabled = true;
  return b;
}

game::ReadDeclarableWarsResult ReadDeclarableWarsForTarget(
    const DeclarationsBindings &b, std::int32_t target_id,
    std::vector<game::DeclarableWarSnapshot> &out) noexcept {
  out.clear();
  CoreSnapshotPrefix current{};
  if (!Ready(b) || !ReadCoreSnapshot(b.core, current) || !current.map_ready ||
      !current.clock.paused) return game::ReadDeclarableWarsResult::unavailable;
  if (!current.has_played_character || !current.played_character_alive)
    return game::ReadDeclarableWarsResult::no_played_character;
  void *actor = ResolveCharacter(b.core, current.played_character_id);
  void *target = ResolveCharacter(b.core, target_id);
  if (!target || target == actor || Load<void *>(target, kCharacterDeathDataOffset))
    return game::ReadDeclarableWarsResult::target_not_found;
  void *types{};
  std::int32_t count{};
  std::vector<game::DeclarableWarSnapshot> result;
  if (!actor || !Database(b, types, count) ||
      !Target(b, types, count, actor, target, target_id, result))
    return game::ReadDeclarableWarsResult::unavailable;
  out = std::move(result);
  return game::ReadDeclarableWarsResult::available;
}

static bool ReadDeclarableWarsFull(const DeclarationsBindings &b,
                       std::vector<game::DeclarableWarSnapshot> &out,
                       bool record_profile = true,
                       std::vector<EnabledCb> *counter_output = nullptr) noexcept {
  out.clear();
  CoreSnapshotPrefix current{};
  if (!Ready(b) || !ReadCoreSnapshot(b.core, current) || !current.map_ready ||
      !current.clock.paused || !current.has_played_character ||
      !current.played_character_alive) return false;
  void *actor = ResolveCharacter(b.core, current.played_character_id);
  void *storage = b.core.character_storage_slot ? *b.core.character_storage_slot : nullptr;
  if (!actor || !storage) return false;
  void *slots = Load<void *>(storage, 0x20);
  const auto cap = Load<std::int32_t>(storage, 0x2C);
  if (!slots || cap <= 0 || cap > 1'000'000) return false;
  void *types{};
  std::int32_t count{};
  if (!Database(b, types, count)) return false;
  std::vector<game::DeclarableWarSnapshot> result;
  std::vector<EnabledCb> enabled;
  QueryProfile profile(current, enabled);
  if (!record_profile) profile.path = nullptr;
  bool definitions_read = false, scratch_is_clear = false;
  for (std::int32_t i = 0; i < cap; ++i) {
    void *target = Load<void *>(slots, i * 0x10ULL + 8);
    if (!target || target == actor || Load<void *>(target, kCharacterDeathDataOffset)) continue;
    const auto id = Load<std::int32_t>(target, 0x18);
    if ((static_cast<std::uint32_t>(id) & 0xFFFFFFU) != static_cast<std::uint32_t>(i)) continue;
    if (!definitions_read) {
      enabled.reserve(static_cast<std::size_t>(count));
      for (std::int32_t cb = 0; cb < count; ++cb) {
        void *type = Load<void *>(types, cb * sizeof(void *));
        if (EnabledType(type)) enabled.push_back({type, cb});
      }
      definitions_read = true;
    }
    if (profile.active()) ++profile.targets;
    if (!CachedTarget(b, enabled, actor, target, id, result, scratch_is_clear,
                      profile.active() || counter_output))
      return false;
  }
  profile.result_rows = result.size();
  profile.success = true;
  if (counter_output) *counter_output = enabled;
  out = std::move(result);
  return true;
}

bool ReadDeclarableWars(const DeclarationsBindings &b,
                       std::vector<game::DeclarableWarSnapshot> &out) noexcept {
  auto options = b.candidate_options;
  if (!options.runtime_policy_path.empty()) {
    // Query-local control only; bounded read and no automatic promotion after
    // shadow. Root may atomically switch this file without restarting CK3.
    options.variant = DeclarationsCandidateVariantV1::full;
    std::ifstream stream(std::filesystem::path(options.runtime_policy_path), std::ios::binary);
    std::array<char, 33> bytes{};
    stream.read(bytes.data(), bytes.size());
    const auto count = stream.gcount();
    if (count > 0 && count <= 32 && stream.eof()) {
      std::string_view value(bytes.data(), static_cast<std::size_t>(count));
      if (value.ends_with("\r\n")) value.remove_suffix(2);
      else if (value.ends_with("\n")) value.remove_suffix(1);
      if (value == "shadow-v1") options.variant = DeclarationsCandidateVariantV1::shadow;
      else if (value == "cb-first-v1") options.variant = DeclarationsCandidateVariantV1::cb_first;
    }
  }
  return ReadDeclarableWarsWithCandidatesV1(b, options, out);
}

bool ReadDeclarableWarsWithCandidatesV1(
    const DeclarationsBindings &b, const DeclarationsCandidateOptionsV1 &options,
    std::vector<game::DeclarableWarSnapshot> &out,
    DeclarationsCandidateDiagnosticV1 *requested_diagnostic) noexcept {
  out.clear();
  if (requested_diagnostic) *requested_diagnostic = {};
  if (options.variant != DeclarationsCandidateVariantV1::cb_first &&
      options.variant != DeclarationsCandidateVariantV1::shadow)
    return ReadDeclarableWarsFull(b, out);
  CoreSnapshotPrefix current{};
  if (!Ready(b) || !ReadCoreSnapshot(b.core, current) || !current.map_ready ||
      !current.clock.paused || !current.has_played_character ||
      !current.played_character_alive) return false;
  void *actor = ResolveCharacter(b.core, current.played_character_id);
  void *storage = b.core.character_storage_slot ? *b.core.character_storage_slot : nullptr;
  if (!actor || !storage) return false;
  void *slots = Load<void *>(storage, 0x20), *types{};
  const auto capacity = Load<std::int32_t>(storage, 0x2C);
  std::int32_t count{};
  if (!slots || capacity <= 0 || capacity > 1'000'000 || !Database(b, types, count)) return false;
  std::vector<EnabledCb> enabled;
  DeclarationsCandidateDiagnosticV1 diagnostic;
  QueryProfile profile(current, enabled);
  profile.variant = options.variant; profile.candidate_diagnostic = &diagnostic;
  struct CandidateTarget { void *object; std::int32_t id; };
  std::vector<CandidateTarget> targets;
  for (std::int32_t i = 0; i < capacity; ++i) {
    void *target = Load<void *>(slots, i * 0x10ULL + 8);
    if (!target || target == actor || Load<void *>(target, kCharacterDeathDataOffset)) continue;
    const auto id = Load<std::int32_t>(target, 0x18);
    if ((static_cast<std::uint32_t>(id) & 0xFFFFFFU) == static_cast<std::uint32_t>(i))
      targets.push_back({target, id});
  }
  std::vector<std::uint32_t> conditions;
  diagnostic.source_qualified = Sha256Text(options.qualified_source_manifest_sha256);
  diagnostic.qualified_source_manifest_sha256 = options.qualified_source_manifest_sha256;
  diagnostic.qualified_actor_source_manifest_sha256 = options.qualified_actor_source_manifest_sha256;
  for (std::int32_t ordinal = 0; ordinal < count; ++ordinal) {
    void *type = Load<void *>(types, ordinal * sizeof(void *));
    if (!EnabledType(type)) continue;
    std::string key;
    const bool key_read = TypeKey(type, key);
    if (!key_read) key.clear();
    enabled.push_back({type, ordinal});
    conditions.push_back(key_read ? CandidateConditions(options, key) : 0);
    diagnostic.casus_belli.push_back({ordinal, std::move(key), targets.size()});
    auto &d = diagnostic.casus_belli.back();
    d.necessary_conditions = conditions.back();
    if (d.necessary_conditions)
      for (const auto &rule : options.qualified_rules)
        if (rule.key == d.key) d.definition_source_sha256 = rule.definition_source_sha256;
    if (b.read_candidate_realm && b.candidate_target_titles_mode_offset)
      d.native_target_titles_mode = Load<std::uint8_t>(type, b.candidate_target_titles_mode_offset);
    d.actor_precheck_qualified = b.read_candidate_actor && key_read &&
        ActorCandidateQualified(options, d.key);
    if (d.actor_precheck_qualified) {
      const auto actor_start = profile.active() ? ProfileClock::now() : ProfileClock::time_point{};
      d.actor_precheck = b.read_candidate_actor(b.candidate_provider_image_base, type, actor);
      if (profile.active()) d.actor_precheck_ns = ElapsedNs(actor_start);
    }
  }
  // Build current-frame identity indexes once; never cache across dates/queries.
  // Unknown facts remain in every affected superset.
  std::array<std::vector<std::size_t>, 4> indexes;
  std::array<std::vector<std::size_t>, 4> realm_indexes;
  std::vector<void *> realm_pointers;
  const bool need_realm = std::any_of(diagnostic.casus_belli.begin(), diagnostic.casus_belli.end(),
      [](const auto &cb) { return cb.native_target_titles_mode >= 1 && cb.native_target_titles_mode <= 4; });
  diagnostic.native_realm_index_complete = need_realm && b.read_candidate_realm &&
      b.read_candidate_realm(b.candidate_provider_image_base, actor, realm_pointers);
  diagnostic.native_realm_index_entries = diagnostic.native_realm_index_complete ? realm_pointers.size() : 0;
  std::unordered_set<void *> realm_members;
  if (diagnostic.native_realm_index_complete)
    realm_members.insert(realm_pointers.begin(), realm_pointers.end());
  const bool need_facts = std::any_of(conditions.begin(), conditions.end(),
                                     [](auto c) { return c != 0; });
  for (std::size_t i = 0; i < targets.size(); ++i) {
    DeclarationsCandidateFactsV1 facts;
    if (need_facts && b.read_candidate_facts &&
        !b.read_candidate_facts(b.candidate_provider_image_base, targets[i].object, facts)) facts = {};
    for (std::uint32_t mask = 0; mask < indexes.size(); ++mask)
      if (!((mask & kDeclarationsCandidateLandedV1) && facts.landed == DeclarationsCandidateFactV1::no) &&
          !((mask & kDeclarationsCandidateIndependentV1) && facts.independent == DeclarationsCandidateFactV1::no))
      {
        indexes[mask].push_back(i);
        if (diagnostic.native_realm_index_complete && realm_members.contains(targets[i].object))
          realm_indexes[mask].push_back(i);
      }
  }
  std::vector<const std::vector<std::size_t> *> candidate_indexes;
  const std::vector<std::size_t> actor_denied_index;
  for (std::size_t i = 0; i < enabled.size(); ++i) {
    auto &d = diagnostic.casus_belli[i];
    d.native_realm_index_used = diagnostic.native_realm_index_complete &&
        d.native_target_titles_mode >= 1 && d.native_target_titles_mode <= 4;
    const auto &index = d.actor_precheck == DeclarationsCandidateFactV1::no ? actor_denied_index :
        d.native_realm_index_used ? realm_indexes[conditions[i]] : indexes[conditions[i]];
    candidate_indexes.push_back(&index);
    d.candidates = index.size(); d.projected_candidate_evaluations = index.size();
  }
  std::vector<game::DeclarableWarSnapshot> baseline, result;
  if (options.variant == DeclarationsCandidateVariantV1::shadow) {
    std::vector<EnabledCb> baseline_counters;
    if (!ReadDeclarableWarsFull(b, baseline, false, &baseline_counters)) return false;
    diagnostic.baseline_compared = true;
    for (std::size_t i = 0; i < enabled.size(); ++i) {
      diagnostic.casus_belli[i].baseline_evaluations = targets.size();
      if (i < baseline_counters.size() && baseline_counters[i].type == enabled[i].type &&
          baseline_counters[i].ordinal == enabled[i].ordinal) enabled[i] = baseline_counters[i];
    }
    // One original target-major full baseline, never a second N*C pass.
    // Test every complete native tuple against its CB's candidate identities.
    // Projected calls are distinct from actually executed baseline calls.
    std::unordered_map<std::int32_t, std::size_t> identity_index;
    for (std::size_t i = 0; i < targets.size(); ++i) identity_index.emplace(targets[i].id, i);
    for (const auto &row : baseline) {
      const auto found = identity_index.find(row.target_character_id);
      for (std::size_t i = 0; i < enabled.size(); ++i) {
        if (enabled[i].ordinal != row.casus_belli_index) continue;
        const auto &index = *candidate_indexes[i];
        if (found != identity_index.end() && std::binary_search(index.begin(), index.end(), found->second))
          result.push_back(row);
        break;
      }
    }
  }
  profile.targets = targets.size();
  bool scratch_is_clear = false, candidate_success = true;
  for (std::size_t i = 0; !diagnostic.baseline_compared && i < enabled.size() && candidate_success; ++i) {
    auto &d = diagnostic.casus_belli[i];
    const auto &candidates = *candidate_indexes[i];
    for (const auto index : candidates) {
      ++d.evaluations;
      const auto previous = result.size();
      if (!CachedEvaluation(b, enabled[i], actor, targets[index].object,
                            targets[index].id, result, scratch_is_clear, profile.active())) {
        candidate_success = false; break;
      }
      d.candidate_rows += result.size() - previous;
    }
  }
  CoreSnapshotPrefix after{};
  diagnostic.same_frame = ReadCoreSnapshot(b.core, after) && after.map_ready &&
      after.clock.paused && after.has_played_character && after.played_character_alive &&
      after.played_character_id == current.played_character_id &&
      after.clock.date_raw == current.clock.date_raw;
  if (diagnostic.baseline_compared) {
    CompareCandidateTuples(baseline, result, diagnostic);
    diagnostic.tuple_sets_equal &= candidate_success && diagnostic.same_frame;
  }
  // Restore original slot-major/CB-ordinal output; stable keeps each native
  // configuration's materialization order and the title sequence untouched.
  std::stable_sort(result.begin(), result.end(), [](const auto &a, const auto &c) {
    const auto ai = static_cast<std::uint32_t>(a.target_character_id) & 0xFFFFFFU;
    const auto ci = static_cast<std::uint32_t>(c.target_character_id) & 0xFFFFFFU;
    return ai != ci ? ai < ci : a.casus_belli_index < c.casus_belli_index;
  });
  if (requested_diagnostic) *requested_diagnostic = diagnostic;
  if (!diagnostic.same_frame) return false;
  if (diagnostic.baseline_compared) out = std::move(baseline);
  else if (candidate_success) out = std::move(result);
  else return false;
  profile.result_rows = out.size(); profile.success = true;
  return true;
}

game::DeclareWarResult SubmitDeclareWar(
    const DeclarationsBindings &b,
    const game::DeclarableWarSnapshot &declaration) noexcept {
  using Result = game::DeclareWarResult;
  if (!Ready(b) || !b.commands.enabled || !b.get_interaction_database ||
      !b.construct_context || !b.refresh_context || !b.finalize_context ||
      !b.validate_context || !b.destroy_context || !b.construct_send ||
      !b.copy_int_array || !b.append_int_array || !b.war_declaration_vtable ||
      !b.send_primary_vtable || !b.send_secondary_vtable) return Result::unavailable;
  CoreSnapshotPrefix current{};
  if (!ReadCoreSnapshot(b.core, current) || !current.map_ready ||
      !current.clock.paused) return Result::unavailable;
  if (!current.has_played_character || !current.played_character_alive)
    return Result::no_played_character;
  void *actor = ResolveCharacter(b.core, current.played_character_id);
  void *target = ResolveCharacter(b.core, declaration.target_character_id);
  if (!target || target == actor || Load<void *>(target, kCharacterDeathDataOffset))
    return Result::target_not_found;
  void *types{};
  std::int32_t count{};
  if (!actor || !Database(b, types, count)) return Result::unavailable;
  if (declaration.casus_belli_index < 0 || declaration.casus_belli_index >= count)
    return Result::declaration_unavailable;
  void *type = Load<void *>(types, declaration.casus_belli_index * sizeof(void *));
  if (!EnabledType(type) || !Clear(b)) return Result::declaration_unavailable;
  std::vector<game::DeclarableWarSnapshot> choices;
  const bool available = b.evaluate_cb(type, actor, target, b.configuration_scratch,
                                      false, false, nullptr);
  bool exact = false;
  if (available && Choices(b, type, declaration.target_character_id,
                           declaration.casus_belli_index, choices))
    for (const auto &row : choices) exact |= row == declaration;
  if (!exact) { Clear(b); return Result::declaration_unavailable; }
  void *database = b.get_interaction_database();
  void *interaction = database ? Load<void *>(database, kDeclarationsInteractionOffset) : nullptr;
  if (!interaction) { Clear(b); return Result::unavailable; }
  ContextStorage storage;
  void *context = storage.bytes.data();
  if (b.construct_context(context, interaction, current.played_character_id,
                          declaration.target_character_id, nullptr, true) != context) {
    Clear(b); return Result::unavailable;
  }
  void *war = Load<void *>(context, kDeclarationsSpecialDataOffset);
  if (!war || Load<std::uintptr_t>(war, 0) != b.war_declaration_vtable) {
    Clear(b); b.destroy_context(context); return Result::unavailable;
  }
  Store(war, kDeclarationsWarCbOffset, type);
  void *titles = static_cast<std::byte *>(war) + kDeclarationsWarTitlesOffset;
  void *data{};
  std::int32_t configurations{};
  if (!Scratch(b, data, configurations)) {
    b.destroy_context(context); return Result::unavailable;
  }
  for (std::int32_t i = 0; i < configurations; ++i) {
    if (declaration.configuration_index >= 0 && i != declaration.configuration_index) continue;
    const auto source = static_cast<std::byte *>(data) + i * kDeclarationsConfigurationSize + 8;
    if (declaration.configuration_index >= 0) b.copy_int_array(titles, source);
    else {
      const auto source_count = Load<std::int32_t>(source, 12);
      const auto source_data = Load<const std::int32_t *>(source, 0);
      if (source_count) b.append_int_array(titles, Load<std::int32_t>(titles, 12),
                                         source_data, source_data + source_count);
    }
  }
  Store(war, kDeclarationsWarClaimantOffset, declaration.claimant_character_id);
  if (!Clear(b)) { b.destroy_context(context); return Result::unavailable; }
  b.refresh_context(context, true);
  b.finalize_context(context);
  if (!b.validate_context(context, nullptr)) {
    b.destroy_context(context); return Result::validation_failed;
  }
  SendStorage command_storage;
  void *command = command_storage.bytes.data();
  const bool built = b.construct_send(command, context) == command;
  const bool tables = Load<std::uintptr_t>(command, 0) == b.send_primary_vtable &&
                      Load<std::uintptr_t>(command, 0x18) == b.send_secondary_vtable;
  if (!built || !tables) {
    if (Load<void *>(command, kDeclarationsSendContextOffset))
      b.destroy_context(static_cast<std::byte *>(command) + kDeclarationsSendContextOffset);
    b.destroy_context(context);
    return Result::unavailable;
  }
  const auto sent = SubmitCommandCopy(b.commands, command, 0x0E);
  b.destroy_context(static_cast<std::byte *>(command) + kDeclarationsSendContextOffset);
  b.destroy_context(context);
  return sent == CommandSubmitResult::submitted ? Result::submitted : Result::unavailable;
}

#if defined(XAR_CK3_ENABLE_ORDINARY_HOLY_WAR_DECLARATION_CONTEXT_PRIVATE_V1)
namespace {
bool ReadSelectedOrdinaryHolyWarDeclarationContextImplV1(
    const DeclarationsBindings &b, const OrdinaryHolyWarCbCostBindingsV1 &cost,
    const game::DeclarableWarSnapshot &selected, OrdinaryHolyWarDeclarationContextV1 &out,
    const religion::holy_war_defender_join::Bindings *defender_join,
    religion::holy_war_defender_join::Context *defender_join_out) noexcept {
  // Frame metadata is supplied by the owning mailbox and retained on failure.
  out.selected = selected;
  if (!IsOrdinaryHolyWarKeyV1(selected.casus_belli_key)) {
    out.unavailable_reason = "unsupported_casus_belli"; return false;
  }
  if (!Ready(b) || !b.get_interaction_database || !b.construct_context ||
      !b.refresh_context || !b.finalize_context || !b.validate_context ||
      !b.destroy_context || !b.copy_int_array || !b.append_int_array || !b.war_declaration_vtable) return false;
  CoreSnapshotPrefix current{};
  if (!ReadCoreSnapshot(b.core, current) || !current.map_ready || !current.clock.paused) return false;
  if (!current.has_played_character || !current.played_character_alive ||
      current.played_character_id != out.played_character_id || current.clock.date_raw != out.date_raw) return false;
  void *actor = ResolveCharacter(b.core, current.played_character_id);
  void *target = ResolveCharacter(b.core, selected.target_character_id);
  if (!target || target == actor || Load<void *>(target, kCharacterDeathDataOffset)) {
    out.unavailable_reason = "target_not_found"; return false;
  }
  void *types{};
  std::int32_t count{};
  if (!actor || !Database(b, types, count)) return false;
  if (selected.casus_belli_index < 0 || selected.casus_belli_index >= count) {
    out.unavailable_reason = "declaration_unavailable"; return false;
  }
  void *type = Load<void *>(types, selected.casus_belli_index * sizeof(void *));
  if (!EnabledType(type) || !Clear(b)) return false;
  struct ScratchOwner {
    const DeclarationsBindings &b;
    bool active = true;
    ~ScratchOwner() { if (active) (void)Clear(b); }
    bool finish() { if (!Clear(b)) return false; active = false; return true; }
  } scratch{b};
  std::vector<game::DeclarableWarSnapshot> choices;
  const bool candidate = b.evaluate_cb(type, actor, target, b.configuration_scratch, false, false, nullptr);
  bool exact = false;
  if (candidate && Choices(b, type, selected.target_character_id, selected.casus_belli_index, choices))
    for (const auto &row : choices) exact |= row == selected;
  if (!exact) { out.unavailable_reason = "declaration_unavailable"; return false; }
  void *database = b.get_interaction_database();
  void *interaction = database ? Load<void *>(database, kDeclarationsInteractionOffset) : nullptr;
  if (!interaction) return false;
  ContextStorage storage;
  void *context = storage.bytes.data();
  if (b.construct_context(context, interaction, current.played_character_id,
      selected.target_character_id, nullptr, true) != context) return false;
  struct ContextOwner {
    const DeclarationsBindings &b;
    void *context;
    ~ContextOwner() { b.destroy_context(context); }
  } owner{b, context};
  void *war = Load<void *>(context, kDeclarationsSpecialDataOffset);
  if (!war || Load<std::uintptr_t>(war, 0) != b.war_declaration_vtable) return false;
  Store(war, kDeclarationsWarCbOffset, type);
  void *titles = static_cast<std::byte *>(war) + kDeclarationsWarTitlesOffset;
  void *data{};
  std::int32_t configurations{};
  if (!Scratch(b, data, configurations)) return false;
  for (std::int32_t i = 0; i < configurations; ++i) {
    if (selected.configuration_index >= 0 && i != selected.configuration_index) continue;
    const auto source = static_cast<std::byte *>(data) + i * kDeclarationsConfigurationSize + 8;
    if (selected.configuration_index >= 0) b.copy_int_array(titles, source);
    else {
      const auto source_count = Load<std::int32_t>(source, 12);
      const auto source_data = Load<const std::int32_t *>(source, 0);
      if (source_count) b.append_int_array(titles, Load<std::int32_t>(titles, 12), source_data, source_data + source_count);
    }
  }
  Store(war, kDeclarationsWarClaimantOffset, selected.claimant_character_id);
  if (!scratch.finish()) return false;
  b.refresh_context(context, true);
  b.finalize_context(context);
  const bool final_can_send = b.validate_context(context, nullptr);
  // Re-read the finalized current selection; additional is an independent role.
  war = Load<void *>(context, kDeclarationsSpecialDataOffset);
  if (!war || Load<std::uintptr_t>(war, 0) != b.war_declaration_vtable ||
      Load<void *>(war, kDeclarationsWarCbOffset) != type) return false;
  titles = static_cast<std::byte *>(war) + kDeclarationsWarTitlesOffset;
  game::DeclarableWarSnapshot actual = selected;
  if (!TypeKey(type, actual.casus_belli_key) || !IntArray(titles, actual.target_title_ids)) return false;
  actual.claimant_character_id = Load<std::int32_t>(war, kDeclarationsWarClaimantOffset);
  if (actual != selected) { out.unavailable_reason = "finalized_selection_changed"; return false; }
  out.selected = std::move(actual);
  out.final_can_send = final_can_send;
  out.context_actor_character_id = Load<std::int32_t>(context, 0x2D8);
  out.context_recipient_character_id = Load<std::int32_t>(context, 0x2DC);
  out.context_additional_role_character_id = Load<std::int32_t>(context, kDeclarationsAdditionalRoleOffset);
  out.context_claimant_character_id = Load<std::int32_t>(war, kDeclarationsWarClaimantOffset);
  const auto resolve = [&](std::int32_t id, bool &fallback) {
    void *character = ResolveCharacter(b.core, id);
    fallback = !character;
    return character ? character : (cost.native_character_fallback_slot ? *cost.native_character_fallback_slot : nullptr);
  };
  void *recipient = resolve(*out.context_recipient_character_id, out.recipient_uses_native_fallback);
  void *additional = resolve(*out.context_additional_role_character_id, out.additional_role_uses_native_fallback);
  void *claimant = resolve(*out.context_claimant_character_id, out.claimant_uses_native_fallback);
  out.available = true; out.unavailable_reason.clear();
  if (Load<std::uint32_t>(type, 0x38) != 0x4744624FU)
    out.cb_cost.unavailable_reason = "selected_cb_native_tag_unavailable";
  else (void)ReadOrdinaryHolyWarCbCostV1(cost, type, additional, recipient, claimant, titles, out.cb_cost);
  if (defender_join && defender_join_out)
    (void)religion::holy_war_defender_join::ReadSelectedHolyWarDefenderJoinInputs12003(
        *defender_join, type, additional, recipient, out, *defender_join_out);
  return true;
}
} // namespace
bool ReadSelectedOrdinaryHolyWarDeclarationContextV1(
    const DeclarationsBindings &b, const OrdinaryHolyWarCbCostBindingsV1 &cost,
    const game::DeclarableWarSnapshot &selected, OrdinaryHolyWarDeclarationContextV1 &out) noexcept {
  return ReadSelectedOrdinaryHolyWarDeclarationContextImplV1(b, cost, selected, out, nullptr, nullptr);
}
bool ReadSelectedOrdinaryHolyWarDeclarationContextV1(
    const DeclarationsBindings &b, const OrdinaryHolyWarCbCostBindingsV1 &cost,
    const game::DeclarableWarSnapshot &selected, OrdinaryHolyWarDeclarationContextV1 &out,
    const religion::holy_war_defender_join::Bindings &defender_join,
    religion::holy_war_defender_join::Context &defender_join_out) noexcept {
  return ReadSelectedOrdinaryHolyWarDeclarationContextImplV1(
      b, cost, selected, out, &defender_join, &defender_join_out);
}
#endif

} // namespace xar::ck3_12002
