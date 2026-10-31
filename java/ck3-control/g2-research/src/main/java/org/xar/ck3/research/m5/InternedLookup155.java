package org.xar.ck3.research.m5;

import java.util.Map;
import java.util.OptionalInt;
import org.xar.ck3.research.m5.InternedLookup155Api.Calls;
import org.xar.ck3.research.m5.InternedLookup155Api.Entry;
import org.xar.ck3.research.m5.InternedLookup155Api.Memory;
import org.xar.ck3.research.m5.InternedPointerSelection.Route;
import org.xar.ck3.research.m5.InternedPointerSelection.Selection;
import org.xar.ck3.research.m5.InternedPointerSelection.Snapshot;

/** Owner implementation after two rejected model rounds; owned ports, normal paths only. */
public final class InternedLookup155 {
    private InternedLookup155() { }

    public static long execute(Entry entry, Memory memory, Calls calls) {
        long image = entry.imageBaseBits();
        int key = entry.nativeStringKey().bits();
        long table = memory.readQword(image + 0x5CBEDE8L);
        int old = memory.lockedXaddDword(table, 2);
        while ((old & 1) != 0) {
            memory.lockedXaddDword(table, -2);
            int observed = memory.readDword(table);
            while ((observed & 1) != 0) {
                calls.pauseSpin();
                observed = memory.readDword(table);
            }
            old = memory.lockedXaddDword(table, 2);
        }

        Snapshot snapshot = new Snapshot(OptionalInt.empty(), Map.of());
        Selection pending = InternedPointerSelection.select(key, snapshot);
        if (pending.route() == Route.NEEDS_UPPER_BOUND) {
            snapshot = new Snapshot(OptionalInt.of(memory.readDword(table + 0x54L)), Map.of());
            pending = InternedPointerSelection.select(key, snapshot);
        }
        if (pending.route() == Route.NEEDS_SLOT) {
            long slots = memory.readQword(table + 0x48L);
            long pointer = memory.readQword(slots + ((long) key) * 8L);
            snapshot = new Snapshot(snapshot.upperInclusive(), Map.of(key, pointer));
        }
        memory.lockedXaddDword(table, -2);
        Selection selected = InternedPointerSelection.select(key, snapshot);
        if (selected.route() == Route.SLOT_POINTER) {
            return selected.observedPointerBits().getAsLong();
        }

        long tlsArray = calls.readGsQword58();
        long tlsBlock = memory.readQword(tlsArray);
        int tlsEpoch = memory.readDword(tlsBlock + 0x10L);
        long guardAddress = image + 0x5DC1124L;
        long fallback = image + 0x5DC1128L;
        int guard = memory.readDword(guardAddress);
        if (guard <= tlsEpoch) {
            return fallback;
        }
        calls.call4223A84(guardAddress);
        if (memory.readDword(guardAddress) != -1) {
            return fallback;
        }
        memory.writeQword(fallback, 0L);
        memory.writeQword(image + 0x5DC1140L, 15L);
        memory.writeQword(image + 0x5DC1138L, 7L);
        int fourBytes = memory.readDword(image + 0x472C488L);
        memory.writeDword(fallback, fourBytes);
        int twoBytes = memory.readUnsignedWord(image + 0x472C48CL);
        memory.writeWord(fallback + 4L, twoBytes);
        int oneByte = memory.readUnsignedByte(image + 0x472C48EL);
        memory.writeByte(fallback + 6L, oneByte);
        memory.writeByte(fallback + 7L, 0);
        calls.call4223F24(image + 0x43D7570L);
        calls.call4223A24(guardAddress);
        return fallback;
    }
}
