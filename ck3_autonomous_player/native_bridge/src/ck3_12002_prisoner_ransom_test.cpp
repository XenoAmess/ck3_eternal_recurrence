#include "xar_bridge/ck3_12002_prisoner.hpp"
#include "xar_bridge/ck3_12002_prisoner_abi.hpp"

#include <array>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <string_view>
#include <unordered_map>
#include <vector>

// These objects and callbacks belong entirely to this executable. The tested
// reader, core snapshot decoder and command ownership path are production code.
namespace {
using namespace xar::ck3_12002;
constexpr std::int32_t kJailer = 0x03000001;
constexpr std::int32_t kPrisoner = 0x04000002;
constexpr std::int32_t kPayer = 0x05000003;
constexpr std::int32_t kDate = 53175816;
constexpr std::int32_t kInteractionHash = 0x12345678;
constexpr std::array<std::string_view, 9> kFlags{
    "extortionate_gold", "extortionate_current_gold", "gold",
    "current_gold", "favor", "influence_send_option", "herd_send_option",
    "current_herd", "invalid"};
using Options = std::array<std::uint8_t, 9>;
using Command = std::array<std::byte, 0x368>;

int checks = 0;
void Check(bool value, const char *message) {
  ++checks;
  if (!value) {
    std::cerr << "FAIL " << message << '\n';
    std::exit(1);
  }
}
template <typename T> void Put(void *base, std::size_t offset, T value) {
  std::memcpy(static_cast<std::byte *>(base) + offset, &value, sizeof(value));
}
template <typename T> T Get(const void *base, std::size_t offset) {
  T result{};
  std::memcpy(&result, static_cast<const std::byte *>(base) + offset,
              sizeof(result));
  return result;
}

enum class Selection { gold, current_gold, replaced_gold, none, current_herd,
                       invalid, extra_option, extortionate };
struct Fixture;
Fixture *fixture = nullptr;
void *LocalPlayer(void *);
void *Database();
std::int32_t Hash(void *, const char *, std::uint32_t);
void *Lookup(void *, std::int32_t);
void Redirect(void *, std::int32_t *, std::int32_t *, std::int32_t *,
              std::int32_t *, std::int32_t *, std::int32_t *);
void *Construct(void *, void *, std::int32_t, std::int32_t, std::int32_t,
                std::int32_t, std::int32_t, void *);
void Clear(void *);
void Select(void *, std::int32_t);
bool Validate(void *, void *);
std::int64_t *Score(void *, std::int64_t *);
std::uint8_t Answer(void *, std::uint8_t, std::uint8_t, void *, void *);
void DestroyContext(void *);
void *IdentifierTable();
std::int32_t *Identifier(void *, std::int32_t *, const void *);
bool NamedCost(void *, std::uintptr_t, const void *, std::int32_t,
               std::int32_t, std::int32_t, std::int64_t &) noexcept;
void *Send(void *, const void *);
void **Clone(const void *, void **);
void *Delete(void *, std::uint32_t);
bool Queue(void *, void **, std::uint32_t);

struct Fixture {
  // Fixed-RVA slots and vtable reside in a normal fixture-owned allocation.
  std::vector<std::byte> image = std::vector<std::byte>(0x5C67600);
  std::array<std::byte, 0xA8> state{};
  std::array<std::byte, 0x28> jomini{};
  std::array<std::byte, 0x1F8> players{};
  std::array<std::byte, 0x78> local_player{};
  std::vector<std::byte> data = std::vector<std::byte>(0x22350);
  std::array<std::byte, 0xE0> entry{};
  std::array<void *, 1> entries{entry.data()};
  std::array<std::byte, 0x30> store{};
  std::array<std::byte, 4 * 0x10> slots{};
  std::array<std::array<std::byte, 0x1D8>, 3> characters{};
  std::array<std::byte, 0x110> payer_extension{};
  std::array<std::byte, 0x2268> definition{};
  std::array<std::byte, 9 * 0x730> option_rows{};
  std::array<std::byte, 8> database{}, identifier_table{};
  void *state_pointer = state.data(), *jomini_pointer = jomini.data();
  void *store_pointer = store.data();
  PrisonerRansomBindings bindings{};
  std::unordered_map<void *, Options *> contexts;
  std::vector<std::string_view> verified_flags;
  Selection selection = Selection::gold;
  bool can_send = true, queue_accepts = true, named_cost_available = true;
  std::uint8_t answer = 1;
  std::int64_t named_raw = 90 * 100000;
  std::int64_t score_raw = 33 * 100000;
  int constructs = 0, destroys = 0, send_copies = 0, clones = 0;
  int queues = 0, deletes = 0, named_reads = 0;
  void *queued = nullptr;

