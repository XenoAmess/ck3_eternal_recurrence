#include "xar_bridge/family_ruler_default_materializer_12004.hpp"

#include <algorithm>
#include <bit>
#include <charconv>
#include <cstdint>
#include <locale>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace xar::bridge {

namespace {

// Helper to append a JSON array of option rows.
void AppendOptionRows(std::ostringstream &os,
                     const std::vector<FamilyOutgoingOptionCopy12004> &options) {
  os << "[";
  for (std::size_t i = 0; i < options.size(); ++i) {
    if (i > 0) {
      os << ",";
    }
    os << "{";
    os << "\"declared_ordinal\":" << i << ",";
    os << "\"flag_full_u32\":" << options[i].flag << ",";
    os << "\"bank_value_u8\":" << static_cast<int>(options[i].bank_byte);
    os << "}";
  }
  os << "]";
}

// Helper to append a JSON object of roles.
void AppendRoles(std::ostringstream &os,
                 const std::array<std::uint32_t, 5> &roles) {
  os << "{";
  os << "\"actor_id\":" << roles[0] << ",";
  os << "\"recipient_id\":";
  if (roles[1] == UINT32_MAX) {
    os << "null";
  } else {
    os << roles[1];
  }
  os << ",\"secondary_actor_id\":";
  if (roles[2] == UINT32_MAX) {
    os << "null";
  } else {
    os << roles[2];
  }
  os << ",\"secondary_recipient_id\":";
  if (roles[3] == UINT32_MAX) {
    os << "null";
  } else {
    os << roles[3];
  }
  os << ",\"intermediary_id\":";
  if (roles[4] == UINT32_MAX) {
    os << "null";
  } else {
    os << roles[4];
  }
  os << "}";
}

// Validate the prepared context copy against the Java contract.
void ValidatePreparedContext(const FamilyRulerPreparedContextCopy12004 &copy) {
  // Actor must be positive and not the sentinel.
  if (copy.roles[0] == 0 || copy.roles[0] == UINT32_MAX) {
    throw std::invalid_argument("Invalid actor ID in prepared context");
  }

  // Other roles must be positive or UINT32_MAX (null).
  for (std::size_t i = 1; i < copy.roles.size(); ++i) {
    if (copy.roles[i] == 0) {
      throw std::invalid_argument("Invalid role ID in prepared context");
    }
  }

  // Options must be <= 4096.
  if (copy.options.size() > 4096) {
    throw std::invalid_argument("Too many options in prepared context");
  }

  // Validate option bytes.
  for (const auto &opt : copy.options) {
    if (opt.bank_byte > 1) {
      throw std::invalid_argument("Invalid option bank byte in prepared context");
    }
  }

  // Definition hash must be valid uint32 (always true for std::uint32_t).
  // Actual definition pointer must be non-zero.
  if (copy.actual_definition == 0) {
    throw std::invalid_argument("Null actual definition in prepared context");
  }
}

} // namespace

std::string SerializeFamilyRulerPreparedContext12004(
    const FamilyRulerPreparedContextCopy12004 &copy) {
  // Validate the input data first.
  ValidatePreparedContext(copy);

  std::ostringstream os;
  os.imbue(std::locale::classic());
  os << "{";

  // schema
  os << "\"schema\":\"ck3-marriage-materialized-send-context-12004-v2\",";

  // status
  os << "\"status\":\"available\",";

  // source
  os << "\"source\":\"original_native_marriage_context_builder\",";

  // read_only
  os << "\"read_only\":true,";

  // send_invoked
  os << "\"send_invoked\":false,";

  // command_constructed
  os << "\"command_constructed\":false,";

  // role_arity
  os << "\"role_arity\":5,";

  // sixth_role_id
  os << "\"sixth_role_id\":null,";

  // definition_stable_hash
  os << "\"definition_stable_hash\":" << copy.definition_hash << ",";

  // interaction_key
  os << "\"interaction_key\":\"arrange_marriage_interaction\",";

  // complete_can_send
  os << "\"complete_can_send\":" << (copy.can_send ? "true" : "false") << ",";

  // matrilineal_option_selected
  os << "\"matrilineal_option_selected\":" << (copy.matrilineal ? "true" : "false") << ",";

  // grand_wedding_option_selected
  os << "\"grand_wedding_option_selected\":" << (copy.grand_wedding ? "true" : "false") << ",";

  // effective_matrilineal_if_accepted
  os << "\"effective_matrilineal_if_accepted\":null,";

  // effective_roles
  os << "\"effective_roles\":";
  AppendRoles(os, copy.roles);
  os << ",";

  // selected_option_rows
  os << "\"selected_option_rows\":";
  AppendOptionRows(os, copy.options);
  os << ",";

  // copy_passes
  os << "\"copy_passes\":2,";

  // unavailable_reason
  os << "\"unavailable_reason\":null";

  os << "}";

  return os.str();
}

} // namespace xar::bridge
