#include "Native202Api.hpp"
#include <iostream>
#include <exception>
#include <string>
#include <stdexcept>
#include <vector>
#include <cstdint>
#include <filesystem>

int main(int argc, char* argv[]) {
    if (argc != 3) {
        std::cerr << "Usage: Native202Main <reverse_path> <caller_path>\n";
        return 1;
    }
    try {
        std::filesystem::path reversePath(argv[1]);
        std::filesystem::path callerPath(argv[2]);
        auto reverse = reverse4220aa4_202::readReverse(reversePath);
        auto caller = reverse4220aa4_202::readCaller(callerPath);
        auto cases = reverse4220aa4_202::frozenCases();
        auto result = reverse4220aa4_202::executeOriginal(reverse, caller, cases);
        reverse4220aa4_202::writeRun(std::cout, result);
    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << "\n";
        return 1;
    }
    return 0;
}