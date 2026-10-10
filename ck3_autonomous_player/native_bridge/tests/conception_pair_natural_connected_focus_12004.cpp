#include "xar_bridge/conception_pair_passive_12004.hpp"
#include "xar_bridge/conception_pair_threshold_consumer_12004.hpp"
#include <exception>
#include <iostream>

// Central10 builds and runs this new compound once. All native originals in
// these fixtures are typed stand-ins or source-bound owned-memory callers.
int main() {
  using namespace xar::ck3_12004;
  try {
    if (!RunConceptionSamplePassiveFixture12004()) return 1;
    if (!RunConceptionPairProviderPassiveFixture12004()) return 2;
    VerifyConceptionThreshold12004ConnectedCases();
    if (!RunConceptionPairPassiveOwnedFixture12004()) return 3;
    std::cout << "native71-conception-connected: passed\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n';
    return 4;
  }
}
