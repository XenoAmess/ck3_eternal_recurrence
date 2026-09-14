#pragma once

#include "xar_bridge/active_scheme_state_v1_private_source_adapter.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <string_view>

namespace xar::bridge {

inline constexpr std::string_view
    kActiveSchemeStateV1PrivateNativeBinderGameVersion = "1.19.0.6";
inline constexpr std::uintptr_t
    kActiveSchemeStateV1PrivateApplicationSlotRva = 0x570E068;
inline constexpr std::uintptr_t
    kActiveSchemeStateV1PrivateManagerOffset = 0xA538;
inline constexpr std::uintptr_t
    kActiveSchemeStateV1PrivateManagerVtableRva = 0x433A840;
inline constexpr std::uintptr_t
    kActiveSchemeStateV1PrivateStorageVtableRva = 0x433A7E8;
inline constexpr std::uintptr_t
    kActiveSchemeStateV1PrivateActiveSchemeVtableRva = 0x433A928;
inline constexpr std::uintptr_t
    kActiveSchemeStateV1PrivateSchemeTypeVtableRva = 0x44081E8;

struct ActiveSchemeStateV1PrivateNativeSignature {
  std::uintptr_t rva = 0;
  std::uint8_t size = 0;
  std::array<std::uint8_t, 16> bytes{};
};

// Exact 1.19.0.6 instruction prefixes used by this binder.  Binding is
// refused unless every prefix and vtable slot below still matches.
inline constexpr std::array<ActiveSchemeStateV1PrivateNativeSignature, 14>
    kActiveSchemeStateV1PrivateNativeSignatures{{
        {0x27FFCF8, 10,
         {0x48, 0x8D, 0x05, 0x41, 0xAB, 0xB3, 0x01, 0x48, 0x89, 0x03}},
        {0x7E91C0, 5, {0x48, 0x8B, 0x41, 0x20, 0xC3}},
        {0x276A120, 4, {0x8B, 0x41, 0x78, 0xC3}},
        {0x276A130, 7, {0x8B, 0x81, 0x50, 0x03, 0x00, 0x00, 0xC3}},
        {0x276A0E0, 8,
         {0x0F, 0xB6, 0x81, 0x4E, 0x0B, 0x00, 0x00, 0xC3}},
        {0x276A0F0, 7, {0x8B, 0x81, 0xBC, 0x09, 0x00, 0x00, 0xC3}},
        {0x276A100, 7, {0x8B, 0x81, 0x9C, 0x02, 0x00, 0x00, 0xC3}},
        {0x25F3340, 8,
         {0x0F, 0xB6, 0x81, 0x7C, 0x02, 0x00, 0x00, 0xC3}},
        {0x26AF030, 11,
         {0x80, 0xB9, 0xA8, 0x02, 0x00, 0x00, 0x01, 0x0F, 0x94, 0xC0,
          0xC3}},
        {0x2777E90, 12,
         {0x83, 0x79, 0x30, 0x00, 0x75, 0x32, 0x48, 0x8B, 0x05, 0x93,
          0x42, 0xF9}},
        {0x2777ED0, 12,
         {0x83, 0x79, 0x30, 0x01, 0x75, 0x32, 0x48, 0x8B, 0x05, 0x33,
          0x45, 0xF9}},
        {0x276ED50, 15,
         {0x48, 0x89, 0x5C, 0x24, 0x10, 0x48, 0x89, 0x74, 0x24, 0x18,
          0x48, 0x89, 0x7C, 0x24, 0x20}},
        {0x276EF50, 15,
         {0x48, 0x89, 0x5C, 0x24, 0x08, 0x48, 0x89, 0x74, 0x24, 0x10,
          0x48, 0x89, 0x7C, 0x24, 0x18}},
        {0x2771530, 12,
         {0x48, 0x83, 0xEC, 0x68, 0x0F, 0x57, 0xC0, 0x48, 0xC7, 0x44,
          0x24, 0x50}},
    }};

struct ActiveSchemeStateV1PrivateNativeSlot {
  std::uintptr_t slot_rva = 0;
  std::uintptr_t function_rva = 0;
};

inline constexpr std::array<ActiveSchemeStateV1PrivateNativeSlot, 4>
    kActiveSchemeStateV1PrivateNativeSlots{{
        {0x433A840, 0x276A7C0},
        {0x433A7E8, 0x2776D60},
        {0x433A928, 0x276CCA0},
        {0x44081E8, 0x7E9220},
    }};

using ActiveSchemeStateV1PrivateNativeReadMemory = bool (*)(
    void *context, const void *address, void *output,
    std::size_t size) noexcept;
using ActiveSchemeStateV1PrivateNativeReadStableKey = bool (*)(
    void *context, const void *native_string, char *output,
    std::size_t output_capacity) noexcept;
using ActiveSchemeStateV1PrivateNativeReadSuccess = bool (*)(
    void *context, std::uintptr_t module_base, const void *scheme,
    std::int32_t &success, std::int32_t &maximum) noexcept;
using ActiveSchemeStateV1PrivateNativeReadSecrecy = bool (*)(
    void *context, std::uintptr_t module_base, const void *scheme,
    std::int32_t &secrecy) noexcept;
using ActiveSchemeStateV1PrivateNativeReadSecretFlag = bool (*)(
    void *context, std::uintptr_t module_base, const void *scheme,
    bool &is_secret) noexcept;

struct ActiveSchemeStateV1PrivateNativeOperations {
  ActiveSchemeStateV1PrivateNativeReadMemory read_memory = nullptr;
  ActiveSchemeStateV1PrivateNativeReadStableKey read_stable_key = nullptr;
  ActiveSchemeStateV1PrivateNativeReadSuccess read_success = nullptr;
  ActiveSchemeStateV1PrivateNativeReadSecrecy read_secrecy = nullptr;
  ActiveSchemeStateV1PrivateNativeReadSecretFlag read_secret_flag = nullptr;
};

struct ActiveSchemeStateV1PrivateNativeEnvironment {
  bool binding_enabled = false;
  bool exact_build_admitted = false;
  std::string_view admitted_executable_sha256{};
  std::string_view admitted_game_version{};
  bool offline_fixture = false;
  std::uintptr_t module_base = 0;
  void *operation_context = nullptr;
  ActiveSchemeStateV1PrivateNativeOperations operations{};
};

// This state retains only module/callback metadata.  Native manager,
// container, scheme, type, and target pointers are re-resolved per callback.
struct ActiveSchemeStateV1PrivateNativeBindingState {
  std::uintptr_t module_base = 0;
  void *operation_context = nullptr;
  ActiveSchemeStateV1PrivateNativeOperations operations{};
  void *upstream_context = nullptr;
  CaptureActiveSchemeStateV1PrivateSourceFrame upstream_capture_frame =
      nullptr;
  bool attached = false;
};

// Installs the private manager/container/row callbacks into the SCHEME3
// adapter.  The caller must already provide the shared paused frame callback
// and application-main thread ids; heartbeat registration remains shared glue.
bool BindActiveSchemeStateV1PrivateNative(
    const ActiveSchemeStateV1PrivateNativeEnvironment &binding,
    ActiveSchemeStateV1PrivateNativeBindingState &state,
    ActiveSchemeStateV1PrivateSourceAccess &access) noexcept;

} // namespace xar::bridge
