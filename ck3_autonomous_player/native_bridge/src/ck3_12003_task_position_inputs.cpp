#include "xar_bridge/ck3_12003_task_position_inputs.hpp"

#include <array>
#include <cstring>
#include <memory>
#include <utility>

#if defined(_MSC_VER)
#include <windows.h>
#endif

namespace xar::ck3_12003::task_position {
namespace {
constexpr std::string_view kSha =
    "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6";
// Reused caller allocation upper bound, NOT sizeof(native modifier vector).
constexpr std::size_t kVectorStorageBound = 0x71E0;
constexpr std::size_t kModifierSize = 0x1C0;

bool Copy(const Bindings &b, const void *address, void *out,
          std::size_t size) noexcept {
  if (!address) return false;
  if (b.read_memory) return b.read_memory(b.read_memory_context, address, out, size);
#if defined(_MSC_VER)
  __try { std::memcpy(out, address, size); return true; }
  __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#else
  std::memcpy(out, address, size); return true;
#endif
}
const void *Offset(const void *p, std::size_t n) noexcept {
  return p ? static_cast<const std::byte *>(p) + n : nullptr;
}
template <class T> bool Read(const Bindings &b, const void *p,
                            std::size_t n, T &value) noexcept {
  return Copy(b, Offset(p, n), &value, sizeof(value));
}
template <class F, class... A> bool Call(F f, A... args) noexcept {
  if (!f) return false;
#if defined(_MSC_VER)
  __try { f(args...); return true; }
  __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#else
  f(args...); return true;
#endif
}
template <class R, class F, class... A>
bool Returned(F f, R &result, A... args) noexcept {
  if (!f) return false;
#if defined(_MSC_VER)
  __try { result = f(args...); return true; }
  __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#else
  result = f(args...); return true;
#endif
}

game::BattleCurrentPersonRawPropertiesSnapshotV1 Properties(
    const Bindings &b, const void *p) {
  game::BattleCurrentPersonRawPropertiesSnapshotV1 out{};
  std::int32_t count{};
  if (!Read(b, p, 0xC, count)) return out;
  out.count = count;
  if (count <= 0) {
    out.keys_u16.emplace(); out.values_q64.emplace(); return out;
  }
  const void *keys{}, *values{};
  if (Read(b, p, 0, keys) && keys) {
    out.keys_u16.emplace(static_cast<std::size_t>(count));
    if (!Copy(b, keys, out.keys_u16->data(), count * sizeof(std::uint16_t)))
      out.keys_u16.reset();
  }
  if (Read(b, p, 0x68, values) && values) {
    out.values_q64.emplace(static_cast<std::size_t>(count));
    if (!Copy(b, values, out.values_q64->data(), count * sizeof(std::int64_t)))
      out.values_q64.reset();
  }
  return out;
}
bool Ready(const game::BattleCurrentPersonRawPropertiesSnapshotV1 &p) noexcept {
  return p.count.has_value() && p.keys_u16.has_value() && p.values_q64.has_value();
}

const void *ResolveTask(const Bindings &b, std::int32_t id,
                       bool &used_default) noexcept {
  const void *store{}, *fallback{}, *slots{}, *task{};
  std::int32_t capacity{}, observed{};
  if (!Read(b, b.task_fallback_slot, 0, fallback)) return nullptr;
  used_default = true;
  if (Read(b, b.task_storage_slot, 0, store) && store &&
      Read(b, store, 0x20, slots) && slots && Read(b, store, 0x2C, capacity)) {
    const auto index = static_cast<std::uint32_t>(id) & 0xFFFFFFU;
    if (index < static_cast<std::uint32_t>(capacity) &&
        Read(b, slots, static_cast<std::size_t>(index) * 16 + 8, task) && task &&
        Read(b, task, 0x10, observed) && observed == id) {
      used_default = false; return task;
    }
  }
  return fallback;
}

class Scope {
public:
  Scope(const Bindings &b, std::int32_t root,
        const std::int32_t *saved0 = nullptr, const std::int32_t *saved4 = nullptr)
      : b_(b) {
    if (!b.construct_actor_scope || !b.destroy_scope) return;
    constructed_ = Returned(b.construct_actor_scope, context_, bytes_.data(), &root);
    ready_ = constructed_ && context_;
    if (saved0) ready_ = Save(b.saved_scope_token_0, *saved0) && ready_;
    if (saved4) ready_ = Save(b.saved_scope_token_4, *saved4) && ready_;
  }
  ~Scope() { if (constructed_) Call(b_.destroy_scope, bytes_.data()); }
  const void *get() const noexcept { return ready_ ? context_ : nullptr; }
private:
  bool Save(const std::int32_t *slot, std::int32_t id) noexcept {
    std::int32_t token{};
    if (!context_ || !Read(b_, slot, 0, token)) return false;
    const ScopeToken scope{4, 0, static_cast<std::uint32_t>(id)};
    return Call(b_.save_scope, static_cast<std::byte *>(context_) + 0x18, token, &scope);
  }
  const Bindings &b_;
  alignas(8) std::array<std::byte, 0x168> bytes_{};
  void *context_ = nullptr;
  bool constructed_ = false, ready_ = false;
};

struct alignas(8) VectorStorage {
  std::array<std::byte, kVectorStorageBound> bytes{};
};
class ModifierVector {
public:
  explicit ModifierVector(const Bindings &b) : b_(b) {}
  ~ModifierVector() {
    if (!constructed_) return;
    const void *data{}, *allocator{}, *vtable{};
    std::int32_t count{};
    if (Read(b_, get(), 0, data) && Read(b_, get(), 0xC, count) && data) {
      for (std::int32_t i = 0; i < count; ++i)
        Call(b_.destroy_modifier, const_cast<void *>(Offset(data, i * kModifierSize)));
      const std::int32_t zero = 0;
      std::memcpy(storage_->bytes.data() + 0xC, &zero, sizeof(zero));
      using Release = void (*)(const void *, const void *, std::size_t);
      Release release{};
      if (Read(b_, get(), 0x10, allocator) && allocator &&
          Read(b_, allocator, 0, vtable) && Read(b_, vtable, 0x10, release))
        Call(release, allocator, data, std::size_t{8});
    }
  }
  bool Ensure() {
    if (constructed_) return true;
    if (!b_.initialize_modifier_vector || !b_.destroy_modifier ||
        !b_.collect_scoped_declarations) return false;
    storage_ = std::make_unique<VectorStorage>();
    constructed_ = Call(b_.initialize_modifier_vector, storage_->bytes.data());
    return constructed_;
  }
  void *get() const noexcept { return storage_ ? storage_->bytes.data() : nullptr; }
private:
  const Bindings &b_;
  std::unique_ptr<VectorStorage> storage_;
  bool constructed_ = false;
};

struct DeclarationHeader {
  const void *data = nullptr;
  std::int32_t capacity = 1, count = 1;
};
static_assert(sizeof(DeclarationHeader) == 0x10);

bool ObserveDeclaration(const Bindings &b, ModifierVector &vector,
    const void *declaration, const Scope &scope, std::int32_t source_index,
    std::string_view kind, std::int32_t root, std::optional<std::int32_t> saved,
    game::BattleCurrentPersonTaskPositionTaskSnapshotV1 &task,
    game::BattleCurrentPersonTaskPositionBranchSnapshotV1 &branch) {
  game::BattleCurrentPersonTaskPositionDeclarationSnapshotV1 declared{};
  declared.native_index = source_index;
  declared.contributor_kind = kind;
  declared.scope_root_character_id_raw = root;
  declared.scope_saved_character_id_raw = saved;
  declared.declared_properties = Properties(b, declaration);
  std::uint32_t flags{};
  if (Read(b, declaration, 0x1B8, flags)) declared.modifier_flags_raw = flags;
  declared.source_provenance = "actual_parsed_declaration;scale_not_separately_evaluated";
  if (kind == "task_owner")
    declared.source_provenance += ";selection=terminal_task_type_438";
  task.declarations->push_back(std::move(declared));
  if (!scope.get() || !vector.Ensure()) return false;
  std::int32_t before{}, after{};
  if (!Read(b, vector.get(), 0xC, before)) return false;
  const DeclarationHeader one{declaration, 1, 1};
  if (!Call(b.collect_scoped_declarations, vector.get(), &one, scope.get()) ||
      !Read(b, vector.get(), 0xC, after)) return false;
  const void *rows{};
  if (!Read(b, vector.get(), 0, rows)) return false;
  bool complete = true;
  for (std::int32_t i = before; i < after; ++i) {
    const void *row = Offset(rows, i * kModifierSize);
    game::BattleCurrentPersonTaskPositionEvaluatedRowSnapshotV1 copied{};
    copied.task_native_index = task.native_index;
    copied.contributor_kind = kind;
    copied.declaration_native_index = source_index;
    copied.scope_root_character_id_raw = root;
    copied.scope_saved_character_id_raw = saved;
    copied.properties = Properties(b, row);
    complete = complete && Ready(*copied.properties);
    // Native2438850 does not append a weighted row for a known empty container.
    if (copied.properties->count == 0) continue;
    if (Read(b, row, 0x1B8, flags)) copied.modifier_flags_raw = flags;
    copied.source_provenance = "native2872840_single_actual_declaration;scaled_finalized;scale_unobserved";
    if (kind == "task_owner")
      copied.source_provenance += ";selection=terminal_task_type_438";
    branch.evaluated_rows->push_back(std::move(copied));
  }
  return complete;
}

bool Collection(const Bindings &b, ModifierVector &vector, const void *header,
    bool pointer_rows, const Scope &scope, std::string_view kind,
    std::int32_t root, std::optional<std::int32_t> saved,
    game::BattleCurrentPersonTaskPositionTaskSnapshotV1 &task,
    game::BattleCurrentPersonTaskPositionBranchSnapshotV1 &branch) {
  const void *data{};
  std::int32_t count{};
  if (!Read(b, header, 0, data) || !Read(b, header, 0xC, count)) return false;
  if (!count) return true;
  if (!data || count < 0) return false;
  bool complete = true;
  for (std::int32_t i = 0; i < count; ++i) {
    const void *declaration = Offset(data, i * std::size_t{0x2B0});
    if (pointer_rows && !Read(b, data, i * std::size_t{8}, declaration)) {
      complete = false; continue;
    }
    if (!declaration) { complete = false; continue; }
    complete = ObserveDeclaration(b, vector, declaration, scope, i, kind, root,
                                 saved, task, branch) && complete;
  }
  return complete;
}

bool Task(const Bindings &b, std::int32_t id, std::int32_t native_index,
    game::BattleCurrentPersonTaskPositionTaskSnapshotV1 &out,
    const void *&node, const void *&type, const void *&position,
    const void *&terminal) {
  out.native_index = native_index; out.task_id_raw = id;
  bool used_default{};
  node = ResolveTask(b, id, used_default);
  if (!node) return false;
  out.used_native_default = used_default;
  std::int32_t identity{}, incumbent{}, owner{};
  std::uint8_t frozen{};
  bool complete = Read(b, node, 0x10, identity);
  if (complete) out.resolved_task_id_raw = identity;
  if (Read(b, node, 0x39, frozen)) out.frozen_raw = frozen; else complete = false;
  if (Read(b, node, 0x40, incumbent)) out.incumbent_character_id_raw = incumbent;
  else complete = false;
  if (Read(b, node, 0x44, owner)) out.owner_character_id_raw = owner;
  else complete = false;
  if (Read(b, node, 0x18, type)) out.task_type_present = type != nullptr;
  else complete = false;
  if (!type) { out.original_position_type_present = false;
    out.terminal_task_type_present = false; return complete; }
  if (Read(b, type, 0x40, position)) out.original_position_type_present = position != nullptr;
  else complete = false;
  terminal = type;
  const void *clone{};
  while (terminal) {
    if (!Read(b, terminal, 0x1358, clone)) { terminal = nullptr; complete = false; break; }
    if (!clone) break;
    terminal = clone;
  }
  out.terminal_task_type_present = terminal != nullptr;
  return complete;
}

struct alignas(8) ActualTaskScopes32 {
  std::int32_t incumbent = -1;
  std::int32_t owner = -1;
  std::uint32_t zero32 = 0;
  std::uint32_t padding0C = 0;
  const void *null64 = nullptr;
  std::uint8_t false8 = 0;
  std::array<std::byte, 7> padding19{};
};
static_assert(sizeof(ActualTaskScopes32) == 32);

void OwnerAggregate(const Bindings &b, const void *type, std::int32_t actual_owner,
    game::BattleCurrentPersonTaskPositionTaskSnapshotV1 &out) {
  if (!type || !out.incumbent_character_id_raw ||
      !b.owner_modifier_builder || !b.destroy_modifier) return;
  const ActualTaskScopes32 scopes{*out.incumbent_character_id_raw, actual_owner};
  alignas(8) std::array<std::byte, kModifierSize> storage{};
  void *returned{};
  if (!Returned(b.owner_modifier_builder, returned, type, storage.data(), &scopes))
    return;
  if (returned == storage.data()) {
    out.owner_aggregate_properties = Properties(b, storage.data());
    out.owner_aggregate_properties_ready = Ready(*out.owner_aggregate_properties);
  }
  Call(b.destroy_modifier, storage.data());
}

void Finish(game::BattleCurrentPersonTaskPositionBranchSnapshotV1 &branch,
            bool complete) {
  branch.vectors_ready = complete;
  branch.status = complete ? "available" : "partial";
  if (!complete) {
    branch.evaluated_rows.reset();
    branch.unavailable_reason = "native_declaration_or_scoped_output_unavailable";
    return;
  }
  bool empty = true;
  for (const auto &row : *branch.evaluated_rows)
    empty = empty && row.properties && row.properties->count == 0;
  branch.complete_no_contribution = empty;
}
} // namespace

Bindings BindImage12003(std::uintptr_t base, std::string_view sha) noexcept {
  Bindings b{};
  if (!base || sha != kSha) return b;
  b.enabled = true;
  b.task_storage_slot = reinterpret_cast<void **>(base + 0x5D1DEA0);
  b.task_fallback_slot = reinterpret_cast<void **>(base + 0x5D1DDF8);
  b.initialize_modifier_vector = reinterpret_cast<InitializeModifierVector>(base + 0x29227F0);
  b.collect_scoped_declarations = reinterpret_cast<CollectScopedDeclarations>(base + 0x2872840);
  b.construct_actor_scope = reinterpret_cast<ConstructActorScope>(base + 0x9F9E20);
  b.destroy_scope = reinterpret_cast<Destroy>(base + 0x87E0E0);
  b.save_scope = reinterpret_cast<SaveScope>(base + 0x373A110);
  b.saved_scope_token_0 = reinterpret_cast<const std::int32_t *>(base + 0x5D4BE24);
  b.saved_scope_token_4 = reinterpret_cast<const std::int32_t *>(base + 0x5D4BE28);
  b.task_gate = reinterpret_cast<TaskGate>(base + 0x31B5450);
  b.owner_modifier_builder = reinterpret_cast<OwnerModifierBuilder>(base + 0x31ABE10);
  b.destroy_modifier = reinterpret_cast<Destroy>(base + 0x9F24F0);
  return b;
}

game::BattleCurrentPersonTaskPositionInputsSnapshotV1 ReadInputs12003(
    const Bindings &b, const void *character, std::int32_t character_id) noexcept {
  game::BattleCurrentPersonTaskPositionInputsSnapshotV1 out{};
  out.character_id = character_id;
  if (!b.enabled || !character) {
    out.unavailable_reason = "task_position_reader_unbound_or_character_unresolved";
    return out;
  }
  try {
    std::int32_t actual{};
    if (!Read(b, character, 0x18, actual) || actual != character_id) {
      out.unavailable_reason = "character_identity_unavailable"; return out;
    }
    ModifierVector vector(b);
    bool raw_complete = true, owned_complete = true, councillor_complete = true;
    out.owned_passive.evaluated_rows.emplace();
    out.councillor_position_task.evaluated_rows.emplace();
    const void *council{};
    if (Read(b, character, 0x1C0, council)) {
      out.owner_council_present = council != nullptr;
      out.ordered_owned_tasks.emplace();
      if (council) {
        const void *ids{}; std::int32_t count{};
        if (!Read(b, council, 0x230, ids) || !Read(b, council, 0x23C, count) ||
            count < 0 || (count && !ids)) { raw_complete = owned_complete = false; }
        else for (std::int32_t i = 0; i < count; ++i) {
          std::int32_t id{};
          if (!Read(b, ids, i * std::size_t{4}, id)) { raw_complete = owned_complete = false; break; }
          game::BattleCurrentPersonTaskPositionTaskSnapshotV1 task{};
          const void *node{}, *type{}, *position{}, *terminal{};
          const bool copied = Task(b, id, i, task, node, type, position, terminal);
          raw_complete = copied && raw_complete;
          task.declarations.emplace();
          if (!task.frozen_raw) owned_complete = false;
          else if (*task.frozen_raw == 0) {
            OwnerAggregate(b, type, actual, task);
            if (!terminal || !position || !task.incumbent_character_id_raw) owned_complete = false;
            else {
              const auto incumbent = *task.incumbent_character_id_raw;
              Scope task_scope(b, incumbent, &incumbent, &actual);
              owned_complete = Collection(b, vector, Offset(terminal, 0x438), true,
                  task_scope, "task_owner", incumbent, actual, task, out.owned_passive) && owned_complete;
              Scope position_scope(b, incumbent);
              owned_complete = Collection(b, vector, Offset(position, 0xDD8), false,
                  position_scope, "position_passive", incumbent, std::nullopt,
                  task, out.owned_passive) && owned_complete;
            }
          }
          out.ordered_owned_tasks->push_back(std::move(task));
        }
      }
    } else raw_complete = owned_complete = false;

    const void *link{};
    if (Read(b, character, 0x1B8, link)) {
      out.councillor_task_link_present = link != nullptr;
      std::int32_t id = -1;
      if (link && !Read(b, link, 0xF0, id)) raw_complete = councillor_complete = false;
      else {
        game::BattleCurrentPersonTaskPositionTaskSnapshotV1 task{};
        const void *node{}, *type{}, *position{}, *terminal{};
        raw_complete = Task(b, id, 0, task, node, type, position, terminal) && raw_complete;
        task.declarations.emplace();
        bool allowed{};
        if (node && Returned(b.task_gate, allowed, node)) task.native_gate_allowed = allowed;
        if (task.frozen_raw && *task.frozen_raw == 0 &&
            task.task_type_present.value_or(false) && !task.native_gate_allowed)
          raw_complete = false;
        if (!task.frozen_raw) councillor_complete = false;
        else if (*task.frozen_raw == 0 && !task.native_gate_allowed) councillor_complete = false;
        else if (*task.frozen_raw == 0 && *task.native_gate_allowed) {
          if (!position || !terminal || !task.owner_character_id_raw) councillor_complete = false;
          else {
            Scope position_scope(b, actual);
            councillor_complete = Collection(b, vector, Offset(position, 0x48), false,
                position_scope, "position_scoped", actual, std::nullopt,
                task, out.councillor_position_task) && councillor_complete;
            const auto owner = *task.owner_character_id_raw;
            Scope task_scope(b, actual, &actual, &owner);
            councillor_complete = Collection(b, vector, Offset(terminal, 0x400), true,
                task_scope, "councillor_task", actual, owner,
                task, out.councillor_position_task) && councillor_complete;
          }
        }
        if (link) out.councillor_task = std::move(task);
      }
    } else raw_complete = councillor_complete = false;
    Finish(out.owned_passive, owned_complete);
    Finish(out.councillor_position_task, councillor_complete);
    out.raw_task_inputs_ready = raw_complete;
    out.branch_vectors_ready = out.owned_passive.vectors_ready && out.councillor_position_task.vectors_ready;
    out.status = raw_complete && out.branch_vectors_ready ? "available" : "partial";
    if (out.status == "partial") out.unavailable_reason = "one_or_more_task_position_inputs_unavailable";
  } catch (...) {
    out.status = "partial"; out.unavailable_reason = "task_position_input_copy_unavailable";
  }
  return out;
}
} // namespace xar::ck3_12003::task_position
