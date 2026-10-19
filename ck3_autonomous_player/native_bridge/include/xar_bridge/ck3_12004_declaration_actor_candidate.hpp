#pragma once

#include "xar_bridge/ck3_12002_declarations.hpp"

#include <array>
#include <cstring>

namespace xar::ck3_12004 {

// Exact .4 stock31F4520: actor root kind4, Character+18 zero-extension;
// 31F4728 evaluates the inline type+48 trigger via37998D0 with null evaluator.
// Call only for a source-qualified, deterministic actor-only trigger closure.
// A missing binding is unknown, never an unavailable CB.
struct DeclarationActorCandidateBindings12004 {
  using Construct = void *(*)(void *);
  using Destroy = void (*)(void *);
  struct Token { std::uint32_t kind, reserved; std::uint64_t payload; };
  using Save = void (*)(void *, std::int32_t, const Token *);
  using Predicate = std::uint8_t (*)(const void *, void *, void *);
  Construct construct = nullptr;
  Destroy destroy = nullptr;
  Save save = nullptr;
  Predicate predicate = nullptr;
  const std::int32_t *attacker_key = nullptr;
};
static_assert(sizeof(DeclarationActorCandidateBindings12004::Token) == 16);

inline ck3_12002::DeclarationsCandidateFactV1 ReadDeclarationActorCandidate12004(
    const DeclarationActorCandidateBindings12004 &b, void *type, void *actor) noexcept {
  using Fact = ck3_12002::DeclarationsCandidateFactV1;
  if (!type || !actor || !b.construct || !b.destroy || !b.save ||
      !b.predicate || !b.attacker_key) return Fact::unknown;
  try {
    class Scope {
    public:
      explicit Scope(const DeclarationActorCandidateBindings12004 &binding)
          : binding_(binding) { (void)binding_.construct(bytes_.data()); }
      ~Scope() { binding_.destroy(bytes_.data()); }
      void *get() noexcept { return bytes_.data(); }
    private:
      const DeclarationActorCandidateBindings12004 &binding_;
      alignas(8) std::array<std::byte, 0x168> bytes_{};
    } scope(b);
    std::uint32_t id = 0;
    std::memcpy(&id, static_cast<const std::byte *>(actor) + 0x18, sizeof(id));
    const DeclarationActorCandidateBindings12004::Token token{4, 0, id};
    const std::uint16_t root_kind = 4;
    std::memcpy(scope.get(), &root_kind, sizeof(root_kind));
    std::memcpy(static_cast<std::byte *>(scope.get()) + 8, &token.payload, sizeof(token.payload));
    b.save(static_cast<std::byte *>(scope.get()) + 0x18, *b.attacker_key, &token);
    const auto raw = b.predicate(static_cast<const std::byte *>(type) + 0x48,
                                 scope.get(), nullptr);
    return raw != 0 ? Fact::yes : Fact::no;
  } catch (...) { return Fact::unknown; }
}

} // namespace xar::ck3_12004
