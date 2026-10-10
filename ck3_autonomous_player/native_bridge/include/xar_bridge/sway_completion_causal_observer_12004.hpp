#pragma once
#include <cstddef>
#include <cstdint>

namespace xar::ck3_12004 {
// A session starts only after the existing execution slots were admitted and
// installed. The termination installer joins that same observer lifetime.
std::uint64_t BeginSwayCausalObserverSession12004() noexcept;
std::uint64_t CurrentSwayCausalObserverSession12004() noexcept;
void EndSwayCausalObserverSession12004(std::uint64_t session) noexcept;
std::uint64_t NextSwayCausalInvocation12004() noexcept;
std::size_t ReadAdmittedSwayImageSize12004(std::uintptr_t image_base) noexcept;
}
