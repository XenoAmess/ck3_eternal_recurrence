#include "xar_bridge/ck3_12003_church_tax_inputs.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace c = xar::ck3_12003::religion::church_tax_inputs;
namespace {
constexpr std::int32_t kRulerId = 0x12000003;
constexpr std::int32_t kContextId = 0x34000005;
constexpr std::int32_t kLesseeId = 0x56000007;
constexpr std::uint32_t kSelectedFaithId = 0x90000017U;
constexpr std::int32_t kDate = 704123;
constexpr std::uint64_t kEpoch = 73;
constexpr char kNativeUtf8[] =
    "#V \"selected\"#! "
    "\xE6\x95\x99\xE4\xBC\x9A\xE7\xA8\x8E\n"
    "native \\ rule";

std::size_t checks = 0;
std::size_t failures = 0;
void Expect(bool condition, const char *message) {
  ++checks;
  if (!condition) { ++failures; std::cerr << "FAIL: " << message << '\n'; }
}

template <typename T> void Store(void *object, std::size_t offset, T value) {
  std::memcpy(static_cast<std::byte *>(object) + offset, &value, sizeof(value));
}
template <typename T> T Load(const void *object, std::size_t offset) {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset, sizeof(value));
  return value;
}
template <typename T> bool Is(const std::optional<T> &value, T expected) {
  return value && *value == expected;
}

struct PriorCall {
  void *rule = nullptr;
  void *node = nullptr;
  std::int64_t override_raw = 0;
  std::int64_t ceiling_raw = 0;
  std::int32_t lessee_id = -1;
  std::int32_t hierarchy_id = -1;
  std::int64_t remaining_raw = 0;
  const void *label = nullptr;
  void *breakdown = nullptr;
};
struct RulerCall {
  void *rule = nullptr;
  void *ruler = nullptr;
  std::int32_t lessee_id = -1;
  bool maximum = true;
  std::int64_t remaining_raw = 0;
  void *breakdown = nullptr;
};

struct Fixture {
  std::array<std::byte, 0x220> ruler{}, context{}, lessee{}, land{};
  std::array<std::byte, 0x20> selected_faith{}, played_faith{};
  std::array<std::byte, 0x400> selected_contract{}, played_contract{};
  std::array<std::byte, 0x40> storage{};
  std::array<std::byte, 16 * 16> slots{};
  std::array<std::byte, 0xB0> game{};
  std::array<std::byte, 0x1F1E8> game_data{};
  void *storage_slot = storage.data();
  void *game_slot = game.data();
  std::array<char, 12> first_label{{'l','e','a','s','e','_','l','i','e','g','e','\0'}};
  std::array<char, 23> second_label{{'t','o','p','_','l','e','a','s','e','_','l','i','e','g','e','_','d','i','r','e','c','t','\0'}};
  std::int32_t mapped_superior = 9, direct_top = 10;
  std::int64_t first_raw = 1111, second_raw = 2222, current_raw = 3333;
  std::int64_t configured_ceiling = 44444;
  std::string native_text = kNativeUtf8;
  std::vector<PriorCall> prior_calls;
  std::vector<RulerCall> ruler_calls;
  std::vector<std::int32_t> top_lessee_inputs;
  std::size_t context_calls = 0, faith_calls = 0, contract_calls = 0;
  std::size_t manager_calls = 0, text_calls = 0, destroy_calls = 0;
  std::size_t heap_allocations = 0, heap_releases = 0;
  c::NativeString32 *owned_output = nullptr;

  std::byte *Rule() { return selected_contract.data() + 0x68; }
  void *Manager() { return game_data.data() + 0x1F1E0; }