  std::uintptr_t Module() const {
    return reinterpret_cast<std::uintptr_t>(image.data());
  }
  std::uintptr_t Primary() const {
    return Module() + kMarriageSendInteractionPrimaryVtableRva;
  }
  void Gold(std::int64_t raw) { Put(payer_extension.data(), 0x100, raw); }
  void CopyContext(void *destination, const void *source) {
    const auto found = contexts.find(const_cast<void *>(source));
    Check(found != contexts.end(), "source context remains fixture-owned");
    std::memcpy(destination, source, 0x338);
    auto *options = new Options(*found->second);
    Check(contexts.emplace(destination, options).second,
          "copied context has unique ownership");
    Put(destination, 0x300, options->data());
  }
  Fixture() {
    fixture = this;
    Put(state.data(), 8, kDate);
    Put(state.data(), 0x70, std::int32_t{2});
    Put(state.data(), 0xA0, data.data());
    Put(jomini.data(), 0x18, players.data());
    Put(jomini.data(), 0x20, std::uint8_t{1});
    Put(players.data(), 0x1F0, std::int32_t{7});
    Put(local_player.data(), 0x70, std::int32_t{7});
    Put(data.data(), kPlayerCharacterManagerOffset + 0x58, entries.data());
    Put(data.data(), kPlayerCharacterManagerOffset + 0x64, std::int32_t{1});
    Put(entry.data(), 0xD8, std::int32_t{7});
    Put(entry.data(), 0xB0, kJailer);
    Put(store.data(), 0x20, slots.data());
    Put(store.data(), 0x2C, std::int32_t{4});
    const std::array ids{kJailer, kPrisoner, kPayer};
    for (std::size_t index = 0; index < ids.size(); ++index) {
      Put(characters[index].data(), 0x18, ids[index]);
      Put(slots.data(), (ids[index] & 0xFFFFFF) * 0x10 + 8,
          characters[index].data());
    }
    Put(image.data(), kCharacterStorageSlotRva, store.data());
    Put(image.data(), kCharacterStorageSlotRva + 8, static_cast<void *>(nullptr));
    Put(characters[2].data(), 0x1B0, payer_extension.data());
    Gold(120 * 100000);
    constexpr std::string_view key = "ransom_interaction";
    Put(definition.data(), 0x14, kInteractionHash);
    Put(definition.data(), 0x18, key.data());
    Put(definition.data(), 0x28, static_cast<std::uint64_t>(key.size()));
    Put(definition.data(), 0x30, static_cast<std::uint64_t>(key.size()));
    Put(definition.data(), 0x2258, option_rows.data());
    Put(definition.data(), 0x2264, std::int32_t{9});
    for (std::size_t index = 0; index < kFlags.size(); ++index)
      Put(option_rows.data(), index * 0x730 + 0x368,
          static_cast<std::int32_t>(100 + index));
    Put(image.data(), kMarriageSendInteractionPrimaryVtableRva, &Delete);
    Put(image.data(), kMarriageSendInteractionPrimaryVtableRva + 0x40, &Clone);
    bindings.enabled = true;
    bindings.context.enabled = true;
    bindings.context.core = {true, &state_pointer, &jomini_pointer,
                             &store_pointer, &LocalPlayer};
    bindings.context.commands.enabled = true;
    bindings.context.commands.command_manager = this;
    bindings.context.commands.queue_owned_command = &Queue;
    bindings.get_character_interaction_database = &Database;
    bindings.hash_stable_key = &Hash;
    bindings.lookup_character_interaction = &Lookup;
    bindings.redirect_character_interaction_roles = &Redirect;
    bindings.construct_character_interaction_context_all_roles = &Construct;
    bindings.validate_character_interaction_context = &Validate;
    bindings.read_character_interaction_answer_score = &Score;
    bindings.evaluate_character_interaction_answer = &Answer;
    bindings.destroy_character_interaction_context = &DestroyContext;
    bindings.get_script_identifier_table = &IdentifierTable;
    bindings.lookup_script_identifier_id = &Identifier;
    bindings.construct_send_character_interaction_command = &Send;
    bindings.send_character_interaction_primary_vtable = Primary();
    bindings.send_character_interaction_secondary_vtable =
        Module() + kMarriageSendInteractionSecondaryVtableRva;
    bindings.clear_local_options = &Clear;
    bindings.select_local_option = &Select;
    bindings.named_cost_context = this;
    bindings.read_named_cost = &NamedCost;
  }
  PlayerPrisonerRansomQuoteV1 Quote() {
    verified_flags.clear();
    auto result = ReadPlayerPrisonerRansomQuotePrivateV1(
        bindings, Module(), kJailer, kPrisoner);
    Check(contexts.empty(), "quote destroys every temporary context");
    return result;
  }
  void ReleaseQueued() {
    Check(queued != nullptr, "queue retained independent owning command");
    Check(DestroyOwnedCommand(queued) && queued == nullptr,
          "production deleting destructor releases queued command");
    Check(contexts.empty(), "all copied options released exactly once");
  }
};

void *LocalPlayer(void *jomini) {
  Check(jomini == fixture->jomini.data(), "production core jomini slot");
  return fixture->local_player.data();
}
void *Database() { return fixture->database.data(); }
std::int32_t Hash(void *database, const char *key, std::uint32_t size) {
  Check(database == fixture->database.data() &&
        std::string_view(key, size) == "ransom_interaction",
        "production requests stock ransom_interaction");
  return kInteractionHash;
}
void *Lookup(void *database, std::int32_t hash) {
  Check(database == fixture->database.data() && hash == kInteractionHash,
        "native interaction lookup identity");
  return fixture->definition.data();
}
void Redirect(void *definition, std::int32_t *actor, std::int32_t *recipient,
              std::int32_t *sa, std::int32_t *sr, std::int32_t *intermediary,
              std::int32_t *added) {
  Check(definition == fixture->definition.data() && *actor == kJailer &&
        *recipient == kPrisoner && *sa == -1 && *sr == -1 &&
        *intermediary == -1 && *added == -1,
        "1.20 seventh role argument is supplied");
  *recipient = kPayer;
  *sr = kPrisoner;
}
void *Construct(void *context, void *definition, std::int32_t actor,
                std::int32_t recipient, std::int32_t sa, std::int32_t sr,
                std::int32_t intermediary, void *extra) {
  Check(definition == fixture->definition.data() && actor == kJailer &&
        recipient == kPayer && sa == -1 && sr == kPrisoner &&
        intermediary == -1 && extra == nullptr, "redirected ransom roles");
  auto *options = new Options{};
  Check(fixture->contexts.emplace(context, options).second,
        "fresh context options ownership");
  Put(context, 0, definition);
  Put(context, 0x2D8, actor); Put(context, 0x2DC, recipient);
  Put(context, 0x2E0, sa); Put(context, 0x2E4, sr);
  Put(context, 0x2E8, intermediary);
  Put(context, 0x300, options->data());
  Put(context, 0x30C, std::int32_t{9});
  ++fixture->constructs;
  return context;
}
void Clear(void *context) { fixture->contexts.at(context)->fill(0); }
void Select(void *context, std::int32_t index) {
  Check(index >= 0 && index < 4, "provider only requests authored gold options");
  auto &options = *fixture->contexts.at(context);
  switch (fixture->selection) {
    case Selection::gold: if (index == 2) options[2] = 1; break;
    case Selection::current_gold: if (index == 3) options[3] = 1; break;
    case Selection::replaced_gold: if (index >= 2) options[3] = 1; break;
    case Selection::none: break;
    case Selection::current_herd: options[7] = 1; break;
    case Selection::invalid: options[8] = 1; break;
    case Selection::extra_option: options[2] = 1; options[8] = 1; break;
    case Selection::extortionate: if (index == 0) options[0] = 1; break;
  }
}
bool Validate(void *context, void *error) {
  Check(error == nullptr && fixture->contexts.count(context) == 1,
        "Can Send operates on live fixture-owned context");
  return fixture->can_send;
}
std::int64_t *Score(void *context, std::int64_t *output) {
  Check(fixture->contexts.count(context) == 1, "score has live context");
  *output = fixture->score_raw;
  return output;
}
std::uint8_t Answer(void *context, std::uint8_t mode, std::uint8_t flag,
                    void *first, void *second) {
  Check(fixture->contexts.count(context) == 1 && mode == 1 && flag == 1 &&
        first == nullptr && second == nullptr, "native final answer ABI");
  return fixture->answer;
}
void DestroyContext(void *context) {
  const auto found = fixture->contexts.find(context);
  Check(found != fixture->contexts.end(), "context is destroyed once");
  delete found->second;
  fixture->contexts.erase(found);
  Put(context, 0, static_cast<void *>(nullptr));
  Put(context, 0x300, static_cast<void *>(nullptr));
  ++fixture->destroys;
}
void *IdentifierTable() { return fixture->identifier_table.data(); }
std::int32_t *Identifier(void *table, std::int32_t *output, const void *view) {
  Check(table == fixture->identifier_table.data() &&
        Get<std::uint8_t>(view, 0xC) == 0, "borrowed native option flag view");
  const auto key = std::string_view(Get<const char *>(view, 0),
      static_cast<std::size_t>(Get<std::int32_t>(view, 8)));
  for (std::size_t index = 0; index < kFlags.size(); ++index) {
    if (key == kFlags[index]) {
      fixture->verified_flags.push_back(kFlags[index]);
      *output = static_cast<std::int32_t>(100 + index);
      return output;
    }
  }
  Check(false, "every requested option identity is authored");
  return nullptr;
}
bool NamedCost(void *owner, std::uintptr_t module, const void *scope,
               std::int32_t jailer, std::int32_t payer, std::int32_t prisoner,
               std::int64_t &output) noexcept {
  auto &f = *fixture;
  Check(owner == &f && module == f.Module() && jailer == kJailer &&
        payer == kPayer && prisoner == kPrisoner, "normal ransom cost role IDs");
  const auto context = static_cast<const std::byte *>(scope) - 8;
  Check(f.contexts.count(const_cast<std::byte *>(context)) == 1 &&
        Get<void *>(context, 0) == f.definition.data() &&
        Get<std::uint8_t>(Get<void *>(context, 0x300), 2) == 1,
        "normal_ransom_cost_value receives selected ordinary gold scope");
  ++f.named_reads;
  output = f.named_raw;
  return f.named_cost_available;
}
void *Send(void *command, const void *context) {
  auto &f = *fixture;
  Put(command, 0, f.Primary());
  Put(command, 0x18, f.bindings.send_character_interaction_secondary_vtable);
  f.CopyContext(static_cast<std::byte *>(command) + 0x20, context);
  ++f.send_copies;
  return command;
}
void **Clone(const void *source, void **output) {
  auto *copy = new Command{};
  std::memcpy(copy->data(), source, copy->size());
  fixture->CopyContext(copy->data() + 0x20,
                       static_cast<const std::byte *>(source) + 0x20);
  ++fixture->clones;
  *output = copy;
  return output;
}
void *Delete(void *command, std::uint32_t flags) {
  Check(flags == 1, "scalar deleting destructor uses owning delete flag");
  DestroyContext(static_cast<std::byte *>(command) + 0x20);
  delete static_cast<Command *>(command);
  ++fixture->deletes;
  return nullptr;
}
bool Queue(void *manager, void **owned, std::uint32_t flags) {
  auto &f = *fixture;
  Check(manager == &f && flags == 0x0E && owned != nullptr && *owned != nullptr,
        "production ransom command queue channel and ownership");
  Check(f.queued == nullptr, "only one outstanding queued fixture command");
  f.queued = *owned;
  *owned = nullptr;
  ++f.queues;
  return f.queue_accepts;
}

void CheckAvailable(const PlayerPrisonerRansomQuoteV1 &quote,
                    std::string_view option, std::int64_t amount,
                    bool acceptance_time) {
  Check(quote.available && quote.failure == PlayerPrisonerRansomQuoteFailureV1::none,
        "production ransom quote available");
  Check(quote.jailer_character_id == kJailer && quote.payer_character_id == kPayer &&
        quote.prisoner_character_id == kPrisoner, "quote retains redirected role IDs");
  Check(quote.selected_option == option && quote.quoted_gold_raw == amount &&
        quote.amount_is_acceptance_time_quote == acceptance_time,
        "quoted amount and timing match selected option");
  Check(quote.observed_definition_option_count == 9 &&
        quote.observed_context_option_count == 9,
        "production reads nine authored and context options");
  Check(quote.recipient_acceptance_raw == fixture->score_raw &&
        quote.recipient_answer_status_raw == fixture->answer &&
        quote.would_accept_now == (fixture->answer != 2),
        "native score and final answer survive quote");
}

void Run() {
  Fixture f;
  auto quote = f.Quote();
  CheckAvailable(quote, "gold", 90 * 100000, false);
  Check(f.verified_flags == std::vector<std::string_view>(kFlags.begin(), kFlags.end()),
        "all nine option flags are checked in stock order including current_herd/invalid");
  Check(f.named_reads == 1, "gold uses named normal ransom cost once");
  const int reads = f.named_reads;
  f.selection = Selection::current_gold;
  quote = f.Quote();
  CheckAvailable(quote, "current_gold", 120 * 100000, true);
  Check(f.named_reads == reads, "current_gold reads payer gold directly");
  f.selection = Selection::replaced_gold;
  quote = f.Quote();
  CheckAvailable(quote, "current_gold", 120 * 100000, true);
  f.can_send = false;
  quote = f.Quote();
  Check(!quote.available && quote.failure ==
        PlayerPrisonerRansomQuoteFailureV1::final_can_send_false,
        "native final Can Send false blocks ordinary ransom");
  f.can_send = true;
  f.selection = Selection::none;
  f.Gold(99999);
  quote = f.Quote();
  Check(!quote.available && quote.failure ==
        PlayerPrisonerRansomQuoteFailureV1::payer_below_one_gold,
        "payer below one gold is distinguished from a missing quote");
  f.Gold(120 * 100000);
  quote = f.Quote();
  Check(!quote.available && quote.failure ==
        PlayerPrisonerRansomQuoteFailureV1::gold_options_not_selected_with_funded_payer,
        "funded payer with no gold option has its own result");
  for (const auto selection : {Selection::current_herd, Selection::invalid,
                              Selection::extra_option}) {
    f.selection = selection;
    quote = f.Quote();
    const auto mask = selection == Selection::current_herd ? 1U << 7 :
        selection == Selection::invalid ? 1U << 8 : (1U << 2) | (1U << 8);
    Check(!quote.available && quote.failure ==
          PlayerPrisonerRansomQuoteFailureV1::option_mask_unexpected &&
          quote.requested_option_index == 2 && quote.observed_option_mask_bits == mask,
          "current_herd 7 and invalid 8 remain diagnostic masks, never gold quotes");
  }
  f.selection = Selection::extortionate;
  quote = f.Quote();
  Check(!quote.available && quote.failure ==
        PlayerPrisonerRansomQuoteFailureV1::extortionate_gold_option_requires_valuation,
        "extortionate option is not priced as ordinary gold");
  f.selection = Selection::gold;
  f.answer = 2;
  quote = f.Quote();
  CheckAvailable(quote, "gold", 90 * 100000, false);
  Check(SubmitPlayerPrisonerRansomPrivateV1(f.bindings, f.Module(), quote, 1, kDate) ==
        PlayerPrisonerRansomSubmitV1::unavailable && f.queues == 0,
        "recipient rejection quote cannot be submitted");
  f.answer = 1;
  f.named_raw = 0;
  quote = f.Quote();
  Check(!quote.available && quote.failure ==
        PlayerPrisonerRansomQuoteFailureV1::quote_unavailable,
        "zero named value does not become a positive payment quote");
  f.named_raw = 90 * 100000;
  quote = f.Quote();
  Check(SubmitPlayerPrisonerRansomPrivateV1(f.bindings, f.Module(), quote, 1, kDate) ==
        PlayerPrisonerRansomSubmitV1::submitted_verification_pending,
        "real production submit calls SubmitCommandCopy and reports only pending verification");
  Check(f.send_copies == 1 && f.clones == 1 && f.queues == 1 &&
        f.contexts.size() == 1 && f.deletes == 0,
        "queue owns one deep clone after both temporary contexts are destroyed");
  const auto copied_context = static_cast<std::byte *>(f.queued) + 0x20;
  Check(Get<void *>(copied_context, 0) == f.definition.data() &&
        Get<std::int32_t>(copied_context, 0x2D8) == kJailer &&
        Get<std::int32_t>(copied_context, 0x2DC) == kPayer &&
        Get<std::int32_t>(copied_context, 0x2E4) == kPrisoner &&
        Get<std::uint8_t>(Get<void *>(copied_context, 0x300), 2) == 1,
        "queued clone retains live roles and selected option after source destruction");
  f.ReleaseQueued();
  f.queue_accepts = false;
  Check(SubmitPlayerPrisonerRansomPrivateV1(f.bindings, f.Module(), quote, 1, kDate) ==
        PlayerPrisonerRansomSubmitV1::command_unavailable,
        "native queue rejection is not a submitted gameplay result");
  f.ReleaseQueued();
  Check(f.clones == 2 && f.queues == 2 && f.deletes == 2 &&
        f.destroys == f.constructs + 2 * f.send_copies,
        "every constructor, send copy and owning clone is released once");
  std::cout << "PASS CK3 1.20.0.2 production prisoner ransom fixture: " << checks
            << " checks; nine options; normal_ransom_cost_value; gold/current_gold; "
            << "CanSend false; payer low gold; selected masks; deep-copy queue ownership\n";
}
} // namespace

int main() { Run(); }
