#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <string_view>

namespace xar::ck3_12003::religion::holy_order::selected_parameters {

using CreateParameters = void *(*)(void *out_unique_pointer);
using DestroyParameters = void (*)(void *native_heap_parameters);
using SetNamedToken = void (*)(void *named_vector, std::uint32_t name_key,
                              const void *token16);
using ConstructScope = void *(*)(void *scope_storage);
using DestroyScope = void (*)(void *scope_storage);

struct Bindings {
  bool enabled = false;
  CreateParameters create_parameters = nullptr;
  DestroyParameters destroy_parameters = nullptr;
  SetNamedToken set_named_token = nullptr;
  ConstructScope construct_scope = nullptr;
  DestroyScope destroy_scope = nullptr;
  const std::uint32_t *ruler_key_slot = nullptr;
  const std::uint32_t *puppeteer_key_slot = nullptr;
  const std::uint32_t *barony_key_slot = nullptr;
  const std::uint32_t *title_key_slot = nullptr;
};

Bindings BindSelectedTitleParametersImage12003(std::uintptr_t module_base,
    std::string_view executable_sha256) noexcept;

// Owns native heap parameters and a native temporary scope. Only scratch
// parameters are modified. No GUI controller/window or command is constructed.
// Current paused application-main owner provides actor and concrete widget key.
#if defined(_MSC_VER)
#pragma warning(push)
#pragma warning(disable : 4324) // Intentional padding for the native 16-byte scope.
#endif
class NativeSelectedTitleParameters {
 public:
  NativeSelectedTitleParameters(const Bindings &, std::uint32_t actor_full_ref) noexcept;
  ~NativeSelectedTitleParameters();
  NativeSelectedTitleParameters(const NativeSelectedTitleParameters &) = delete;
  NativeSelectedTitleParameters &operator=(const NativeSelectedTitleParameters &) = delete;
  bool available() const noexcept { return initialized_; }
  const char *failure() const noexcept { return failure_; }
  // Caller reads the real selected name from the fixed decision widget+0x18.
  // Both selected key and Title ID retain all native bits.
  bool SelectTitle(std::uint32_t selected_name_key,
                   std::uint32_t title_full_ref) noexcept;
  // Reconstructs current actor root, the native null puppeteer token, then
  // exports every params row. Third evaluation scope and fourth CanTake params
  // are separate native objects, as the reviewed command validation caller.
  bool ExportPlayerScope() noexcept;
  void *parameters() const noexcept { return parameters_; }
  void *evaluation_scope() noexcept {
    return scope_ready_ ? scope_.data() : nullptr;
  }

 private:
  const Bindings &bindings_;
  std::uint32_t actor_full_ref_ = UINT32_MAX;
  void *parameters_ = nullptr;
  alignas(16) std::array<std::byte, 0x168> scope_{};
  bool initialized_ = false;
  bool scope_constructed_ = false;
  bool scope_ready_ = false;
  const char *failure_ = "bindings_unavailable";
};
#if defined(_MSC_VER)
#pragma warning(pop)
#endif

} // namespace xar::ck3_12003::religion::holy_order::selected_parameters