  Fixture() {
    Store(ruler.data(), 0x18, kRulerId);
    Store(context.data(), 0x18, kContextId);
    Store(lessee.data(), 0x18, kLesseeId);
    Store(ruler.data(), 0x1C0, static_cast<void *>(land.data()));
    Store(land.data(), 0x1B8, kLesseeId);
    Store(selected_faith.data(), 0x8, kSelectedFaithId);
    Store(played_faith.data(), 0x8, std::uint32_t{23});
    Store(game.data(), 0xA0, static_cast<void *>(game_data.data()));
    SetupCharacterStorage();
    Store(Rule(), 0x8, std::int64_t{-100000});
    Store(Rule(), 0x10, std::int64_t{777});
    Store(Rule(), 0x2E8, std::int64_t{55555});
    Store(Rule(), 0x2F0, std::int64_t{66666});
    Store(Rule(), 0x2F8, configured_ceiling);
    Store(played_contract.data(), 0x360, std::int64_t{99999});
  }

  void SetupCharacterStorage() {
    // Uses the production ResolveCoreCharacter implementation, never a test resolver.
    Store(storage.data(), 0x20, static_cast<void *>(slots.data()));
    Store(storage.data(), 0x2C, std::int32_t{16});
    const auto index = static_cast<std::uint32_t>(kLesseeId) & 0x00FFFFFFU;
    Store(slots.data(), static_cast<std::size_t>(index) * 16 + 8,
          static_cast<void *>(lessee.data()));
  }
};
Fixture *active = nullptr;

void *IncomeContext(void *ruler) {
  auto &f = *active;
  ++f.context_calls;
  Expect(ruler == f.ruler.data(), "income context receives actual played ruler");
  return f.context.data();
}
void *CharacterFaith(void *character) {
  auto &f = *active;
  ++f.faith_calls;
  Expect(character == f.context.data(), "faith must come from selected income context");
  return character == f.context.data() ? f.selected_faith.data() : f.played_faith.data();
}
void *FaithLeaseContract(void *faith) {
  auto &f = *active;
  ++f.contract_calls;
  Expect(faith == f.selected_faith.data(), "contract getter receives context Faith, not played Faith");
  return faith == f.selected_faith.data() ? f.selected_contract.data() : f.played_contract.data();
}
std::int32_t *LeaseLiege(void *manager, std::int32_t *out, std::int32_t lessee) {
  auto &f = *active;
  ++f.manager_calls;
  Expect(manager == f.Manager(), "native lease manager uses game+0xA0 data+0x1F1E0");
  Expect(lessee == kLesseeId, "lease manager receives complete actual lessee ID");
  *out = f.mapped_superior;
  return out;
}
std::int32_t *TopLeaseLiegeDirect(std::int32_t *out, std::int32_t lessee) {
  auto &f = *active;
  f.top_lessee_inputs.push_back(lessee);
  Expect(lessee == kLesseeId, "top getter receives complete actual lessee ID");
  *out = f.direct_top;
  return out;
}
std::int64_t *PriorShare(void *rule, std::int64_t *out, void *node,
    std::int64_t override_raw, std::int64_t ceiling_raw, std::int32_t lessee,
    std::int32_t hierarchy, std::int64_t remaining, const void *label, void *breakdown) {
  auto &f = *active;
  f.prior_calls.push_back({rule, node, override_raw, ceiling_raw, lessee, hierarchy,
                          remaining, label, breakdown});
  *out = f.prior_calls.size() == 1 ? f.first_raw : f.second_raw;
  return out;
}
std::int64_t *RulerShare(void *rule, std::int64_t *out, void *ruler,
    std::int32_t lessee, bool maximum, std::int64_t remaining, void *breakdown) {
  auto &f = *active;
  f.ruler_calls.push_back({rule, ruler, lessee, maximum, remaining, breakdown});
  *out = f.current_raw;
  return out;
}
c::NativeString32 *IncomeRules(void *rule, c::NativeString32 *out,
    void *ruler, void *lessee) {
  auto &f = *active;
  ++f.text_calls;
  Expect(rule == f.Rule(), "formatter receives selected income context TaxRule+0x68");
  Expect(ruler == f.ruler.data(), "formatter third arg is played ruler");
  Expect(lessee == f.lessee.data(), "formatter fourth arg is production-core-resolved lessee");
  Expect(f.owned_output == nullptr, "one owned native result per read");
  Expect(Load<std::uint64_t>(out, 0x10) == 0, "formatter receives fresh output slot");
  f.owned_output = out;
  std::memset(out, 0, sizeof(*out));
  const auto size = static_cast<std::uint64_t>(f.native_text.size());
  Store(out, 0x10, size);
  if (size < 16) {
    Store(out, 0x18, std::uint64_t{15});
    std::memcpy(out->bytes.data(), f.native_text.data(), static_cast<std::size_t>(size));
  } else {
    auto *heap = new char[f.native_text.size() + 1];
    std::memcpy(heap, f.native_text.c_str(), f.native_text.size() + 1);
    Store(out, 0, heap);
    Store(out, 0x18, size);
    ++f.heap_allocations;
  }
  return out;
}
void DestroyString(c::NativeString32 *value) {
  auto &f = *active;
  ++f.destroy_calls;
  Expect(value == f.owned_output, "native destructor receives exact formatter output");
  Expect(f.destroy_calls == f.text_calls, "native owned result destroyed exactly once");
  const auto capacity = Load<std::uint64_t>(value, 0x18);
  if (capacity >= 16) {
    auto *heap = Load<char *>(value, 0);
    const auto size = Load<std::uint64_t>(value, 0x10);
    std::memset(heap, '#', static_cast<std::size_t>(size));
    delete[] heap;
    ++f.heap_releases;
  }
  // Overwrite source storage so a borrowed result cannot pass copy verification.
  std::memset(value, '#', sizeof(*value));
  Store(value, 0x10, std::uint64_t{0});
  Store(value, 0x18, std::uint64_t{15});
  Store(value, 0, char{0});
}

