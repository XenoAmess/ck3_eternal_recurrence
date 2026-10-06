#include "xar_bridge/ck3_12004_prisoner_named.hpp"

#include <array>
#include <cstring>

#if defined(_WIN32)
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#endif

namespace xar::ck3_12004 {
namespace {
constexpr std::uint32_t kNamedDefinitionTag = 0x4744624FU; // ObDG
constexpr std::int32_t kMaximumNamedRows = 1 << 20;

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
  return xar::ck3_12004::ResolveCoreCharacter(core, static_cast<std::int32_t>(id));
}

using Deallocate = void (*)(void *, void *, std::size_t);
bool ReleaseRows(void *owner, std::size_t data_offset,
                 std::size_t capacity_offset, std::size_t count_offset,
                 std::size_t allocator_offset,
                 PrisonerDestroyScopePart12004 destructor) noexcept {
  void *rows = nullptr;
  std::int32_t count = 0;
  if (!Load(owner, data_offset, rows) || !Load(owner, count_offset, count) ||
      count < 0 || count > kMaximumNamedRows ||
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

bool DestroyEvaluation(const PrisonerNamedBindings12004 &b, void *scope,
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

bool ReadNamedInteractionFixed12004(
    const PrisonerNamedBindings12004 &b, const void *interaction_scope,
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
  // Native 310CEE0/37616A0: both support vectors and the scope slot
  // belong to one 0x3D8 scratch object; the first constructor writes +0x120.
  alignas(16) std::array<std::byte, 0x3D8> scratch{};
  alignas(16) std::array<std::byte, 0x28> internal{};
  if (b.clone_scope(scope.data(), interaction_scope) != scope.data()) return false;
  Store(scope.data(), 0, std::uint16_t{4});
  Store(scope.data(), 8, static_cast<std::uint64_t>(root_id));
  void *support_pointer = scratch.data();
  void *support_second = scratch.data() + 0x128;
  const bool support_ok = b.construct_support_118(support_pointer) == support_pointer &&
      b.construct_support_2a8(support_second) == support_second;
  void *scope_pointer = scope.data();
  Store(scratch.data(), 0x3D0, scope_pointer);
  Store(internal.data(), 0, scope_pointer);
  Store(internal.data(), 8, scope_pointer);
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
  const bool released = DestroyEvaluation(b, scope.data(), support_pointer,
                                          support_second);
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


PrisonerNamedBindings12004 BindPrisonerNamedImage12004(
    std::uintptr_t module, std::string_view actual_sha) noexcept {
  PrisonerNamedBindings12004 b{};
  if (module == 0 || actual_sha != kExecutableSha256) return b;
  b.core = BindCoreImage(module, actual_sha);
  if (!b.core.enabled) return b;
  b.module_base = module;
  b.named_database = reinterpret_cast<PrisonerNamedDatabase12004>(
      module + kPrisonerNamedDatabaseRva12004);
  b.lookup_named = reinterpret_cast<PrisonerLookupNamed12004>(
      module + kPrisonerNamedLookupRva12004);
  b.clone_scope = reinterpret_cast<PrisonerCloneScope12004>(
      module + kPrisonerNamedCloneScopeRva12004);
  b.construct_support_118 = reinterpret_cast<PrisonerConstructSupport12004>(
      module + kPrisonerNamedSupport118Rva12004);
  b.construct_support_2a8 = reinterpret_cast<PrisonerConstructSupport12004>(
      module + kPrisonerNamedSupport2a8Rva12004);
  b.intern_database = reinterpret_cast<PrisonerNamedDatabase12004>(
      module + kPrisonerNamedInternDatabaseRva12004);
  b.intern_string = reinterpret_cast<PrisonerInternString12004>(
      module + kPrisonerNamedInternStringRva12004);
  b.evaluate_fixed = reinterpret_cast<PrisonerEvaluateNamedFixed12004>(
      module + kPrisonerNamedFixedRva12004);
  b.destroy_scope_tail = reinterpret_cast<PrisonerDestroyScopePart12004>(
      module + kPrisonerNamedDestroyTailRva12004);
  b.destroy_scope_rows = reinterpret_cast<PrisonerDestroyScopePart12004>(
      module + kPrisonerNamedDestroyScopeRowsRva12004);
  b.destroy_support_rows = reinterpret_cast<PrisonerDestroyScopePart12004>(
      module + kPrisonerNamedDestroySupportRowsRva12004);
  b.evaluation_flag = reinterpret_cast<const std::uint8_t *>(
      module + kPrisonerNamedEvaluationFlagRva12004);
  b.named_primary_vtable = module + kPrisonerNamedPrimaryVtableRva12004;
  b.named_secondary_vtable = module + kPrisonerNamedSecondaryVtableRva12004;
  b.enabled = true;
  return b;
}

} // namespace xar::ck3_12004
