#include "Native205Api.hpp"
#include <iostream>
#include <string>
#include <vector>

int main(int argc, char* argv[]) {
    if (argc != 5) {
        std::cerr << "Usage: " << argv[0] << " <upper_path> <range_path> <add_path> <literal_path>" << std::endl;
        return 1;
    }

    try {
        std::filesystem::path upperPath(argv[1]);
        std::filesystem::path rangePath(argv[2]);
        std::filesystem::path addPath(argv[3]);
        std::filesystem::path literalPath(argv[4]);

        auto upper = upper172doublegrowth205::readUpper(upperPath);
        auto range = upper172doublegrowth205::readRange(rangePath);
        auto add = upper172doublegrowth205::readAdd(addPath);
        auto literal = upper172doublegrowth205::readLiteral(literalPath);
        auto cases = upper172doublegrowth205::frozenCases();

        auto result = upper172doublegrowth205::executeOriginal(upper, range, add, literal, cases);

        upper172doublegrowth205::writeRun(std::cout, result);
        std::cout << std::endl;

        return 0;
    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << std::endl;
        return 1;
    }
}