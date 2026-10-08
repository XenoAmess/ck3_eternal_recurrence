#include "xar_bridge/actor_cached_succession12004_v1.hpp"

#include <bit>
#include <limits>
#include <utility>

namespace xar::ck3_12004::actor_cached_succession {
namespace {

bool Address(std::uintptr_t base, std::size_t offset,
             std::uintptr_t &output) noexcept {
  if (base == 0 || offset > std::numeric_limits<std::uintptr_t>::max() - base)
    return false;
  output = base + offset;
  return true;
}

template <typename T>
bool Load(const Bindings &bindings, std::uintptr_t base, std::size_t offset,
          T &output) noexcept {
  std::uintptr_t address = 0;
  return Address(base, offset, address) &&
      bindings.read_memory(bindings.user_context, address, &output, sizeof(T));
}

bool FullId(const Bindings &bindings, std::uintptr_t character,
            std::uint32_t expected_id) noexcept {
  std::uint32_t actual_id = 0xFFFFFFFFU;
  return character != 0 &&
      Load(bindings, character, kCharacterFullIdOffset, actual_id) &&
      actual_id == expected_id;
}

struct Header {
  std::uintptr_t land_state = 0;
  std::uintptr_t data = 0;
  std::int32_t count = -1;
};

bool ReadHeader(const Bindings &bindings, std::uintptr_t actor,
                Header &header) noexcept {
  header = {};
  if (!Load(bindings, actor, kActorLandStateOffset, header.land_state))
    return false;
  if (header.land_state == 0) return true;
  std::uintptr_t collection = 0;
  return Address(header.land_state, kLandStateCachedSuccessorsOffset,
                 collection) &&
      Load(bindings, collection, kCachedSuccessorsDataOffset, header.data) &&
      Load(bindings, collection, kCachedSuccessorsCountOffset, header.count);
}

bool SameHeader(const Header &first, const Header &second) noexcept {
  return first.land_state == second.land_state &&
      first.data == second.data && first.count == second.count;
}

bool CopyIds(const Bindings &bindings, const Header &header,
             std::vector<std::uint32_t> &ids) {
  static_assert(sizeof(std::uint32_t) == kCachedSuccessorStride);
  if (header.count == 0) {
    ids.clear();
    return true;
  }
  const auto count = static_cast<std::size_t>(header.count);
  if (count > ids.max_size() ||
      count > std::numeric_limits<std::size_t>::max() / kCachedSuccessorStride)
    return false;
  const auto bytes = count * kCachedSuccessorStride;
  if (header.data == 0 ||
      bytes > std::numeric_limits<std::uintptr_t>::max() - header.data)
    return false;
  ids.resize(count);
  return bindings.read_memory(bindings.user_context, header.data,
                              ids.data(), bytes);
}

void AppendString(std::string &output, std::string_view value) {
  constexpr char hex[] = "0123456789abcdef";
  output += '"';
  for (const unsigned char character : value) {
    switch (character) {
    case '"': output += "\\\""; break;
    case '\\': output += "\\\\"; break;
    case '\b': output += "\\b"; break;
    case '\f': output += "\\f"; break;
    case '\n': output += "\\n"; break;
    case '\r': output += "\\r"; break;
    case '\t': output += "\\t"; break;
    default:
      if (character < 0x20) {
        output += "\\u00";
        output += hex[character >> 4];
        output += hex[character & 15];
      } else output += static_cast<char>(character);
    }
  }
  output += '"';
}

} // namespace

Bindings BindImage(std::uintptr_t image_base,
                   std::string_view actual_executable_sha256,
                   ReadMemory read_memory,
                   ResolveCharacter resolve_character,
                   void *user_context) noexcept {
  Bindings output{};
  if (image_base == 0 || actual_executable_sha256 != kExecutableSha256 ||
      read_memory == nullptr || resolve_character == nullptr) return output;
  output.enabled = true;
  output.image_base = image_base;
  output.actual_executable_sha256 = kExecutableSha256;
  output.read_memory = read_memory;
  output.resolve_character = resolve_character;
  output.user_context = user_context;
  return output;
}

bool Read(const Bindings &bindings, std::uint64_t capture_epoch,
          std::uint32_t expected_actor_id, std::uint32_t date_raw,
          Snapshot &output) noexcept {
  output = {};
  output.capture_epoch = capture_epoch;
  output.date_raw = std::bit_cast<std::int32_t>(date_raw);
  output.actor_character_id_raw = expected_actor_id;
  const auto fail = [&output](std::string_view reason) noexcept {
    output.available = false;
    output.roster_complete = false;
    output.unavailable_reason = reason;
    output.actor_pointer = 0;
    output.land_state_pointer = 0;
    output.original_data_pointer = 0;
    output.native_count_raw = -1;
    output.ordered_candidate_character_ids_raw.clear();
    return false;
  };
  try {
    if (!bindings.enabled || bindings.image_base == 0 ||
        bindings.actual_executable_sha256 != kExecutableSha256 ||
        bindings.read_memory == nullptr || bindings.resolve_character == nullptr)
      return fail("cached_successor_bindings_unavailable");
    if (capture_epoch == 0)
      return fail("cached_successor_capture_epoch_unavailable");
    if (expected_actor_id == 0xFFFFFFFFU)
      return fail("cached_successor_owner_unavailable");
    const auto actor = bindings.resolve_character(bindings.user_context,
                                                  expected_actor_id);
    if (!FullId(bindings, actor, expected_actor_id))
      return fail("cached_successor_owner_unavailable");
    Header first{};
    if (!ReadHeader(bindings, actor, first))
      return fail("cached_successor_header_unavailable");
    if (first.land_state == 0)
      return fail("cached_successor_land_state_unavailable");
    if (first.count < 0 || (first.count > 0 && first.data == 0))
      return fail("cached_successor_count_or_data_invalid");

    std::vector<std::uint32_t> ids;
    if (!CopyIds(bindings, first, ids))
      return fail("cached_successor_rows_unavailable");
    std::vector<std::uintptr_t> characters;
    characters.reserve(ids.size());
    for (const auto id : ids) {
      if (id == 0xFFFFFFFFU)
        return fail("cached_successor_candidate_unavailable");
      const auto character = bindings.resolve_character(bindings.user_context, id);
      if (!FullId(bindings, character, id))
        return fail("cached_successor_candidate_unavailable");
      characters.push_back(character);
    }

    if (bindings.resolve_character(bindings.user_context, expected_actor_id) !=
            actor || !FullId(bindings, actor, expected_actor_id))
      return fail("cached_successor_owner_changed");
    Header second{};
    if (!ReadHeader(bindings, actor, second) || !SameHeader(first, second))
      return fail("cached_successor_header_changed");
    std::vector<std::uint32_t> second_ids;
    if (!CopyIds(bindings, second, second_ids) || second_ids != ids)
      return fail("cached_successor_rows_changed");
    for (std::size_t index = 0; index < ids.size(); ++index) {
      if (bindings.resolve_character(bindings.user_context, ids[index]) !=
              characters[index] ||
          !FullId(bindings, characters[index], ids[index]))
        return fail("cached_successor_candidate_changed");
    }
    // Bracket the second row/identity pass with one final header/owner check.
    Header final{};
    if (!ReadHeader(bindings, actor, final) || !SameHeader(first, final) ||
        bindings.resolve_character(bindings.user_context, expected_actor_id) !=
            actor || !FullId(bindings, actor, expected_actor_id))
      return fail("cached_successor_owner_or_header_changed");

    output.actor_pointer = actor;
    output.land_state_pointer = first.land_state;
    output.original_data_pointer = first.data;
    output.native_count_raw = first.count;
    output.ordered_candidate_character_ids_raw = std::move(ids);
    output.available = true;
    output.roster_complete = true;
    output.unavailable_reason = {};
    return true;
  } catch (...) {
    return fail("cached_successor_read_failed");
  }
}

std::string Serialize(const Snapshot &snapshot) {
  const bool complete = snapshot.available && snapshot.roster_complete &&
      snapshot.native_count_raw >= 0 &&
      static_cast<std::size_t>(snapshot.native_count_raw) ==
          snapshot.ordered_candidate_character_ids_raw.size();
  std::string output = "{\"schema\":";
  AppendString(output, kSchema);
  output += ",\"read_only\":true,\"game_version\":";
  AppendString(output, kGameVersion);
  output += ",\"executable_sha256\":";
  AppendString(output, kExecutableSha256);
  output += ",\"available\":";
  output += complete ? "true" : "false";
  output += ",\"unavailable_reason\":";
  if (complete) output += "null";
  else AppendString(output, snapshot.available
      ? "cached_successor_snapshot_incomplete" : snapshot.unavailable_reason);
  output += ",\"capture_epoch\":" + std::to_string(snapshot.capture_epoch);
  output += ",\"date_raw\":" + std::to_string(snapshot.date_raw);
  output += ",\"played_character_id\":" + std::to_string(
      std::bit_cast<std::int32_t>(snapshot.actor_character_id_raw));
  output += ",\"played_character_full_id\":" +
      std::to_string(snapshot.actor_character_id_raw);
  output += ",\"native_count\":";
  output += complete ? std::to_string(snapshot.native_count_raw) : "null";
  output += ",\"complete_cached_successor_ids\":";
  if (complete) {
    output += '[';
    bool first = true;
    for (const auto id : snapshot.ordered_candidate_character_ids_raw) {
      if (!first) output += ',';
      output += std::to_string(id);
      first = false;
    }
    output += ']';
  } else output += "null";
  output += ",\"native_data_pointer\":";
  output += complete ? std::to_string(
      static_cast<std::uint64_t>(snapshot.original_data_pointer)) : "null";
  output += ",\"land_state_pointer\":";
  output += complete ? std::to_string(
      static_cast<std::uint64_t>(snapshot.land_state_pointer)) : "null";
  output += ",\"roster_complete\":";
  output += complete ? "true}" : "false}";
  return output;
}

} // namespace xar::ck3_12004::actor_cached_succession
