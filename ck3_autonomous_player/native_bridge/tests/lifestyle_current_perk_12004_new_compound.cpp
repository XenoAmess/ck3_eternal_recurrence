#include "xar_bridge/lifestyle_character_scope_12004.hpp"
#include <exception>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <string_view>

bool RunLifestyleSelectedPerkConnectedNewCase12004();
bool RunLifestyleOwnedPerkCollection2919340NewCases12004(std::string &failure);
bool RunLifestylePerkTruthProducer12004NewCases();
bool RunLifestylePerkFinalNaturalFocus12004();
bool VerifyStockPerkCurrentQuerySourceJoin12004();
std::string_view StockPerkCurrentQuerySourceWire12004();
namespace xar::ck3_12004 {
void RunSourceTriggerRootScopeGate12004Cases();
void VerifyTriggerScopeTableProvider3795A60ConnectedCases12004();
void RunSourceAutoAcceptTriggerConditionGenericFocus12004();
}

int main(int argc, char **argv) {
  try {
    if (argc != 2)
      throw std::runtime_error("one source wire output path is required");
    const auto completed = [](unsigned fragment) {
      std::cout << "new_m5_fragment_completed=" << fragment << std::endl;
    };
    std::string failure;
    if (!RunLifestyleOwnedPerkCollection2919340NewCases12004(failure))
      throw std::runtime_error("new owned collection fragment: " + failure);
    completed(1);
    if (xar::ck3_12004::lifestyle::RunLifestyleCharacterScope9D78D0NewCases12004() != 4)
      throw std::runtime_error("new Character scope fragment failed");
    completed(2);
    xar::ck3_12004::RunSourceTriggerRootScopeGate12004Cases();
    completed(3);
    xar::ck3_12004::VerifyTriggerScopeTableProvider3795A60ConnectedCases12004();
    completed(4);
    xar::ck3_12004::RunSourceAutoAcceptTriggerConditionGenericFocus12004();
    completed(5);
    if (!RunLifestylePerkTruthProducer12004NewCases())
      throw std::runtime_error("new truth input fragment failed");
    completed(6);
    if (!RunLifestylePerkFinalNaturalFocus12004())
      throw std::runtime_error("new final source connector fragment failed");
    completed(7);
    if (!RunLifestyleSelectedPerkConnectedNewCase12004())
      throw std::runtime_error("new selected-perk connected fragment failed");
    completed(8);
    if (!VerifyStockPerkCurrentQuerySourceJoin12004())
      throw std::runtime_error("new current-query source join fragment failed");
    completed(9);
    const auto wire = StockPerkCurrentQuerySourceWire12004();
    if (wire.empty())
      throw std::runtime_error("current-query production source wire is empty");
    std::ofstream output(argv[1], std::ios::binary);
    output.write(wire.data(), static_cast<std::streamsize>(wire.size()));
    output.close();
    if (!output)
      throw std::runtime_error("current-query source wire output failed");
    std::cout << "lifestyle_current_perk_12004_new_compound: GREEN "
                 "new_fragments=9 whole_truth_qualified=false live_credit=false\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "lifestyle_current_perk_12004_new_compound: RED "
              << error.what() << '\n';
    return 1;
  }
}