c::Bindings Bindings(Fixture &f) {
  c::Bindings b{};
  b.enabled = true;
  b.core.enabled = true;
  b.core.character_storage_slot = &f.storage_slot;
  b.game_state_slot = &f.game_slot;
  b.income_context = &IncomeContext;
  b.character_faith = &CharacterFaith;
  b.faith_lease_contract = &FaithLeaseContract;
  b.lease_liege = &LeaseLiege;
  b.top_lease_liege_direct = &TopLeaseLiegeDirect;
  b.prior_share = &PriorShare;
  b.ruler_share = &RulerShare;
  b.income_rules = &IncomeRules;
  b.string_destroy = &DestroyString;
  b.lease_liege_label = f.first_label.data();
  b.top_lease_liege_direct_label = f.second_label.data();
  return b;
}

void CheckCalls(Fixture &f, const c::Terms &out, std::int32_t superior,
                std::size_t top_calls) {
  Expect(f.context_calls == 1 && f.faith_calls == 1 && f.contract_calls == 1,
         "one income context Faith/contract selection");
  Expect(f.manager_calls == 1 && f.top_lessee_inputs.size() == top_calls,
         "native hierarchy call counts preserve fallback behavior");
  Expect(f.prior_calls.size() == 2, "exactly two prior native share calls");
  Expect(f.ruler_calls.size() == 1, "one current ruler native share call");
  if (f.prior_calls.size() != 2 || f.ruler_calls.size() != 1) return;
  const auto &first = f.prior_calls[0];
  const auto &second = f.prior_calls[1];
  Expect(first.rule == f.Rule() && second.rule == f.Rule(), "prior context is selected TaxRule");
  Expect(first.node == f.Rule() + 0x108 && second.node == f.Rule() + 0x1F8,
         "native authored value nodes preserve exact offsets");
  Expect(first.override_raw == -100000 && second.override_raw == 777,
         "native override sentinel and direct override are forwarded unchanged");
  Expect(first.ceiling_raw == 55555 && second.ceiling_raw == 66666,
         "native prior allocation ceilings are forwarded unchanged");
  Expect(first.lessee_id == kLesseeId && second.lessee_id == kLesseeId,
         "both prior consumers receive actual full lessee ID");
  Expect(first.hierarchy_id == superior && second.hierarchy_id == f.direct_top,
         "prior consumers receive native hierarchy identities");
  Expect(first.remaining_raw == 100000 && second.remaining_raw == 100000 - f.first_raw,
         "second native call subtracts first allocation from remaining");
  Expect(first.label == f.first_label.data() && second.label == f.second_label.data(),
         "native label pointers preserve order");
  Expect(first.breakdown == nullptr && second.breakdown == nullptr,
         "numeric calls do not construct native reason sinks");
  const auto &current = f.ruler_calls[0];
  Expect(current.rule == f.Rule() && current.ruler == f.ruler.data(),
         "current share receives selected rule and actual ruler pointer");
  Expect(current.lessee_id == kLesseeId && !current.maximum && current.breakdown == nullptr,
         "current share fourth arg is lessee ID and remains current-only");
  Expect(current.remaining_raw == 100000 - f.first_raw - f.second_raw,
         "current native call subtracts both prior allocations");
  Expect(Is(out.lease_liege_share_raw, f.first_raw) && Is(out.top_lease_liege_direct_share_raw, f.second_raw),
         "raw prior outputs are preserved without rescaling");
  Expect(Is(out.effective_ruler_tax_share_raw, f.current_raw) &&
         Is(out.remaining_before_ruler_share_raw, current.remaining_raw),
         "raw current and remaining outputs are preserved");
  Expect(Is(out.native_configured_ruler_tax_ceiling_raw, f.configured_ceiling),
         "configured ceiling comes from selected rule, not played Faith rule");
  Expect(Is(out.income_context_faith_id, kSelectedFaithId),
         "context Faith full uint32 high bits are retained");
  Expect(Is(out.income_context_character_id, kContextId) &&
         Is(out.actual_lessee_character_id, kLesseeId), "native source identities retained");
  Expect(out.income_rules_text && *out.income_rules_text == f.native_text,
         "owned native text is copied before source destruction");
  Expect(f.text_calls == 1 && f.destroy_calls == 1, "formatter and native destructor each called once");
  Expect(f.heap_allocations == f.heap_releases, "native heap text allocation released once");
  Expect(out.available && out.unavailable_reason.empty(), "successful read independently available");
}

