package org.xar.ck3.control.application.planning.finance;

import java.util.Arrays;
import java.util.List;
import java.util.Set;
import java.util.stream.Stream;

/** Select new actual worlds without replaying already-green worlds; default CI requires all five final worlds. */
public final class FactionNativeWorlds {
    private FactionNativeWorlds() { }
    public static Stream<String> worlds() {
        List<String> selected=Arrays.asList(System.getProperty("xar.faction.native.worlds","faction-zero-final,faction-min,generation81,faction-high,mixed").split(",",-1));
        if(selected.isEmpty()||!Set.of("faction-zero-final","faction-min","generation81","faction-high","mixed").containsAll(selected)||selected.stream().distinct().count()!=selected.size())throw new IllegalArgumentException("explicit unique retained Native faction worlds required");
        return selected.stream();
    }
}
