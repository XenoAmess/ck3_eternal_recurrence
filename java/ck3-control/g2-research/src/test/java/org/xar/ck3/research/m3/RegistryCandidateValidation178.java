package org.xar.ck3.research.m3;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

/** First finite checks of owner source-derived literals; the book owner saw target source. */
public final class RegistryCandidateValidation178 {
    private RegistryCandidateValidation178() { }

    public static void main(String[] args) {
        List<RegistryRankBook178.Case> cases = RegistryRankBook178.cases();
        for (RegistryRankBook178.Case c : cases) {
            RegistryMemory176 memory = new RegistryMemory176(Map.of());
            List<String> expectedReads = new ArrayList<>();
            long row = c.begin();
            for (RegistryRankBook178.Bytes flags : c.entries()) {
                memory.seed8(row + 0x22L, flags.at22());
                memory.seed8(row + 0x21L, flags.at21());
                memory.seed8(row + 0x20L, flags.at20());
                expectedReads.add("R8:" + Long.toHexString(row + 0x22L));
                expectedReads.add("R8:" + Long.toHexString(row + 0x21L));
                expectedReads.add("R8:" + Long.toHexString(row + 0x20L));
                row += 0x28L;
            }
            Map<Long, Byte> before = memory.bytes();
            long selected = RegistryCandidateSelect178.select(memory, c.begin(), row);
            if (selected != c.expectedSelected()) {
                throw new AssertionError(c.id() + ": selected address mismatch");
            }
            if (!memory.events().equals(expectedReads)) {
                throw new AssertionError(c.id() + ": exact ordered byte reads mismatch");
            }
            if (!memory.bytes().equals(before)) {
                throw new AssertionError(c.id() + ": storage changed");
            }
        }
        System.out.println("rank_cases=" + cases.size() + " semantic_checks=" + cases.size() * 3
                + " Native=0 Game=0 old_green=0");
    }
}