std::string WriteWire(const std::filesystem::path &folder, std::string_view name,
                      const c::Terms &out) {
  const auto wire = c::SerializePlayerChurchTaxInputs12003(out);
  Expect(wire.find("\"schema\":\"ck3_12003_player_church_tax_inputs_v1\"") != std::string::npos,
         "actual leaf serializer publishes schema");
  Expect(wire.find("\"raw_scale\":100000,\"share_unit\":\"fraction\"") != std::string::npos,
         "wire declares native share fraction scale");
  Expect(wire.find("\"income_context_faith_id\":2415919127") != std::string::npos,
         "serializer retains unsigned Faith full ID");
  std::ofstream stream(folder / (std::string(name) + ".json"), std::ios::binary);
  Expect(stream.is_open(), "leaf wire file opens");
  stream << wire << '\n';
  stream.close();
  Expect(!stream.fail(), "leaf wire file is written");
  return wire;
}

void RunSuccess(const std::filesystem::path &folder, std::string_view name,
    std::int32_t mapped, std::int32_t top, std::int64_t first,
    std::int64_t second, std::int64_t current, std::int64_t ceiling,
    std::string_view text) {
  Fixture f;
  active = &f;
  f.mapped_superior = mapped; f.direct_top = top;
  f.first_raw = first; f.second_raw = second; f.current_raw = current;
  f.configured_ceiling = ceiling; f.native_text = text;
  Store(f.Rule(), 0x2F8, ceiling);
  c::Terms out{};
  Expect(c::ReadPlayerChurchTaxInputs12003(Bindings(f), f.ruler.data(),
      kRulerId, kDate, kEpoch, out), "actual new leaf reader returns success");
  const auto superior = mapped == -1 ? (top == kLesseeId ? -1 : top) : mapped;
  CheckCalls(f, out, superior, mapped == -1 ? 2U : 1U);
  Expect(out.played_character_id == kRulerId && out.date_raw == kDate && out.capture_epoch == kEpoch,
         "paused frame identity is retained");
  const auto wire = WriteWire(folder, name, out);
  if (text == kNativeUtf8) {
    Expect(wire.find("\xE6\x95\x99\xE4\xBC\x9A\xE7\xA8\x8E") != std::string::npos,
           "native UTF8 bytes survive serialization");
    Expect(wire.find("\\u000a") != std::string::npos &&
           wire.find("\\\"selected\\\"") != std::string::npos &&
           wire.find("\\\\ rule") != std::string::npos,
           "native newline quote and slash are JSON-escaped");
  }
  if (text.empty()) {
    Expect(wire.find("\"income_rules_text\":\"\"") != std::string::npos,
           "valid empty native text remains an available empty string");
    Expect(wire.find("\"effective_ruler_tax_share_raw\":0") != std::string::npos &&
           wire.find("\"native_configured_ruler_tax_ceiling_raw\":0") != std::string::npos,
           "valid native zero shares and zero ceiling remain numeric zero");
  }
  active = nullptr;
}

