#include "xar_bridge/conception_candidate_pending_12004.hpp"

#include <array>
#include <bit>
#include <cstring>
#include <iostream>
#include <stdexcept>

namespace {
namespace pending = xar::ck3_12004::conception_candidate_pending;
constexpr std::int32_t kOwnerId = 0x03000002;
constexpr std::uint32_t kTargetId = 0x83000004U;

void Check(bool condition, const char *message) {
  if (!condition) throw std::runtime_error(message);
}
template <typename T, std::size_t Size>
void Put(std::array<std::byte, Size> &object, std::size_t offset, T value) {
  Check(offset + sizeof(T) <= object.size(), "owned fixture write in bounds");
  std::memcpy(object.data() + offset, &value, sizeof(value));
}

struct Fixture {
  std::array<std::byte, 0x1B8> owner{};
  std::array<std::byte, 0x3F8> extended{};
  std::array<std::byte, 0x20> target{};
  std::uintptr_t denied_address = 0;
  bool target_generation_present = true;
  std::size_t reads = 0;
  std::size_t flag_reads = 0;
  std::size_t target_pointer_reads = 0;
  std::size_t resolver_calls = 0;
  std::int32_t resolved_full_id = -1;

  explicit Fixture(std::uint8_t flag) {
    Put(owner, 0x18, kOwnerId);
    Put(owner, 0x1C, pending::kCharacterMagic);
    Put(owner, 0x1B0, Address(extended));
    Put(extended, 0x3E8, flag);
    Put(extended, 0x3F0, Address(target));
    Put(target, 0x18, kTargetId);
    Put(target, 0x1C, pending::kCharacterMagic);
  }

