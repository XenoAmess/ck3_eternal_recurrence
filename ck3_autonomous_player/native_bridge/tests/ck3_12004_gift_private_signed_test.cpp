#include "xar_bridge/ck3_12004_gift_opinion.hpp"
#include "xar_bridge/ck3_12004_faction_gift.hpp"

#include <array>
#include <cstring>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string_view>

namespace {
using namespace xar::ck3_12004;
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
std::uint32_t actor_id = 0x03000001U;
std::uint32_t recipient_id = 0x04000002U;
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

extern void *state_pointer,*jomini_pointer;
void *GetLocal(void *);
CoreBindings Core() {
  CoreBindings b; b.enabled = true; b.character_storage_slot = &store_pointer; b.game_state_slot=&state_pointer; b.jomini_state_slot=&jomini_pointer; b.get_local_player=GetLocal; return b;
}
GiftOpinionBindings12004 OpinionBindings() {
  GiftOpinionBindings12004 b;
  b.enabled = true; b.core = Core(); b.modifier_database_slot = &database_pointer;
  b.read_opinion = ReadOpinion; b.lookup_modifier = LookupModifier;
  b.find_group = FindGroup; b.sum_modifier = Sum;
  b.modifier_primary_vtable = 0x1000; b.modifier_secondary_vtable = 0x1010;
  b.active_opinion_vtable = 0x3000; b.temporary_opinion_vtable = 0x3010;
  return b;
}
GiftNamedOpinionBindings12004 NamedBindings() {
  GiftNamedOpinionBindings12004 b;
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
  Check(ReadGiftOpinion12004(b, recipient_id, actor_id, result) &&
        result.query_complete && result.recipient_opinion_of_player == 0 &&
        !result.gift_opinion_present && !result.gift_opinion_modifier_value,
        "legal zero opinion and absent modifier");
  Put(recipient.data(), 0x1B0, static_cast<void *>(extension.data()));
  opinion = -8;
  Check(ReadGiftOpinion12004(b, recipient_id, actor_id, result) &&
        result.gift_opinion_present && result.gift_opinion_modifier_value == 0 &&
        result.recipient_opinion_of_player == -8, "present zero is not absent");
  modifier_value = 12;
  Check(ReadGiftOpinion12004(b, recipient_id, actor_id, result) &&
        result.gift_opinion_modifier_value == 12, "native current decay value");
  Put(group.data(), 0x14, std::int32_t{0});
  Check(ReadGiftOpinion12004(b, recipient_id, actor_id, result) &&
        !result.gift_opinion_present && !result.gift_opinion_modifier_value,
        "empty active group remains available");
  Put(group.data(), 0x14, std::int32_t{-1});
  Check(!ReadGiftOpinion12004(b, recipient_id, actor_id, result) &&
        !result.query_complete, "bad group is unavailable");
  Put(group.data(), 0x14, std::int32_t{1});
  Put(active.data(), 0, std::uintptr_t{0x4300DF8});
  Check(!ReadGiftOpinion12004(b, recipient_id, actor_id, result),
        "old version active opinion rejected");
  Put(active.data(), 0, std::uintptr_t{0x3000});
  Put(modifier.data(), 0x38, std::uint32_t{0x6C6C754E});
  Check(!ReadGiftOpinion12004(b, recipient_id, actor_id, result),
        "new null definition tag rejected");
  Put(modifier.data(), 0x38, std::uint32_t{0x4744624F});
  Put(recipient.data(), 0x18, std::uint32_t{0x05000002});
  Check(!ReadGiftOpinion12004(b, recipient_id, actor_id, result),
        "same index different generation rejected");
  Put(recipient.data(), 0x18, recipient_id);
  change_opinion = true;
  Check(!ReadGiftOpinion12004(b, recipient_id, actor_id, result) &&
        !result.query_complete, "unstable opinion is unavailable");
  change_opinion = false;
  Put(prepared_scope.data(), 0, std::uint16_t{4});
  Put(prepared_scope.data(), 8, static_cast<std::uint64_t>(actor_id));
  Put(prepared_scope.data(), 0x80, actor_id); Put(prepared_scope.data(), 0x84, recipient_id);
  auto n = NamedBindings(); std::int32_t delta = 0;
  Check(ReadGiftOpinionDelta12004(n, prepared_scope.data(), recipient_id, actor_id,
                                 delta) && delta == 36, "positive half rounds away");
  Check(Get<std::uint64_t>(prepared_scope.data(), 8) == actor_id &&
        tail_destroys == 1, "borrowed scope unchanged and clone destroyed");
  named_raw = -3550000;
  Check(ReadGiftOpinionDelta12004(n, prepared_scope.data(), recipient_id, actor_id,
                                 delta) && delta == -36, "negative half rounds away");
  named_raw = 0;
  Check(ReadGiftOpinionDelta12004(n, prepared_scope.data(), recipient_id, actor_id,
                                 delta) && delta == 0, "native legal zero delta");
  change_raw = true;
  Check(!ReadGiftOpinionDelta12004(n, prepared_scope.data(), recipient_id, actor_id,
                                  delta) && delta == 0 && tail_destroys == 4,
        "unstable evaluator still cleans clone");
  change_raw = false;
  wanted_key = "gift_value"; wanted_root = actor_id; named_raw = 1537501;
  std::int64_t cost = 0;
  Check(ReadNamedInteractionFixed12004(n, prepared_scope.data(), actor_id, actor_id,
          recipient_id, "gift_value", 0x58DD38F9U, cost) && cost == 1537501,
        "gift payment keeps unrounded native gold and actor root");
  Put(gift_value.data(), 0x38, std::uint32_t{0x6C6C754E});
  const auto before = evaluations;
  Check(!ReadNamedInteractionFixed12004(n, prepared_scope.data(), actor_id, actor_id,
          recipient_id, "gift_value", 0x58DD38F9U, cost) && cost == 0 &&
          evaluations == before, "null named definition does not evaluate");
  Check(ConvertGiftOpinionFixed12004(49999, delta) && delta == 0 &&
        ConvertGiftOpinionFixed12004(50000, delta) && delta == 1 &&
        ConvertGiftOpinionFixed12004(-49999, delta) && delta == 0 &&
        ConvertGiftOpinionFixed12004(-50000, delta) && delta == -1,
        "exact signed ties conversion");
  Check(!ConvertGiftOpinionFixed12004((std::numeric_limits<std::int64_t>::max)(),
                                    delta) && delta == 0, "integer range failure");
  Check(!BindGiftOpinionImage12004(0x140000000, "old-sha").enabled &&
        !BindGiftNamedOpinionImage12004(0, kExecutableSha256).enabled,
        "exact image binding");
  const auto actual = BindGiftOpinionImage12004(0x140000000, kExecutableSha256);
  Check(actual.enabled && reinterpret_cast<std::uintptr_t>(actual.read_opinion) ==
        0x140000000 + kGiftReadCharacterOpinionRva12004, "actual receiver RVA");
}


std::array<std::byte,0xA8> game_state{};
std::array<std::byte,0x28> jomini{};
std::array<std::byte,0x1F8> players{};
std::array<std::byte,0x78> local_player{};
std::array<std::byte,0x22400> game_data{};
std::array<std::byte,0xE0> player_entry{};
std::array<void *,1> player_entries{player_entry.data()};
std::array<std::byte,0x2720> gift_definition{};
void *state_pointer=game_state.data(),*jomini_pointer=jomini.data();
int preview_constructs=0,preview_destroys=0;
bool preview_legal=true,preview_extra_cost=false;
void *GetLocal(void *) { return local_player.data(); }
void PrepareFrame() {
  Put(game_state.data(),8,std::int32_t{53144328});
  Put(game_state.data(),0x70,std::int32_t{0});
  Put(game_state.data(),0xA0,static_cast<void *>(game_data.data()));
  Put(jomini.data(),0x18,static_cast<void *>(players.data()));
  Put(jomini.data(),0x20,std::uint8_t{1});
  Put(players.data(),0x1F0,std::int32_t{7});
  Put(local_player.data(),0x70,std::int32_t{7});
  Put(game_data.data(),kPlayerCharacterManagerOffset+0x58,static_cast<void *>(player_entries.data()));
  Put(game_data.data(),kPlayerCharacterManagerOffset+0x64,std::int32_t{1});
  Put(player_entry.data(),0xD8,std::int32_t{7});
  Put(player_entry.data(),0xB0,actor_id);
  Put(gift_definition.data(),0x14,kFactionGiftDefinitionStableHashV1);
  const std::string_view key="gift_interaction";
  Put(gift_definition.data(),0x18,key.data());
  Put(gift_definition.data(),0x28,static_cast<std::uint64_t>(key.size()));
  Put(gift_definition.data(),0x30,static_cast<std::uint64_t>(key.size()));
  Put(gift_definition.data(),0x2718,std::uint8_t{1});
}
void *GiftDatabase() { return gift_definition.data(); }
std::int32_t GiftHash(void *db,const char *key,std::uint32_t size) {
  Check(db==gift_definition.data()&&std::string_view(key,size)=="gift_interaction","loaded gift hash");
  return static_cast<std::int32_t>(kFactionGiftDefinitionStableHashV1);
}
void *GiftLookup(void *db,std::int32_t hash) {
  Check(db==gift_definition.data()&&static_cast<std::uint32_t>(hash)==kFactionGiftDefinitionStableHashV1,"loaded gift lookup");
  return gift_definition.data();
}
void *GiftConstruct(void *context_storage,void *definition,std::int32_t actor_bits,
                    std::int32_t recipient_bits,void *extra,bool redirect) {
  Check(static_cast<std::uint32_t>(actor_bits)==actor_id&&
        static_cast<std::uint32_t>(recipient_bits)==recipient_id&&extra==nullptr&&redirect,
        "two-role int32 ABI preserves raw bits");
  ++preview_constructs;
  Put(context_storage,0,definition);
  Put(context_storage,0x2D8,actor_bits); Put(context_storage,0x2DC,recipient_bits);
  Put(context_storage,0x2EC,actor_bits);
  auto *scope=static_cast<std::byte *>(context_storage)+8;
  Put(scope,0,std::uint16_t{4}); Put(scope,8,static_cast<std::uint64_t>(actor_id));
  Put(scope,0x80,actor_id); Put(scope,0x84,recipient_id);
  return context_storage;
}
void GiftRefresh(void *,bool update) { Check(update,"preview refresh"); }
void GiftFinalize(void *) {}
bool GiftValidate(void *,void *error) { Check(error==nullptr,"preview CanSend receiver"); return preview_legal; }
void GiftDestroy(void *) { ++preview_destroys; }
void GiftCost(const void *block,const void *scope,std::int64_t *costs) {
  Check(block==gift_definition.data()+0x40&&scope!=nullptr,"preview native cost receiver");
  for(int i=0;i<10;++i) costs[i]=0;
  if(preview_extra_cost) costs[2]=1;
}
bool GiftTrigger(void *,const void *) { return true; }
bool GiftDelta(void *,std::uintptr_t,const void *scope,std::uint32_t recipient_bits,
               std::uint32_t actor_bits,std::int32_t &delta) noexcept {
  wanted_key="send_gift_opinion"; wanted_root=recipient_id; named_raw=3550000;
  return ReadGiftOpinionDelta12004(NamedBindings(),scope,recipient_bits,actor_bits,delta);
}
bool GiftValue(void *,std::uintptr_t,const void *scope,std::uint32_t recipient_bits,
               std::uint32_t actor_bits,std::int64_t &value) noexcept {
  wanted_key="gift_value"; wanted_root=actor_id; named_raw=1537501;
  return ReadNamedInteractionFixed12004(NamedBindings(),scope,actor_bits,actor_bits,
      recipient_bits,"gift_value",0x58DD38F9U,value);
}
void PreviewProbe() {
  PrepareFrame();
  FactionGiftBindings12004 b{};
  b.enabled=true; b.interaction.enabled=true; b.interaction.core=Core();
  b.get_database=GiftDatabase; b.stable_hash=GiftHash; b.lookup_definition=GiftLookup;
  b.construct_two_role=GiftConstruct; b.interaction.refresh=GiftRefresh;
  b.interaction.finalize=GiftFinalize; b.interaction.validate=GiftValidate;
  b.interaction.destroy=GiftDestroy; b.interaction.evaluate_cost=GiftCost;
  b.interaction.evaluate_trigger=GiftTrigger; b.read_opinion_delta=GiftDelta;
  b.read_gift_value=GiftValue;
  xar::game::FactionGiftPreviewV1 preview{};
  const auto destroyed=preview_destroys;
  Check(ReadFactionGiftPreview12004(b,actor_id,recipient_id,preview)&&preview.available&&
        preview.interaction_legal&&preview.auto_accept&&preview.gold_cost_raw==1537501&&
        preview.opinion_delta==36&&preview_destroys==destroyed+1,
        "full production preview plus actual named readers");
  preview_legal=false;
  Check(ReadFactionGiftPreview12004(b,actor_id,recipient_id,preview)&&preview.available&&
        !preview.interaction_legal,"negative CanSend remains complete preview");
  preview_legal=true; preview_extra_cost=true;
  Check(!ReadFactionGiftPreview12004(b,actor_id,recipient_id,preview)&&!preview.available,
        "nonzero on-send cost still unavailable");
  preview_extra_cost=false;
  const auto constructed=preview_constructs;
  Put(jomini.data(),0x20,std::uint8_t{0});
  Check(!ReadFactionGiftPreview12004(b,actor_id,recipient_id,preview)&&
        preview_constructs==constructed,"unpaused preview rejected before construction");
  Put(jomini.data(),0x20,std::uint8_t{1});
}

void PairProbe(std::uint32_t actor_bits, std::uint32_t recipient_bits) {
  actor_id = actor_bits; recipient_id = recipient_bits;
  slots.fill(std::byte{});
  Put(actor.data(), 0x18, actor_id); Put(recipient.data(), 0x18, recipient_id);
  Put(slots.data(), (actor_id & 0x00ffffffU) * 0x10ULL + 8,
      static_cast<void *>(actor.data()));
  Put(slots.data(), (recipient_id & 0x00ffffffU) * 0x10ULL + 8,
      static_cast<void *>(recipient.data()));
  Put(recipient.data(), 0x1b0, static_cast<void *>(extension.data()));
  Put(group.data(), 0x14, std::int32_t{1});
  Definition(gift_value.data(), "gift_value", 0x58DD38F9U, 0x2000);
  PreviewProbe();
  GiftOpinionResult result;
  Check(ReadGiftOpinion12004(OpinionBindings(), recipient_id, actor_id, result) &&
        result.query_complete && result.gift_opinion_present &&
        result.gift_opinion_modifier_value == modifier_value,
        "exact private opinion pair resolves complete ID");
  prepared_scope.fill(std::byte{});
  Put(prepared_scope.data(), 0, std::uint16_t{4});
  Put(prepared_scope.data(), 8, static_cast<std::uint64_t>(actor_id));
  Put(prepared_scope.data(), 0x80, actor_id);
  Put(prepared_scope.data(), 0x84, recipient_id);
  wanted_key = "send_gift_opinion"; wanted_root = recipient_id;
  named_raw = 3550000;
  std::int32_t delta{};
  Check(ReadGiftOpinionDelta12004(NamedBindings(), prepared_scope.data(),
        recipient_id, actor_id, delta) && delta == 36,
        "exact private recipient-root named opinion");
  wanted_key = "gift_value"; wanted_root = actor_id;
  named_raw = 1537501;
  std::int64_t gold{};
  Check(ReadNamedInteractionFixed12004(NamedBindings(), prepared_scope.data(),
        actor_id, actor_id, recipient_id, "gift_value", 0x58DD38F9U, gold) &&
        gold == 1537501, "exact private actor-root named gift value");
  const auto calls = evaluations;
  Put(recipient.data(), 0x18, recipient_id ^ 0x01000000U);
  Check(!ReadGiftOpinion12004(OpinionBindings(), recipient_id, actor_id, result) &&
        !result.query_complete, "private stale recipient generation rejects");
  Check(!ReadNamedInteractionFixed12004(NamedBindings(), prepared_scope.data(),
        actor_id, actor_id, recipient_id, "gift_value", 0x58DD38F9U, gold) &&
        evaluations == calls && gold == 0, "stale generation never evaluates");
  Put(recipient.data(), 0x18, recipient_id);
  Check(!ReadGiftOpinion12004(OpinionBindings(), 0xffffffffU, actor_id, result) &&
        !result.query_complete, "minus-one recipient remains unavailable");
  Check(!ReadNamedInteractionFixed12004(NamedBindings(), prepared_scope.data(),
        actor_id, 0xffffffffU, recipient_id, "gift_value", 0x58DD38F9U, gold) &&
        evaluations == calls, "minus-one actor never evaluates");
}

} // namespace
int legacy_main() {
  try { Run(); std::cout << "PASS gift opinion 1.20.0.4: " << checks
                         << " assertions; no CK3 process access\n"; return 0; }
  catch (const std::exception &e) { std::cerr << "FAIL " << e.what() << '\n'; return 1; }
}

