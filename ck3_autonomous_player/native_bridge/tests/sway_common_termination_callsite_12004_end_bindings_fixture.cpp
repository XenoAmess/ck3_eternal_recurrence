#include "xar_bridge/sway_end_invocation_12004.hpp"

// Keep all actual capture/forward/readers. Rename this one pure definition so
// the test can supply owned memory at native acquisition without a Game image.
#define BindSwayEndInvocationImage12004 SwayFixtureBindEndImage12004
#include "../src/sway_end_invocation_12004.cpp"
#undef BindSwayEndInvocationImage12004
