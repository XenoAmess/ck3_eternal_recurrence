#include <filesystem>
#include <iostream>

void RunAfterGatedTailFixture(const std::filesystem::path &);

int main(int argc, char **argv) {
  if (argc != 2) return 2;
  const std::filesystem::path directory(argv[1]);
  std::filesystem::create_directories(directory);
  RunAfterGatedTailFixture(directory);
  std::cout << "person after gated tail fixtures GREEN\n";
  return 0;
}
