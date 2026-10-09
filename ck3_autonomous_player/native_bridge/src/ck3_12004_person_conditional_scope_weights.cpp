#include "xar_bridge/ck3_12004_person_conditional_scope_weights.hpp"

#include <algorithm>
#include <array>
#include <cstring>
#include <sstream>
#include <utility>

namespace xar::ck3_12004 {
namespace {
template <typename T> T Load(const void *object, std::size_t offset = 0) {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset, sizeof(value));
  return value;
}
template <typename T> void Store(void *object, std::size_t offset, T value) {
  std::memcpy(static_cast<std::byte *>(object) + offset, &value, sizeof(value));
}
template <typename T> std::optional<T> Copy(
    const PersonCarrierDirect12004Bindings &b, std::uintptr_t address) {
  T value{};
  if (!b.read_memory || !b.read_memory(b.read_context,
      reinterpret_cast<const void *>(address), &value, sizeof(value)))
    return std::nullopt;
  return value;
}
using DestroyElement = void (*)(void *, std::uint32_t);
using FreeVector = void (*)(void *, void *, std::uint32_t);

class OwnedScope {
public:
  alignas(16) std::array<std::byte, kPersonConditionalScopeStorageBytes12004> bytes{};
  bool constructed = false;
  OwnedScope() = default;
  OwnedScope(const OwnedScope &) = delete;
  OwnedScope &operator=(const OwnedScope &) = delete;
  ~OwnedScope() { if (constructed) Cleanup(); }

  bool Initialize(const PersonConditionalScopeWeights12004Bindings &b,
                  std::uint32_t payload) {
    auto *s = bytes.data();
    Store(s, 0, std::uint32_t{0});
    Store(s, 8, std::uint64_t{0});
    Store(s, 0x10, std::uint32_t{0xFFFFFFFFU});
    const auto result = b.construct_vector(s + 0x18);
    constructed = true;
    Store(s, 0x100, std::uintptr_t{0});
    Store(s, 0x108, std::uint64_t{0});
    Store(s, 0x110, b.module_base + 0x54DE270);
    Store(s, 0x118, b.module_base + 0x448D1F8);
    Store(s, 0x120, b.module_base + 0x448D268);
    Store(s, 0x128, std::uintptr_t{0});
    Store(s, 0x130, std::uint64_t{0});
    Store(s, 0x138, b.module_base + 0x54DE278);
    Store(s, 0x140, std::uint32_t{0});
    Store(s, 0x148, std::uintptr_t{0});
    Store(s, 0x150, std::uint64_t{0});
    Store(s, 0x158, b.module_base + 0x54DE270);
    Store(s, 0x160, std::uint32_t{0xFFFFFFFFU});
    Store(s, 0x164, std::uint16_t{0});
    Store(s, 0x166, std::uint8_t{0});
    Store(s, 0, std::uint16_t{4});
    Store(s, 8, static_cast<std::uint64_t>(payload));
    return result == s + 0x18;
  }
private:
  void Vector(std::size_t pointer_offset, std::size_t count_offset,
              std::size_t capacity_offset, std::size_t allocator_offset,
              std::size_t stride) {
    auto *s = bytes.data();
    auto *pointer = Load<void *>(s, pointer_offset);
    if (pointer == nullptr) return;
    const auto count = Load<std::int32_t>(s, count_offset);
    for (std::int32_t i = 0; i < count; ++i) {
      auto *element = static_cast<std::byte *>(pointer) + static_cast<std::size_t>(i) * stride;
      const auto table = Load<const void *>(element);
      const auto destroy = reinterpret_cast<DestroyElement>(Load<std::uintptr_t>(table));
      destroy(element, 0);
    }
    Store(s, count_offset, std::int32_t{0});
    auto *allocator = Load<void *>(s, allocator_offset);
    const auto table = Load<const void *>(allocator);
    const auto free = reinterpret_cast<FreeVector>(Load<std::uintptr_t>(table, 0x10));
    free(allocator, pointer, 8);
    Store(s, pointer_offset, static_cast<void *>(nullptr));
    Store(s, capacity_offset, std::int32_t{0});
  }
  void Cleanup() {
    Vector(0x148, 0x154, 0x150, 0x158, 0x48);
    Vector(0x128, 0x134, 0x130, 0x138, 0x20);
    Vector(0x100, 0x10C, 0x108, 0x110, 0x48);
    auto *s = bytes.data();
    auto *pointer = Load<void *>(s, 0x18);
    if (pointer != nullptr) {
      auto *allocator = Load<void *>(s, 0x28);
      Store(s, 0x24, std::int32_t{0});
      const auto table = Load<const void *>(allocator);
      const auto free = reinterpret_cast<FreeVector>(Load<std::uintptr_t>(table, 0x10));
      free(allocator, pointer, 8);
    }
    constructed = false;
  }
};

PersonConditional2921a90Row Unavailable(const PersonConditional2921a90Row &source,
                                      std::string_view reason) {
  auto row = source;
  row.ready = false;
  row.reason = reason;
  row.weight_q64.reset();
  return row;
}
class Json {
public:
  std::ostringstream out;
  bool first = true;
  Json() { out << '{'; }
  void Text(std::string_view value) {
    constexpr char hex[] = "0123456789abcdef";
    out << '"';
    for (const unsigned char c : value) {
      if (c == '"' || c == '\\') out << '\\' << static_cast<char>(c);
      else if (c < 0x20) out << "\\u00" << hex[c >> 4] << hex[c & 0xF];
      else out << static_cast<char>(c);
    }
    out << '"';
  }
  void Key(std::string_view name) {
    if (!first) out << ',';
    first = false; Text(name); out << ':';
  }
  void String(std::string_view name, std::string_view value, bool nullable = false) {
    Key(name); if (nullable && value.empty()) out << "null"; else Text(value);
  }
  void Bool(std::string_view name, bool value) { Key(name); out << (value ? "true" : "false"); }
  template <typename T> void Number(std::string_view name, std::optional<T> value) {
    Key(name); if (value) out << +*value; else out << "null";
  }
  void Pointer(std::string_view name, std::optional<std::uintptr_t> value) {
    Key(name); if (value) out << "\"0x" << std::hex << *value << std::dec << '"'; else out << "null";
  }
  std::string End() { out << '}'; return out.str(); }
};
} // namespace

