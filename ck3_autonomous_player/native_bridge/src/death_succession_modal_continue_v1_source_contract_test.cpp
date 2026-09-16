#include <fstream>
#include <iostream>
#include <iterator>
#include <string>
#include <string_view>

namespace {

std::string ReadAll(const char *path) {
  std::ifstream input(path, std::ios::binary);
  return {std::istreambuf_iterator<char>(input),
          std::istreambuf_iterator<char>()};
}

bool Contains(std::string_view source, std::string_view token) {
  return source.find(token) != std::string_view::npos;
}

} // namespace

int main(int argc, char **argv) {
  if (argc != 2) {
    std::cerr << "expected death-succession modal native source path\n";
    return 1;
  }
  const auto source = ReadAll(argv[1]);
  if (source.empty()) {
    std::cerr << "death-succession modal native source is unreadable\n";
    return 1;
  }
  if (!Contains(source, "kControllerCloseVslot = 0x88") ||
      !Contains(source, "kControllerCloseTargetRva = 0xFD4870") ||
      !Contains(source,
                "reinterpret_cast<ControllerCloseV1>(target)(controller)") ||
      Contains(source, "kControllerCloseVslot = 0x20") ||
      Contains(source, "kControllerCloseTargetRva = 0x1006FB0") ||
      Contains(source, "0x25EA9C0")) {
    std::cerr << "death-succession Close dispatch source contract drifted\n";
    return 1;
  }
  return 0;
}
