#include "xar_bridge/active_scheme_interaction_definition_resolver_v1_private.hpp"

#include <algorithm>
#include <array>
#include <bit>
#include <limits>
#include <string>

namespace xar::bridge {
namespace {

using CommandEnvironment =
    ActiveSchemeSemanticActionV1PrivateNativeCommandEnvironment;
using CommandOperations =
    ActiveSchemeSemanticActionV1PrivateNativeCommandOperations;
using DefinitionLease =
    ActiveSchemeSemanticActionV1PrivateNativeInteractionLease;
using Frame = ActiveSchemeInteractionDefinitionResolverV1PrivateFrame;
using State = ActiveSchemeInteractionDefinitionResolverV1PrivateState;

constexpr std::size_t kMsvcStringSizeOffset = 0x10;
constexpr std::size_t kMsvcStringCapacityOffset = 0x18;
constexpr std::size_t kMsvcStringInlineCapacity = 0x0F;
constexpr std::size_t kMaximumKeyBytes = 96;
constexpr std::uint64_t kFnvOffset = 1469598103934665603ULL;
constexpr std::uint64_t kFnvPrime = 1099511628211ULL;
constexpr std::string_view kDefinitionRttiName =
    ".?AVCCharacterInteraction@@";

struct DefinitionIdentity {
  std::uintptr_t address = 0;
  std::int32_t ordinal = -1;
  std::int32_t stable_hash = 0;
  std::string key;

  friend bool operator==(const DefinitionIdentity &,
                         const DefinitionIdentity &) = default;
};

struct DatabaseScan {
  std::uintptr_t database = 0;
  std::uintptr_t rows = 0;
  std::int32_t count = 0;
  std::uint64_t generation = 0;
  DefinitionIdentity selected{};

