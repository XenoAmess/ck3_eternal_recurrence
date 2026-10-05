#include <filesystem>
#include <iostream>

void RunGatedTemporaryTailFixture(const std::filesystem::path &);

int main(int argc, char **argv) {
  if (argc != 2) return 2;
  const std::filesystem::path directory(argv[1]);
  std::filesystem::create_directories(directory);
  RunGatedTemporaryTailFixture(directory);
  std::cout << "person gated temporary tail fixtures GREEN\n";
  return 0;
}
