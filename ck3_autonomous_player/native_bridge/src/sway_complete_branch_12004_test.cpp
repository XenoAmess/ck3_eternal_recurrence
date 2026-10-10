#include "xar_bridge/sway_complete_branch_12004.hpp"
#include "xar_bridge/ck3_12004.hpp"

#include <cstring>
#include <iostream>
#include <map>
#include <memory>
#include <new>
#include <stdexcept>

namespace {
using namespace xar::ck3_12002;
namespace current = xar::ck3_12004;
constexpr std::uintptr_t base = 0x140000000;
constexpr std::uint32_t actor = 29829;
constexpr std::uint32_t target = 34333;
constexpr std::uint32_t scheme = 134217986;
constexpr std::int32_t date = 53289936;
static_assert(sizeof(std::string) == 0x20);
std::size_t checks{}, lookups{}, inherited{}, identifiers{}, core_calls{};
bool changed_frame{};
std::map<std::int32_t, std::string> names{{101, "send_interface_toast"},
    {201, "owner"}, {202, "target"}, {203, "scheme"}};

void Check(bool value, const char *message) {
  ++checks;
  if (!value) throw std::runtime_error(message);
}
template <class T> void Put(void *object, std::size_t offset, const T &value) {
  std::memcpy(static_cast<std::byte *>(object) + offset, &value, sizeof(value));
}
template <class T> T Get(const void *object, std::size_t offset) {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset, sizeof(value));
  return value;
}
SwayExecutionScopeToken12002 Token(std::uint16_t type, std::uint32_t id) {
  return {type, 0xA5A5, 0x12345678,
          (std::uint64_t{0xFEDCBA98} << 32) | id};
}
void *Table() { return &names; }
const std::string *Command(std::int32_t id) {
  const auto found = names.find(id);
  return found == names.end() ? nullptr : &found->second;
}
struct View { const char *data; std::int32_t size; std::int32_t padding; };
std::int32_t *Identifier(void *table, std::int32_t *output, const void *input) {
  ++identifiers;
  if (table != &names) return nullptr;
  const auto view = Get<View>(input, 0);
  if (view.padding != 0 || view.size < 0) return nullptr;
  *output = -1;
  for (const auto &[id, name] : names)
    if (name == std::string_view(view.data, static_cast<std::size_t>(view.size))) {
      *output = id;
      break;
    }
  return output;
}
SwayExecutionScopeToken12002 *Lookup(const void *environment,
    SwayExecutionScopeToken12002 *output, std::int32_t id) {
  ++lookups;
  auto rows = Get<const std::byte *>(environment, 0);
  const auto count = Get<std::int32_t>(environment, 0x0C);
  for (std::int32_t i = 0; i < count; ++i) {
    const auto row = rows + static_cast<std::size_t>(i) * 0x20;
    if (Get<std::int32_t>(row, 0) == id) {
      *output = Get<SwayExecutionScopeToken12002>(row, 8);
      return output;
    }
  }
  const auto script = Get<const void *>(environment, 0x3D0);
  if (script != nullptr) {
    rows = Get<const std::byte *>(script, 0x18);
    for (std::int32_t i = 0; i < Get<std::int32_t>(script, 0x24); ++i) {
      const auto row = rows + static_cast<std::size_t>(i) * 0x18;
      if (Get<std::int32_t>(row, 0) == id) {
        *output = Get<SwayExecutionScopeToken12002>(row, 8);
        ++inherited;
        return output;
      }
    }
  }
  // Native missing-path semantics preserve padding DWORD+4.
  Put(output, 0, std::uint32_t{0});
  Put(output, 8, std::uint64_t{0});
  return output;
}
bool Core(const CoreBindings &, CoreSnapshotPrefix &output) noexcept {
  ++core_calls;
  output = {};
  output.clock.date_raw = date + (changed_frame && core_calls % 2 == 0 ? 24 : 0);
  output.clock.paused = false;
  output.map_ready = output.has_played_character = output.played_character_alive = true;
  output.played_character_id = static_cast<std::int32_t>(actor);
  return true;
}

struct Fixture {
  alignas(8) std::array<std::byte, 0xC0> effect{};
  alignas(8) std::array<std::byte, 0x50> scalar{};
  alignas(8) std::array<std::byte, 0x20> context{};
  alignas(8) std::array<std::byte, 0x3D8> environment{};
  alignas(8) std::array<std::byte, 0x28> script{};
  alignas(8) std::array<std::byte, 3 * 0x18> rows{};
  alignas(8) std::array<std::byte, 0x20> overlay{};
  SwayExecutionScopeToken12002 root = Token(4, actor);
  SwayExecutionScopeToken12002 owner = Token(4, actor);
  SwayExecutionScopeToken12002 target_token = Token(4, target);
  SwayExecutionScopeToken12002 scheme_token = Token(9, scheme);
  std::string *title{};
  SwayExecutionBindings12002 bindings;
  Fixture() : bindings(current::BindSwayCompleteBranchImage12004(base, current::kExecutableSha256)) {
    bindings.read_core_snapshot = &Core;
    bindings.get_global_command_key = &Command;
    bindings.get_script_identifier_table = &Table;
    bindings.lookup_script_identifier_id = &Identifier;
    bindings.lookup = &Lookup;
    Put(effect.data(), 0, base + current::kSwayExecutionVtableRvas12004[1]);
    Put(effect.data(), 8, std::int32_t{101});
    Put(effect.data(), 0x60, base + current::kSwayExecutionTitleWrapperRva12004);
    Put(effect.data(), 0x68, std::uint16_t{4});
    Put(effect.data(), 0x70, scalar.data());
    Put(scalar.data(), 0, base + current::kSwayExecutionScalarRva12004);
    title = ::new(scalar.data() + 0x30) std::string("sway_complete");
    Put(context.data(), 0, &root);
    Put(context.data(), 0x18, environment.data());
    Put(environment.data(), 0x3D0, script.data());
    Put(script.data(), 0x18, rows.data());
    Put(script.data(), 0x24, std::int32_t{3});
    Put(rows.data(), 0, std::int32_t{201});
    Put(rows.data(), 8, owner);
    Put(rows.data(), 0x18, std::int32_t{202});
    Put(rows.data(), 0x20, target_token);
    Put(rows.data(), 0x30, std::int32_t{203});
    Put(rows.data(), 0x38, scheme_token);
  }
  ~Fixture() { std::destroy_at(title); }
  SwayExecutionCaptureResult12002 Capture(current::SwayCompleteBranchSource12004 &out) {
    core_calls = 0;
    return current::CaptureSwayCompleteBranch12004(bindings, effect.data(), context.data(), out);
  }
};
} // namespace

