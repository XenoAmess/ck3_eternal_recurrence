#include "xar_bridge/ck3_12002_gift_opinion.hpp"

#include <array>
#include <cstring>
#include <limits>
#include <string>

#if defined(_WIN32)
#include <windows.h>
#endif

namespace xar::ck3_12002 {
namespace {
constexpr std::uint32_t kGiftModifierHash = 0xCA82155BU;
constexpr std::uint32_t kSendGiftOpinionHash = 0xF8A1F946U;
constexpr std::uint32_t kNamedDefinitionTag = 0x4744624FU; // ObDG
constexpr std::size_t kCharacterExtensionOffset = 0x1B0;
constexpr std::int32_t kMaximumOpinionRows = 1 << 20;

template <typename T>
bool Load(const void *base, std::size_t offset, T &value) noexcept {
  value = {};
  if (base == nullptr) return false;
#if defined(_MSC_VER)
  __try {
#endif
    std::memcpy(&value, static_cast<const std::byte *>(base) + offset,
                sizeof(value));
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    value = {};
    return false;
  }
#endif
}

bool DefinitionIdentity(const void *definition, std::uintptr_t primary,
                        std::uintptr_t secondary, std::uint32_t hash,
                        std::string_view key) noexcept {
  std::uintptr_t actual_primary = 0, actual_secondary = 0;
  std::uint32_t actual_hash = 0, tag = 0;
  std::uint64_t length = 0, capacity = 0;
  if (primary == 0 || secondary == 0 ||
      !Load(definition, 0, actual_primary) || actual_primary != primary ||
      !Load(definition, 0x88, actual_secondary) || actual_secondary != secondary ||
      !Load(definition, 0x14, actual_hash) || actual_hash != hash ||
      !Load(definition, 0x38, tag) || tag != kNamedDefinitionTag ||
      !Load(definition, 0x28, length) || length != key.size() ||
      !Load(definition, 0x30, capacity) || length > capacity) return false;
  const char *data = static_cast<const char *>(definition) + 0x18;
  if (capacity >= 16 && !Load(definition, 0x18, data)) return false;
  if (data == nullptr) return false;
  for (std::size_t index = 0; index < key.size(); ++index) {
    char value = 0;
    if (!Load(data, index, value) || value != key[index]) return false;
  }
  // 1.20 slot zero is a destructor/empty ret, not the old validity predicate.
  // The native initializer checks the ObDG tag instead.
  return true;
}

void *Character(const CoreBindings &core, std::uint32_t id) noexcept {
  if (id == 0 || id == 0xFFFFFFFFU) return nullptr;
  return ResolveCoreCharacter(core, static_cast<std::int32_t>(id));
}

bool OpinionPair(const CoreBindings &core, GiftReadCharacterOpinion12002 reader,
                 std::uint32_t owner_id, std::uint32_t toward_id,
                 std::int32_t &output) noexcept {
  output = 0;
  if (!core.enabled || reader == nullptr) return false;
  void *owner = Character(core, owner_id);
  void *toward = Character(core, toward_id);
  if (owner == nullptr || toward == nullptr) return false;
  const auto first = reader(owner, toward);
  const auto second = reader(owner, toward);
  if (first != second || Character(core, owner_id) != owner ||
      Character(core, toward_id) != toward) return false;
  output = first;
  return true;
}

struct OpinionSample {
  void *recipient = nullptr;
  void *player = nullptr;
  void *database = nullptr;
  void *definition = nullptr;
  std::int32_t opinion = 0;
  bool present = false;
  std::optional<std::int32_t> value;
  friend bool operator==(const OpinionSample &, const OpinionSample &) = default;
};

bool ReadSample(const GiftOpinionBindings12002 &b, std::uint32_t recipient_id,
                std::uint32_t player_id, OpinionSample &sample) noexcept {
  sample = {};
  sample.recipient = Character(b.core, recipient_id);
  sample.player = Character(b.core, player_id);
  if (sample.recipient == nullptr || sample.player == nullptr ||
      !Load(b.modifier_database_slot, 0, sample.database) ||
      sample.database == nullptr) return false;
  sample.definition = b.lookup_modifier(sample.database, kGiftModifierHash);
  if (!DefinitionIdentity(sample.definition, b.modifier_primary_vtable,
                          b.modifier_secondary_vtable, kGiftModifierHash,
                          "gift_opinion")) return false;
  sample.opinion = b.read_opinion(sample.recipient, sample.player);
  void *extension = nullptr;
  if (!Load(sample.recipient, kCharacterExtensionOffset, extension)) return false;
  if (extension != nullptr) {
    void *group = b.find_group(extension, player_id);
    if (group != nullptr) {
      void *rows = nullptr;
      std::int32_t count = 0;
      if (!Load(group, 8, rows) || !Load(group, 0x14, count) || count < 0 ||
          count > kMaximumOpinionRows || (count != 0 && rows == nullptr))
        return false;
      for (std::int32_t index = 0; index < count; ++index) {
        void *active = nullptr, *modifier = nullptr;
        std::uintptr_t vtable = 0;
        if (!Load(rows, static_cast<std::size_t>(index) * 8, active)) return false;
        if (active == nullptr) continue;
        if (!Load(active, 0, vtable) ||
            (vtable != b.active_opinion_vtable &&
             vtable != b.temporary_opinion_vtable) ||
            !Load(active, 8, modifier)) return false;
        if (modifier == sample.definition) sample.present = true;
      }
      if (sample.present) sample.value = b.sum_modifier(group, sample.definition);
    }
  }
  void *database_after = nullptr;
  if (!Load(b.modifier_database_slot, 0, database_after) ||
      database_after != sample.database ||
      b.lookup_modifier(database_after, kGiftModifierHash) != sample.definition ||
      !DefinitionIdentity(sample.definition, b.modifier_primary_vtable,
                          b.modifier_secondary_vtable, kGiftModifierHash,
                          "gift_opinion") ||
      Character(b.core, recipient_id) != sample.recipient ||
      Character(b.core, player_id) != sample.player) return false;
  return true;
}

using Deallocate = void (*)(void *, void *, std::size_t);
bool ReleaseRows(void *owner, std::size_t data_offset,
                 std::size_t capacity_offset, std::size_t count_offset,
                 std::size_t allocator_offset,
                 GiftDestroyScopePart12002 destructor) noexcept {
  void *rows = nullptr;
  std::int32_t count = 0;
  if (!Load(owner, data_offset, rows) || !Load(owner, count_offset, count) ||
      count < 0 || count > kMaximumOpinionRows ||
      (count != 0 && rows == nullptr)) return false;
  if (rows == nullptr) return count == 0;
  if (destructor != nullptr)
    destructor(static_cast<std::byte *>(owner) + data_offset);
  void *allocator = nullptr;
  std::uintptr_t vtable = 0, deallocate = 0;
  if (!Load(owner, allocator_offset, allocator) || allocator == nullptr ||
      !Load(allocator, 0, vtable) || vtable == 0 ||
      !Load(reinterpret_cast<const void *>(vtable), 0x10, deallocate) ||
      deallocate == 0) return false;
  const std::int32_t zero = 0;
  void *const empty = nullptr;
  std::memcpy(static_cast<std::byte *>(owner) + data_offset, &empty, sizeof(empty));
  std::memcpy(static_cast<std::byte *>(owner) + capacity_offset, &zero, sizeof(zero));
  std::memcpy(static_cast<std::byte *>(owner) + count_offset, &zero, sizeof(zero));
  reinterpret_cast<Deallocate>(deallocate)(allocator, rows, 8);
  return true;
}

bool DestroyEvaluation(const GiftNamedOpinionBindings12002 &b, void *scope,
                       void *support118, void *support2a8) noexcept {
  const bool a = ReleaseRows(support2a8, 0, 8, 0xC, 0x10, b.destroy_support_rows);
  const bool c = ReleaseRows(support118, 0, 8, 0xC, 0x10, nullptr);
  b.destroy_scope_tail(static_cast<std::byte *>(scope) + 0x118);
  const bool d = ReleaseRows(scope, 0x100, 0x108, 0x10C, 0x110,
                             b.destroy_scope_rows);
  const bool e = ReleaseRows(scope, 0x18, 0x20, 0x24, 0x28, nullptr);
  return a && c && d && e;
}

template <typename T>
void Store(void *base, std::size_t offset, const T &value) noexcept {
  std::memcpy(static_cast<std::byte *>(base) + offset, &value, sizeof(value));
}
} // namespace

GiftOpinionBindings12002 BindGiftOpinionImage12002(
    std::uintptr_t module, std::string_view hash) noexcept {
  GiftOpinionBindings12002 b;
  b.core = BindCoreImage(module, hash);
  if (!b.core.enabled) return b;
  b.enabled = true;
  b.module_base = module;
  b.modifier_database_slot = reinterpret_cast<void **>(
      module + kGiftOpinionModifierDatabaseSlotRva12002);
  b.read_opinion = reinterpret_cast<GiftReadCharacterOpinion12002>(
      module + kGiftReadCharacterOpinionRva12002);
  b.lookup_modifier = reinterpret_cast<GiftLookupOpinionModifier12002>(
      module + kGiftOpinionModifierLookupRva12002);
  b.find_group = reinterpret_cast<GiftFindOpinionGroup12002>(
      module + kGiftFindActiveOpinionGroupRva12002);
  b.sum_modifier = reinterpret_cast<GiftSumOpinionModifier12002>(
      module + kGiftSumOpinionModifierRva12002);
  b.modifier_primary_vtable = module + kGiftOpinionModifierVtableRva12002;
  b.modifier_secondary_vtable = module + kGiftOpinionModifierSecondaryVtableRva12002;
  b.active_opinion_vtable = module + kGiftActiveOpinionVtableRva12002;
  b.temporary_opinion_vtable = module + kGiftTemporaryOpinionVtableRva12002;
  return b;
}

bool ReadGiftOpinion12002(const GiftOpinionBindings12002 &b,
                         std::uint32_t recipient_id, std::uint32_t player_id,
                         GiftOpinionResult &output) noexcept {
  output = {};
  if (!b.enabled || !b.core.enabled || b.read_opinion == nullptr ||
      b.lookup_modifier == nullptr || b.find_group == nullptr ||
      b.sum_modifier == nullptr || b.modifier_database_slot == nullptr)
    return false;
  OpinionSample first, second;
  if (!ReadSample(b, recipient_id, player_id, first) ||
      !ReadSample(b, recipient_id, player_id, second) || first != second)
    return false;
  output.query_complete = true;
  output.recipient_opinion_of_player = first.opinion;
  output.gift_opinion_present = first.present;
  output.gift_opinion_modifier_value = first.value;
  return true;
}

bool ReadGiftOpinionExact12002(std::uintptr_t module, const CoreBindings &core,
                              std::uint32_t recipient_id, std::uint32_t player_id,
                              GiftOpinionResult &output) noexcept {
  auto b = BindGiftOpinionImage12002(module, kExecutableSha256);
  if (!core.enabled || reinterpret_cast<std::uintptr_t>(core.character_storage_slot) !=
      module + kCharacterStorageSlotRva) { output = {}; return false; }
  b.core = core;
  return ReadGiftOpinion12002(b, recipient_id, player_id, output);
}

bool ReadCharacterOpinion12002(std::uintptr_t module, const CoreBindings &core,
                              std::uint32_t recipient_id, std::uint32_t player_id,
                              std::int32_t &output) noexcept {
  output = 0;
  if (module == 0 || !core.enabled ||
      reinterpret_cast<std::uintptr_t>(core.character_storage_slot) !=
          module + kCharacterStorageSlotRva) return false;
  return OpinionPair(core, reinterpret_cast<GiftReadCharacterOpinion12002>(
      module + kGiftReadCharacterOpinionRva12002), recipient_id, player_id, output);
}

bool ConvertGiftOpinionFixed12002(std::int64_t raw, std::int32_t &output) noexcept {
  output = 0;
  constexpr std::int64_t scale = 100000;
  if (raw < static_cast<std::int64_t>((std::numeric_limits<std::int32_t>::min)()) * scale ||
      raw > static_cast<std::int64_t>((std::numeric_limits<std::int32_t>::max)()) * scale)
    return false;
  const auto rounded = (raw < 0 ? raw - scale / 2 : raw + scale / 2) / scale;
  if (rounded < (std::numeric_limits<std::int32_t>::min)() ||
      rounded > (std::numeric_limits<std::int32_t>::max)()) return false;
  output = static_cast<std::int32_t>(rounded);
  return true;
}

bool ReadNamedInteractionFixed12002(
    const GiftNamedOpinionBindings12002 &b, const void *interaction_scope,
    std::uint32_t root_id, std::uint32_t player_id, std::uint32_t recipient_id,
    std::string_view canonical_key, std::uint32_t stable_hash,
    std::int64_t &output) noexcept {
  output = 0;
  if (!b.enabled || !b.core.enabled || interaction_scope == nullptr ||
      b.named_database == nullptr || b.lookup_named == nullptr ||
      b.clone_scope == nullptr || b.construct_support_118 == nullptr ||
      b.construct_support_2a8 == nullptr || b.intern_database == nullptr ||
      b.intern_string == nullptr || b.evaluate_fixed == nullptr ||
      b.destroy_scope_tail == nullptr || b.evaluation_flag == nullptr ||
      canonical_key.empty()) return false;
  void *recipient = Character(b.core, recipient_id);
  void *player = Character(b.core, player_id);
  void *root = Character(b.core, root_id);
  void *database = b.named_database();
  if (recipient == nullptr || player == nullptr || root == nullptr ||
      database == nullptr) return false;
  const void *definition = b.lookup_named(database, stable_hash);
  if (!DefinitionIdentity(definition, b.named_primary_vtable,
                          b.named_secondary_vtable, stable_hash,
                          canonical_key)) return false;
  alignas(16) std::array<std::byte, 0x168> scope{};
  alignas(16) std::array<std::byte, 0x118> support118{};
  alignas(16) std::array<std::byte, 0x2A8> support2a8{};
  alignas(16) std::array<std::byte, 0x28> internal{};
  if (b.clone_scope(scope.data(), interaction_scope) != scope.data()) return false;
  Store(scope.data(), 0, std::uint16_t{4});
  Store(scope.data(), 8, static_cast<std::uint64_t>(root_id));
  const bool support_ok = b.construct_support_118(support118.data()) == support118.data() &&
      b.construct_support_2a8(support2a8.data()) == support2a8.data();
  void *scope_pointer = scope.data(), *support_pointer = support118.data();
  Store(internal.data(), 0, scope_pointer);
  Store(internal.data(), 0x10, scope_pointer);
  Store(internal.data(), 0x18, support_pointer);
  std::uint8_t flag = 0;
  bool evaluated = support_ok && Load(b.evaluation_flag, 0, flag);
  Store(internal.data(), 0x20, flag);
  alignas(16) std::array<std::byte, 0x10> key_view{};
  const char *key = canonical_key.data();
  Store(key_view.data(), 0, key);
  Store(key_view.data(), 8, static_cast<std::uint32_t>(canonical_key.size()));
  const void *intern = nullptr;
  if (evaluated) {
    void *intern_database = b.intern_database();
    if (intern_database != nullptr) intern = b.intern_string(intern_database, key_view.data());
    evaluated = intern != nullptr;
  }
  alignas(16) std::array<std::byte, 0x20> source{};
  Store(source.data(), 0, intern);
  Store(source.data(), 0x14, std::uint8_t{1});
  Store(source.data(), 0x18, std::int32_t{-1});
  std::int64_t first = 0, second = 0;
  if (evaluated) {
    evaluated = b.evaluate_fixed(definition, &first, internal.data(), nullptr,
                                source.data()) == &first &&
                b.evaluate_fixed(definition, &second, internal.data(), nullptr,
                                source.data()) == &second && first == second;
  }
  const bool released = DestroyEvaluation(b, scope.data(), support118.data(),
                                          support2a8.data());
  if (!evaluated || !released || b.named_database() != database ||
      b.lookup_named(database, stable_hash) != definition ||
      !DefinitionIdentity(definition, b.named_primary_vtable,
                          b.named_secondary_vtable, stable_hash,
                          canonical_key) ||
      Character(b.core, recipient_id) != recipient ||
      Character(b.core, player_id) != player ||
      Character(b.core, root_id) != root) return false;
  output = first;
  return true;
}

bool ReadGiftOpinionDelta12002(const GiftNamedOpinionBindings12002 &b,
                             const void *interaction_scope,
                             std::uint32_t recipient_id,
                             std::uint32_t player_id,
                             std::int32_t &delta) noexcept {
  delta = 0;
  std::int64_t raw = 0;
  return ReadNamedInteractionFixed12002(b, interaction_scope, recipient_id,
      player_id, recipient_id, "send_gift_opinion", kSendGiftOpinionHash, raw) &&
      ConvertGiftOpinionFixed12002(raw, delta);
}

// Image binding for named evaluation is below the reader so fixture callbacks
// exercise its complete scope, source descriptor and teardown path.
GiftNamedOpinionBindings12002 BindGiftNamedOpinionImage12002(
    std::uintptr_t module, std::string_view hash) noexcept {
  GiftNamedOpinionBindings12002 b;
  b.core = BindCoreImage(module, hash);
  if (!b.core.enabled) return b;
  b.enabled = true;
  b.named_database = reinterpret_cast<GiftNamedDatabase12002>(module + 0xA07970);
  b.lookup_named = reinterpret_cast<GiftLookupNamed12002>(module + 0xA07830);
  b.clone_scope = reinterpret_cast<GiftCloneScope12002>(module + 0x373AD10);
  b.construct_support_118 = reinterpret_cast<GiftConstructSupport12002>(module + 0x3736060);
  b.construct_support_2a8 = reinterpret_cast<GiftConstructSupport12002>(module + 0x3735FB0);
  b.intern_database = reinterpret_cast<GiftNamedDatabase12002>(module + 0x3F79B20);
  b.intern_string = reinterpret_cast<GiftInternString12002>(module + 0x3F79DF0);
  b.evaluate_fixed = reinterpret_cast<GiftEvaluateNamedFixed12002>(module + 0x37542F0);
  b.destroy_scope_tail = reinterpret_cast<GiftDestroyScopePart12002>(module + 0x889700);
  b.destroy_scope_rows = reinterpret_cast<GiftDestroyScopePart12002>(module + 0x889780);
  b.destroy_support_rows = reinterpret_cast<GiftDestroyScopePart12002>(module + 0x9D7340);
  b.evaluation_flag = reinterpret_cast<const std::uint8_t *>(module + 0x5D1DADC);
  b.named_primary_vtable = module + 0x49290A0;
  b.named_secondary_vtable = module + 0x49290B0;
  return b;
}

bool ReadGiftOpinionDeltaExact12002(std::uintptr_t module,
                                   const void *interaction_scope,
                                   std::uint32_t recipient_id,
                                   std::uint32_t player_id,
                                   std::int32_t &delta) noexcept {
  return ReadGiftOpinionDelta12002(
      BindGiftNamedOpinionImage12002(module, kExecutableSha256),
      interaction_scope, recipient_id, player_id, delta);
}

bool ReadNamedInteractionFixedExact12002(
    std::uintptr_t module, const void *interaction_scope, std::uint32_t root_id,
    std::uint32_t player_id, std::uint32_t recipient_id,
    std::string_view canonical_key, std::uint32_t stable_hash,
    std::int64_t &output) noexcept {
  return ReadNamedInteractionFixed12002(
      BindGiftNamedOpinionImage12002(module, kExecutableSha256),
      interaction_scope, root_id, player_id, recipient_id, canonical_key,
      stable_hash, output);
}

bool ReadGiftValueExact12002(std::uintptr_t module, const void *interaction_scope,
                           std::uint32_t recipient_id, std::uint32_t player_id,
                           std::int64_t &gold_raw) noexcept {
  return ReadNamedInteractionFixedExact12002(module, interaction_scope, player_id,
      player_id, recipient_id, "gift_value", 0x58DD38F9U, gold_raw);
}

} // namespace xar::ck3_12002
