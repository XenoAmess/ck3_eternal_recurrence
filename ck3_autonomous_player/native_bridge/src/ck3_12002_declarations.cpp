#include "xar_bridge/ck3_12002_declarations.hpp"

#include <array>
#include <cstring>
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
  for (std::int32_t i = 0; i < cap; ++i) {
    void *target = Load<void *>(slots, i * 0x10ULL + 8);
    if (!target || target == actor || Load<void *>(target, kCharacterDeathDataOffset)) continue;
    const auto id = Load<std::int32_t>(target, 0x18);
    if ((static_cast<std::uint32_t>(id) & 0xFFFFFFU) != static_cast<std::uint32_t>(i)) continue;
    if (!Target(b, types, count, actor, target, id, result)) return false;
  }
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

} // namespace xar::ck3_12002