PersonConditionalScopeWeights12004Bindings BindPersonConditionalScopeWeightsImage12004(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept {
  PersonConditionalScopeWeights12004Bindings b;
  if (module_base == 0 || executable_sha256 != kExecutableSha256) return b;
  b.enabled = true; b.module_base = module_base;
  b.construct_vector = reinterpret_cast<PersonConditionalScopeConstructVector12004>(
      module_base + kPersonConditionalScopeConstructorRva12004);
  b.read_weight = reinterpret_cast<PersonConditionalScopeReadWeight12004>(
      module_base + kPersonConditionalScopeRowWeightRva12004);
  return b;
}

PersonConditionalScopeWeights12004DTO ReadPersonConditionalScopeWeights12004(
    const PersonConditionalScopeWeights12004Bindings &b,
    const PersonCarrierDirect12004Bindings &memory,
    const PersonFollowing2921a90DTO &direct,
    const PersonConditionalOpinion12004DTO &opinion) {
  PersonConditionalScopeWeights12004DTO d;
  d.build_version = kGameVersion; d.executable_sha256 = kExecutableSha256;
  d.character_id = opinion.character_id;
  d.selected_object_identity = opinion.source_inputs.selected_object_identity;
  d.classifier_ready = opinion.classifier_ready;
  d.classifier_result_i32 = opinion.classifier_result_i32;
  d.selected_family = opinion.selected_family;
  d.selected_array_identity = opinion.selected_array_identity;
  d.selected_count_i32 = opinion.selected_count_i32;
  if (direct.character_id != opinion.character_id ||
      direct.selected_object_identity != d.selected_object_identity) {
    d.reason = "scope_source_receiver_mismatch"; return d;
  }
  if (opinion.rows.empty()) {
    d.ready = opinion.ready;
    d.reason = opinion.reason;
    d.occurrence_count = opinion.occurrence_count;
    return d;
  }
  const bool native_demanded = std::any_of(opinion.rows.begin(), opinion.rows.end(),
      [](const auto &row) { return !row.weight_q64; });
  OwnedScope scope;
  bool prefix = !native_demanded;
  std::string scope_reason;
  if (native_demanded) {
    if (!b.enabled || !b.construct_vector || !b.read_weight) {
      scope_reason = "scope_weight_binding_unavailable";
    } else if (!memory.enabled || !memory.read_memory ||
        !d.selected_object_identity || *d.selected_object_identity == 0) {
      scope_reason = "scope_weight_payload_unread";
    } else {
      d.scope_payload_u32 = Copy<std::uint32_t>(memory, *d.selected_object_identity + 0x20);
      if (!d.scope_payload_u32) scope_reason = "scope_weight_payload_unread";
      else {
        d.scope_initialized = scope.Initialize(b, *d.scope_payload_u32);
        if (!d.scope_initialized) scope_reason = "scope_constructor_return_mismatch";
        else { d.scope_kind_u16 = std::uint16_t{4}; prefix = true; }
      }
    }
  }
  d.ready = true;
  std::uint32_t ordinal = 0, occurrences = 0;
  for (const auto &source : opinion.rows) {
    PersonConditionalScopeWeightRow12004 row;
    row.native_index = source.native_index;
    row.source_inputs = source;
    row.scope_prefix_ready = prefix;
    if (!native_demanded || (!prefix && source.weight_q64)) {
      row.evaluation_selection = "same_sample_source";
      row.evaluated_inputs = source;
    } else if (!prefix) {
      row.evaluated_inputs = Unavailable(source, scope_reason.empty()
          ? "scope_weight_source_prefix_unavailable" : scope_reason);
    } else if (!source.object_identity || *source.object_identity == 0) {
      prefix = false; row.scope_prefix_ready = false;
      row.evaluated_inputs = Unavailable(source, "scope_weight_source_row_unavailable");
      scope_reason.clear();
    } else {
      row.weight_call_ordinal = ordinal++;
      std::int64_t observed{};
      const auto result = b.read_weight(reinterpret_cast<const void *>(*source.object_identity),
                                        &observed, scope.bytes.data());
      if (result != &observed) {
        prefix = false; row.scope_prefix_ready = false;
        row.evaluated_inputs = Unavailable(source, "scope_native_weight_unavailable");
        scope_reason.clear();
      } else {
        row.evaluation_selection = "native_row_2872300";
        row.evaluated_inputs = ReadPersonConditional2921a90RowWithWeightInputs12004(
            memory, *d.selected_array_identity, source.native_index, observed);
      }
    }
    if (!row.evaluated_inputs || !row.evaluated_inputs->ready) {
      d.ready = false;
      if (d.reason.empty()) d.reason = row.evaluated_inputs
          ? row.evaluated_inputs->reason : "scope_weight_source_prefix_unavailable";
    } else if (row.evaluated_inputs->weight_q64 && *row.evaluated_inputs->weight_q64 != 0) ++occurrences;
    d.rows.push_back(std::move(row));
  }
  if (d.ready) d.occurrence_count = occurrences;
  return d;
}

std::string SerializePersonConditionalScopeWeights12004(const PersonConditionalScopeWeights12004DTO &d) {
  Json j;
  j.String("schema", kPersonConditionalScopeWeights12004Schema);
  j.String("build_version", d.build_version); j.String("executable_sha256", d.executable_sha256);
  j.Number("character_id", d.character_id); j.Pointer("selected_object_identity", d.selected_object_identity);
  j.Bool("classifier_ready", d.classifier_ready); j.Number("classifier_result_i32", d.classifier_result_i32);
  j.String("selected_family", d.selected_family); j.Pointer("selected_array_identity", d.selected_array_identity);
  j.Number("selected_count_i32", d.selected_count_i32); j.Bool("scope_initialized", d.scope_initialized);
  j.Number("scope_kind_u16", d.scope_kind_u16); j.Number("scope_payload_u32", d.scope_payload_u32);
  j.Bool("ready", d.ready); j.String("reason", d.reason, true);
  j.Key("rows"); j.out << '['; bool first = true;
  for (const auto &r : d.rows) {
    if (!first) j.out << ',';
    first = false;
    Json q;
    q.Number("native_index", std::optional<std::uint32_t>{r.native_index});
    q.String("evaluation_selection", r.evaluation_selection);
    q.Number("weight_call_ordinal", r.weight_call_ordinal);
    q.Bool("scope_prefix_ready", r.scope_prefix_ready);
    q.Key("source_inputs"); q.out << SerializePersonConditional2921a90RowInputs12004(r.source_inputs);
    q.Key("evaluated_inputs");
    if (!r.evaluated_inputs) q.out << "null";
    else q.out << SerializePersonConditional2921a90RowInputs12004(*r.evaluated_inputs);
    j.out << q.End();
  }
  j.out << ']'; j.Number("occurrence_count", d.occurrence_count);
  return j.End();
}
} // namespace xar::ck3_12004
