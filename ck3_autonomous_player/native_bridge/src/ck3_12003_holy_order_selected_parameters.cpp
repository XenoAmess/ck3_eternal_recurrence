#include "xar_bridge/ck3_12003_holy_order_selected_parameters.hpp"
#include "xar_bridge/ck3_12003_player_holy_order_context.hpp"

#include <cstring>

#if defined(_MSC_VER)
#include <Windows.h>
#endif

namespace xar::ck3_12003::religion::holy_order::selected_parameters {
namespace {
template <typename T>
bool Read(const void *object, std::size_t offset, T &value) noexcept {
  if (object == nullptr) return false;
#if defined(_MSC_VER)
  __try {
#endif
    std::memcpy(&value, static_cast<const std::byte *>(object) + offset, sizeof(T));
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
}
template <typename T> void Store(void *object, std::size_t offset, T value) noexcept {
  std::memcpy(static_cast<std::byte *>(object) + offset, &value, sizeof(value));
}
template <typename Fn, typename Result, typename... Args>
bool Call(Fn fn, Result &result, Args... args) noexcept {
  if (fn == nullptr) return false;
#if defined(_MSC_VER)
  __try {
#endif
    result = fn(args...);
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
}
template <typename Fn, typename... Args>
bool CallVoid(Fn fn, Args... args) noexcept {
  if (fn == nullptr) return false;
#if defined(_MSC_VER)
  __try {
#endif
    fn(args...);
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
}
struct ScopeToken {
  std::uint32_t kind = 0;
  std::uint32_t reserved = 0;
  std::uint64_t full_reference = UINT32_MAX;
};
static_assert(sizeof(ScopeToken) == 16);
} // namespace

Bindings BindSelectedTitleParametersImage12003(std::uintptr_t base,
                                             std::string_view sha) noexcept {
  Bindings b{};
  if (base == 0 || sha != holy_order::kExecutableSha256) return b;
  b.enabled = true;
  b.create_parameters = reinterpret_cast<CreateParameters>(base + 0x26119A0);
  b.destroy_parameters = reinterpret_cast<DestroyParameters>(base + 0xCA9AD0);
  b.set_named_token = reinterpret_cast<SetNamedToken>(base + 0x373A110);
  b.construct_scope = reinterpret_cast<ConstructScope>(base + 0x889F60);
  b.destroy_scope = reinterpret_cast<DestroyScope>(base + 0x87E0E0);
  b.ruler_key_slot = reinterpret_cast<const std::uint32_t *>(base + 0x5D4BEB4);
  b.puppeteer_key_slot = reinterpret_cast<const std::uint32_t *>(base + 0x5D4C0D8);
  b.barony_key_slot = reinterpret_cast<const std::uint32_t *>(base + 0x5D4BE20);
  b.title_key_slot = reinterpret_cast<const std::uint32_t *>(base + 0x5D4BDC8);
  return b;
}

NativeSelectedTitleParameters::NativeSelectedTitleParameters(
    const Bindings &bindings, std::uint32_t actor) noexcept
    : bindings_(bindings), actor_full_ref_(actor) {
  const auto &b = bindings_;
  if (!b.enabled || b.create_parameters == nullptr || b.destroy_parameters == nullptr ||
      b.set_named_token == nullptr || b.construct_scope == nullptr ||
      b.destroy_scope == nullptr || b.ruler_key_slot == nullptr ||
      b.puppeteer_key_slot == nullptr) return;
  void *returned = nullptr;
  if (!Call(b.create_parameters, returned, static_cast<void *>(&parameters_)) ||
      returned != &parameters_ || parameters_ == nullptr) {
    failure_ = "selected_parameters_construction_unavailable";
    return;
  }
  std::uint32_t ruler_key = 0;
  const ScopeToken ruler{4, 0, actor_full_ref_};
  if (!Read(b.ruler_key_slot, 0, ruler_key) ||
      !CallVoid(b.set_named_token, static_cast<std::byte *>(parameters_) + 0x28,
                ruler_key, static_cast<const void *>(&ruler))) {
    failure_ = "selected_ruler_parameter_unavailable";
    return;
  }
  initialized_ = true;
  failure_ = "none";
}

NativeSelectedTitleParameters::~NativeSelectedTitleParameters() {
  if (scope_constructed_) CallVoid(bindings_.destroy_scope, scope_.data());
  if (parameters_ != nullptr) CallVoid(bindings_.destroy_parameters, parameters_);
}

bool NativeSelectedTitleParameters::SelectTitle(std::uint32_t selected_key,
                                               std::uint32_t title) noexcept {
  scope_ready_ = false;
  if (!initialized_) return false;
  const ScopeToken token{5, 0, title};
  if (!CallVoid(bindings_.set_named_token,
                static_cast<std::byte *>(parameters_) + 0x28,
                selected_key, static_cast<const void *>(&token))) {
    failure_ = "selected_title_parameter_unavailable";
    return false;
  }
  failure_ = "none";
  return true;
}

bool NativeSelectedTitleParameters::ExportPlayerScope() noexcept {
  scope_ready_ = false;
  if (!initialized_) return false;
  if (scope_constructed_) {
    if (!CallVoid(bindings_.destroy_scope, scope_.data())) {
      failure_ = "selected_scope_reconstruction_unavailable";
      return false;
    }
    scope_constructed_ = false;
  }
  scope_.fill(std::byte{});
  void *constructed = nullptr;
  if (!Call(bindings_.construct_scope, constructed, static_cast<void *>(scope_.data())) ||
      constructed != scope_.data()) {
    failure_ = "selected_scope_construction_unavailable";
    return false;
  }
  scope_constructed_ = true;
  Store<std::uint16_t>(scope_.data(), 0, 4);
  Store<std::uint64_t>(scope_.data(), 8, actor_full_ref_);
  std::uint32_t puppeteer_key = 0;
  const ScopeToken puppeteer{4, 0, UINT32_MAX};
  if (!Read(bindings_.puppeteer_key_slot, 0, puppeteer_key) ||
      !CallVoid(bindings_.set_named_token, scope_.data() + 0x18,
                puppeteer_key, static_cast<const void *>(&puppeteer))) {
    failure_ = "selected_scope_puppeteer_unavailable";
    return false;
  }
  const void *rows = nullptr;
  std::int32_t count = -1;
  if (!Read(parameters_, 0x28, rows) || !Read(parameters_, 0x34, count) ||
      count < 0 || (count != 0 && rows == nullptr)) {
    failure_ = "selected_parameters_rows_unavailable";
    return false;
  }
  for (std::int32_t i = 0; i < count; ++i) {
    const auto *row = static_cast<const std::byte *>(rows) +
                      static_cast<std::size_t>(i) * 24;
    std::uint32_t name = 0;
    ScopeToken token{};
    if (!Read(row, 0, name) || !Read(row, 8, token) ||
        !CallVoid(bindings_.set_named_token, scope_.data() + 0x18,
                  name, static_cast<const void *>(&token))) {
      failure_ = "selected_parameters_scope_export_unavailable";
      return false;
    }
  }
  scope_ready_ = true;
  failure_ = "none";
  return true;
}
} // namespace xar::ck3_12003::religion::holy_order::selected_parameters
