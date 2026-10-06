#include "xar_bridge/ck3_12003_religious_title_readback.hpp"

#include <array>
#include <bit>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <string>
#include <vector>

// Focused fixture SOURCE ONLY: author did not compile or execute it. Every byte
// below is fixture-owned synthetic memory; no CK3 module is loaded or called.
// Link the candidate aggregate/properties/laws with the frozen runtime target
// which supplies ResolveObjectiveTitle, BindTitleHolderImageV1 and its reader.
namespace rt = xar::ck3_12003::religious_title;
namespace props = xar::ck3_12003::title_properties;
namespace laws = xar::ck3_12003::title_laws;
namespace {
template <class T, std::size_t N>
void Put(std::array<std::byte, N> &bytes, std::size_t offset, const T &value) {
  assert(offset + sizeof(value) <= bytes.size());
  std::memcpy(bytes.data() + offset, &value, sizeof(value));
}
template <class T>
T Get(const void *base, std::size_t offset) {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(base) + offset, sizeof(value));
  return value;
}
struct Fixture;
Fixture *active = nullptr;
void *CharacterFaith(void *);
void *FaithTitle(void *);
void *FaithHead(void *);
void *Immediate(void *) { return nullptr; }
void *Top(void *character) { return character; }

struct Fixture {
  static constexpr std::uintptr_t base = 0x10000000;
  static constexpr std::uint32_t actor_id = 0x01000000;
  static constexpr std::uint32_t holder_id = 0x82000002;
  static constexpr std::uint32_t faith_id = 0xAB000003;
  std::uint32_t title_id = 0x01000001;
  std::array<std::byte, 0x80> character_storage{}, title_storage{};
  std::array<std::byte, 0x30> character_slots{}, title_slots{};
  std::array<std::byte, 0x220> actor{}, holder{}, character_fallback{};
  std::array<std::byte, 0x400> faith{}, faith_fallback{}, title{}, title_fallback{}, stale_title{};
  std::array<std::byte, 0x80> title_definition{}, law{}, second_law{};
  std::string key = std::string(laws::kExpectedLawKey);
  std::array<void *, 2> law_slots{};
  void *character_storage_pointer = character_storage.data();
  void *title_storage_pointer = title_storage.data();
  void *character_fallback_pointer = character_fallback.data();
  void *title_fallback_pointer = title_fallback.data();
  void *faith_fallback_pointer = faith_fallback.data();
  rt::Bindings bindings{};
  xar::game::Snapshot frame{};
  bool mismatched_title_getter = false;
  bool use_faith_fallback = false;
  bool flip_property_on_second_graph = false;
  std::uint32_t title_getter_calls = 0;

  explicit Fixture(bool high_bit_title = false) {
    active = this;
    if (high_bit_title) title_id = 0x81000001;
    Put(character_storage, 0x20, static_cast<void *>(character_slots.data()));
    Put(character_storage, 0x2C, std::int32_t{3});
    Put(character_slots, 8, static_cast<void *>(actor.data()));
    Put(character_slots, 2 * 0x10 + 8, static_cast<void *>(holder.data()));
    Put(actor, 0x18, actor_id);
    Put(actor, 0x1C, std::uint32_t{0x43686172});
    Put(holder, 0x18, holder_id);
    Put(holder, 0x1C, std::uint32_t{0x43686172});
    Put(title_storage, 0x20, static_cast<void *>(title_slots.data()));
    Put(title_storage, 0x2C, std::int32_t{3});
    Put(title_slots, 0x10 + 8, static_cast<void *>(title.data()));
    Put(faith, rt::kFaithReferenceIdentityOffset, faith_id);
    Put(faith, rt::kFaithHeadTitleIdOffset, title_id);
    Put(title, 0, base + props::kCLandedTitlePrimaryVtableRva);
    Put(title, 0x10, title_id);
    Put(title, 0x128, holder_id);
    Put(title, 0x48, static_cast<void *>(title_definition.data()));
    Put(title_definition, 0x64, std::int32_t{3});
    Put(title, props::kNativeDestroyIfInvalidHeirOffset, std::uint8_t{1});
    Put(title, props::kNativeNoAutomaticClaimsOffset, std::uint8_t{1});
    Put(title, props::kNativeDefinitiveFormOffset, std::uint8_t{1});
    Put(title, props::kNativeAlwaysFollowsPrimaryHeirOffset, std::uint8_t{0});
    Put(law, 0, base + laws::kCLawPrimaryVtableRva);
    Put(law, 0x10, std::uint32_t{27});
    Put(law, 0x18, key.c_str());
    Put(law, 0x28, static_cast<std::uint64_t>(key.size()));
    Put(law, 0x30, static_cast<std::uint64_t>(key.size()));
    Put(law, 0x38, laws::kCLawDatabaseObjectMagic);
    law_slots[0] = law.data();
    law_slots[1] = law.data();
    Put(title, 0x228, static_cast<void *>(law_slots.data()));
    Put(title, 0x230, std::int32_t{2});
    Put(title, 0x234, std::int32_t{1});
    bindings.enabled = true;
    bindings.properties.enabled = true;
    bindings.properties.image_base = base;
    auto &h = bindings.properties.title_holder;
    h.enabled = true;
    h.provinces.enabled = true;
    h.provinces.landed_title_storage_slot = &title_storage_pointer;
    h.character_storage_slot = &character_storage_pointer;
    h.character_fallback_slot = &character_fallback_pointer;
    h.immediate_liege = &Immediate;
    h.top_liege = &Top;
    bindings.title_fallback_slot = &title_fallback_pointer;
    bindings.faith_fallback_slot = &faith_fallback_pointer;
    bindings.character_faith = &CharacterFaith;
    bindings.faith_head_title = &FaithTitle;
    bindings.faith_head = &FaithHead;
    frame.date_raw = 720123;
    frame.played_character_id = std::bit_cast<std::int32_t>(actor_id);
    frame.paused = true;
    frame.map_ready = true;
    frame.has_played_character = true;
    frame.played_character_alive = true;
  }
};