  template <std::size_t Size>
  static std::uintptr_t Address(const std::array<std::byte, Size> &object) {
    return reinterpret_cast<std::uintptr_t>(object.data());
  }
  template <std::size_t Size>
  static bool Copy(const std::array<std::byte, Size> &object,
                   std::uintptr_t address, void *output, std::size_t size) {
    const auto begin = Address(object);
    if (address < begin || size > Size || address - begin > Size - size)
      return false;
    std::memcpy(output, object.data() + (address - begin), size);
    return true;
  }
  static bool Memory(void *opaque, std::uintptr_t address, void *output,
                     std::size_t size) noexcept {
    auto &fixture = *static_cast<Fixture *>(opaque);
    ++fixture.reads;
    if (address == Address(fixture.extended) + 0x3E8) {
      ++fixture.flag_reads;
      if (size != 1) return false;
    }
    if (address == Address(fixture.extended) + 0x3F0) {
      ++fixture.target_pointer_reads;
      if (size != 8) return false;
    }
    if (address == fixture.denied_address || output == nullptr) return false;
    return Copy(fixture.owner, address, output, size) ||
        Copy(fixture.extended, address, output, size) ||
        Copy(fixture.target, address, output, size);
  }
  static void *Resolve(void *opaque, std::int32_t id) noexcept {
    auto &fixture = *static_cast<Fixture *>(opaque);
    ++fixture.resolver_calls;
    fixture.resolved_full_id = id;
    // Canonical full-ID resolution is supplied by Root in production. This
    // owned-memory seam verifies the exact ID forwarded and pointer match;
    // it does not replace or rerun the already-qualified Character store.
    return fixture.target_generation_present &&
        std::bit_cast<std::uint32_t>(id) == kTargetId
        ? fixture.target.data() : nullptr;
  }
  pending::Access Access() {
    return {true, xar::ck3_12004::kExecutableSha256,
        this, &Memory, &Resolve};
  }
  pending::Observation Observe() {
    const auto old_owner = owner;
    const auto old_extended = extended;
    const auto old_target = target;
    const auto result = pending::Read(Access(), owner.data(), kOwnerId);
    Check(owner == old_owner && extended == old_extended && target == old_target,
          "observer writes no Character, extended or target memory");
    return result;
  }
};

std::size_t scenes = 0;
void KnownByte(const pending::Observation &result, std::uint8_t raw) {
  Check(result.candidate_state_available &&
            result.candidate_state_unavailable_reason.empty() &&
            result.extended_data_present == true &&
            result.candidate_flag_raw == raw,
        "raw byte remains independently available");
}

void Run() {
  {
    Fixture fixture(0);
    fixture.denied_address = Fixture::Address(fixture.extended) + 0x3F0;
    const auto result = fixture.Observe();
    KnownByte(result, 0);
    Check(result.target_status == "not_requested" &&
              !result.target_pointer_raw && !result.target_full_id_raw &&
              fixture.flag_reads == 1 && fixture.target_pointer_reads == 0 &&
              fixture.resolver_calls == 0,
          "zero byte never demands an unused target");
    ++scenes;
  }
  for (const std::uint8_t raw : std::array<std::uint8_t, 2>{1, 0xFF}) {
    Fixture fixture(raw);
    const auto result = fixture.Observe();
    KnownByte(result, raw);
    Check(result.target_status == "resolved" &&
              result.target_unavailable_reason.empty() &&
              result.target_pointer_raw == Fixture::Address(fixture.target) &&
              result.target_full_id_raw == kTargetId &&
              result.resolved_target_character_id == std::bit_cast<std::int32_t>(kTargetId) &&
              fixture.resolved_full_id == std::bit_cast<std::int32_t>(kTargetId) &&
              fixture.flag_reads == 1 && fixture.target_pointer_reads == 1 &&
              fixture.resolver_calls == 1,
          "QWORD target and complete generation-bearing ID remain exact");
    ++scenes;
  }
  {
    Fixture fixture(1);
    Put(fixture.owner, 0x1B0, std::uintptr_t{0});
    const auto result = fixture.Observe();
    Check(!result.candidate_state_available &&
              result.extended_data_present == false && !result.candidate_flag_raw &&
              fixture.flag_reads == 0,
          "absent extension is unavailable, never a false flag");
    ++scenes;
  }
  {
    Fixture fixture(1);
    fixture.denied_address = Fixture::Address(fixture.extended) + 0x3E8;
    const auto result = fixture.Observe();
    Check(!result.candidate_state_available &&
              result.extended_data_present == true && !result.candidate_flag_raw &&
              result.candidate_state_unavailable_reason == "conception_candidate_flag_unavailable" &&
              fixture.target_pointer_reads == 0,
          "unread byte is unavailable and not false");
    ++scenes;
  }
  {
    Fixture fixture(1);
    fixture.denied_address = Fixture::Address(fixture.extended) + 0x3F0;
    const auto result = fixture.Observe();
    KnownByte(result, 1);
    Check(result.target_status == "unavailable" && !result.target_pointer_raw &&
              !result.target_full_id_raw && fixture.resolver_calls == 0,
          "target read failure does not erase known pending byte");
    ++scenes;
  }
  {
    Fixture fixture(1);
    Put(fixture.extended, 0x3F0, std::uintptr_t{0});
    const auto result = fixture.Observe();
    KnownByte(result, 1);
    Check(result.target_status == "null_pointer" && result.target_pointer_raw == 0 &&
              !result.target_full_id_raw && fixture.resolver_calls == 0,
          "known null target is distinct from an unread target");
    ++scenes;
  }
  {
    Fixture fixture(1);
    fixture.denied_address = Fixture::Address(fixture.target) + 0x18;
    const auto result = fixture.Observe();
    KnownByte(result, 1);
    Check(result.target_status == "unavailable" && result.target_pointer_raw &&
              !result.target_full_id_raw && fixture.resolver_calls == 0,
          "unread target identity remains separate from known byte and pointer");
    ++scenes;
  }
  {
    Fixture fixture(1);
    Put(fixture.target, 0x1C, std::uint32_t{0});
    const auto result = fixture.Observe();
    KnownByte(result, 1);
    Check(result.target_status == "invalid_identity" && result.target_full_id_raw == kTargetId &&
              !result.resolved_target_character_id && fixture.resolver_calls == 0,
          "non-Character target is not resolved as a Character");
    ++scenes;
  }
  {
    Fixture fixture(1);
    fixture.target_generation_present = false;
    const auto result = fixture.Observe();
    KnownByte(result, 1);
    Check(result.target_status == "generation_mismatch" &&
              result.target_full_id_raw == kTargetId && !result.resolved_target_character_id &&
              fixture.resolver_calls == 1,
          "full-ID lookup failure cannot be accepted by its low slot index");
    ++scenes;
  }
  {
    Fixture fixture(1);
    Put(fixture.owner, 0x18, std::int32_t{0x04000002});
    const auto result = fixture.Observe();
    Check(!result.candidate_state_available && !result.candidate_flag_raw &&
              fixture.flag_reads == 0,
          "owner generation mismatch is unavailable before slot reads");
    ++scenes;
  }
  {
    Fixture fixture(1);
    auto access = fixture.Access();
    access.executable_sha256 = "different-build";
    const auto result = pending::Read(access, fixture.owner.data(), kOwnerId);
    Check(!result.candidate_state_available && !result.candidate_flag_raw && fixture.reads == 0,
          "different executable does not admit actual4 slots");
    ++scenes;
  }
}
} // namespace

int main() {
  try {
    Run();
    std::cout << "PASS actual4 conception candidate pending: " << scenes
              << " owned-memory scenes; no native action or live pregnancy credit\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "FAIL " << error.what() << '\n';
    return 1;
  }
}
