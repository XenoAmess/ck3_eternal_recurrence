#include <iostream>

bool RunActivityPlannerStart12004Fixture();
bool RunActivityGuestCost12004Fixture();
bool RunActivityHostedResources12004Fixture();

int main() {
  if (!RunActivityPlannerStart12004Fixture()) {
    std::cerr << "actual4 planner/start fixture failed\n";
    return 1;
  }
  if (!RunActivityGuestCost12004Fixture()) {
    std::cerr << "actual4 guest/cost/opinion fixture failed\n";
    return 1;
  }
  if (!RunActivityHostedResources12004Fixture()) {
    std::cerr << "actual4 hosted/resource/trait binding fixture failed\n";
    return 1;
  }
  std::cout << "actual4 Activity migration: three production fixture groups GREEN\n";
  return 0;
}
