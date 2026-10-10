#include "xar_bridge/person_transfer_block78_12004.hpp"

#include <iostream>
#include <stdexcept>
#include <cstring>
#include <array>

using namespace xar::ck3_12004;
namespace {
void Require(bool condition, const char *message) {
  if (!condition) throw std::runtime_error(message);
}
PersonTransferBlock78Input12004 ExternalPair() {
  PersonTransferBlock78Input12004 in;
  in.a = {0x1078, 0x9000, 17, 3,
          std::vector<std::uint16_t>{0, 65535, 7}};
  in.b = {0x2078, 0xA000, 23, 2,
          std::vector<std::uint16_t>{9, 9}};
  in.initial_a_range = PersonTransferKeyRange12004{0x10A0, 32};
  in.initial_b_range = PersonTransferKeyRange12004{0x20A0, 32};
  in.b_allocator_identity = 0xCAFE;
  in.a_allocator_identity = 0xCAFE;
  in.repeated_a_allocator_identity = 0xCAFE;
  in.later_b_range = in.initial_b_range;
  in.later_a_range = in.initial_a_range;
  return in;
}
void NoNativeOrFullTransfer(const PersonTransferBlock78Postimage12004 &out) {
  Require(!out.actual_native_write_performed && !out.full_person_transfer_ready,
          "local reconstruction claimed native write or full transfer");
}
struct Header {
  std::uintptr_t data;
  std::int32_t capacity, count;
};
static_assert(sizeof(Header) == 16);
bool ReadOwned(void *context, const void *source, void *destination,
               std::size_t bytes) noexcept {
  if (context != nullptr && source == context) return false;
  std::memcpy(destination, source, bytes);
  return true;
}
} // namespace

