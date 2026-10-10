#include <exception>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string_view>

void RunLifestyleDescriptorFrontierFreshCases12004();
int RunLifestyleTriggerPreferredKind12004NewCases();
bool VerifyStockPerkTriggerFrontierCurrentQuery12004();
std::string_view StockPerkTriggerFrontierCurrentQueryWire12004();

int main(int argc, char **argv) {
  try {
    if (argc != 2) throw std::runtime_error("one owned source-wire output path is required");
    RunLifestyleDescriptorFrontierFreshCases12004();
    std::cout << "lifestyle_trigger_frontier:descriptor 14 new checks GREEN\n" << std::flush;
    const auto preferred_checks = RunLifestyleTriggerPreferredKind12004NewCases();
    if (preferred_checks != 31) throw std::runtime_error("preferred-kind new check count differs");
    std::cout << "lifestyle_trigger_frontier:preferred 31 new checks GREEN\n" << std::flush;
    // The one new stock export runs three new copied-target queries. Its host
    // reaches all four lane adapters; all returned output planes stay null.
    if (!VerifyStockPerkTriggerFrontierCurrentQuery12004())
      throw std::runtime_error("new current-query copied-target join failed");
    std::cout << "lifestyle_trigger_frontier:stock 3 new query cases GREEN\n" << std::flush;
    const auto wire = StockPerkTriggerFrontierCurrentQueryWire12004();
    if (wire.empty() || wire == "null") throw std::runtime_error("new owned source wire unavailable");
    std::ofstream output(argv[1], std::ios::binary | std::ios::trunc);
    if (!output) throw std::runtime_error("owned source-wire output could not be opened");
    output.write(wire.data(), static_cast<std::streamsize>(wire.size()));
    output.close();
    if (!output) throw std::runtime_error("owned source-wire output write failed");
    std::cout << "lifestyle_trigger_frontier:3/3 NEW GREEN; owned-memory output only\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "lifestyle_trigger_frontier:RED " << error.what() << '\n';
    return 1;
  }
}
