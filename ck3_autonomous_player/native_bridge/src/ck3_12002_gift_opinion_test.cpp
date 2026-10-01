#include "xar_bridge/ck3_12002_gift_opinion.hpp"

#include <array>
#include <cstring>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string_view>

namespace {
using namespace xar::ck3_12002;
template <typename T> void Put(void *p, std::size_t n, const T &v) {
  std::memcpy(static_cast<std::byte *>(p) + n, &v, sizeof(v));
}
template <typename T> T Get(const void *p, std::size_t n) {
  T v{}; std::memcpy(&v, static_cast<const std::byte *>(p) + n, sizeof(v)); return v;
}
int checks = 0;
void Check(bool value, const char *message) {
  ++checks; if (!value) throw std::runtime_error(message);
}
constexpr std::uint32_t actor_id = 0x03000001U;
constexpr std::uint32_t recipient_id = 0x04000002U;
std::array<std::byte, 0x200> actor{}, recipient{};
std::array<std::byte, 0x40> storage{}, extension{}, group{};
std::array<std::byte, 0x30> slots{};
std::array<std::byte, 0x98> modifier{}, named{}, gift_value{};
std::array<std::byte, 0x30> active{};
std::array<void *, 1> active_rows{};
std::array<std::byte, 0x168> prepared_scope{};
void *store_pointer = storage.data(), *database_pointer = storage.data();
std::int32_t opinion = 0, modifier_value = 0;
std::int64_t named_raw = 3550000;
bool change_opinion = false, change_raw = false;
std::uint32_t wanted_root = recipient_id;
std::string_view wanted_key = "send_gift_opinion";
int opinion_reads = 0, evaluations = 0, tail_destroys = 0;
std::uint8_t evaluation_flag = 1;
const char interned_key[] = "interned-send-gift-value";

void Definition(void *p, std::string_view key, std::uint32_t hash,
                std::uintptr_t vtable) {
  Put(p, 0, vtable); Put(p, 0x88, vtable + 0x10);
  Put(p, 0x14, hash); Put(p, 0x38, std::uint32_t{0x4744624F});
  Put(p, 0x28, static_cast<std::uint64_t>(key.size()));
  Put(p, 0x30, static_cast<std::uint64_t>(key.size() < 16 ? 15 : key.size()));
  if (key.size() < 16) std::memcpy(static_cast<std::byte *>(p) + 0x18, key.data(), key.size());
  else Put(p, 0x18, key.data());
}
std::int32_t ReadOpinion(void *owner, void *toward) {
  Check(owner == recipient.data() && toward == actor.data(), "opinion direction");
  return opinion + (change_opinion ? opinion_reads++ : 0);
}
void *LookupModifier(void *db, std::uint32_t hash) {
  Check(db == database_pointer && hash == 0xCA82155BU, "modifier lookup identity");
  return modifier.data();
}
void *FindGroup(void *p, std::uint32_t target) {
  Check(p == extension.data() && target == actor_id, "new extension and full target");
  return group.data();
}
std::int32_t Sum(void *p, void *m) {
  Check(p == group.data() && m == modifier.data(), "native modifier sum");
  return modifier_value;
}
void *NamedDatabase() { return database_pointer; }
const void *LookupNamed(void *db, std::uint32_t hash) {
  Check(db == database_pointer, "named database");
  if (hash == 0xF8A1F946U) return named.data();
  if (hash == 0x58DD38F9U) return gift_value.data();
  return nullptr;
}
void *Clone(void *dest, const void *src) {
  std::memcpy(dest, src, 0x168); return dest;
}
void *Support118(void *p) { std::memset(p, 0, 0x118); return p; }
void *Support2a8(void *p) { std::memset(p, 0, 0x2A8); return p; }
const void *Intern(void *db, const void *view) {
  Check(db == database_pointer, "intern database");
  const auto data = Get<const char *>(view, 0);
  const auto size = Get<std::uint32_t>(view, 8);
  Check(std::string_view(data, size) == wanted_key &&
        Get<std::uint8_t>(view, 0xC) == 0, "new source intern view");
  return interned_key;
}
std::int64_t *Evaluate(const void *definition, std::int64_t *out,
                       void *context, void *outer, const void *source) {
  const auto scope = Get<void *>(context, 0);
  Check(scope == Get<void *>(context, 0x10), "internal current/root scope");
  Check(Get<std::uint16_t>(scope, 0) == 4 &&
        Get<std::uint64_t>(scope, 8) == wanted_root, "stock character root");
  Check(Get<std::uint32_t>(scope, 0x80) == actor_id &&
        Get<std::uint32_t>(scope, 0x84) == recipient_id, "preserve role aliases");
  Check(outer == nullptr && Get<void *>(context, 0x18) != nullptr &&
        Get<std::uint8_t>(context, 0x20) == 1, "five argument fixed evaluation");
  Check(Get<const void *>(source, 0) == interned_key &&
        Get<std::uint64_t>(source, 8) == 0 &&
        Get<std::uint32_t>(source, 0x10) == 0 &&
        Get<std::uint8_t>(source, 0x14) == 1 &&
        Get<std::int32_t>(source, 0x18) == -1 &&
        Get<std::uint32_t>(source, 0x1C) == 0, "new interned source descriptor");
  Check(definition == (wanted_key == "gift_value" ? gift_value.data() : named.data()),
        "named definition selected");
  *out = named_raw + (change_raw ? evaluations : 0);
  ++evaluations; return out;
}
void DestroyTail(void *) { ++tail_destroys; }
void DestroyRows(void *) {}

CoreBindings Core() {
  CoreBindings b; b.enabled = true; b.character_storage_slot = &store_pointer; return b;
}
GiftOpinionBindings12002 OpinionBindings() {
  GiftOpinionBindings12002 b;
  b.enabled = true; b.core = Core(); b.modifier_database_slot = &database_pointer;
  b.read_opinion = ReadOpinion; b.lookup_modifier = LookupModifier;
  b.find_group = FindGroup; b.sum_modifier = Sum;
  b.modifier_primary_vtable = 0x1000; b.modifier_secondary_vtable = 0x1010;
  b.active_opinion_vtable = 0x3000; b.temporary_opinion_vtable = 0x3010;
  return b;
}
GiftNamedOpinionBindings12002 NamedBindings() {
  GiftNamedOpinionBindings12002 b;
  b.enabled = true; b.core = Core(); b.named_database = NamedDatabase;
  b.lookup_named = LookupNamed; b.clone_scope = Clone;
  b.construct_support_118 = Support118; b.construct_support_2a8 = Support2a8;
  b.intern_database = NamedDatabase; b.intern_string = Intern;
  b.evaluate_fixed = Evaluate; b.destroy_scope_tail = DestroyTail;
  b.destroy_scope_rows = DestroyRows; b.destroy_support_rows = DestroyRows;
  b.evaluation_flag = &evaluation_flag;
  b.named_primary_vtable = 0x2000; b.named_secondary_vtable = 0x2010;
  return b;
}

void Run() {
  Put(storage.data(), 0x20, static_cast<void *>(slots.data()));
  Put(storage.data(), 0x2C, std::int32_t{3});
  Put(slots.data(), 0x18, static_cast<void *>(actor.data()));
  Put(slots.data(), 0x28, static_cast<void *>(recipient.data()));
  Put(actor.data(), 0x18, actor_id); Put(recipient.data(), 0x18, recipient_id);
  Definition(modifier.data(), "gift_opinion", 0xCA82155BU, 0x1000);
  Definition(named.data(), "send_gift_opinion", 0xF8A1F946U, 0x2000);
  Definition(gift_value.data(), "gift_value", 0x58DD38F9U, 0x2000);
  Put(active.data(), 0, std::uintptr_t{0x3000});
  Put(active.data(), 8, static_cast<void *>(modifier.data()));
  active_rows[0] = active.data();
  Put(group.data(), 8, static_cast<void *>(active_rows.data()));
  Put(group.data(), 0x14, std::int32_t{1});
  auto b = OpinionBindings(); GiftOpinionResult result;
  Check(ReadGiftOpinion12002(b, recipient_id, actor_id, result) &&
        result.query_complete && result.recipient_opinion_of_player == 0 &&
        !result.gift_opinion_present && !result.gift_opinion_modifier_value,
        "legal zero opinion and absent modifier");
  Put(recipient.data(), 0x1B0, static_cast<void *>(extension.data()));
  opinion = -8;
  Check(ReadGiftOpinion12002(b, recipient_id, actor_id, result) &&
        result.gift_opinion_present && result.gift_opinion_modifier_value == 0 &&
        result.recipient_opinion_of_player == -8, "present zero is not absent");
  modifier_value = 12;
  Check(ReadGiftOpinion12002(b, recipient_id, actor_id, result) &&
        result.gift_opinion_modifier_value == 12, "native current decay value");
  Put(group.data(), 0x14, std::int32_t{0});
  Check(ReadGiftOpinion12002(b, recipient_id, actor_id, result) &&
        !result.gift_opinion_present && !result.gift_opinion_modifier_value,
        "empty active group remains available");
  Put(group.data(), 0x14, std::int32_t{-1});
  Check(!ReadGiftOpinion12002(b, recipient_id, actor_id, result) &&
        !result.query_complete, "bad group is unavailable");
  Put(group.data(), 0x14, std::int32_t{1});
  Put(active.data(), 0, std::uintptr_t{0x4300DF8});
  Check(!ReadGiftOpinion12002(b, recipient_id, actor_id, result),
        "old version active opinion rejected");
  Put(active.data(), 0, std::uintptr_t{0x3000});
  Put(modifier.data(), 0x38, std::uint32_t{0x6C6C754E});
  Check(!ReadGiftOpinion12002(b, recipient_id, actor_id, result),
        "new null definition tag rejected");
  Put(modifier.data(), 0x38, std::uint32_t{0x4744624F});
  Put(recipient.data(), 0x18, std::uint32_t{0x05000002});
  Check(!ReadGiftOpinion12002(b, recipient_id, actor_id, result),
        "same index different generation rejected");
  Put(recipient.data(), 0x18, recipient_id);
  change_opinion = true;
  Check(!ReadGiftOpinion12002(b, recipient_id, actor_id, result) &&
        !result.query_complete, "unstable opinion is unavailable");
  change_opinion = false;
  Put(prepared_scope.data(), 0, std::uint16_t{4});
  Put(prepared_scope.data(), 8, static_cast<std::uint64_t>(actor_id));
  Put(prepared_scope.data(), 0x80, actor_id); Put(prepared_scope.data(), 0x84, recipient_id);
  auto n = NamedBindings(); std::int32_t delta = 0;
  Check(ReadGiftOpinionDelta12002(n, prepared_scope.data(), recipient_id, actor_id,
                                 delta) && delta == 36, "positive half rounds away");
  Check(Get<std::uint64_t>(prepared_scope.data(), 8) == actor_id &&
        tail_destroys == 1, "borrowed scope unchanged and clone destroyed");
  named_raw = -3550000;
  Check(ReadGiftOpinionDelta12002(n, prepared_scope.data(), recipient_id, actor_id,
                                 delta) && delta == -36, "negative half rounds away");
  named_raw = 0;
  Check(ReadGiftOpinionDelta12002(n, prepared_scope.data(), recipient_id, actor_id,
                                 delta) && delta == 0, "native legal zero delta");
  change_raw = true;
  Check(!ReadGiftOpinionDelta12002(n, prepared_scope.data(), recipient_id, actor_id,
                                  delta) && delta == 0 && tail_destroys == 4,
        "unstable evaluator still cleans clone");
  change_raw = false;
  wanted_key = "gift_value"; wanted_root = actor_id; named_raw = 1537501;
  std::int64_t cost = 0;
  Check(ReadNamedInteractionFixed12002(n, prepared_scope.data(), actor_id, actor_id,
          recipient_id, "gift_value", 0x58DD38F9U, cost) && cost == 1537501,
        "gift payment keeps unrounded native gold and actor root");
  Put(gift_value.data(), 0x38, std::uint32_t{0x6C6C754E});
  const auto before = evaluations;
  Check(!ReadNamedInteractionFixed12002(n, prepared_scope.data(), actor_id, actor_id,
          recipient_id, "gift_value", 0x58DD38F9U, cost) && cost == 0 &&
          evaluations == before, "null named definition does not evaluate");
  Check(ConvertGiftOpinionFixed12002(49999, delta) && delta == 0 &&
        ConvertGiftOpinionFixed12002(50000, delta) && delta == 1 &&
        ConvertGiftOpinionFixed12002(-49999, delta) && delta == 0 &&
        ConvertGiftOpinionFixed12002(-50000, delta) && delta == -1,
        "exact signed ties conversion");
  Check(!ConvertGiftOpinionFixed12002((std::numeric_limits<std::int64_t>::max)(),
                                    delta) && delta == 0, "integer range failure");
  Check(!BindGiftOpinionImage12002(0x140000000, "old-sha").enabled &&
        !BindGiftNamedOpinionImage12002(0, kExecutableSha256).enabled,
        "exact image binding");
  const auto actual = BindGiftOpinionImage12002(0x140000000, kExecutableSha256);
  Check(actual.enabled && reinterpret_cast<std::uintptr_t>(actual.read_opinion) ==
        0x140000000 + kGiftReadCharacterOpinionRva12002, "actual receiver RVA");
}
} // namespace
int main() {
  try { Run(); std::cout << "PASS gift opinion 1.20.0.2: " << checks
                         << " assertions; no CK3 process access\n"; return 0; }
  catch (const std::exception &e) { std::cerr << "FAIL " << e.what() << '\n'; return 1; }
}