void *CharacterFaith(void *actor) {
  if (actor != active->actor.data()) return nullptr;
  return active->use_faith_fallback ? active->faith_fallback_pointer : active->faith.data();
}
void *FaithTitle(void *faith) {
  if (faith != active->faith.data()) return nullptr;
  ++active->title_getter_calls;
  if (active->flip_property_on_second_graph && active->title_getter_calls == 2)
    Put(active->title, props::kNativeDefinitiveFormOffset, std::uint8_t{0});
  if (Get<std::uint32_t>(faith, rt::kFaithHeadTitleIdOffset) == UINT32_MAX)
    return active->title_fallback_pointer;
  return active->mismatched_title_getter ? active->stale_title.data() : active->title.data();
}
void *FaithHead(void *faith) {
  if (faith != active->faith.data()) return nullptr;
  if (Get<std::uint32_t>(faith, rt::kFaithHeadTitleIdOffset) == UINT32_MAX ||
      Get<std::uint32_t>(active->title.data(), 0x128) == UINT32_MAX)
    return active->character_fallback_pointer;
  return active->holder.data();
}

void AssertUnknown(const rt::Observation &o) {
  assert(!o.available && !o.graph_available);
  assert(!o.head_title_full_id && !o.native_title_holder_full_id);
  assert(!o.native_title_holder_absent && !o.legal_head_title_absent);
  assert(!o.title_properties.available && !o.title_properties.destroy_if_invalid_heir);
  assert(!o.title_properties.no_automatic_claims && !o.title_properties.definitive_form);
  assert(!o.title_properties.always_follows_primary_heir);
  assert(!o.title_laws.available && !o.title_laws.complete_laws);
  assert(!o.title_laws.native_count && !o.title_laws.temporal_head_of_faith_succession_law_member);
}
} // namespace