int main() {
  try {
    Fixture f;
    current::SwayCompleteBranchSource12004 source;
    Check(f.bindings.enabled && !current::BindSwayCompleteBranchImage12004(
          base, xar::ck3_12002::kExecutableSha256).enabled,
          "admitted actual4 binder rejects the historical02 image");
    Check(f.Capture(source) == SwayExecutionCaptureResult12002::captured &&
          identifiers == 3 && lookups == 3 && inherited == 3,
          "completion toast uses named ID ABI and inherited native scope callback");
    Check(source.date_raw == date && source.actor_character_id == actor &&
          source.target_character_id == target && source.scheme_id == scheme &&
          source.root == f.root && source.owner == f.owner &&
          source.target == f.target_token && source.scheme == f.scheme_token,
          "completion100 input copies full actor/target/instance and all16-byte tokens");
    Check(source.executing_input_observed && !source.message_enqueue_observed &&
          !source.material_effect_observed && !source.native_terminal_state_observed,
          "authored executing input supplies no notification/material/native-end attribution");
    const auto copied = source;
    Put(f.rows.data(), 0x38, Token(9, scheme ^ 0x01000000u));
    *f.title = "released_after_capture";
    Check(copied.scheme == f.scheme_token && copied.scheme_id == scheme,
          "owned source retains original generation when producer operands change");
    Put(f.rows.data(), 0x38, f.scheme_token);
    *f.title = "sway_complete_extra";
    Check(f.Capture(source) == SwayExecutionCaptureResult12002::ignored &&
          !source.executing_input_observed, "near-prefix title does not become completion100");
    *f.title = "sway_complete";
    names[101] = "send_interface_message";
    Check(f.Capture(source) == SwayExecutionCaptureResult12002::ignored,
          "hidden-phase message command is a separate branch");
    names[101] = "send_interface_toast";
    Put(f.effect.data(), 0, base + current::kSwayExecutionVtableRvas12004[0]);
    Check(f.Capture(source) == SwayExecutionCaptureResult12002::ignored,
          "message class cannot stand in for authored toast class");
    Put(f.effect.data(), 0, base + current::kSwayExecutionVtableRvas12004[1]);
    Put(f.scalar.data(), 0x28, std::uintptr_t{1});
    Check(f.Capture(source) == SwayExecutionCaptureResult12002::unavailable,
          "native renderer delegate takes precedence over plain scalar title");
    Put(f.scalar.data(), 0x28, std::uintptr_t{0});
    Put(f.rows.data(), 8, Token(4, actor ^ 0x01000000u));
    Check(f.Capture(source) == SwayExecutionCaptureResult12002::unavailable,
          "same-index owner from another full generation does not join actor");
    Put(f.rows.data(), 8, f.owner);
    Put(f.script.data(), 0x24, std::int32_t{2});
    Check(f.Capture(source) == SwayExecutionCaptureResult12002::unavailable,
          "missing named scheme cannot manufacture a completion input");
    Put(f.script.data(), 0x24, std::int32_t{3});
    Put(f.overlay.data(), 0, std::int32_t{202});
    const auto override_target = Token(4, target ^ 0x01000000u);
    Put(f.overlay.data(), 8, override_target);
    Put(f.environment.data(), 0, f.overlay.data());
    Put(f.environment.data(), 0x0C, std::int32_t{1});
    Check(f.Capture(source) == SwayExecutionCaptureResult12002::captured &&
          source.target == override_target,
          "Env32 override precedes inherited24 rather than copying stale target");
    changed_frame = true;
    Check(f.Capture(source) == SwayExecutionCaptureResult12002::unavailable &&
          !source.executing_input_observed, "changed native actor/date frame is not recorded");
    changed_frame = false;
    f.bindings.lookup = nullptr;
    Check(f.Capture(source) == SwayExecutionCaptureResult12002::unavailable,
          "completion leaf has no legacy Env32-only production substitute");
    std::cout << "PASS " << checks << " checks; new actual4 completion100 toast executing input, "
        "inherited scopes and full copied tokens; fixture operands; end/material/enqueue remain false\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "FAIL " << error.what() << '\n';
    return 1;
  }
}
