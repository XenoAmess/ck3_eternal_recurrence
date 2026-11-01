#include "Native203Api.hpp"
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

int main(int argc, char* argv[]) {
    if (argc != 5) {
        std::cerr << "Usage: Native203Main <upper351> <caller126> <reverse194> <literal4>\n";
        return 1;
    }
    try {
        std::filesystem::path upperPath(argv[1]);
        std::filesystem::path callerPath(argv[2]);
        std::filesystem::path reversePath(argv[3]);
        std::filesystem::path literalPath(argv[4]);

        auto upper = copy4knownreverse203::readUpper(upperPath);
        auto caller = copy4knownreverse203::readCaller(callerPath);
        auto reverse = copy4knownreverse203::readReverse(reversePath);
        auto literal = copy4knownreverse203::readLiteral(literalPath);
        auto cases = copy4knownreverse203::frozenCases();

        auto result = copy4knownreverse203::executeOriginal(upper, caller, reverse, literal, cases);
        copy4knownreverse203::writeRun(std::cout, result);
    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << "\n";
        return 1;
    }
    return 0;
}