  friend bool operator==(const DatabaseScan &, const DatabaseScan &) =
      default;
};

bool ResolveSpec(std::string_view interaction_key,
                 std::string_view &scheme_type_key,
                 std::int32_t &expected_hash) noexcept {
  if (interaction_key == "sway_interaction") {
    scheme_type_key = "sway";
    expected_hash =
        std::bit_cast<std::int32_t>(kActiveSchemeSwayInteractionStableHash);
    return true;
  }
  if (interaction_key == "start_murder_interaction") {
    scheme_type_key = "murder";
    expected_hash =
        std::bit_cast<std::int32_t>(kActiveSchemeMurderInteractionStableHash);
    return true;
  }
  return false;
}

bool CompleteExceptResolver(const CommandOperations &operations) noexcept {
  return operations.read_memory != nullptr &&
         operations.resolve_character != nullptr &&
         operations.resolve_interaction == nullptr &&
         operations.resolve_submit_route != nullptr &&
         operations.construct_context != nullptr &&
         operations.validate_context != nullptr &&
         operations.construct_command != nullptr &&
         operations.submit != nullptr &&
         operations.release_context != nullptr &&
         operations.release_command != nullptr;
}

bool CheckedAddress(std::uintptr_t base, std::size_t offset,
                    std::uintptr_t &output) noexcept {
  if (base == 0 ||
      offset > (std::numeric_limits<std::uintptr_t>::max)() - base) {
    output = 0;
    return false;
  }
  output = base + offset;
  return true;
}

template <typename T>
bool Read(const State &state, std::uintptr_t base, std::size_t offset,
          T &output) noexcept {
  std::uintptr_t address = 0;
  return CheckedAddress(base, offset, address) &&
         state.upstream_operations.read_memory(
             state.upstream_context, reinterpret_cast<const void *>(address),
             &output, sizeof(output));
}

std::uint64_t HashValue(std::uint64_t hash, std::uint64_t value) noexcept {
  for (unsigned shift = 0; shift != 64; shift += 8) {
    hash ^= (value >> shift) & 0xFFU;
    hash *= kFnvPrime;
  }
  return hash;
}

bool ReadStableKey(const State &state, std::uintptr_t definition,
                   std::string &output) noexcept {
  output.clear();
  std::size_t size = 0;
  std::size_t capacity = 0;
  if (!Read(state, definition,
            kActiveSchemeInteractionDefinitionCanonicalKeyOffset +
                kMsvcStringSizeOffset,
            size) ||
      !Read(state, definition,
            kActiveSchemeInteractionDefinitionCanonicalKeyOffset +
                kMsvcStringCapacityOffset,
            capacity) ||
      size == 0 || size > capacity || size >= kMaximumKeyBytes) {
    return false;
  }

  std::uintptr_t bytes = 0;
  if (capacity <= kMsvcStringInlineCapacity) {
    if (!CheckedAddress(
            definition,
            kActiveSchemeInteractionDefinitionCanonicalKeyOffset, bytes)) {
      return false;
    }
  } else if (!Read(state, definition,
                   kActiveSchemeInteractionDefinitionCanonicalKeyOffset,
                   bytes) ||
             bytes == 0) {
    return false;
  }

  std::array<char, kMaximumKeyBytes> copied{};
  if (!state.upstream_operations.read_memory(
          state.upstream_context, reinterpret_cast<const void *>(bytes),
          copied.data(), size)) {
    return false;
  }
  for (std::size_t index = 0; index < size; ++index) {
    const auto byte = static_cast<unsigned char>(copied[index]);
    if (byte == 0 || byte < 0x20U || byte > 0x7EU) return false;
  }
  output.assign(copied.data(), size);
  return true;
}

bool ReadDefinitionIdentity(const State &state, std::uintptr_t definition,
                            bool read_key,
                            DefinitionIdentity &output) noexcept {
  output = {};
  std::uintptr_t primary_vtable = 0;
  std::uintptr_t secondary_vtable = 0;
  std::int32_t ordinal = -1;
  std::uint32_t stable_hash = 0;
  if (!Read(state, definition, 0, primary_vtable) ||
      primary_vtable !=
          state.module_base +
              kActiveSchemeInteractionDefinitionPrimaryVtableRva ||
      !Read(state, definition,
            kActiveSchemeInteractionDefinitionSecondarySubobjectOffset,
            secondary_vtable) ||
      secondary_vtable !=
          state.module_base +
              kActiveSchemeInteractionDefinitionSecondaryVtableRva ||
      !Read(state, definition,
            kActiveSchemeInteractionDefinitionRuntimeOrdinalOffset,
            ordinal) ||
      !Read(state, definition,
            kActiveSchemeInteractionDefinitionStableHashOffset,
            stable_hash) ||
      ordinal < 0 || stable_hash == 0) {
    return false;
  }
  output.address = definition;
  output.ordinal = ordinal;
  output.stable_hash = std::bit_cast<std::int32_t>(stable_hash);
  return !read_key || ReadStableKey(state, definition, output.key);
}

bool ScanDatabase(const State &state, std::uintptr_t database,
                  std::int32_t requested_hash, std::string_view requested_key,
                  DatabaseScan &output) noexcept {
  output = {};
  output.database = database;
  if (!Read(state, database, kActiveSchemeInteractionDatabaseRowsOffset,
            output.rows) ||
      !Read(state, database, kActiveSchemeInteractionDatabaseCountOffset,
            output.count) ||
      output.rows == 0 || output.count <= 0 ||
      output.count > kActiveSchemeInteractionDefinitionMaximumCount) {
    return false;
  }

  std::array<std::int32_t,
             static_cast<std::size_t>(
                 kActiveSchemeInteractionDefinitionMaximumCount)>
      ordinals{};
  std::size_t ordinal_count = 0;
  std::size_t matching_count = 0;
  auto generation = HashValue(kFnvOffset, database);
  generation = HashValue(generation, output.rows);
  generation =
      HashValue(generation, static_cast<std::uint32_t>(output.count));

  for (std::int32_t index = 0; index < output.count; ++index) {
    std::uintptr_t definition = 0;
    if (!Read(state, output.rows,
              static_cast<std::size_t>(index) * sizeof(std::uintptr_t),
              definition) ||
        definition == 0) {
      return false;
    }
    DefinitionIdentity identity{};
    if (!ReadDefinitionIdentity(state, definition, false, identity)) {
      return false;
    }
    if (std::find(ordinals.begin(), ordinals.begin() + ordinal_count,
                  identity.ordinal) != ordinals.begin() + ordinal_count) {
      return false;
    }
    ordinals[ordinal_count++] = identity.ordinal;
    generation = HashValue(generation, identity.address);
    generation = HashValue(
        generation, static_cast<std::uint32_t>(identity.ordinal));
    generation = HashValue(
        generation, std::bit_cast<std::uint32_t>(identity.stable_hash));

    if (identity.stable_hash != requested_hash) continue;
    if (!ReadStableKey(state, definition, identity.key)) return false;
    if (identity.key != requested_key) continue;
    output.selected = identity;
    ++matching_count;
  }
  if (matching_count != 1) return false;
  if (generation == 0) generation = 1;
  output.generation = generation;
  return true;
}

bool VerifyExactImage(const CommandEnvironment &binding) noexcept {
  std::array<std::uint8_t, 48> observed{};
  for (const auto &signature :
       kActiveSchemeInteractionDefinitionResolverV1PrivateSignatures) {
    observed.fill(0);
    std::uintptr_t address = 0;
    if (!CheckedAddress(binding.module_base, signature.rva, address) ||
        !binding.operations.read_memory(
            binding.operation_context,
            reinterpret_cast<const void *>(address),
            observed.data(), signature.size) ||
        !std::equal(observed.begin(), observed.begin() + signature.size,
                    signature.bytes.begin())) {
      return false;
    }
  }
  for (const auto &slot :
       kActiveSchemeInteractionDefinitionResolverV1PrivateImagePointerSlots) {
    std::uintptr_t observed_function = 0;
    std::uintptr_t slot_address = 0;
    std::uintptr_t target_address = 0;
    if (!CheckedAddress(binding.module_base, slot.slot_rva, slot_address) ||
        !CheckedAddress(binding.module_base, slot.target_rva,
                        target_address) ||
        !binding.operations.read_memory(
            binding.operation_context,
            reinterpret_cast<const void *>(slot_address),
            &observed_function, sizeof(observed_function)) ||
        observed_function != target_address) {
      return false;
    }
  }
  std::array<char, 32> rtti{};
  std::uintptr_t rtti_address = 0;
  if (kDefinitionRttiName.size() + 1 > rtti.size() ||
      !CheckedAddress(binding.module_base,
                      kActiveSchemeInteractionDefinitionRttiRva + 0x10,
                      rtti_address) ||
      !binding.operations.read_memory(
          binding.operation_context,
          reinterpret_cast<const void *>(rtti_address),
          rtti.data(), kDefinitionRttiName.size() + 1)) {
    return false;
  }
  return std::equal(kDefinitionRttiName.begin(), kDefinitionRttiName.end(),
                    rtti.begin()) &&
         rtti[kDefinitionRttiName.size()] == '\0';
}

bool ReadMemoryThunk(void *context, const void *address, void *output,
                     std::size_t size) noexcept {
  auto &state = *static_cast<State *>(context);
  return state.attached && state.upstream_operations.read_memory(
                               state.upstream_context, address, output, size);
}

bool ResolveCharacterThunk(
    void *context, std::uint32_t full_id,
    ActiveSchemeSemanticActionV1PrivateNativeCharacterLease &output) noexcept {
  auto &state = *static_cast<State *>(context);
  return state.attached && state.upstream_operations.resolve_character(
                               state.upstream_context, full_id, output);
}

bool ResolveSubmitRouteThunk(
    void *context,
    ActiveSchemeSemanticActionV1PrivateNativeSubmitRouteLease &output) noexcept {
  auto &state = *static_cast<State *>(context);
  return state.attached && state.upstream_operations.resolve_submit_route(
                               state.upstream_context, output);
}

bool ConstructContextThunk(
    void *context,
    const ActiveSchemeSemanticActionV1PrivateCommand &semantic_command,
    const ActiveSchemeSemanticActionV1PrivateNativeCharacterLease &actor,
    const ActiveSchemeSemanticActionV1PrivateNativeCharacterLease &target,
    const ActiveSchemeSemanticActionV1PrivateNativeInteractionLease
        &interaction,
    ActiveSchemeSemanticActionV1PrivateNativeContextLease &output) noexcept {
  auto &state = *static_cast<State *>(context);
  return state.attached && state.upstream_operations.construct_context(
                               state.upstream_context, semantic_command, actor,
                               target, interaction, output);
}

bool ValidateContextThunk(
    void *context,
    const ActiveSchemeSemanticActionV1PrivateNativeContextLease
        &native_context,
    ActiveSchemeSemanticActionV1PrivateNativeValidationProof
        &output) noexcept {
  auto &state = *static_cast<State *>(context);
  return state.attached && state.upstream_operations.validate_context(
                               state.upstream_context, native_context, output);
}

bool ConstructCommandThunk(
    void *context,
    const ActiveSchemeSemanticActionV1PrivateNativeContextLease
        &native_context,
    ActiveSchemeSemanticActionV1PrivateNativeCommandLease &output) noexcept {
  auto &state = *static_cast<State *>(context);
  return state.attached && state.upstream_operations.construct_command(
                               state.upstream_context, native_context, output);
}

bool SubmitThunk(
    void *context,
    const ActiveSchemeSemanticActionV1PrivateNativeSubmitRouteLease &route,
    const ActiveSchemeSemanticActionV1PrivateNativeCommandLease &command,
    std::uint32_t channel_flags) noexcept {
  auto &state = *static_cast<State *>(context);
  return state.attached && state.upstream_operations.submit(
                               state.upstream_context, route, command,
                               channel_flags);
}

void ReleaseContextThunk(
    void *context,
    const ActiveSchemeSemanticActionV1PrivateNativeContextLease
        &native_context) noexcept {
  auto &state = *static_cast<State *>(context);
  if (state.attached) {
    state.upstream_operations.release_context(state.upstream_context,
                                              native_context);
  }
}

void ReleaseCommandThunk(
    void *context,
    const ActiveSchemeSemanticActionV1PrivateNativeCommandLease
        &native_command) noexcept {
  auto &state = *static_cast<State *>(context);
  if (state.attached) {
    state.upstream_operations.release_command(state.upstream_context,
                                              native_command);
  }
}

bool ResolveInteractionThunk(
    void *context, std::string_view interaction_key,
    DefinitionLease &output) noexcept {
  auto &state = *static_cast<State *>(context);
  output = {};
  std::string_view scheme_type_key;
  std::int32_t expected_hash = 0;
  if (!state.attached ||
      !ResolveSpec(interaction_key, scheme_type_key, expected_hash)) {
    return false;
  }

  Frame before{};
  Frame after{};
  std::uintptr_t getter_address = 0;
  std::uintptr_t hash_address = 0;
  std::uintptr_t lookup_address = 0;
  std::uintptr_t database_slot_address = 0;
  std::uintptr_t fallback_slot_address = 0;
  std::uintptr_t first_database = 0;
  std::uintptr_t second_database = 0;
  std::uintptr_t first_slot_database = 0;
  std::uintptr_t second_slot_database = 0;
  std::uintptr_t first_lookup = 0;
  std::uintptr_t second_lookup = 0;
  std::uintptr_t first_fallback = 0;
  std::uintptr_t second_fallback = 0;
  std::int32_t first_hash = 0;
  std::int32_t second_hash = 0;
  if (!CheckedAddress(
          state.module_base,
          kActiveSchemeInteractionDefinitionDatabaseGetterRva,
          getter_address) ||
      !CheckedAddress(state.module_base,
                      kActiveSchemeInteractionStableKeyHashRva,
                      hash_address) ||
      !CheckedAddress(state.module_base,
                      kActiveSchemeInteractionLoadedLookupReferenceRva,
                      lookup_address) ||
      !CheckedAddress(state.module_base,
                      kActiveSchemeInteractionDatabaseSingletonSlotRva,
                      database_slot_address) ||
      !CheckedAddress(state.module_base,
                      kActiveSchemeInteractionLookupFallbackSlotRva,
                      fallback_slot_address) ||
      !state.capture_frame(state.resolver_context, before) ||
      !before.application_main_thread || !before.paused ||
      before.proof_epoch == 0 ||
      !Read(state, database_slot_address, 0, first_slot_database) ||
      first_slot_database == 0 ||
      !state.invoke_database_getter(state.resolver_context, getter_address,
                                    first_database) ||
      first_database != first_slot_database ||
      !state.invoke_stable_key_hash(
          state.resolver_context, hash_address, first_database,
          interaction_key, first_hash) ||
      first_hash != expected_hash ||
      !state.invoke_loaded_lookup(state.resolver_context, lookup_address,
                                  first_database, first_hash,
                                  first_lookup) ||
      first_lookup == 0 ||
      !Read(state, fallback_slot_address, 0, first_fallback) ||
      first_fallback == 0 || first_lookup == first_fallback) {
    return false;
  }

  DatabaseScan first{};
  DatabaseScan second{};
  if (!ScanDatabase(state, first_database, first_hash, interaction_key,
                    first) ||
      first.selected.address != first_lookup ||
      !Read(state, database_slot_address, 0, second_slot_database) ||
      second_slot_database != first_slot_database ||
      !state.invoke_database_getter(state.resolver_context, getter_address,
                                    second_database) ||
      second_database != second_slot_database ||
      !state.invoke_stable_key_hash(
          state.resolver_context, hash_address, second_database,
          interaction_key, second_hash) ||
      second_hash != first_hash ||
      !state.invoke_loaded_lookup(state.resolver_context, lookup_address,
                                  second_database, second_hash,
                                  second_lookup) ||
      second_lookup != first_lookup ||
      !Read(state, fallback_slot_address, 0, second_fallback) ||
      second_fallback != first_fallback ||
      second_lookup == second_fallback ||
      !ScanDatabase(state, second_database, second_hash, interaction_key,
                    second) ||
      second.selected.address != second_lookup ||
      first != second ||
      !state.capture_frame(state.resolver_context, after) ||
      before != after) {
    return false;
  }

  auto generation = HashValue(first.generation, first.selected.address);
  generation = HashValue(
      generation, static_cast<std::uint32_t>(first.selected.ordinal));
  generation = HashValue(
      generation,
      std::bit_cast<std::uint32_t>(first.selected.stable_hash));
  if (generation == 0) generation = 1;
  output.identity_round_trip = true;
  output.native_address = first.selected.address;
  output.interaction_key.assign(interaction_key);
  output.scheme_type_key.assign(scheme_type_key);
  output.stable_key_hash = first.selected.stable_hash;
  output.definition_generation = generation;
  output.proof_epoch = before.proof_epoch;
  return true;
}

} // namespace

bool BindActiveSchemeInteractionDefinitionResolverV1Private(
    const ActiveSchemeInteractionDefinitionResolverV1PrivateEnvironment
        &resolver,
    ActiveSchemeInteractionDefinitionResolverV1PrivateState &state,
    CommandEnvironment &command_binding) noexcept {
  if (!resolver.binding_enabled || !resolver.exact_build_admitted ||
      resolver.admitted_executable_sha256 !=
          kActiveSchemeInteractionDefinitionResolverV1PrivateExecutableSha256 ||
      resolver.admitted_game_version !=
          kActiveSchemeInteractionDefinitionResolverV1PrivateGameVersion ||
      resolver.evidence_revision !=
          kActiveSchemeInteractionDefinitionResolverV1PrivateEvidenceRevision ||
      resolver.module_base == 0 || resolver.capture_frame == nullptr ||
      resolver.invoke_database_getter == nullptr ||
      resolver.invoke_stable_key_hash == nullptr ||
      resolver.invoke_loaded_lookup == nullptr || state.attached ||
      command_binding.module_base != resolver.module_base ||
      !command_binding.binding_enabled ||
      !command_binding.exact_build_admitted ||
      command_binding.admitted_executable_sha256 !=
          resolver.admitted_executable_sha256 ||
      command_binding.admitted_game_version !=
          resolver.admitted_game_version ||
      command_binding.operation_context == &state ||
      !CompleteExceptResolver(command_binding.operations) ||
      command_binding.proof_gate.stable_interaction_key_lookup_proven ||
      !VerifyExactImage(command_binding)) {
    return false;
  }

  state = {};
  state.module_base = resolver.module_base;
  state.resolver_context = resolver.operation_context;
  state.capture_frame = resolver.capture_frame;
  state.invoke_database_getter = resolver.invoke_database_getter;
  state.invoke_stable_key_hash = resolver.invoke_stable_key_hash;
  state.invoke_loaded_lookup = resolver.invoke_loaded_lookup;
  state.upstream_context = command_binding.operation_context;
  state.upstream_operations = command_binding.operations;
  state.attached = true;

  command_binding.operation_context = &state;
  command_binding.operations.read_memory = &ReadMemoryThunk;
  command_binding.operations.resolve_character = &ResolveCharacterThunk;
  command_binding.operations.resolve_interaction = &ResolveInteractionThunk;
  command_binding.operations.resolve_submit_route = &ResolveSubmitRouteThunk;
  command_binding.operations.construct_context = &ConstructContextThunk;
  command_binding.operations.validate_context = &ValidateContextThunk;
  command_binding.operations.construct_command = &ConstructCommandThunk;
  command_binding.operations.submit = &SubmitThunk;
  command_binding.operations.release_context = &ReleaseContextThunk;
  command_binding.operations.release_command = &ReleaseCommandThunk;
  command_binding.proof_gate.stable_interaction_key_lookup_proven = true;
  return true;
}

} // namespace xar::bridge
