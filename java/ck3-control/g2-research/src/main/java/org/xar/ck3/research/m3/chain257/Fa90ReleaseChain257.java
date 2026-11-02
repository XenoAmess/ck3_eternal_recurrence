package org.xar.ck3.research.m3.chain257;

import org.xar.ck3.research.m3.callee246.Callee68d4Memory246;
import org.xar.ck3.research.m3.callee246.Callee68fcApi246;
import org.xar.ck3.research.m3.callee246.Callee68d4From68fcBinding247;
import org.xar.ck3.research.m3.callee246.Callee68fcFromFa90Binding246;
import org.xar.ck3.research.m3.fa90245.Fa90Api245;
import org.xar.ck3.research.m3.fa90245.Fa90Target424FA90;

public final class Fa90ReleaseChain257 {
    private Fa90ReleaseChain257() { }

    public static void execute(
            Callee68d4Memory246 memory,
            Fa90Api245.Ports remainder,
            Fa90Api245.Input input) {
        if (memory == null) {
            throw new RuntimeException("memory");
        }
        if (remainder == null) {
            throw new RuntimeException("remainder");
        }
        if (input == null) {
            throw new RuntimeException("input");
        }

        long base = input.moduleBase();

        Callee68fcApi246.Ports child = Callee68d4From68fcBinding247.bind(base, memory);
        Fa90Api245.Ports bound = Callee68fcFromFa90Binding246.bind(base, memory, child, remainder);

        Fa90Target424FA90.execute(memory, bound, input);
    }
}