int main() {
  assert(!rt::BindImage(Fixture::base, "wrong").enabled);
  assert(!rt::BindImage(0, xar::ck3_12003::kExecutableSha256).enabled);
  const auto current = rt::BindImage(Fixture::base, xar::ck3_12003::kExecutableSha256);
  assert(current.enabled);
  assert(reinterpret_cast<std::uintptr_t>(current.character_faith) ==
         Fixture::base + rt::kCurrentCharacterFaithGetterRva);
  {
    Fixture f;
    rt::Observation o;
    assert(rt::Read(f.bindings, f.frame, 9, o));
    assert(o.available && o.graph_available && o.capture_epoch == 9);
    assert(o.faith_full_id == Fixture::faith_id && o.head_title_full_id == f.title_id);
    assert(o.native_title_holder_full_id == Fixture::holder_id);
    assert(o.native_title_holder_absent == false && o.legal_head_title_absent == false);
    assert(o.title_properties.destroy_if_invalid_heir == true);
    assert(o.title_properties.always_follows_primary_heir == false);
    assert(o.title_laws.temporal_head_of_faith_succession_law_member == true);
    assert(o.title_laws.native_count == 1 && o.title_laws.complete_laws->size() == 1);
    const auto json = rt::Serialize(o);
    assert(json.find("\"native_title_holder_full_id\":2181038082") != std::string::npos);
    assert(json.find("\"mod_owner_faith_variable\":null") != std::string::npos);
  }
  {
    Fixture f(true);
    rt::Observation o;
    assert(rt::Read(f.bindings, f.frame, 10, o));
    assert(o.head_title_full_id == 0x81000001U && o.native_title_holder_full_id == Fixture::holder_id);
    assert(!o.title_holder.available);
    assert(o.title_holder.unavailable_reason == "legacy_signed_title_id_boundary");
    assert(o.title_properties.available && o.title_laws.available);
    assert(rt::Serialize(o).find("\"head_title_full_id\":2164260865") != std::string::npos);
  }
  {
    Fixture f;
    Put(f.faith, rt::kFaithHeadTitleIdOffset, UINT32_MAX);
    rt::Observation o;
    assert(rt::Read(f.bindings, f.frame, 11, o));
    assert(o.graph_available && o.legal_head_title_absent == true);
    assert(!o.head_title_full_id && !o.title_properties.available && !o.title_laws.available);
    // A qualified absent Title observation is not an accepted charter Title row.
    assert(!o.title_laws.temporal_head_of_faith_succession_law_member);
  }
  {
    Fixture f;
    Put(f.title, 0x128, UINT32_MAX);
    rt::Observation o;
    assert(rt::Read(f.bindings, f.frame, 12, o));
    assert(o.native_title_holder_absent == true && !o.native_title_holder_full_id);
  }
  {
    Fixture f;
    Put(f.title, 0x234, std::int32_t{0});
    rt::Observation o;
    assert(rt::Read(f.bindings, f.frame, 13, o));
    assert(o.title_laws.native_count == 0 && o.title_laws.complete_laws->empty());
    assert(o.title_laws.temporal_head_of_faith_succession_law_member == false);
  }
  {
    Fixture f;
    Put(f.title, 0x234, std::int32_t{2}); // Duplicate native CLaw row is incomplete evidence.
    rt::Observation o;
    assert(!rt::Read(f.bindings, f.frame, 14, o));
    AssertUnknown(o);
  }
  {
    Fixture f;
    Put(f.title, props::kNativeNoAutomaticClaimsOffset, std::uint8_t{2});
    rt::Observation o;
    assert(!rt::Read(f.bindings, f.frame, 15, o));
    AssertUnknown(o);
  }
  {
    Fixture f;
    f.mismatched_title_getter = true;
    rt::Observation o;
    assert(!rt::Read(f.bindings, f.frame, 16, o));
    AssertUnknown(o);
  }
  {
    Fixture f;
    Put(f.title, 0x10, std::uint32_t{0x02000001}); // Same index, wrong generation.
    rt::Observation o;
    assert(!rt::Read(f.bindings, f.frame, 17, o));
    AssertUnknown(o);
  }
  {
    Fixture f;
    f.flip_property_on_second_graph = true;
    rt::Observation o;
    assert(!rt::Read(f.bindings, f.frame, 18, o));
    AssertUnknown(o);
  }
  {
    Fixture f;
    Put(f.holder, 0x1C, std::uint32_t{0}); // Full ID alone is not Character kind.
    rt::Observation o;
    assert(!rt::Read(f.bindings, f.frame, 19, o));
    AssertUnknown(o);
  }
  {
    Fixture f;
    f.frame.paused = false;
    rt::Observation o;
    assert(!rt::Read(f.bindings, f.frame, 20, o));
    AssertUnknown(o);
    assert(rt::Serialize(o).find("\"temporal_head_of_faith_succession_law_member\":null") !=
           std::string::npos);
  }
  {
    Fixture f;
    f.title_id = 0;
    Put(f.title_slots, 8, static_cast<void *>(f.title.data()));
    Put(f.title, 0x10, std::uint32_t{0});
    Put(f.faith, rt::kFaithHeadTitleIdOffset, std::uint32_t{0});
    Put(f.faith, rt::kFaithReferenceIdentityOffset, std::uint32_t{0});
    rt::Observation o;
    assert(rt::Read(f.bindings, f.frame, 21, o));
    assert(o.head_title_full_id == 0U && o.faith_full_id == 0U);
    assert(o.legal_head_title_absent == false);
  }
  {
    Fixture f;
    f.key = "another_title_succession_law";
    Put(f.law, 0x18, f.key.c_str());
    Put(f.law, 0x28, static_cast<std::uint64_t>(f.key.size()));
    Put(f.law, 0x30, static_cast<std::uint64_t>(f.key.size()));
    rt::Observation o;
    assert(rt::Read(f.bindings, f.frame, 22, o));
    assert(o.title_laws.native_count == 1 && o.title_laws.complete_laws->size() == 1);
    assert(o.title_laws.temporal_head_of_faith_succession_law_member == false);
  }
  {
    Fixture f;
    Put(f.law, 0x38, std::uint32_t{0});
    rt::Observation o;
    assert(!rt::Read(f.bindings, f.frame, 23, o));
    AssertUnknown(o);
  }
  {
    Fixture f;
    f.use_faith_fallback = true;
    Put(f.faith_fallback, rt::kFaithReferenceIdentityOffset, std::uint32_t{0});
    Put(f.faith_fallback, rt::kFaithHeadTitleIdOffset, UINT32_MAX);
    rt::Observation o;
    assert(!rt::Read(f.bindings, f.frame, 24, o));
    AssertUnknown(o);
    assert(o.unavailable_reason == "native_faith_unavailable");
  }
  {
    rt::Observation o;
    o.unavailable_reason = "line\n\"quoted\"\\backslash";
    const auto json = rt::Serialize(o);
    assert(json.find("line\\u000a\\\"quoted\\\"\\\\backslash") != std::string::npos);
  }
}
