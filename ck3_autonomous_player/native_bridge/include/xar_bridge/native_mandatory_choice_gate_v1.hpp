#pragma once

#include <cstdint>
#include <functional>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace xar::mandatory_choice_v1 {

// This gate is independent of CK3's process layout. The owning-thread adapter
// must prove each observation from the exact admitted executable before using it.
struct Frame {
  std::uint32_t game_pid = 0;
  std::uint64_t connection_generation = 0;
  std::uint64_t revision = 0;
  std::uint64_t native_revision = 0;
  std::int32_t date_raw = 0;
  std::int32_t actor_character_id = 0;
  std::string episode_run_id;
  std::string snapshot_id;
  friend bool operator==(const Frame &, const Frame &) = default;
};

enum class BlockerKind {
  none,
  blocks_simulation,
  exclusive_modal_blocks_input,
};

struct BlockingProof {
  BlockerKind kind = BlockerKind::none;
  bool verified = false;
  // Native mechanism, e.g. succession blocker or modal receiver vector.
  std::string source;
  std::uintptr_t receiver = 0;
  friend bool operator==(const BlockingProof &, const BlockingProof &) = default;
};

struct Bounds {
  double left = 0;
  double top = 0;
  double width = 0;
  double height = 0;
  friend bool operator==(const Bounds &, const Bounds &) = default;
};

struct CallbackIdentity {
  std::uint64_t vtable_module_rva = 0;
  std::uint64_t function_module_rva = 0;
  friend bool operator==(const CallbackIdentity &, const CallbackIdentity &) = default;
};

struct Choice {
  // Internal handles are never serialized as action authority.
  std::uintptr_t native_target = 0;
  std::string choice_id;
  std::string label;
  bool visible = false;
  bool enabled = false;
  bool is_choice = false;
  bool actionable_callback_verified = false;
  std::string candidate_basis;
  std::optional<Bounds> bounds;
  std::optional<std::uint32_t> rendered_index;
  std::uint64_t widget_vtable_module_rva = 0;
  std::vector<CallbackIdentity> callback_identities;
  friend bool operator==(const Choice &, const Choice &) = default;
};

struct Observation {
  Frame frame;
  BlockingProof blocking_proof;
  std::string window_id;
  std::string window_instance_id;
  std::string window_type;
  std::string source_identity;
  std::string executable_sha256;
  std::uint64_t root_vtable_module_rva = 0;
  std::string rendered_order_source;
  bool choices_complete = false;
  std::vector<Choice> choices;
  friend bool operator==(const Observation &, const Observation &) = default;
};

struct PublishedChoice {
  std::string choice_id;
  std::string label;
  std::string action_token;
  bool visible = false;
  bool enabled = false;
  bool is_choice = false;
  std::optional<Bounds> bounds;
  std::optional<std::uint32_t> rendered_index;
  std::uint64_t widget_vtable_module_rva = 0;
  std::vector<CallbackIdentity> callback_identities;
};

struct QueryResult {
  bool available = false;
  std::string unavailable_reason;
  std::string query_id;
  Frame frame;
  BlockingProof blocking_proof;
  std::string window_id;
  std::string window_instance_id;
  std::string window_type;
  std::string source_identity;
  std::string executable_sha256;
  std::uint64_t root_vtable_module_rva = 0;
  bool choices_complete = false;
  std::vector<PublishedChoice> choices;
};

struct SelectRequest {
  std::string query_id;
  std::string action_token;
  Frame expected_frame;
  std::string expected_window_instance_id;
};

struct SelectResult {
  bool accepted = false;
  std::string selected_choice_id;
  bool dispatch_attempted = false;
  bool dispatch_invoked = false;
  bool native_handled = false;
  bool verification_pending = false;
  std::string unavailable_reason;
};

// The adapter provides a cryptographically unpredictable nonce and a fresh
// owning-thread observation. It must consume the query before invoking once.
class Gate {
 public:
  using Nonce = std::function<std::string()>;
  using Observe = std::function<Observation()>;
  using Dispatch = std::function<bool(std::uintptr_t, bool &)>;

  QueryResult Query(const Observation &observation, const Nonce &nonce);
  SelectResult Select(const SelectRequest &request, const Observe &observe,
                      const Dispatch &dispatch);
  void Clear() noexcept;

 private:
  Observation pending_;
  std::vector<std::string> tokens_;
  std::string query_id_;
};

bool Qualified(const Observation &observation, std::string &reason);
} // namespace xar::mandatory_choice_v1