extern "C" __declspec(dllexport)
int PersonTransferBlock78FocusedTest12004() {
  try {
    {
      auto in = ExternalPair();
      const auto original = in;
      auto out = EvaluatePersonTransferBlock78Postimage12004(in);
      Require(out.ready && out.key_elements_ready && out.after_a && out.after_b,
              "external compatible-allocator source stores not reconstructed");
      Require(out.after_a->storage_identity == 0x1078 &&
              out.after_b->storage_identity == 0x2078 &&
              out.a_allocator_receiver_identity == 0x1090 &&
              out.b_allocator_receiver_identity == 0x2090,
              "physical storage/allocator receiver changed owner");
      Require(out.after_a->data_identity == 0xA000 &&
              out.after_a->count_i32 == 2 && out.after_a->capacity_i32 == 23 &&
              out.after_a->keys_u16 == std::vector<std::uint16_t>({9, 9}) &&
              out.after_b->data_identity == 0x9000 &&
              out.after_b->count_i32 == 3 && out.after_b->capacity_i32 == 17 &&
              out.after_b->keys_u16 == std::vector<std::uint16_t>({0, 65535, 7}),
              "literal header stores lost count/capacity/order/duplicate/raw U16");
      Require(in.a == original.a && in.b == original.b,
              "conditional evaluator modified supplied preimage");
      NoNativeOrFullTransfer(out);
    }
    {
      auto in = ExternalPair();
      in.b.count_i32 = 0;
      in.b.keys_u16 = std::vector<std::uint16_t>{};
      auto out = EvaluatePersonTransferBlock78Postimage12004(in);
      Require(out.ready && out.key_elements_ready && out.after_a->count_i32 == 0 &&
              out.after_a->keys_u16 && out.after_a->keys_u16->empty() &&
              out.after_b->count_i32 == 3,
              "known empty donor was replaced by unavailable keys or lost other side");
      NoNativeOrFullTransfer(out);
    }
    {
      auto in = ExternalPair();
      in.a.keys_u16.reset();
      auto out = EvaluatePersonTransferBlock78Postimage12004(in);
      Require(out.ready && !out.key_elements_ready && out.after_b &&
              !out.after_b->keys_u16 && out.after_b->count_i32 == 3,
              "unread key payload was fabricated from known header");
      NoNativeOrFullTransfer(out);
    }
    {
      auto in = ExternalPair();
      in.a.data_identity = 0x10A0;
      in.initial_b_range.reset();
      in.b_allocator_identity.reset();
      auto out = EvaluatePersonTransferBlock78Postimage12004(in);
      Require(out.ready && out.after_a && out.after_b &&
              out.path == PersonTransferBlock78Path12004::element_swap &&
              out.demanded_callees == std::vector<std::uintptr_t>{0x17140D0} &&
              out.after_a->data_identity == in.a.data_identity &&
              out.after_a->capacity_i32 == in.a.capacity_i32 &&
              out.after_a->count_i32 == in.b.count_i32 &&
              out.after_b->keys_u16 == in.a.keys_u16,
              "A-inline branch demanded skipped B callback or changed source-held fixed backing");
      NoNativeOrFullTransfer(out);
    }
    {
      auto in = ExternalPair();
      in.a.data_identity = 0x10E0; // base+2*32: exclusive end is external.
      auto out = EvaluatePersonTransferBlock78Postimage12004(in);
      Require(out.ready && out.path ==
                  PersonTransferBlock78Path12004::compatible_allocator_header_swap,
              "literal unsigned half-open range included its end");
      NoNativeOrFullTransfer(out);
    }
    {
      auto in = ExternalPair();
      in.repeated_a_allocator_identity = 0;
      auto out = EvaluatePersonTransferBlock78Postimage12004(in);
      Require(!out.ready && out.path == PersonTransferBlock78Path12004::allocator_fallback &&
              out.demanded_callees == std::vector<std::uintptr_t>{0x1714F50},
              "third slot30 result was replaced by the earlier equal identity");
      NoNativeOrFullTransfer(out);
    }
    {
      auto in = ExternalPair();
      in.later_b_range = PersonTransferKeyRange12004{0xA000, 1};
      auto out = EvaluatePersonTransferBlock78Postimage12004(in);
      Require(!out.ready && !out.after_a && !out.after_b &&
              out.demanded_callees == std::vector<std::uintptr_t>{0x11E10D0},
              "later B callback was reused from initial callback or resize ACK treated as stores");
      NoNativeOrFullTransfer(out);
    }
    {
      auto in = ExternalPair();
      in.initial_b_range.reset();
      auto out = EvaluatePersonTransferBlock78Postimage12004(in);
      Require(!out.ready && out.path == PersonTransferBlock78Path12004::unknown &&
              out.reason == "initial_b_slot28_response_unread" &&
              out.demanded_callees.empty(),
              "missing demanded range was treated as external storage");
      NoNativeOrFullTransfer(out);
    }
    {
      auto in = ExternalPair();
      in.b_allocator_identity = 0xBEEF;
      in.a_allocator_field10 = 0x1234;
      in.b_allocator_field10 = 0x1234;
      auto out = EvaluatePersonTransferBlock78Postimage12004(in);
      Require(out.ready && out.key_elements_ready &&
              out.path == PersonTransferBlock78Path12004::allocator_fallback &&
              out.after_a->data_identity == in.b.data_identity &&
              out.after_b->storage_identity == in.b.storage_identity,
              "source-held fallback +10 equality did not reconstruct direct stores");
      NoNativeOrFullTransfer(out);
    }
    {
      std::array<std::uint16_t,3> keys_a{1,65535,0};
      std::array<std::uint16_t,2> keys_b{5,5};
      Header a{reinterpret_cast<std::uintptr_t>(keys_a.data()),17,3};
      Header b{reinterpret_cast<std::uintptr_t>(keys_b.data()),23,2};
      auto before_a = CopyPersonTransferBlock78Keys12004(
          reinterpret_cast<std::uintptr_t>(&a),nullptr,ReadOwned);
      auto before_b = CopyPersonTransferBlock78Keys12004(
          reinterpret_cast<std::uintptr_t>(&b),nullptr,ReadOwned);
      Header old_a = a; a = b; b = old_a;
      auto after_a = CopyPersonTransferBlock78Keys12004(
          reinterpret_cast<std::uintptr_t>(&a),nullptr,ReadOwned);
      auto after_b = CopyPersonTransferBlock78Keys12004(
          reinterpret_cast<std::uintptr_t>(&b),nullptr,ReadOwned);
      auto relation = ComparePersonTransferBlock78Copies12004(
          before_a,before_b,after_a,after_b);
      keys_a[0] = 111;
      Require(relation.header_cross_equal == true &&
              relation.key_payload_cross_equal == true &&
              relation.key_exchange_relation_observed &&
              before_a.keys_u16->at(0) == 1 && after_b.keys_u16->at(0) == 1 &&
              !relation.all_native_delegate_postimages_ready &&
              !relation.full_person_transfer_ready,
              "raw U16 copy/observed cross equality borrowed mutable backing or claimed delegates");
    }
    {
      PersonTransferKeyCopy12004 before_a, before_b, after_a, after_b;
      before_a.count_i32 = 1; before_a.keys_u16 = std::vector<std::uint16_t>{7};
      before_b.count_i32 = 1; before_b.keys_u16 = std::vector<std::uint16_t>{9};
      before_a.key_elements_ready = before_b.key_elements_ready = true;
      after_a = before_b; after_b = before_a;
      after_a.keys_u16 = std::vector<std::uint16_t>{8};
      auto relation = ComparePersonTransferBlock78Copies12004(before_a,before_b,after_a,after_b);
      Require(relation.key_payload_cross_equal == false &&
              !relation.key_exchange_relation_observed,
              "postimage key mismatch was hidden by call/identity association");
    }
    {
      std::array<std::uint16_t,1> keys{123};
      Header header{reinterpret_cast<std::uintptr_t>(keys.data()),32,1};
      auto copy = CopyPersonTransferBlock78Keys12004(
          reinterpret_cast<std::uintptr_t>(&header),keys.data(),ReadOwned);
      auto relation = ComparePersonTransferBlock78Copies12004(copy,copy,copy,copy);
      Require(copy.header_ready && !copy.key_elements_ready && !copy.keys_u16 &&
              !relation.key_payload_cross_equal,
              "header-ready unread payload was relabeled empty or exchanged");
    }
    {
      Header header{0,32,0};
      auto copy = CopyPersonTransferBlock78Keys12004(
          reinterpret_cast<std::uintptr_t>(&header),nullptr,ReadOwned);
      Require(copy.header_ready && copy.key_elements_ready && copy.keys_u16 &&
              copy.keys_u16->empty(),
              "source count0 demanded backing bytes or was confused with unread count");
    }
    {
      auto in = ExternalPair();
      in.later_b_range = PersonTransferKeyRange12004{0xA000,1};
      in.b_conversion_postimage = in.b;
      in.b_conversion_postimage->data_identity = 0xB000;
      in.b_conversion_postimage->capacity_i32 = 33;
      auto out = EvaluatePersonTransferBlock78Postimage12004(in);
      Require(out.ready && out.after_a->data_identity == 0xB000 &&
              out.after_a->capacity_i32 == 33 && out.after_a->keys_u16 == in.b.keys_u16 &&
              out.after_a->storage_identity == in.a.storage_identity,
              "header stores did not consume actual completed conversion storage");
      NoNativeOrFullTransfer(out);
    }
    {
      auto in = ExternalPair();
      in.b_allocator_identity = 0xBEEF;
      in.a_allocator_field10 = 0x1234;
      in.b_allocator_field10 = 0x5678;
      auto out = EvaluatePersonTransferBlock78Postimage12004(in);
      Require(!out.ready && !out.after_a && !out.after_b && out.key_elements_ready &&
              out.after_a_keys_u16 == in.b.keys_u16 &&
              out.after_b_count_i32 == in.a.count_i32 &&
              out.reason == "allocator_selected_backing_not_supplied",
              "logical three-move key result invented unknown physical backing");
      NoNativeOrFullTransfer(out);
    }
    std::cout << "PASS 15 new block78 copy/compare and conditional source-store cases; no game or full transfer\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
