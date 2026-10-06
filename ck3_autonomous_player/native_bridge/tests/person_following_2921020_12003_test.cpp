#include <filesystem>
#include <iostream>

void RunFollowing2921020Fixture(const std::filesystem::path &);

int main(int argc, char **argv) {
  if (argc != 2) return 2;
  const std::filesystem::path directory(argv[1]);
  std::filesystem::create_directories(directory);
  RunFollowing2921020Fixture(directory);
  std::cout << "person following2921020 owner runs and two-PC raw fixtures GREEN\n";
  return 0;
}
