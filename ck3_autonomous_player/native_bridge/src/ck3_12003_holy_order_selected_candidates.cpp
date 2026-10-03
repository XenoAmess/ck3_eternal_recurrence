#include "xar_bridge/ck3_12003_holy_order_selected_candidates.hpp"

#include <cstring>

#if defined(_MSC_VER) && defined(_WIN32)
#include <Windows.h>
#endif

namespace xar::ck3_12003::religion::holy_order::selected_candidates {
namespace {

bool ExactHash(std::string_view hash) noexcept {
  if (hash.size() != kExeSha256.size()) return false;
  for (std::size_t i = 0; i < hash.size(); ++i) {
    char value = hash[i];
    if (value >= 'A' && value <= 'F')
      value = static_cast<char>(value + ('a' - 'A'));
    if (value != kExeSha256[i]) return false;
  }
  return true;
}

bool ReadBytes(const void* address, void* out, std::size_t size) noexcept {
  if (address == nullptr) return false;
#if defined(_MSC_VER) && defined(_WIN32)
  __try { std::memcpy(out, address, size); }
  __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#else
  std::memcpy(out, address, size);
#endif
  return true;
}

template <typename T>
bool Read(const void* object, std::size_t offset, T& output) noexcept {
  if (object == nullptr) return false;
  return ReadBytes(static_cast<const std::byte*>(object) + offset, &output,
                   sizeof(output));
}

bool Initialize(const Bindings& bindings, void* allocator,
                NativeTitleRefVector& vector) noexcept {
  vector.allocator = allocator;
#if defined(_MSC_VER) && defined(_WIN32)
  __try {
    bindings.initialize_vector(allocator, &vector.data, &vector.capacity);
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#else
  bindings.initialize_vector(allocator, &vector.data, &vector.capacity);
#endif
  return true;
}

bool Produce(NativeProduce producer, void* widget, void* actor,
             NativeTitleRefVector& vector, void* params) noexcept {
#if defined(_MSC_VER) && defined(_WIN32)
  __try { producer(widget, actor, &vector, params, -1); }
  __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#else
  producer(widget, actor, &vector, params, -1);
#endif
  return true;
}

bool Release(const Bindings& bindings, NativeTitleRefVector& vector) noexcept {
  if (vector.data == nullptr) return true;
  vector.count = 0;
#if defined(_MSC_VER) && defined(_WIN32)
  __try { bindings.release_vector(vector.allocator, vector.data, 4); }
  __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#else
  bindings.release_vector(vector.allocator, vector.data, 4);
#endif
  vector.data = nullptr;
  vector.capacity = 0;
  return true;
}

bool SelectedValid(NativeSelectedValid predicate, void* widget, void* params,
                   bool& valid) noexcept {
#if defined(_MSC_VER) && defined(_WIN32)
  __try { valid = predicate(widget, params, nullptr); }
  __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#else
  valid = predicate(widget, params, nullptr);
#endif
  return true;
}

struct TitleRefAllocator {
  std::uintptr_t vtable{};
  std::uint64_t inline_storage{};
  std::uintptr_t fallback{};
};
static_assert(offsetof(TitleRefAllocator, fallback) == 0x10);
static_assert(sizeof(TitleRefAllocator) == 0x18);

}  // namespace

Bindings BindHolyOrderSelectedCandidatesImage12003(
    std::uintptr_t module_base, std::string_view exe_sha256) noexcept {
  Bindings output{};
  if (module_base == 0 || !ExactHash(exe_sha256)) return output;
  output.module_base = module_base;
  output.military_vtable = module_base + 0x4743b48;
  output.landed_title_vtable = module_base + 0x4743988;
  output.title_ref_allocator_vtable = module_base + 0x4524fd8;
  output.title_ref_fallback_allocator = module_base + 0x54deba0;
  output.military_produce = reinterpret_cast<NativeProduce>(module_base + 0x260ee10);
  output.landed_title_produce = reinterpret_cast<NativeProduce>(module_base + 0x260f5d0);
  output.military_selected_valid =
      reinterpret_cast<NativeSelectedValid>(module_base + 0x260eb30);
  output.landed_title_selected_valid =
      reinterpret_cast<NativeSelectedValid>(module_base + 0x260f410);
  output.initialize_vector =
      reinterpret_cast<NativeInitializeVector>(module_base + 0x855a50);
  output.release_vector =
      reinterpret_cast<NativeReleaseVector>(module_base + 0x855830);
  output.available = true;
  return output;
}

bool GetHolyOrderDecisionWidget12003(const Bindings& bindings,
                                    const void* decision, Widget& output) noexcept {
  output = {};
  if (!bindings.available || decision == nullptr) return false;
  void* configuration = nullptr;
  void* pointer = nullptr;
  std::uintptr_t vtable = 0;
  Widget observed{};
  if (!Read(decision, 0x1e20, configuration) ||
      !Read(configuration, 0x40, pointer) || !Read(pointer, 0, vtable) ||
      !Read(pointer, 0x18, observed.selected_name_key) ||
      !Read(configuration, 0x48, observed.configuration_type)) return false;
  observed.pointer = pointer;
  if (vtable == bindings.military_vtable) {
    observed.military = true;
    observed.expected_tier = 1;
    observed.produce = bindings.military_produce;
    observed.selected_valid = bindings.military_selected_valid;
  } else if (vtable == bindings.landed_title_vtable) {
    if (!Read(pointer, 0xf0, observed.expected_tier)) return false;
    observed.produce = bindings.landed_title_produce;
    observed.selected_valid = bindings.landed_title_selected_valid;
  } else {
    return false;
  }
  output = observed;
  return true;
}

bool CollectHolyOrderTitleCandidates12003(
    const Bindings& bindings, const Widget& widget, void* actor, void* params,
    std::vector<std::uint32_t>& output) noexcept {
  output.clear();
  if (!bindings.available || widget.pointer == nullptr || widget.produce == nullptr ||
      actor == nullptr || params == nullptr) return false;
  TitleRefAllocator allocator{bindings.title_ref_allocator_vtable, 0,
                              bindings.title_ref_fallback_allocator};
  NativeTitleRefVector vector{};
  bool succeeded = Initialize(bindings, &allocator, vector);
  if (succeeded) succeeded = Produce(widget.produce, widget.pointer, actor, vector, params);
  if (succeeded) {
    succeeded = vector.count >= 0 && vector.capacity >= vector.count &&
                (vector.count == 0 || vector.data != nullptr);
    if (succeeded) {
      try {
        output.resize(static_cast<std::size_t>(vector.count));
        if (vector.count != 0)
          succeeded = ReadBytes(vector.data, output.data(), output.size() * 4);
      } catch (...) {
        succeeded = false;
      }
    }
  }
  const bool released = Release(bindings, vector);
  if (!succeeded || !released) output.clear();
  return succeeded && released;
}

bool ReadSelectedTitleValid12003(const Bindings& bindings, const Widget& widget,
                               void* params, bool& valid) noexcept {
  valid = false;
  if (!bindings.available || widget.pointer == nullptr ||
      widget.selected_valid == nullptr || params == nullptr) return false;
  return SelectedValid(widget.selected_valid, widget.pointer, params, valid);
}

}  // namespace xar::ck3_12003::religion::holy_order::selected_candidates