void RunAbsentLessee(const std::filesystem::path &folder) {
  Fixture f;
  active = &f;
  Store(f.land.data(), 0x1B8, std::int32_t{-1});
  c::Terms out{};
  Expect(!c::ReadPlayerChurchTaxInputs12003(Bindings(f), f.ruler.data(),
      kRulerId, kDate, kEpoch, out), "absent direct lessee is unavailable");
  Expect(!out.available && out.unavailable_reason == "actual_direct_lessee_absent",
         "absent source gets precise unavailable reason");
  Expect(Is(out.actual_lessee_character_id, std::int32_t{-1}), "native absent source sentinel retained");
  Expect(f.manager_calls == 0 && f.prior_calls.empty() && f.ruler_calls.empty() &&
         f.text_calls == 0 && f.destroy_calls == 0, "absence does not evaluate shares or allocate text");
  Expect(!out.effective_ruler_tax_share_raw && !out.income_rules_text,
         "absent source does not fabricate current share or literal rules");
  const auto wire = WriteWire(folder, "actual_lessee_absent", out);
  Expect(wire.find("\"available\":false") != std::string::npos &&
         wire.find("\"effective_ruler_tax_share_raw\":null") != std::string::npos,
         "actual leaf wire reports absent current share");
  active = nullptr;
}
} // namespace

int main(int argc, char **argv) {
  if (argc != 2) {
    std::cerr << "Usage: ck3_12003_church_tax_inputs_test <new-leaf-wire-folder>\n";
    return 2;
  }
  const std::filesystem::path folder(argv[1]);
  std::filesystem::create_directories(folder);
  RunSuccess(folder, "selected_context_faith_utf8", 9, 10, 1111, 2222, 3333, 44444, kNativeUtf8);
  RunSuccess(folder, "hierarchy_fallback", -1, 10, 1111, 2222, 3333, 44444, kNativeUtf8);
  RunSuccess(folder, "hierarchy_self_absent", -1, kLesseeId, 0, 2222, 3333, 44444, kNativeUtf8);
  RunSuccess(folder, "zero_empty_rules", 9, 10, 0, 0, 0, 0, "");
  RunSuccess(folder, "inline_rules", 9, 10, 1111, 2222, 3333, 44444, "rule\n\"x\"\\");
  RunAbsentLessee(folder);
  std::cout << "church_tax_inputs_new_leaf cases=6 checks=" << checks
            << " failures=" << failures << '\n';
  return failures == 0 ? 0 : 1;
}
