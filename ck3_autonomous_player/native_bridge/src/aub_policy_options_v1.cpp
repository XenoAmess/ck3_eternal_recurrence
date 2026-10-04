#include "xar_bridge/aub_policy_options_v1.hpp"

#include <Windows.h>

#include <array>
#include <cstring>
#include <limits>
#include <utility>

namespace xar::ck3_12003 {
namespace {
using ck3_11906::ZhongguoScoreboardAccessV1;
using ck3_11906::ZhongguoScoreboardNativeEnvironmentV1;
constexpr std::string_view kExactExe =
    "94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6";
constexpr std::uintptr_t kImageSize = 0x61C5000;
constexpr std::size_t kMaximumRows = 64;
constexpr std::size_t kMaximumDefinitions = 256;
constexpr std::size_t kMaximumKeyBytes = 192;
constexpr std::size_t kEntryStride = 0x200;
constexpr std::size_t kDefinitionStride = 0x2C8;

bool ReadBytes(const ZhongguoScoreboardAccessV1 &access,
               const void *address, void *output, std::size_t size) noexcept {
  if (!address || !output || size == 0) return false;
  if (access.read_memory)
    return access.read_memory(access.context, address, output, size);
#if defined(_MSC_VER)
  __try {
    std::memcpy(output, address, size);
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#else
  return false;
#endif
}

template <typename T>
bool ReadAt(const ZhongguoScoreboardAccessV1 &access, const void *object,
            std::size_t offset, T &value) noexcept {
  const auto address = reinterpret_cast<std::uintptr_t>(object);
  return address != 0 &&
         offset <= std::numeric_limits<std::uintptr_t>::max() - address &&
         ReadBytes(access, reinterpret_cast<const void *>(address + offset),
                   &value, sizeof(value));
}

const void *At(const void *object, std::size_t offset) noexcept {
  const auto address = reinterpret_cast<std::uintptr_t>(object);
  if (address == 0 || offset >
      std::numeric_limits<std::uintptr_t>::max() - address) return nullptr;
  return reinterpret_cast<const void *>(address + offset);
}

bool IsTyped(const ZhongguoScoreboardAccessV1 &access, std::uintptr_t module,
             const void *object, std::uintptr_t vtable_rva,
             std::uint32_t descriptor_rva) noexcept {
  const void *vtable = nullptr;
  if (!ReadAt(access, object, 0, vtable) ||
      reinterpret_cast<std::uintptr_t>(vtable) != module + vtable_rva)
    return false;
  const void *locator = nullptr;
  if (!ReadBytes(access, reinterpret_cast<const void *>(module + vtable_rva - 8),
                 &locator, sizeof(locator))) return false;
  const auto col = reinterpret_cast<std::uintptr_t>(locator);
  if (col < module || col - module > kImageSize - 24) return false;
  std::array<std::uint32_t, 6> fields{};
  return ReadBytes(access, locator, fields.data(), sizeof(fields)) &&
         fields[0] == 1 && fields[1] == 0 &&
         fields[3] == descriptor_rva && fields[5] == col - module;
}

struct Pass {
  const void *application = nullptr;
  const void *logical = nullptr;
  const void *gfx = nullptr;
  const void *handler = nullptr;
  const void *detail = nullptr;
  const void *controller = nullptr;
  const void *root = nullptr;
  const void *decision = nullptr;
  const void *widget_definition = nullptr;
  const void *options_definition = nullptr;
  const void *definitions = nullptr;
  const void *scope = nullptr;
  const void *records = nullptr;
  const void *pool_records = nullptr;
  std::uint32_t definition_count = 0, capacity = 0, count = 0;
  std::uint32_t pool_count = 0, pool_lock = 0;
  std::int32_t selected_index = -1;
  std::int32_t actor_reference = -1;
  std::string decision_key;
  std::vector<const void *> row_definitions;
  std::vector<std::uint32_t> row_key_ids;
  std::vector<AubPolicyEntryV1> entries;
  bool operator==(const Pass &) const = default;
};

bool ReadPooledKey(const ZhongguoScoreboardAccessV1 &access, const Pass &pass,
                   std::uint32_t key_id, std::string &value) {
  const auto index = key_id & 0xFFFFFFU; // Exact real pool getter masks 24 bits.
  if (index >= pass.pool_count) return false;
  const void *text = At(pass.pool_records, static_cast<std::size_t>(index) * 0x20);
  std::uint64_t size = 0, capacity = 0;
  if (!ReadAt(access, text, 0x10, size) ||
      !ReadAt(access, text, 0x18, capacity) || size == 0 ||
      size > kMaximumKeyBytes || size > capacity ||
      (capacity < 16 && capacity != 15)) return false;
  const void *bytes = text;
  if (capacity >= 16 && (!ReadAt(access, text, 0, bytes) || !bytes)) return false;
  std::array<char, kMaximumKeyBytes + 1> buffer{};
  if (!ReadBytes(access, bytes, buffer.data(), static_cast<std::size_t>(size) + 1) ||
      buffer[size] != 0) return false;
  for (std::size_t i = 0; i < size; ++i) {
    const auto c = buffer[i];
    if (!((c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') ||
          (c >= '0' && c <= '9') || c == '_')) return false;
  }
  value.assign(buffer.data(), static_cast<std::size_t>(size));
  return true;
}

bool ReadPass(const ZhongguoScoreboardNativeEnvironmentV1 &environment,
              const ZhongguoScoreboardAccessV1 &access,
              const AubPolicyNativeAdmissionV1 &admission, Pass &pass, std::string &reason) {
  const auto module = environment.module_base;
  std::uint8_t root_flags=0;
  if(!ReadAt(access,admission.decision_detail_root,0xD0,root_flags) || (root_flags&0x08)!=0) { reason="actual_detail_root_hidden_or_unreadable"; return false; }
  const void *backref = nullptr;
  if (!ReadAt(access, environment.gui_global_slot, 0, pass.application) ||
      !IsTyped(access, module, pass.application, 0x449BDA8, 0x5667F88) ||
      !ReadAt(access, reinterpret_cast<const void *>(module + 0x5C6A520), 0, pass.logical) ||
      pass.logical != admission.jomini_state ||
      !IsTyped(access, module, pass.logical, 0x44D6048, 0x55072C0) ||
      !ReadAt(access, pass.logical, 0x18, backref) || backref != pass.application ||
      !ReadAt(access, pass.logical, 0x10, pass.gfx) ||
      !IsTyped(access, module, pass.gfx, 0x44BC408, 0x5514460) ||
      !ReadAt(access, pass.gfx, 0x90, backref) || backref != pass.application ||
      !ReadAt(access, pass.gfx, 0x20, backref) || backref != pass.logical ||
      !ReadAt(access, pass.gfx, 0x88, pass.handler) ||
      !IsTyped(access, module, pass.handler, 0x44BA890, 0x5694B50) ||
      !ReadAt(access, pass.handler, 0x1B8, pass.detail) ||
      !IsTyped(access, module, pass.detail, 0x455D4E8, 0x5795080) ||
      !ReadAt(access, pass.detail, 0xA0, backref) || backref != pass.handler ||
      !ReadAt(access, pass.detail, 0x60, pass.root) || pass.root != admission.decision_detail_root ||
      !ReadAt(access, pass.detail, 0x248, pass.controller) ||
      !IsTyped(access, module, pass.controller, 0x45A0918, 0x5802C40) ||
      !ReadAt(access, pass.controller, 8, backref) || backref != pass.detail ||
      !ReadAt(access, pass.controller, 0x10, backref) || backref != pass.handler) {
    reason = "current_decision_option_owner_or_root_unverified";
    return false;
  }
  if (!ReadAt(access, pass.detail, 0xD0, pass.decision) ||
      !IsTyped(access, module, pass.decision, 0x48BD140, 0x5586B90) ||
      !ReadAt(access, pass.detail, 0xD8, pass.actor_reference) ||
      pass.actor_reference != admission.played_character_id ||
      !ReadAt(access, pass.decision, 0x1E20, pass.widget_definition) ||
      !pass.widget_definition ||
      !ReadAt(access, pass.widget_definition, 0x40, pass.options_definition) ||
      !pass.options_definition ||
      !ReadAt(access, pass.options_definition, 0x18, pass.definitions) ||
      !ReadAt(access, pass.options_definition, 0x24, pass.definition_count) ||
      pass.definition_count > kMaximumDefinitions ||
      (pass.definition_count && !pass.definitions) ||
      !ReadAt(access, pass.controller, 0x18, pass.scope) || !pass.scope ||
      !ReadAt(access, pass.controller, 0x20, pass.records) ||
      !ReadAt(access, pass.controller, 0x28, pass.capacity) ||
      !ReadAt(access, pass.controller, 0x2C, pass.count) ||
      !ReadAt(access, pass.controller, 0x38, pass.selected_index) ||
      pass.count > kMaximumRows || pass.count > pass.capacity ||
      pass.count > pass.definition_count || (pass.count && !pass.records) ||
      pass.selected_index < -1 ||
      (pass.selected_index >= 0 &&
       static_cast<std::uint32_t>(pass.selected_index) >= pass.count)) {
    reason = "decision_option_collection_unverified";
    return false;
  }
  // Exact CDecisionType +0x18 MSVC string, independently RTTI qualified.
  std::uint64_t key_size = 0, key_capacity = 0;
  const void *key_bytes = At(pass.decision, 0x18);
  std::array<char, 18> key{};
  if (!ReadAt(access, pass.decision, 0x28, key_size) || key_size != 17 ||
      !ReadAt(access, pass.decision, 0x30, key_capacity) || key_capacity < key_size ||
      !ReadAt(access, pass.decision, 0x18, key_bytes) || !key_bytes ||
      !ReadBytes(access, key_bytes, key.data(), key.size()) ||
      std::string_view(key.data(), 17) != "enable_auto_build" || key[17] != 0) {
    reason = "actual_selected_decision_key_unverified"; return false;
  }
  pass.decision_key.assign(key.data(), 17);
  const void *pool = reinterpret_cast<const void *>(module + 0x5DC1390);
  std::int32_t initialized = 0;
  if (!ReadBytes(access, reinterpret_cast<const void *>(module + 0x5DC1388),
                 &initialized, sizeof(initialized)) || initialized != -1 ||
      !ReadAt(access, pool, 0x30, pass.pool_records) ||
      !ReadAt(access, pool, 0x3C, pass.pool_count) ||
      !ReadAt(access, pool, 0x48, pass.pool_lock) || (pass.pool_lock & 1) ||
      pass.pool_count > 0x1000000U || (pass.count && !pass.pool_records)) {
    reason = "decision_key_pool_uninitialized_or_unstable";
    return false;
  }
  std::size_t selected_count = 0;
  for (std::size_t i = 0; i < pass.count; ++i) {
    const void *row = At(pass.records, i * kEntryStride);
    const void *definition = nullptr;
    std::uint32_t key_id = 0, definition_key_id = 0;
    std::uint8_t selected = 0;
    if (!ReadAt(access, row, 0, definition) || !definition ||
        !ReadAt(access, row, 0x1F8, key_id) ||
        !ReadAt(access, row, 0x1FD, selected) || selected > 1) {
      reason = "decision_option_entry_unverified";
      return false;
    }
    const auto begin = reinterpret_cast<std::uintptr_t>(pass.definitions);
    const auto candidate = reinterpret_cast<std::uintptr_t>(definition);
    if (candidate < begin || (candidate - begin) % kDefinitionStride != 0 ||
        (candidate - begin) / kDefinitionStride >= pass.definition_count ||
        !ReadAt(access, definition, 0, definition_key_id) ||
        definition_key_id != key_id) {
      reason = "decision_option_entry_definition_mismatch";
      return false;
    }
    AubPolicyEntryV1 value{};
    value.selected = selected != 0;
    if (!ReadPooledKey(access, pass, key_id, value.value_key)) {
      reason = "decision_option_key_unverified";
      return false;
    }
    for (const auto &existing : pass.entries) {
      if (existing.value_key == value.value_key) {
        reason = "decision_option_duplicate_key";
        return false;
      }
    }
    if (value.selected) {
      ++selected_count;
      if (pass.selected_index != static_cast<std::int32_t>(i)) {
        reason = "decision_option_selected_index_mismatch";
        return false;
      }
    }
    pass.row_definitions.push_back(definition);
    pass.row_key_ids.push_back(key_id);
    pass.entries.push_back(std::move(value));
  }
  if (selected_count > 1 ||
      (selected_count == 0 && pass.selected_index != -1)) {
    reason = "decision_option_selection_incoherent";
    return false;
  }
  static constexpr std::array<std::string_view, 6> policies{
    "aub_policy_treasury_only_pause_choice", "aub_policy_treasury_only_continue_choice",
    "aub_policy_personal_only_pause_choice", "aub_policy_personal_only_continue_choice",
    "aub_policy_treasury_first_pause_choice", "aub_policy_treasury_first_continue_choice"};
  if (pass.entries.size() != policies.size()) {
    reason = "actual_six_policy_collection_unverified"; return false;
  }
  for (auto policy : policies) {
    bool found = false;
    for (const auto &entry : pass.entries) found |= entry.value_key == policy;
    if (!found) { reason = "actual_six_policy_key_set_unverified"; return false; }
  }
  std::uint32_t lock_after = 0;
  if (!ReadAt(access, pool, 0x48, lock_after) || lock_after != pass.pool_lock ||
      (lock_after & 1)) {
    reason = "decision_key_pool_changed_during_pass";
    return false;
  }
  return true;
}

constexpr std::array<std::uint8_t, 114> kOnSelectPin{0x48,0x83,0x79,0x18,0x00,0x4C,0x8B,0xD2,0x4C,0x8B,0xC9,0x74,0x64,0x48,0x63,0x41,0x38,0x83,0xF8,0xFF,0x74,0x14,0x4C,0x8B,0xC0,0x48,0x8B,0x41,0x20,0x49,0xC1,0xE0,0x09,0x41,0xC6,0x84,0x00,0xFD,0x01,0x00,0x00,0x00,0x8B,0x51,0x2C,0x33,0xC0,0x85,0xD2,0x7E,0x36,0x45,0x8B,0x82,0xF8,0x01,0x00,0x00,0x48,0x8B,0x49,0x20,0x66,0x90,0x44,0x39,0x81,0xF8,0x01,0x00,0x00,0x74,0x15,0xFF,0xC0,0x48,0x81,0xC1,0x00,0x02,0x00,0x00,0x3B,0xC2,0x7C,0xEA,0x49,0x8B,0xC9,0xE9,0xC2,0xFE,0xFF,0xFF,0x41,0x89,0x41,0x38,0xC6,0x81,0xFD,0x01,0x00,0x00,0x01,0x49,0x8B,0xC9,0xE9,0xAF,0xFE,0xFF,0xFF,0xC3};
constexpr std::array<std::uint8_t, 213> kUpdateScopePin{0x40,0x57,0x48,0x83,0xEC,0x30,0x48,0x83,0x79,0x18,0x00,0x48,0x8B,0xF9,0x0F,0x84,0xBB,0x00,0x00,0x00,0x48,0x89,0x5C,0x24,0x40,0x48,0x8B,0x59,0x20,0x48,0x89,0x6C,0x24,0x48,0x33,0xED,0x48,0x89,0x74,0x24,0x50,0x48,0x63,0x71,0x2C,0x48,0xC1,0xE6,0x09,0x48,0x03,0xF3,0x4C,0x89,0x74,0x24,0x58,0xC7,0x44,0x24,0x20,0x02,0x00,0x00,0x00,0x48,0x89,0x6C,0x24,0x28,0x48,0x3B,0xDE,0x74,0x29,0x0F,0x1F,0x44,0x00,0x00,0x48,0x8B,0x4F,0x18,0x4C,0x8D,0x44,0x24,0x20,0x8B,0x93,0xF8,0x01,0x00,0x00,0x48,0x83,0xC1,0x28,0xE8,0xC8,0x91,0xE6,0x01,0x48,0x81,0xC3,0x00,0x02,0x00,0x00,0x48,0x3B,0xDE,0x75,0xDC,0x48,0x63,0x47,0x38,0x48,0x8B,0x74,0x24,0x50,0x48,0x8B,0x5C,0x24,0x40,0x83,0xF8,0xFF,0x74,0x35,0x48,0x8B,0x4F,0x18,0x4C,0x8D,0x44,0x24,0x20,0x48,0x8B,0xD0,0xC7,0x44,0x24,0x20,0x02,0x00,0x00,0x00,0x48,0x8B,0x47,0x20,0x48,0x83,0xC1,0x28,0x48,0xC1,0xE2,0x09,0x48,0xC7,0x44,0x24,0x28,0x01,0x00,0x00,0x00,0x8B,0x94,0x02,0xF8,0x01,0x00,0x00,0xE8,0x74,0x91,0xE6,0x01,0x48,0x8B,0x4F,0x08,0xE8,0x7B,0x07,0xBA,0xFF,0x4C,0x8B,0x74,0x24,0x58,0x48,0x8B,0x6C,0x24,0x48,0x48,0x83,0xC4,0x30,0x5F,0xC3};
constexpr std::array<std::uint8_t, 149> kWrapperPin{0x48,0x89,0x5C,0x24,0x08,0x48,0x89,0x74,0x24,0x10,0x57,0x48,0x83,0xEC,0x20,0x41,0x8B,0x40,0x08,0x49,0x8B,0xF0,0x48,0x8B,0xF9,0x4C,0x8D,0x0C,0x80,0x49,0x8B,0x00,0x48,0x8B,0x10,0x4A,0x8D,0x1C,0xCA,0xE8,0xD4,0xA4,0x00,0x00,0x48,0x39,0x03,0x75,0x52,0x8B,0x46,0x08,0x48,0x8D,0x14,0x80,0x48,0x8B,0x06,0x48,0x8B,0x08,0x48,0x8B,0x1C,0xD1,0x48,0x8D,0x34,0xD1,0xE8,0xB5,0xA4,0x00,0x00,0x48,0x3B,0xD8,0x74,0x04,0x33,0xC0,0xEB,0x0D,0x48,0x8B,0x03,0x48,0x8D,0x56,0x08,0x48,0x8B,0xCB,0xFF,0x50,0x28,0x48,0x85,0xFF,0x74,0x1D,0x48,0x8B,0x10,0x48,0x8B,0xCF,0xE8,0x1F,0xCF,0xFF,0xFF,0xB0,0x01,0x48,0x8B,0x5C,0x24,0x30,0x48,0x8B,0x74,0x24,0x38,0x48,0x83,0xC4,0x20,0x5F,0xC3,0x48,0x8B,0x5C,0x24,0x30,0x32,0xC0,0x48,0x8B,0x74,0x24,0x38,0x48,0x83,0xC4,0x20,0x5F,0xC3};
constexpr std::array<std::uint8_t, 341> kRegistrationPin{0x40,0x55,0x53,0x57,0x48,0x8D,0x6C,0x24,0xB9,0x48,0x81,0xEC,0xD0,0x00,0x00,0x00,0x48,0x8D,0x45,0xB7,0x48,0x89,0x45,0x67,0x33,0xFF,0x48,0x89,0x7D,0xBF,0x48,0x89,0x7D,0xB7,0x48,0x89,0x7D,0xC7,0x48,0xC7,0x45,0xCF,0x0F,0x00,0x00,0x00,0x48,0x89,0x7D,0xD7,0x48,0x89,0x7D,0xDF,0x48,0x8D,0x1D,0xDB,0x1D,0x1D,0x05,0x48,0x89,0x5D,0xE7,0x48,0x8D,0x45,0xB7,0x48,0x89,0x45,0x67,0x48,0xC7,0x45,0x07,0x0F,0x00,0x00,0x00,0x48,0xC7,0x45,0xFF,0x08,0x00,0x00,0x00,0x48,0xB8,0x4F,0x6E,0x53,0x65,0x6C,0x65,0x63,0x74,0x48,0x89,0x45,0xEF,0x40,0x88,0x7D,0xF7,0x48,0x8D,0x45,0x0F,0x48,0x89,0x45,0x6F,0x48,0x8D,0x55,0xB7,0x48,0x8D,0x4D,0x0F,0xE8,0x80,0x9A,0x54,0x00,0x90,0x48,0x8D,0x45,0x2F,0x48,0x89,0x45,0x77,0x0F,0x57,0xC0,0x0F,0x11,0x45,0x2F,0x48,0x89,0x7D,0x2F,0x48,0x89,0x7D,0x37,0x48,0x89,0x5D,0x3F,0x4C,0x63,0x4D,0xE3,0x49,0xC1,0xE1,0x05,0x4C,0x8B,0x45,0xD7,0x4D,0x03,0xC8,0x33,0xD2,0x48,0x8D,0x4D,0x2F,0xE8,0x5A,0x7E,0x56,0x00,0x90,0x48,0x8D,0x45,0x0F,0x48,0x89,0x44,0x24,0x30,0x48,0x89,0x7C,0x24,0x20,0x45,0x33,0xC9,0x4C,0x8D,0x05,0x61,0x7B,0x5C,0x01,0x33,0xD2,0x48,0x8D,0x4D,0xEF,0xE8,0xF6,0xEF,0x5C,0x01,0x90,0x48,0x39,0x7D,0xD7,0x74,0x22,0x48,0x8D,0x4D,0xD7,0xE8,0xA6,0xA1,0x54,0x00,0x48,0x8B,0x4D,0xE7,0x48,0x8B,0x01,0x44,0x8D,0x47,0x08,0x48,0x8B,0x55,0xD7,0xFF,0x50,0x10,0x48,0x89,0x7D,0xD7,0x89,0x7D,0xDF,0x48,0x8D,0x4D,0xB7,0xE8,0x44,0x9B,0x54,0x00,0x90,0x48,0x8B,0x55,0x07,0x48,0x83,0xFA,0x10,0x72,0x2D,0x48,0xFF,0xC2,0x48,0x8B,0x4D,0xEF,0x48,0x8B,0xC1,0x48,0x81,0xFA,0x00,0x10,0x00,0x00,0x72,0x15,0x48,0x83,0xC2,0x27,0x48,0x8B,0x49,0xF8,0x48,0x2B,0xC1,0x48,0x83,0xC0,0xF8,0x48,0x83,0xF8,0x1F,0x77,0x10,0xE8,0x20,0x7A,0xF1,0x03,0x48,0x81,0xC4,0xD0,0x00,0x00,0x00,0x5F,0x5B,0x5D,0xC3,0xE8,0x3C,0x65,0xF2,0x03,0xCC};
template<std::size_t N> bool Pin(const ZhongguoScoreboardAccessV1 &access,
    std::uintptr_t address, const std::array<std::uint8_t, N> &expected) noexcept {
  std::array<std::uint8_t,N> actual{};
  return ReadBytes(access,reinterpret_cast<const void *>(address),actual.data(),N) && actual == expected;
}
bool SourcePins(const ZhongguoScoreboardNativeEnvironmentV1 &environment,
    const ZhongguoScoreboardAccessV1 &access) noexcept {
  return Pin(access, environment.module_base + 0x18D0FC0, kOnSelectPin) &&
      Pin(access, environment.module_base + 0x18D0EE0, kUpdateScopePin) &&
      Pin(access, environment.module_base + 0x18D4030, kWrapperPin) &&
      Pin(access, environment.module_base + 0x30C400, kRegistrationPin);
}
bool ActualActor(const ZhongguoScoreboardNativeEnvironmentV1 &env,
    const ZhongguoScoreboardAccessV1 &access, std::int32_t id) noexcept {
  std::int32_t current=-1,observed=-1; const void *storage=nullptr,*data=nullptr,*actor=nullptr,*death=nullptr;
  std::uint32_t count=0; const auto base=env.module_base;
  return id>0 && ReadAt(access,reinterpret_cast<const void *>(base+0x54DBC00),0,current) && current==id &&
    ReadAt(access,reinterpret_cast<const void *>(base+0x5C67568),0,storage) && storage &&
    ReadAt(access,storage,0x20,data) && data && ReadAt(access,storage,0x2C,count) && count>0 && count<=0x1000000 &&
    (static_cast<std::uint32_t>(id)&0xFFFFFF)<count &&
    ReadAt(access,data,(static_cast<std::uint32_t>(id)&0xFFFFFF)*0x10ULL+8,actor) && actor &&
    ReadAt(access,actor,0x18,observed) && observed==id && ReadAt(access,actor,0x1D0,death) && !death;
}
bool Admission(const ZhongguoScoreboardNativeEnvironmentV1 &env,
    const ZhongguoScoreboardAccessV1 &access, const AubPolicyNativeAdmissionV1 &a) noexcept {
  return a.executable_sha256==kExactExe && env.exact_build_admitted && env.module_base &&
    env.module_base<=std::numeric_limits<std::uintptr_t>::max()-kImageSize &&
    env.gui_abi_revision==ck3_11906::GuiAbiRevisionV1::crozier12003 &&
    reinterpret_cast<std::uintptr_t>(env.gui_global_slot)==env.module_base+ck3_11906::kCrozierGuiGlobalSlotRva &&
    a.jomini_state && a.decision_detail_root && a.gui_context && a.native_root_effectively_visible && a.native_tree_complete &&
    access.is_main_thread && access.is_main_thread(access.context) &&
    a.revalidate_paused_episode_frame && a.revalidate_paused_episode_frame(a.frame_context) && ActualActor(env,access,a.played_character_id);
}
bool StablePass(const ZhongguoScoreboardNativeEnvironmentV1 &env,
    const ZhongguoScoreboardAccessV1 &access,const AubPolicyNativeAdmissionV1 &a,Pass &out,std::string &reason) {
  if (!Admission(env,access,a)) { reason="exact_visible_paused_episode_owner_unverified"; return false; }
  Pass first{};
  if (!ReadPass(env,access,a,first,reason) || !ReadPass(env,access,a,out,reason)) return false;
  if (first!=out || !Admission(env,access,a)) { reason="actual_policy_model_or_frame_changed"; return false; }
  return true;
}
void Project(const Pass &pass,AubPolicyOptionsObservationV1 &out) {
  out.ready=true; out.played_character_id=pass.actor_reference; out.decision_key=pass.decision_key;
  out.selected_index=pass.selected_index; out.entries=pass.entries;
  for (const auto &entry:pass.entries) if(entry.selected) out.selected_key=entry.value_key;
}
bool NoVisibleModals(const ZhongguoScoreboardAccessV1 &access,const void *context) noexcept {
  const void *data=nullptr; std::int32_t count=-1;
  if (!ReadAt(access,context,0x290,data) || !ReadAt(access,context,0x29C,count) || count<0 || count>256 || (count&&!data)) return false;
  for (std::int32_t n=0;n<count;++n) {
    const void *receiver=nullptr; std::uint8_t flags=0;
    if(!ReadAt(access,data,static_cast<std::size_t>(n)*sizeof(void *),receiver) || !receiver ||
       !ReadAt(access,receiver,0xD0,flags) || (flags&0x08)==0) return false;
  }
  return true;
}
bool CallSource(const ZhongguoScoreboardNativeEnvironmentV1 &env,void *controller,const void *entry) noexcept {
  using Function=void(__fastcall *)(void *,const void *);
#if defined(_MSC_VER)
  __try { reinterpret_cast<Function>(env.module_base+0x18D0FC0)(controller,entry); return true; }
  __except(EXCEPTION_EXECUTE_HANDLER) { return false; }
#else
  return false;
#endif
}
} // namespace
bool ProbeAubPolicyOptionsV1(const ZhongguoScoreboardNativeEnvironmentV1 &env,
    const ZhongguoScoreboardAccessV1 &access,const AubPolicyNativeAdmissionV1 &a,
    AubPolicyOptionsObservationV1 &out) noexcept {
  out={}; try { Pass pass{}; if(StablePass(env,access,a,pass,out.unavailable_reason)) Project(pass,out); return true; }
  catch(...) { out={}; out.unavailable_reason="actual_policy_read_failed"; return false; }
}
bool SelectAubPolicyOptionV1(const ZhongguoScoreboardNativeEnvironmentV1 &env,
    const ZhongguoScoreboardAccessV1 &access,const AubPolicyNativeAdmissionV1 &a,
    std::string_view expected,std::string_view desired,AubPolicySelectionResultV1 &out,
    const AubPolicyOfflineActionV1 *offline) noexcept {
  out={}; try {
    Pass before{};
    if(!StablePass(env,access,a,before,out.unavailable_reason)) return true;
    Project(before,out.before);
    if(expected.empty() || out.before.selected_key!=expected) { out.unavailable_reason="actual_expected_selected_policy_mismatch"; return true; }
    std::size_t target=before.entries.size();
    for(std::size_t n=0;n<before.entries.size();++n) if(before.entries[n].value_key==desired) target=n;
    if(target==before.entries.size()) { out.unavailable_reason="desired_policy_not_actual_six_keys"; return true; }
    if(!SourcePins(env,access) || !NoVisibleModals(access,a.gui_context) ||
       (offline && (!env.offline_fixture_function_overrides || !offline->select)) ||
       (!offline && env.offline_fixture_function_overrides)) {
      out.unavailable_reason="source_pins_modal_or_offline_action_unqualified"; return true;
    }
    Pass immediate{};
    if(!StablePass(env,access,a,immediate,out.unavailable_reason) || immediate!=before ||
       !NoVisibleModals(access,a.gui_context)) { out.unavailable_reason="policy_predispatch_owner_frame_or_model_changed"; return true; }
    out.already_selected=expected==desired;
    if(!out.already_selected) {
      out.dispatch_invoked=true; // Consumed even when handler faults: no retries.
      const auto entry=At(immediate.records,target*kEntryStride);
      out.native_call_completed=offline?offline->select(offline->context,const_cast<void *>(immediate.controller),entry):
          CallSource(env,const_cast<void *>(immediate.controller),entry);
      if(!out.native_call_completed) { out.unavailable_reason="source_onselect_fault_result_unknown_no_retry"; return true; }
    }
    Pass after{};
    if(!StablePass(env,access,a,after,out.unavailable_reason)) return true;
    Project(after,out.after);
    Pass normalized=after;
    normalized.selected_index=before.selected_index;
    for(std::size_t n=0;n<normalized.entries.size();++n) normalized.entries[n].selected=before.entries[n].selected;
    out.postcondition_verified=normalized==before && out.after.selected_key==desired;
    if(!out.postcondition_verified) out.unavailable_reason="actual_selected_policy_after_or_model_binding_unverified";
    return true;
  } catch(...) { out.unavailable_reason="policy_action_read_failed_result_unknown_no_retry"; return false; }
}
} // namespace xar::ck3_12003
