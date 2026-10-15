#include "xar_bridge/ck3_12002_declarations.hpp"

#if defined(XAR_CK3_ENABLE_ORDINARY_HOLY_WAR_DECLARATION_CONTEXT_PRIVATE_V1)
#include "xar_bridge/ordinary_holy_war_cb_cost_v1.hpp"
#include "xar_bridge/ck3_12003_holy_war_defender_join_inputs.hpp"
#endif

#include <array>
#include <chrono>
#include <cstdlib>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <utility>

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
#pragma warning(suppress : 4996)
#endif
  return _wgetenv(L"XAR_CK3_DECLARATIONS_PROFILE_JSONL");
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
      stream << "]}\n";
    } catch (...) { /* Diagnostic output is independent of gameplay. */ }
  }
};

bool CachedTarget(const DeclarationsBindings &b,
                  std::vector<EnabledCb> &enabled,
                  void *actor, void *target, std::int32_t target_id,
                  std::vector<game::DeclarableWarSnapshot> &out,
                  bool &scratch_is_clear, bool profile) noexcept {
  for (auto &cb : enabled) {
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
  }
  return true;
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

bool ReadDeclarableWars(const DeclarationsBindings &b,
                       std::vector<game::DeclarableWarSnapshot> &out) noexcept {
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
                      profile.active()))
      return false;
  }
  profile.result_rows = result.size();
  profile.success = true;
  out = std::move(result);
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
