#include "xar_bridge/conception_value_arithmetic_12004.hpp"
#include <limits>
using namespace xar::ck3_12004;
// The compiler evaluates the actual shared production helper. No test EXE,
// mock implementation or replacement arithmetic path is produced.
static_assert(MultiplyConceptionRaw12004(100000, 50000) == 50000);
static_assert(MultiplyConceptionRaw12004(-100000, 50000) == -50000);
static_assert(MultiplyConceptionRaw12004(100000, -50000) == -50000);
static_assert(MultiplyConceptionRaw12004(99999, 1) == 0);
static_assert(MultiplyConceptionRaw12004(-99999, 1) == 0);
static_assert(MultiplyConceptionRaw12004(3037000499LL, 3037000499LL) == 92233720309262LL);
static_assert(MultiplyConceptionRaw12004(-3037000499LL, 3037000499LL) == -92233720309262LL);
static_assert(MultiplyConceptionRaw12004(std::numeric_limits<std::int64_t>::max(), 100000) == std::numeric_limits<std::int64_t>::max());
static_assert(MultiplyConceptionRaw12004(std::numeric_limits<std::int64_t>::min(), 100000) == std::numeric_limits<std::int64_t>::min());
static_assert(MultiplyConceptionRaw12004(std::numeric_limits<std::int64_t>::min(), 0) == 0);
static_assert(ConceptionAdjustedAgeRaw12004(35, 49999) == 35);
static_assert(ConceptionAdjustedAgeRaw12004(35, 50000) == 34);
static_assert(ConceptionAdjustedAgeRaw12004(35, -49999) == 35);
static_assert(ConceptionAdjustedAgeRaw12004(35, -50000) == 36);
static_assert(ConceptionAdjustedAgeRaw12004(-1, 0) == -1);
