#include "xar_bridge/faction_targeting_row_observer_v1.hpp"

#include <algorithm>
#include <array>
#include <cstring>
#include <initializer_list>
#include <limits>

namespace xar::bridge {
namespace {

static_assert(sizeof(void *) == 8,
              "faction targeting row observer is x64-only");

constexpr std::array<std::uint8_t,
                     kFactionTargetingRowObserverPatchBytesV1>
    kPatchAnchor{0xE8, 0x7D, 0x98, 0xBD, 0xFF,
                 0x48, 0x89, 0x44, 0x24, 0x20,
                 0x48, 0x8D, 0x54, 0x24, 0x30};

std::atomic<FactionTargetingRowObserverStateV1 *> g_active_observer{nullptr};

struct TargetingContainerHeaderV1 {
  std::uintptr_t row_data = 0;
  std::int32_t count = 0;
};

struct CharacterMemberContainerHeaderV1 {
  std::uintptr_t row_data = 0;
  std::int32_t count = 0;
};

struct ResolvedTargetingRowV1 {
  std::uint32_t faction_id = 0;
  std::uintptr_t resolved_faction_address = 0;
  std::uint32_t target_character_id = 0;
  std::uint32_t raw_leader_character_id = 0;
  bool leader_present = false;
  std::uint32_t leader_character_id = 0;
  std::uintptr_t character_member_row_data = 0;
  std::uint32_t character_member_count = 0;
  std::array<std::uint32_t,
             kFactionTargetingRowObserverMaximumCharacterMembersPerFactionV1>
      character_member_ids{};
};

struct CharacterMemberIdentityRowV1 {
  std::uint32_t character_id = 0;
  std::uint32_t owner_faction_id = 0;
};

void AddFailure(FactionTargetingRowObserverStateV1 &state,
                FactionTargetingRowObserverFailureV1 failure) noexcept {
  state.failure_flags.fetch_or(static_cast<std::uint32_t>(failure),
                               std::memory_order_acq_rel);
}

bool DefaultMemoryRead(void *, std::uintptr_t address, void *output,
                       std::size_t size) noexcept {
  if (address == 0 || output == nullptr || size == 0) return false;
#if defined(_MSC_VER)
  __try {
#endif
    std::memcpy(output, reinterpret_cast<const void *>(address), size);
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#endif
}

bool DefaultMemoryWrite(void *, std::uintptr_t address, const void *source,
                        std::size_t size) noexcept {
  if (address == 0 || source == nullptr || size == 0) return false;
#if defined(_MSC_VER)
  __try {
#endif
    std::memcpy(reinterpret_cast<void *>(address), source, size);
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#endif
}

void *DefaultVirtualAlloc(void *, std::size_t size, DWORD allocation_type,
                          DWORD protection) noexcept {
  return VirtualAlloc(nullptr, size, allocation_type, protection);
}

bool DefaultVirtualFree(void *, void *address, std::size_t size,
                        DWORD free_type) noexcept {
  return VirtualFree(address, size, free_type) != FALSE;
}

bool DefaultVirtualProtect(void *, void *address, std::size_t size,
                           DWORD new_protection,
                           DWORD &old_protection) noexcept {
  old_protection = 0;
  return VirtualProtect(address, size, new_protection, &old_protection) != FALSE;
}

bool DefaultFlushInstructionCache(void *, const void *address,
                                  std::size_t size) noexcept {
  return FlushInstructionCache(GetCurrentProcess(), address, size) != FALSE;
}

bool AddRva(std::uintptr_t base, std::uintptr_t rva,
            std::uintptr_t &output) noexcept {
  if (base == 0 ||
      rva > (std::numeric_limits<std::uintptr_t>::max)() - base) {
    output = 0;
    return false;
  }
  output = base + rva;
  return true;
}

std::uintptr_t Resolve(std::uintptr_t override_address,
                       std::uintptr_t module_base,
                       std::uintptr_t rva) noexcept {
  if (override_address != 0) return override_address;
  std::uintptr_t output = 0;
  (void)AddRva(module_base, rva, output);
  return output;
}

bool ReadMemory(const FactionTargetingRowObserverStateV1 &state,
                std::uintptr_t address, void *output,
                std::size_t size) noexcept {
  return state.memory_read != nullptr &&
      state.memory_read(state.memory_context, address, output, size);
}

bool WriteMemory(const FactionTargetingRowObserverStateV1 &state,
                 std::uintptr_t address, const void *source,
                 std::size_t size) noexcept {
  return state.memory_write != nullptr &&
      state.memory_write(state.memory_context, address, source, size);
}

bool BytesEqual(const FactionTargetingRowObserverStateV1 &state,
                std::uintptr_t address, const std::uint8_t *expected,
                std::size_t size) noexcept {
  std::array<std::uint8_t, kFactionTargetingRowObserverPatchBytesV1> actual{};
  if (size > actual.size() ||
      !ReadMemory(state, address, actual.data(), size)) {
    return false;
  }
  return std::memcmp(actual.data(), expected, size) == 0;
}

template <std::size_t Size>
void Emit(std::array<std::uint8_t, Size> &output, std::size_t &cursor,
          std::initializer_list<std::uint8_t> bytes) noexcept {
  for (const auto byte : bytes) output[cursor++] = byte;
}

template <std::size_t Size>
void EmitU64(std::array<std::uint8_t, Size> &output, std::size_t &cursor,
             std::uintptr_t value) noexcept {
  const auto encoded = static_cast<std::uint64_t>(value);
  std::memcpy(output.data() + cursor, &encoded, sizeof(encoded));
  cursor += sizeof(encoded);
}

template <std::size_t Size>
void EmitAbsoluteCall(std::array<std::uint8_t, Size> &output,
                      std::size_t &cursor, std::uintptr_t target) noexcept {
  Emit(output, cursor, {0xFF, 0x15, 0x02, 0x00, 0x00, 0x00, 0xEB, 0x08});
  EmitU64(output, cursor, target);
}

template <std::size_t Size>
void EmitAbsoluteJump(std::array<std::uint8_t, Size> &output,
                      std::size_t &cursor, std::uintptr_t target) noexcept {
  Emit(output, cursor, {0xFF, 0x25, 0x00, 0x00, 0x00, 0x00});
  EmitU64(output, cursor, target);
}

template <std::size_t Size>
void EmitPreserveVolatile(std::array<std::uint8_t, Size> &output,
                          std::size_t &cursor) noexcept {
  Emit(output, cursor,
       {0x9C, 0x50, 0x51, 0x52, 0x41, 0x50,
        0x41, 0x51, 0x41, 0x52, 0x41, 0x53});
  Emit(output, cursor, {0x48, 0x83, 0xEC, 0x20});
}

template <std::size_t Size>
void EmitRestoreVolatile(std::array<std::uint8_t, Size> &output,
                         std::size_t &cursor) noexcept {
  Emit(output, cursor, {0x48, 0x83, 0xC4, 0x20});
  Emit(output, cursor,
       {0x41, 0x5B, 0x41, 0x5A, 0x41, 0x59,
        0x41, 0x58, 0x5A, 0x59, 0x58, 0x9D});
}

extern "C" void FactionTargetingRowPostGetterThunkV1(
    std::uintptr_t targeting_container_address) noexcept {
  auto *state = g_active_observer.load(std::memory_order_acquire);
  if (state == nullptr) return;
  LARGE_INTEGER timestamp{};
  (void)QueryPerformanceCounter(&timestamp);
  (void)CaptureFactionTargetingRowsV1(
      *state, targeting_container_address, GetCurrentThreadId(),
      static_cast<std::uint64_t>(timestamp.QuadPart));
}

bool BuildStub(FactionTargetingRowObserverStateV1 &state,
               std::array<std::uint8_t,
                          kFactionTargetingRowObserverStubCapacityV1>
                   &stub) noexcept {
  stub.fill(0x90);
  std::size_t cursor = 0;

  EmitAbsoluteCall(stub, cursor, state.original_getter_target);
  Emit(stub, cursor, {0x48, 0x89, 0x44, 0x24, 0x20});
  Emit(stub, cursor, {0x48, 0x8D, 0x54, 0x24, 0x30});
  EmitPreserveVolatile(stub, cursor);
  Emit(stub, cursor, {0x48, 0x8B, 0xC8});
  EmitAbsoluteCall(
      stub, cursor,
      reinterpret_cast<std::uintptr_t>(&FactionTargetingRowPostGetterThunkV1));
  EmitRestoreVolatile(stub, cursor);
  EmitAbsoluteJump(stub, cursor, state.continue_target);
  return cursor <= stub.size();
}

void BuildPatch(std::uintptr_t stub_address,
                std::array<std::uint8_t,
                           kFactionTargetingRowObserverPatchBytesV1>
                    &patch) noexcept {
  patch.fill(0x90);
  std::size_t cursor = 0;
  EmitAbsoluteJump(patch, cursor, stub_address);
}

enum class TargetWriteResult { success, failed, rollback_unproven };

TargetWriteResult WriteTarget(
    FactionTargetingRowObserverStateV1 &state,
    const std::uint8_t *expected, const std::uint8_t *replacement) noexcept {
  if (!BytesEqual(state, state.patch_target, expected,
                  kFactionTargetingRowObserverPatchBytesV1)) {
    AddFailure(state, faction_targeting_row_observer_failure_anchor);
    return TargetWriteResult::failed;
  }
  DWORD old_protection = 0;
  if (state.virtual_protect == nullptr ||
      !state.virtual_protect(state.memory_context,
                             reinterpret_cast<void *>(state.patch_target),
                             kFactionTargetingRowObserverPatchBytesV1,
                             PAGE_EXECUTE_READWRITE, old_protection)) {
    AddFailure(state,
               faction_targeting_row_observer_failure_target_protection);
    return TargetWriteResult::failed;
  }
  const bool wrote = WriteMemory(state, state.patch_target, replacement,
                                 kFactionTargetingRowObserverPatchBytesV1);
  const bool flushed = wrote && state.flush_instruction_cache != nullptr &&
      state.flush_instruction_cache(
          state.memory_context,
          reinterpret_cast<const void *>(state.patch_target),
          kFactionTargetingRowObserverPatchBytesV1);
  DWORD ignored = 0;
  const bool restored = state.virtual_protect(
      state.memory_context, reinterpret_cast<void *>(state.patch_target),
      kFactionTargetingRowObserverPatchBytesV1, old_protection, ignored);
  if (wrote && flushed && restored &&
      BytesEqual(state, state.patch_target, replacement,
                 kFactionTargetingRowObserverPatchBytesV1)) {
    return TargetWriteResult::success;
  }
  if (!flushed) AddFailure(state, faction_targeting_row_observer_failure_flush);
  DWORD rollback_old = 0;
  const bool rollback_protected = state.virtual_protect(
      state.memory_context, reinterpret_cast<void *>(state.patch_target),
      kFactionTargetingRowObserverPatchBytesV1, PAGE_EXECUTE_READWRITE,
      rollback_old);
  const bool rollback_written = rollback_protected &&
      WriteMemory(state, state.patch_target, expected,
                  kFactionTargetingRowObserverPatchBytesV1);
  const bool rollback_flushed = rollback_written &&
      state.flush_instruction_cache(
          state.memory_context,
          reinterpret_cast<const void *>(state.patch_target),
          kFactionTargetingRowObserverPatchBytesV1);
  DWORD rollback_ignored = 0;
  const bool rollback_restored = rollback_protected &&
      state.virtual_protect(
          state.memory_context, reinterpret_cast<void *>(state.patch_target),
          kFactionTargetingRowObserverPatchBytesV1, rollback_old,
          rollback_ignored);
  const bool rollback_proven = rollback_flushed && rollback_restored &&
      BytesEqual(state, state.patch_target, expected,
                 kFactionTargetingRowObserverPatchBytesV1);
  if (!rollback_proven) {
    AddFailure(state, faction_targeting_row_observer_failure_rollback);
    return TargetWriteResult::rollback_unproven;
  }
  return TargetWriteResult::failed;
}

bool SameAdmission(const FactionTargetingRowCaptureAdmissionV1 &first,
                   const FactionTargetingRowCaptureAdmissionV1 &second) {
  return first.application_main_thread_id ==
             second.application_main_thread_id &&
      first.paused == second.paused &&
      first.proof_epoch == second.proof_epoch &&
      first.snapshot_revision == second.snapshot_revision &&
      first.date_raw == second.date_raw &&
      first.player_character_id == second.player_character_id &&
      first.player_targeting_faction_count ==
          second.player_targeting_faction_count;
}

bool ReadContainer(
    const FactionTargetingRowObserverStateV1 &state,
    std::uintptr_t address, TargetingContainerHeaderV1 &header) noexcept {
  if (address == 0 ||
      address > (std::numeric_limits<std::uintptr_t>::max)() - 0x0C ||
      !ReadMemory(state, address, &header.row_data, sizeof(header.row_data)) ||
      !ReadMemory(state, address + 0x0C, &header.count,
                  sizeof(header.count)) ||
      header.count < 0 ||
      header.count >
          static_cast<std::int32_t>(kFactionTargetingRowObserverMaximumRowsV1) ||
      (header.count != 0 && header.row_data == 0)) {
    return false;
  }
  const auto count = static_cast<std::size_t>(header.count);
  return count == 0 ||
      header.row_data <=
          (std::numeric_limits<std::uintptr_t>::max)() -
               (count - 1) * kFactionTargetingRowStrideV1;
}

bool ReadCharacterMemberContainer(
    const FactionTargetingRowObserverStateV1 &state,
    std::uintptr_t resolved_faction,
    CharacterMemberContainerHeaderV1 &header) noexcept {
  constexpr std::uintptr_t kContainerOffset = 0x48;
  constexpr std::uintptr_t kCountOffset = 0x54;
  constexpr std::size_t kMemberStride = 0x20;
  constexpr std::size_t kOwnerEndOffset = 0x10;
  if (resolved_faction == 0 ||
      resolved_faction >
          (std::numeric_limits<std::uintptr_t>::max)() - kCountOffset ||
      !ReadMemory(state, resolved_faction + kContainerOffset,
                  &header.row_data, sizeof(header.row_data)) ||
      !ReadMemory(state, resolved_faction + kCountOffset, &header.count,
                  sizeof(header.count)) ||
      header.count < 0 ||
      header.count > static_cast<std::int32_t>(
          kFactionTargetingRowObserverMaximumCharacterMembersPerFactionV1) ||
      (header.count != 0 && header.row_data == 0)) {
    return false;
  }
  const auto count = static_cast<std::size_t>(header.count);
  return count == 0 ||
      header.row_data <=
          (std::numeric_limits<std::uintptr_t>::max)() -
              (count - 1) * kMemberStride - kOwnerEndOffset;
}

enum class CharacterIdentityResolutionV1 {
  resolved,
  unresolved,
  invalid,
};

CharacterIdentityResolutionV1 ResolveCharacterIdentity(
    FactionTargetingRowObserverStateV1 &state,
    std::uint32_t character_id) noexcept {
  std::uintptr_t resolved_character = 0;
  if (state.character_identity_resolver_override != nullptr) {
    if (!state.character_identity_resolver_override(
            state.character_identity_resolver_context, character_id,
            resolved_character)) {
      resolved_character = 0;
      return CharacterIdentityResolutionV1::unresolved;
    }
  } else {
    using Resolver = void *(*)(const std::uint32_t *) noexcept;
    if (state.character_identity_resolver_target == 0) {
      return CharacterIdentityResolutionV1::invalid;
    }
    const auto resolver = reinterpret_cast<Resolver>(
        state.character_identity_resolver_target);
    resolved_character = reinterpret_cast<std::uintptr_t>(
        resolver(&character_id));
    if (resolved_character == 0) {
      return CharacterIdentityResolutionV1::unresolved;
    }
  }
  std::uint32_t character_round_trip = 0;
  if (resolved_character == 0 ||
      resolved_character >
          (std::numeric_limits<std::uintptr_t>::max)() - 0x18 ||
      !ReadMemory(state, resolved_character + 0x18, &character_round_trip,
                  sizeof(character_round_trip)) ||
      character_round_trip != character_id) {
    return CharacterIdentityResolutionV1::invalid;
  }
  return CharacterIdentityResolutionV1::resolved;
}

enum class ResolveRowIdentityResultV1 {
  success,
  faction_identity_failed,
  target_character_failed,
  leader_character_failed,
  member_span_failed,
  member_identity_failed,
  member_ownership_failed,
};

ResolveRowIdentityResultV1 ResolveRowIdentity(
    FactionTargetingRowObserverStateV1 &state,
    std::uintptr_t row_address, std::uint32_t admitted_player_character_id,
    ResolvedTargetingRowV1 &output) noexcept {
  output = {};
  if (!ReadMemory(state, row_address, &output.faction_id,
                  sizeof(output.faction_id)) ||
      output.faction_id == 0) {
    return ResolveRowIdentityResultV1::faction_identity_failed;
  }
  std::uintptr_t resolved_faction = 0;
  if (state.identity_resolver_override != nullptr) {
    if (!state.identity_resolver_override(state.identity_resolver_context,
                                          output.faction_id,
                                          resolved_faction)) {
      return ResolveRowIdentityResultV1::faction_identity_failed;
    }
  } else {
    using Resolver = void *(*)(const std::uint32_t *) noexcept;
    if (state.identity_resolver_target == 0) {
      return ResolveRowIdentityResultV1::faction_identity_failed;
    }
    const auto resolver =
        reinterpret_cast<Resolver>(state.identity_resolver_target);
    resolved_faction = reinterpret_cast<std::uintptr_t>(
        resolver(&output.faction_id));
  }
  std::uint32_t faction_round_trip = 0;
  if (resolved_faction == 0 ||
      resolved_faction >
          (std::numeric_limits<std::uintptr_t>::max)() - 0x40 ||
      !ReadMemory(state, resolved_faction + 0x10, &faction_round_trip,
                  sizeof(faction_round_trip)) ||
      faction_round_trip != output.faction_id) {
    return ResolveRowIdentityResultV1::faction_identity_failed;
  }
  output.resolved_faction_address = resolved_faction;
  if (!ReadMemory(state, resolved_faction + 0x40,
                  &output.target_character_id,
                  sizeof(output.target_character_id)) ||
      output.target_character_id == 0 ||
      output.target_character_id != admitted_player_character_id) {
    return ResolveRowIdentityResultV1::target_character_failed;
  }

  if (ResolveCharacterIdentity(state, output.target_character_id) !=
      CharacterIdentityResolutionV1::resolved) {
    return ResolveRowIdentityResultV1::target_character_failed;
  }

  if (resolved_faction >
          (std::numeric_limits<std::uintptr_t>::max)() - 0x44 ||
      !ReadMemory(state, resolved_faction + 0x44,
                  &output.raw_leader_character_id,
                  sizeof(output.raw_leader_character_id))) {
    return ResolveRowIdentityResultV1::leader_character_failed;
  }
  const auto leader_resolution = output.raw_leader_character_id == 0
      ? CharacterIdentityResolutionV1::unresolved
      : ResolveCharacterIdentity(state, output.raw_leader_character_id);
  if (leader_resolution == CharacterIdentityResolutionV1::invalid) {
    return ResolveRowIdentityResultV1::leader_character_failed;
  }
  output.leader_present =
      leader_resolution == CharacterIdentityResolutionV1::resolved;
  output.leader_character_id = output.leader_present
      ? output.raw_leader_character_id
      : 0;

  CharacterMemberContainerHeaderV1 member_header{};
  if (!ReadCharacterMemberContainer(state, resolved_faction,
                                    member_header)) {
    return ResolveRowIdentityResultV1::member_span_failed;
  }
  output.character_member_row_data = member_header.row_data;
  output.character_member_count =
      static_cast<std::uint32_t>(member_header.count);
  for (std::size_t index = 0;
       index < static_cast<std::size_t>(member_header.count); ++index) {
    CharacterMemberIdentityRowV1 member{};
    const auto member_row_address = member_header.row_data + index * 0x20;
    if (!ReadMemory(state, member_row_address + 0x08, &member,
                    sizeof(member))) {
      return ResolveRowIdentityResultV1::member_span_failed;
    }
    if (member.owner_faction_id != output.faction_id) {
      return ResolveRowIdentityResultV1::member_ownership_failed;
    }
    if (ResolveCharacterIdentity(state, member.character_id) !=
        CharacterIdentityResolutionV1::resolved) {
      return ResolveRowIdentityResultV1::member_identity_failed;
    }
    if (std::find(output.character_member_ids.begin(),
                  output.character_member_ids.begin() + index,
                  member.character_id) !=
        output.character_member_ids.begin() + index) {
      return ResolveRowIdentityResultV1::member_identity_failed;
    }
    output.character_member_ids[index] = member.character_id;
  }
  return ResolveRowIdentityResultV1::success;
}

bool RecordRowResolutionFailure(
    FactionTargetingRowObserverStateV1 &state,
    ResolveRowIdentityResultV1 result) noexcept {
  auto &observation = state.observation;
  switch (result) {
  case ResolveRowIdentityResultV1::success:
    return false;
  case ResolveRowIdentityResultV1::faction_identity_failed:
    observation.identity_failure_count.fetch_add(1,
                                                 std::memory_order_relaxed);
    AddFailure(state,
               faction_targeting_row_observer_failure_identity_resolver);
    return true;
  case ResolveRowIdentityResultV1::target_character_failed:
    observation.target_character_failure_count.fetch_add(
        1, std::memory_order_relaxed);
    AddFailure(state,
               faction_targeting_row_observer_failure_target_character);
    return true;
  case ResolveRowIdentityResultV1::leader_character_failed:
    observation.leader_character_failure_count.fetch_add(
        1, std::memory_order_relaxed);
    AddFailure(state,
               faction_targeting_row_observer_failure_leader_character);
    return true;
  case ResolveRowIdentityResultV1::member_span_failed:
    observation.member_span_failure_count.fetch_add(
        1, std::memory_order_relaxed);
    AddFailure(state, faction_targeting_row_observer_failure_member_span);
    return true;
  case ResolveRowIdentityResultV1::member_identity_failed:
    observation.member_identity_failure_count.fetch_add(
        1, std::memory_order_relaxed);
    AddFailure(state, faction_targeting_row_observer_failure_member_identity);
    return true;
  case ResolveRowIdentityResultV1::member_ownership_failed:
    observation.member_ownership_failure_count.fetch_add(
        1, std::memory_order_relaxed);
    AddFailure(state,
               faction_targeting_row_observer_failure_member_ownership);
    return true;
  }
  return true;
}

void ClearResolved(FactionTargetingRowObserverStateV1 &state) noexcept {
  state.offline_fixture = false;
  state.module_base = 0;
  state.patch_target = 0;
  state.continue_target = 0;
  state.original_getter_target = 0;
  state.identity_resolver_target = 0;
  state.character_identity_resolver_target = 0;
  state.stub = nullptr;
  state.memory_context = nullptr;
  state.memory_read = nullptr;
  state.memory_write = nullptr;
  state.virtual_free = nullptr;
  state.virtual_protect = nullptr;
  state.flush_instruction_cache = nullptr;
  state.capture_admission_context = nullptr;
  state.capture_admission_probe = nullptr;
  state.identity_resolver_context = nullptr;
  state.identity_resolver_override = nullptr;
  state.character_identity_resolver_context = nullptr;
  state.character_identity_resolver_override = nullptr;
}

bool ReleaseStub(FactionTargetingRowObserverStateV1 &state) noexcept {
  if (state.stub == nullptr || state.virtual_free == nullptr) return true;
  return state.virtual_free(state.memory_context, state.stub, 0, MEM_RELEASE);
}

} // namespace

bool CaptureFactionTargetingRowsV1(
    FactionTargetingRowObserverStateV1 &state,
    std::uintptr_t targeting_container_address,
    std::uint32_t current_thread_id, std::uint64_t timestamp_qpc) noexcept {
  auto &observation = state.observation;
  observation.callback_count.fetch_add(1, std::memory_order_relaxed);

  FactionTargetingRowCaptureAdmissionV1 first_admission{};
  if (state.capture_admission_probe == nullptr ||
      !state.capture_admission_probe(state.capture_admission_context,
                                     first_admission)) {
    AddFailure(state, faction_targeting_row_observer_failure_capture_admission);
    return false;
  }
  if (first_admission.application_main_thread_id == 0 ||
      current_thread_id != first_admission.application_main_thread_id) {
    observation.rejected_application_main_count.fetch_add(
        1, std::memory_order_relaxed);
    return false;
  }
  if (!first_admission.paused) {
    observation.rejected_paused_count.fetch_add(1,
                                                std::memory_order_relaxed);
    return false;
  }

  TargetingContainerHeaderV1 first_header{};
  TargetingContainerHeaderV1 second_header{};
  if (!ReadContainer(state, targeting_container_address, first_header)) {
    observation.span_read_failure_count.fetch_add(1,
                                                  std::memory_order_relaxed);
    return false;
  }

  const auto count = static_cast<std::size_t>(first_header.count);
  if (first_admission.player_targeting_faction_count < 0 ||
      first_admission.player_targeting_faction_count != first_header.count) {
    observation.count_equivalence_failure_count.fetch_add(
        1, std::memory_order_relaxed);
    AddFailure(state,
               faction_targeting_row_observer_failure_count_equivalence);
    return false;
  }
  std::array<ResolvedTargetingRowV1,
             kFactionTargetingRowObserverMaximumRowsV1>
      first_rows{};
  for (std::size_t index = 0; index < count; ++index) {
    const auto row_address =
        first_header.row_data + index * kFactionTargetingRowStrideV1;
    const auto resolved = ResolveRowIdentity(
        state, row_address, first_admission.player_character_id,
        first_rows[index]);
    if (RecordRowResolutionFailure(state, resolved)) {
      return false;
    }
  }

  if (!ReadContainer(state, targeting_container_address, second_header)) {
    observation.span_read_failure_count.fetch_add(1,
                                                  std::memory_order_relaxed);
    return false;
  }
  if (first_header.row_data != second_header.row_data ||
      first_header.count != second_header.count) {
    observation.span_stability_failure_count.fetch_add(
        1, std::memory_order_relaxed);
    return false;
  }
  std::array<ResolvedTargetingRowV1,
             kFactionTargetingRowObserverMaximumRowsV1>
      second_rows{};
  for (std::size_t index = 0; index < count; ++index) {
    const auto row_address =
        second_header.row_data + index * kFactionTargetingRowStrideV1;
    const auto resolved = ResolveRowIdentity(
        state, row_address, first_admission.player_character_id,
        second_rows[index]);
    if (RecordRowResolutionFailure(state, resolved)) {
      return false;
    }
  }

  FactionTargetingRowCaptureAdmissionV1 second_admission{};
  if (!state.capture_admission_probe(state.capture_admission_context,
                                     second_admission) ||
      !SameAdmission(first_admission, second_admission)) {
    observation.rejected_state_change_count.fetch_add(
        1, std::memory_order_relaxed);
    return false;
  }

  const bool same_targeting_span = std::equal(
      first_rows.begin(), first_rows.begin() + count, second_rows.begin(),
      [](const ResolvedTargetingRowV1 &left,
         const ResolvedTargetingRowV1 &right) {
        return left.faction_id == right.faction_id &&
            left.resolved_faction_address == right.resolved_faction_address &&
            left.target_character_id == right.target_character_id;
      });
  if (!same_targeting_span) {
    observation.span_stability_failure_count.fetch_add(
        1, std::memory_order_relaxed);
    return false;
  }

  const bool same_leaders = std::equal(
      first_rows.begin(), first_rows.begin() + count, second_rows.begin(),
      [](const ResolvedTargetingRowV1 &left,
         const ResolvedTargetingRowV1 &right) {
        return left.raw_leader_character_id ==
                   right.raw_leader_character_id &&
            left.leader_present == right.leader_present &&
            left.leader_character_id == right.leader_character_id;
      });
  if (!same_leaders) {
    observation.leader_stability_failure_count.fetch_add(
        1, std::memory_order_relaxed);
    AddFailure(state,
               faction_targeting_row_observer_failure_leader_stability);
    return false;
  }

  const bool same_member_spans = std::equal(
      first_rows.begin(), first_rows.begin() + count, second_rows.begin(),
      [](const ResolvedTargetingRowV1 &left,
         const ResolvedTargetingRowV1 &right) {
        return left.character_member_row_data ==
                   right.character_member_row_data &&
            left.character_member_count == right.character_member_count &&
            std::equal(
                left.character_member_ids.begin(),
                left.character_member_ids.begin() +
                    left.character_member_count,
                right.character_member_ids.begin());
      });
  if (!same_member_spans) {
    observation.member_stability_failure_count.fetch_add(
        1, std::memory_order_relaxed);
    AddFailure(state,
               faction_targeting_row_observer_failure_member_stability);
    return false;
  }

  for (std::size_t index = 0; index < count; ++index) {
    auto &row = first_rows[index];
    std::sort(row.character_member_ids.begin(),
              row.character_member_ids.begin() +
                  row.character_member_count);
  }

  std::sort(first_rows.begin(), first_rows.begin() + count,
            [](const ResolvedTargetingRowV1 &left,
               const ResolvedTargetingRowV1 &right) {
              return left.faction_id < right.faction_id;
            });
  if (std::adjacent_find(
          first_rows.begin(), first_rows.begin() + count,
          [](const ResolvedTargetingRowV1 &left,
             const ResolvedTargetingRowV1 &right) {
            return left.faction_id == right.faction_id;
          }) != first_rows.begin() + count) {
    observation.identity_failure_count.fetch_add(1,
                                                 std::memory_order_relaxed);
    return false;
  }

  const auto generation = observation.published_generation.load(
      std::memory_order_relaxed);
  observation.published_generation.store(generation + 1,
                                         std::memory_order_release);
  observation.last_proof_epoch.store(first_admission.proof_epoch,
                                     std::memory_order_relaxed);
  observation.last_snapshot_revision.store(first_admission.snapshot_revision,
                                            std::memory_order_relaxed);
  observation.last_date_raw.store(first_admission.date_raw,
                                  std::memory_order_relaxed);
  observation.last_player_character_id.store(
      first_admission.player_character_id, std::memory_order_relaxed);
  observation.last_campaign_root_targeting_faction_count.store(
      first_admission.player_targeting_faction_count,
      std::memory_order_relaxed);
  observation.last_faction_count.store(static_cast<std::uint32_t>(count),
                                       std::memory_order_relaxed);
  for (std::size_t index = 0;
       index < kFactionTargetingRowObserverMaximumRowsV1; ++index) {
    observation.last_faction_ids[index].store(first_rows[index].faction_id,
                                              std::memory_order_relaxed);
    observation.last_target_character_ids[index].store(
        first_rows[index].target_character_id, std::memory_order_relaxed);
    observation.last_leader_present[index].store(
        first_rows[index].leader_present ? 1U : 0U,
        std::memory_order_relaxed);
    observation.last_leader_character_ids[index].store(
        first_rows[index].leader_character_id, std::memory_order_relaxed);
    const bool leader_present_in_members =
        first_rows[index].leader_present &&
        std::binary_search(
            first_rows[index].character_member_ids.begin(),
            first_rows[index].character_member_ids.begin() +
                first_rows[index].character_member_count,
            first_rows[index].leader_character_id);
    observation.last_leader_present_in_character_members[index].store(
        leader_present_in_members ? 1U : 0U, std::memory_order_relaxed);
    observation.last_character_member_counts[index].store(
        first_rows[index].character_member_count,
        std::memory_order_relaxed);
    for (std::size_t member_index = 0;
         member_index <
             kFactionTargetingRowObserverMaximumCharacterMembersPerFactionV1;
         ++member_index) {
      const auto flat_index =
          index *
              kFactionTargetingRowObserverMaximumCharacterMembersPerFactionV1 +
          member_index;
      observation.last_character_member_ids[flat_index].store(
          first_rows[index].character_member_ids[member_index],
          std::memory_order_relaxed);
    }
  }
  observation.last_thread_id.store(current_thread_id,
                                   std::memory_order_relaxed);
  observation.last_timestamp_qpc.store(timestamp_qpc,
                                       std::memory_order_relaxed);
  observation.accepted_capture_count.fetch_add(1,
                                               std::memory_order_relaxed);
  observation.published_generation.store(generation + 2,
                                         std::memory_order_release);
  return true;
}

bool InstallFactionTargetingRowObserverV1(
    FactionTargetingRowObserverStateV1 &state,
    const FactionTargetingRowObserverEnvironmentV1 &environment) noexcept {
  if (state.installed.load(std::memory_order_acquire) != 0 ||
      g_active_observer.load(std::memory_order_acquire) != nullptr) {
    AddFailure(state, faction_targeting_row_observer_failure_already_installed);
    return false;
  }
  if (!environment.exact_build_admitted ||
      environment.admitted_executable_sha256 !=
          kFactionTargetingRowObserverExecutableSha256V1) {
    AddFailure(state, faction_targeting_row_observer_failure_exact_build);
    return false;
  }
  if (!environment.primary_thread_suspended_proven) {
    AddFailure(
        state,
        faction_targeting_row_observer_failure_primary_thread_suspended);
    return false;
  }
  if (environment.capture_admission_probe == nullptr) {
    AddFailure(state, faction_targeting_row_observer_failure_capture_admission);
    return false;
  }
  const bool has_override =
      environment.patch_target_override != 0 ||
      environment.continue_target_override != 0 ||
      environment.original_getter_target_override != 0 ||
      environment.identity_resolver_target_override != 0 ||
      environment.character_identity_resolver_target_override != 0 ||
      environment.memory_read_override != nullptr ||
      environment.memory_write_override != nullptr ||
      environment.virtual_alloc_override != nullptr ||
      environment.virtual_free_override != nullptr ||
      environment.virtual_protect_override != nullptr ||
      environment.flush_instruction_cache_override != nullptr ||
      environment.identity_resolver_override != nullptr ||
      environment.character_identity_resolver_override != nullptr;
  if (has_override && !environment.offline_fixture) {
    AddFailure(state,
               faction_targeting_row_observer_failure_unsupported_override);
    return false;
  }

  state.offline_fixture = environment.offline_fixture;
  state.module_base = environment.module_base;
  state.patch_target = Resolve(environment.patch_target_override,
                               environment.module_base,
                               kFactionTargetingRowObserverPatchRvaV1);
  state.continue_target = Resolve(environment.continue_target_override,
                                  environment.module_base,
                                  kFactionTargetingRowObserverContinueRvaV1);
  state.original_getter_target = Resolve(
      environment.original_getter_target_override, environment.module_base,
      kFactionTargetingRowGetterRvaV1);
  state.identity_resolver_target = Resolve(
      environment.identity_resolver_target_override, environment.module_base,
      kFactionTargetingIdentityResolverRvaV1);
  state.character_identity_resolver_target = Resolve(
      environment.character_identity_resolver_target_override,
      environment.module_base,
      kFactionTargetingCharacterIdentityResolverRvaV1);
  state.memory_context = environment.memory_context;
  state.memory_read = environment.memory_read_override != nullptr
      ? environment.memory_read_override
      : &DefaultMemoryRead;
  state.memory_write = environment.memory_write_override != nullptr
      ? environment.memory_write_override
      : &DefaultMemoryWrite;
  auto virtual_alloc = environment.virtual_alloc_override != nullptr
      ? environment.virtual_alloc_override
      : &DefaultVirtualAlloc;
  state.virtual_free = environment.virtual_free_override != nullptr
      ? environment.virtual_free_override
      : &DefaultVirtualFree;
  state.virtual_protect = environment.virtual_protect_override != nullptr
      ? environment.virtual_protect_override
      : &DefaultVirtualProtect;
  state.flush_instruction_cache =
      environment.flush_instruction_cache_override != nullptr
      ? environment.flush_instruction_cache_override
      : &DefaultFlushInstructionCache;
  state.capture_admission_context = environment.capture_admission_context;
  state.capture_admission_probe = environment.capture_admission_probe;
  state.identity_resolver_context = environment.identity_resolver_context;
  state.identity_resolver_override = environment.identity_resolver_override;
  state.character_identity_resolver_context =
      environment.character_identity_resolver_context;
  state.character_identity_resolver_override =
      environment.character_identity_resolver_override;

  if (state.patch_target == 0 || state.continue_target == 0 ||
      state.original_getter_target == 0 ||
      state.identity_resolver_target == 0 ||
      state.character_identity_resolver_target == 0 ||
      !BytesEqual(state, state.patch_target, kPatchAnchor.data(),
                  kPatchAnchor.size())) {
    AddFailure(state, faction_targeting_row_observer_failure_anchor);
    ClearResolved(state);
    return false;
  }
  std::memcpy(state.original_patch_bytes.data(), kPatchAnchor.data(),
              kPatchAnchor.size());
  state.stub = virtual_alloc(state.memory_context,
                             kFactionTargetingRowObserverStubCapacityV1,
                             MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE);
  if (state.stub == nullptr) {
    AddFailure(state, faction_targeting_row_observer_failure_allocation);
    ClearResolved(state);
    return false;
  }
  std::array<std::uint8_t, kFactionTargetingRowObserverStubCapacityV1> stub{};
  if (!BuildStub(state, stub) ||
      !WriteMemory(state, reinterpret_cast<std::uintptr_t>(state.stub),
                   stub.data(), stub.size())) {
    AddFailure(state, faction_targeting_row_observer_failure_allocation);
    (void)ReleaseStub(state);
    ClearResolved(state);
    return false;
  }
  DWORD old_stub_protection = 0;
  if (!state.virtual_protect(state.memory_context, state.stub, stub.size(),
                             PAGE_EXECUTE_READ, old_stub_protection) ||
      !state.flush_instruction_cache(state.memory_context, state.stub,
                                     stub.size())) {
    AddFailure(state,
               faction_targeting_row_observer_failure_stub_protection);
    (void)ReleaseStub(state);
    ClearResolved(state);
    return false;
  }

  BuildPatch(reinterpret_cast<std::uintptr_t>(state.stub),
             state.installed_patch_bytes);
  g_active_observer.store(&state, std::memory_order_release);
  const auto write = WriteTarget(state, state.original_patch_bytes.data(),
                                 state.installed_patch_bytes.data());
  if (write == TargetWriteResult::success) {
    state.installed.store(1, std::memory_order_release);
    return true;
  }
  if (write == TargetWriteResult::rollback_unproven) {
    state.installed.store(1, std::memory_order_release);
    return false;
  }
  g_active_observer.store(nullptr, std::memory_order_release);
  (void)ReleaseStub(state);
  ClearResolved(state);
  return false;
}

bool UninstallFactionTargetingRowObserverV1(
    FactionTargetingRowObserverStateV1 &state) noexcept {
  if (state.installed.load(std::memory_order_acquire) == 0 ||
      g_active_observer.load(std::memory_order_acquire) != &state) {
    AddFailure(state, faction_targeting_row_observer_failure_already_installed);
    return false;
  }
  const auto write = WriteTarget(state, state.installed_patch_bytes.data(),
                                 state.original_patch_bytes.data());
  if (write != TargetWriteResult::success) {
    AddFailure(state, faction_targeting_row_observer_failure_rollback);
    return false;
  }
  state.installed.store(0, std::memory_order_release);
  g_active_observer.store(nullptr, std::memory_order_release);
  const bool released = ReleaseStub(state);
  if (released) ClearResolved(state);
  return released;
}

FactionTargetingRowObserverDiagnosticsV1
ReadFactionTargetingRowObserverDiagnosticsV1(
    const FactionTargetingRowObserverStateV1 &state) noexcept {
  FactionTargetingRowObserverDiagnosticsV1 output{};
  output.installed = state.installed.load(std::memory_order_acquire) != 0;
  output.offline_fixture = state.offline_fixture;
  output.failure_flags = state.failure_flags.load(std::memory_order_acquire);
  const auto &source = state.observation;
  auto &target = output.observation;
  target.callback_count = source.callback_count.load(std::memory_order_acquire);
  target.rejected_application_main_count =
      source.rejected_application_main_count.load(std::memory_order_acquire);
  target.rejected_paused_count =
      source.rejected_paused_count.load(std::memory_order_acquire);
  target.rejected_state_change_count =
      source.rejected_state_change_count.load(std::memory_order_acquire);
  target.span_read_failure_count =
      source.span_read_failure_count.load(std::memory_order_acquire);
  target.span_stability_failure_count =
      source.span_stability_failure_count.load(std::memory_order_acquire);
  target.identity_failure_count =
      source.identity_failure_count.load(std::memory_order_acquire);
  target.target_character_failure_count =
      source.target_character_failure_count.load(std::memory_order_acquire);
  target.count_equivalence_failure_count =
      source.count_equivalence_failure_count.load(std::memory_order_acquire);
  target.leader_character_failure_count =
      source.leader_character_failure_count.load(std::memory_order_acquire);
  target.leader_stability_failure_count =
      source.leader_stability_failure_count.load(std::memory_order_acquire);
  target.member_span_failure_count =
      source.member_span_failure_count.load(std::memory_order_acquire);
  target.member_stability_failure_count =
      source.member_stability_failure_count.load(std::memory_order_acquire);
  target.member_identity_failure_count =
      source.member_identity_failure_count.load(std::memory_order_acquire);
  target.member_ownership_failure_count =
      source.member_ownership_failure_count.load(std::memory_order_acquire);
  target.accepted_capture_count =
      source.accepted_capture_count.load(std::memory_order_acquire);

  for (std::size_t attempt = 0; attempt < 8; ++attempt) {
    const auto before =
        source.published_generation.load(std::memory_order_acquire);
    if ((before & 1U) != 0) continue;
    target.last_proof_epoch =
        source.last_proof_epoch.load(std::memory_order_relaxed);
    target.last_snapshot_revision =
        source.last_snapshot_revision.load(std::memory_order_relaxed);
    target.last_date_raw =
        source.last_date_raw.load(std::memory_order_relaxed);
    target.last_player_character_id =
        source.last_player_character_id.load(std::memory_order_relaxed);
    target.last_campaign_root_targeting_faction_count =
        source.last_campaign_root_targeting_faction_count.load(
            std::memory_order_relaxed);
    target.last_faction_count =
        source.last_faction_count.load(std::memory_order_relaxed);
    for (std::size_t index = 0; index < target.last_faction_ids.size();
         ++index) {
      target.last_faction_ids[index] =
          source.last_faction_ids[index].load(std::memory_order_relaxed);
      target.last_target_character_ids[index] =
          source.last_target_character_ids[index].load(
              std::memory_order_relaxed);
      target.last_leader_present[index] =
          source.last_leader_present[index].load(std::memory_order_relaxed);
      target.last_leader_character_ids[index] =
          source.last_leader_character_ids[index].load(
              std::memory_order_relaxed);
      target.last_leader_present_in_character_members[index] =
          source.last_leader_present_in_character_members[index].load(
              std::memory_order_relaxed);
      target.last_character_member_counts[index] =
          source.last_character_member_counts[index].load(
              std::memory_order_relaxed);
      for (std::size_t member_index = 0;
           member_index <
               kFactionTargetingRowObserverMaximumCharacterMembersPerFactionV1;
           ++member_index) {
        const auto flat_index =
            index *
                kFactionTargetingRowObserverMaximumCharacterMembersPerFactionV1 +
            member_index;
        target.last_character_member_ids[flat_index] =
            source.last_character_member_ids[flat_index].load(
                std::memory_order_relaxed);
      }
    }
    target.last_thread_id =
        source.last_thread_id.load(std::memory_order_relaxed);
    target.last_timestamp_qpc =
        source.last_timestamp_qpc.load(std::memory_order_relaxed);
    const auto after =
        source.published_generation.load(std::memory_order_acquire);
    if (before == after && (after & 1U) == 0) {
      target.published_generation = after;
      break;
    }
  }
  return output;
}

} // namespace xar::bridge
