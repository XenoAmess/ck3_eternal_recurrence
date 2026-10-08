#pragma once

#include "xar_bridge/ck3_12004.hpp"

#include <cstddef>
#include <cstdint>
#include <string>
#include <string_view>
#include <vector>

namespace xar::ck3_12004::actor_cached_succession {

inline constexpr char kSchema[] =
    "ck3-1.20.0.4-actor-cached-succession-v1";

// ACTUAL4-CACHED-CANDIDATE-CONSUMER.actual.json (73146 bytes), SHA-256:
// 3821768e9beb831332b81715dbc30d5a7939e4e4c10c90057fd316f7bc011820.
// Actual .4 member uses: 2C0B66F actor+1C0; 2C0B67B LandState+3A0;
// 2C0B687 signed count+C; 2C0B6AE data+0; 2C0B6B4 DWORD stride4;
// 2C0B6D7 candidate full ID+18. Capacity+8 is not admitted or read.
// This value reader neither binds nor invokes the enclosing classifier.
inline constexpr std::size_t kActorLandStateOffset = 0x1C0;
inline constexpr std::size_t kLandStateCachedSuccessorsOffset = 0x3A0;
inline constexpr std::size_t kCachedSuccessorsDataOffset = 0;
inline constexpr std::size_t kCachedSuccessorsCountOffset = 0x0C;
inline constexpr std::size_t kCachedSuccessorStride = 4;

using ReadMemory = bool (*)(void *context, std::uintptr_t address,
                           void *output, std::size_t size) noexcept;
using ResolveCharacter = std::uintptr_t (*)(
    void *context, std::uint32_t full_character_id) noexcept;

struct Bindings {
  bool enabled = false;
  std::uintptr_t image_base = 0;
  std::string_view actual_executable_sha256{};
  ReadMemory read_memory = nullptr;
  ResolveCharacter resolve_character = nullptr;
  void *user_context = nullptr;
};

// Pure admission of caller-provided callbacks. No process discovery, memory
// read, native function call, or CoreBindings lifetime is hidden here.
Bindings BindImage(std::uintptr_t image_base,
                   std::string_view actual_executable_sha256,
                   ReadMemory read_memory,
                   ResolveCharacter resolve_character,
                   void *user_context) noexcept;

struct Snapshot {
  bool available = false;
  bool roster_complete = false;
  std::string_view unavailable_reason = "cached_successors_not_read";
  std::uint64_t capture_epoch = 0;
  std::int32_t date_raw = 0;
  std::uint32_t actor_character_id_raw = 0xFFFFFFFFU;
  std::uintptr_t actor_pointer = 0;
  std::uintptr_t land_state_pointer = 0;
  std::uintptr_t original_data_pointer = 0;
  std::int32_t native_count_raw = -1;
  std::vector<std::uint32_t> ordered_candidate_character_ids_raw;
};

// The caller owns application-thread admission and before/after frame checks.
// A successful read copies every original occurrence in native order, resolves
// each full generation ID and verifies the owner/header/rows twice. It does
// not filter, score, truncate, refresh, or infer saved-succession serialization.
bool Read(const Bindings &bindings, std::uint64_t capture_epoch,
          std::uint32_t expected_actor_id, std::uint32_t date_raw,
          Snapshot &output) noexcept;

std::string Serialize(const Snapshot &snapshot);

} // namespace xar::ck3_12004::actor_cached_succession
