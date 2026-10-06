#include <filesystem>
#include <iostream>

void RunFollowing2921350Fixture(const std::filesystem::path &);
int main(int argc, char **argv) {
  if (argc != 2) return 2;
  const std::filesystem::path directory(argv[1]);
  std::filesystem::create_directories(directory);
  RunFollowing2921350Fixture(directory);
  std::cout << "person following2921350 source input fixtures GREEN\n";
  return 0;
}