int main() {
  int failed = 0, passed = 0;
  try { Run(); ++passed; std::cout << "PASS existing-positive-controls\n"; }
  catch (const std::exception &e) { ++failed; std::cout << "FAIL controls " << e.what() << '\n'; }
  struct Case { const char *name; std::uint32_t actor_bits, recipient_bits; };
  const Case cases[] = {
    {"actor-zero", 0U, 0x04000002U},
    {"recipient-zero", 0x03000001U, 0U},
    {"actor-high-bit", 0x80000001U, 0x04000002U},
    {"recipient-high-bit", 0x03000001U, 0x80000002U},
    {"both-high-bit", 0xff000001U, 0x80000002U},
    {"actor-int32-min", 0x80000000U, 0x04000002U},
    {"recipient-int32-min", 0x03000001U, 0x80000000U}
  };
  for (const auto &c : cases) {
    try { PairProbe(c.actor_bits,c.recipient_bits); ++passed; std::cout << "PASS " << c.name << '\n'; }
    catch (const std::exception &e) { ++failed; std::cout << "FAIL " << c.name << " " << e.what() << '\n'; }
  }
  std::cout << "RESULT passed=" << passed << " failed=" << failed << " checks=" << checks << "; authored memory and callbacks; no CK3 process access\n";
  return failed == 0 ? 0 : 1;
}
