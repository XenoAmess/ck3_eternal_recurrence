package org.xar.ck3.control.g2.common.nativecore.task;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.Assertions;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class NativeIdlerConstructionTest {

    // --- Constants from Host ---
    private static final long PAGE_BYTES = 4096L;
    private static final long ALLOCATION_BYTES = 8192L;

    private static final long[] SYMBOL_RVAS = {
        0x44BC418L, 0x54DF888L, 0x54DF890L, 0x44BC3F0L, 0x54DF760L,
        0x54E0928L, 0x54E0930L, 0x54E0938L, 0x54E0940L, 0x54E0948L,
        0x5434F38L, 0x5434F50L, 0x5434F48L, 0x5CBF858L
    };

    private static final long[] CAPACITIES = {
        0L, 15L, 16L, 17L, Long.MIN_VALUE, -1L, 16L, 0L
    };

    private static final int[] LENGTHS = {
        0, 7, -1, Integer.MIN_VALUE, Integer.MAX_VALUE, -32, 23, -128
    };

    // --- Helper Classes ---

    private record Event(String kind, long a, long b, long c, long d) { }

    private static final class Scenario implements NativeIdlerConstruction.Symbols, NativeIdlerConstruction.Calls {
        private final Map<Long, Long> symbols = new HashMap<>();
        private final List<Event> events = new ArrayList<>();

        // Bounded byte storage simulation
        private final Map<Long, byte[]> regions = new HashMap<>();

        private int caseId;
        private int allocationCount;
        private int checks;

        // Synthetic addresses
        private long objectAddr;
        private long initialHAddr;
        private long helperHAddr;
        private long headerHAddr;
        private long inputKAddr;
        private long separateSmallAddr;
        private long firstStorageAddr;
        private long headerAddr;
        private long childResultAddr;
        private long registryAddr;
        private long lookupResultAddr;
        private long globalReceiverAddr;
        private long globalVtableAddr;
        private long changedO50Addr;
        private long oldStringAddr;
        private long freshStringAddr;
        private long allocationFallbackAddr;

        Scenario() {
            // Allocate synthetic addresses
            objectAddr = 0x1000L;
            initialHAddr = 0x2000L;
            helperHAddr = 0x3000L;
            headerHAddr = 0x4000L;
            inputKAddr = 0x5000L;
            separateSmallAddr = 0x6000L;
            firstStorageAddr = 0x7000L;
            headerAddr = 0x8000L;
            childResultAddr = 0x9000L;
            registryAddr = 0xA000L;
            lookupResultAddr = 0xB000L;
            globalReceiverAddr = 0xC000L;
            globalVtableAddr = 0xD000L;
            changedO50Addr = 0xE000L;
            oldStringAddr = 0xF000L;
            freshStringAddr = 0x10000L;
            allocationFallbackAddr = 0x11000L;

            // Map RVAs to synthetic addresses
            for (int i = 0; i < SYMBOL_RVAS.length; i++) {
                symbols.put(SYMBOL_RVAS[i], 0x20000L + (i * 0x40L));
            }

            // Initialize regions
            initRegion(objectAddr, 0x98L);
            initRegion(initialHAddr, 8L);
            initRegion(helperHAddr, 8L);
            initRegion(headerHAddr, 8L);
            initRegion(inputKAddr, 8L);
            initRegion(separateSmallAddr, 8L);
            initRegion(firstStorageAddr, 0xB0L);
            initRegion(headerAddr, 0xB0L);
            initRegion(childResultAddr, 16L);
            initRegion(registryAddr, 32L);
            initRegion(lookupResultAddr, 16L);
            initRegion(globalReceiverAddr, 8L);
            initRegion(globalVtableAddr, 0x38L);
            initRegion(changedO50Addr, 8L);
            initRegion(oldStringAddr, 64L);
            initRegion(freshStringAddr, 64L);
            initRegion(allocationFallbackAddr, 0x200L);

            for (int i = 0; i < SYMBOL_RVAS.length; i++) {
                initRegion(0x20000L + (i * 0x40L), 0x40L);
            }
        }

        private void initRegion(long address, long size) {
            regions.put(address, new byte[(int) size]);
        }

        private long regionStart(long address, int bytes) {
            for (Map.Entry<Long, byte[]> entry : regions.entrySet()) {
                long offset = address - entry.getKey();
                if (offset >= 0L && bytes >= 0 && bytes <= entry.getValue().length
                        && offset <= entry.getValue().length - bytes) {
                    return entry.getKey();
                }
            }
            throw new IllegalArgumentException("Address outside owned memory: "
                    + Long.toHexString(address) + " width=" + bytes);
        }

        private long readPointer(long address) {
            long start = regionStart(address, 8);
            byte[] region = regions.get(start);
            int offset = (int) (address - start);
            long value = 0L;
            for (int i = 0; i < 8; i++) {
                value |= (long) (region[offset + i] & 0xFF) << (8 * i);
            }
            return value;
        }

        private int readInt32(long address) {
            long start = regionStart(address, 4);
            byte[] region = regions.get(start);
            int offset = (int) (address - start);
            int value = 0;
            for (int i = 0; i < 4; i++) {
                value |= (region[offset + i] & 0xFF) << (8 * i);
            }
            return value;
        }

        private void writeInt32(long address, int value) {
            long start = regionStart(address, 4);
            byte[] region = regions.get(start);
            int offset = (int) (address - start);
            for (int i = 0; i < 4; i++) {
                region[offset + i] = (byte) (value >>> (8 * i));
            }
        }

        private void writeInt64(long address, long value) {
            long start = regionStart(address, 8);
            byte[] region = regions.get(start);
            int offset = (int) (address - start);
            for (int i = 0; i < 8; i++) {
                region[offset + i] = (byte) (value >>> (8 * i));
            }
        }

        public long address(long rva) {
            Long result = symbols.get(rva);
            if (result == null) {
                throw new IllegalArgumentException("Unmapped literal RVA " + Long.toHexString(rva));
            }
            return result.longValue();
        }

        private void note(boolean condition, String message) {
            checks++;
            if (!condition) {
                throw new AssertionError("case=" + caseId + " " + message);
            }
        }

        private void check(boolean condition, String message) {
            checks++;
            if (!condition) {
                throw new AssertionError("case=" + caseId + " " + message);
            }
        }

        private boolean mutateBeforeHelper() {
            return (caseId & 1) != 0;
        }

        private boolean mutateBeforeHeader() {
            return (caseId & 2) != 0;
        }

        private boolean finalGlobalPresent() {
            return (caseId & 4) != 0;
        }

        private boolean aliasSmall() {
            return (caseId & 3) == 0;
        }

        private long small() {
            return aliasSmall() ? objectAddr + 0x20L : separateSmallAddr;
        }

        private long expectedHelperH() {
            if (mutateBeforeHelper()) {
                return helperHAddr;
            }
            return aliasSmall() ? address(0x44BC3F0L) : initialHAddr;
        }

        private long expectedHeaderH() {
            return mutateBeforeHeader() ? headerHAddr : expectedHelperH();
        }

        private long expectedNameData() {
            return Long.compareUnsigned(CAPACITIES[caseId], 16L) >= 0
                    ? freshStringAddr : address(0x5434F38L);
        }

        void prepare(int id) {
            caseId = id;
            allocationCount = 0;
            events.clear();
            checks = 0;

            // Reset all regions to zero
            for (byte[] region : regions.values()) {
                for (int i = 0; i < region.length; i++) {
                    region[i] = 0;
                }
            }

            // Seed globals
            writeInt64(globalReceiverAddr, globalVtableAddr);
            writeInt64(globalVtableAddr + 0x30L, address(0x5CBF858L)); // virtualStub address
            writeInt64(address(0x5434F38L), oldStringAddr);
            writeInt32(address(0x5434F48L), 0x12345678 + id);
            writeInt64(address(0x5434F50L),
                    Long.compareUnsigned(CAPACITIES[id], 16L) >= 0 ? 0L : 16L);
            writeInt64(address(0x5CBF858L),
                    finalGlobalPresent() ? 0L : globalReceiverAddr);
        }

        public long allocate(long size) {
            allocationCount++;
            long result;
            if (allocationCount == 1) {
                note(size == 8L, "first allocation size");
                result = small();
            } else if (allocationCount == 2) {
                note(size == 0xB0L, "second allocation size");
                result = firstStorageAddr;
                if (mutateBeforeHelper()) {
                    writeInt64(objectAddr + 0x20L, helperHAddr);
                }
            } else if (allocationCount == 3) {
                note(size == 0xB0L, "third allocation size");
                note(readPointer(objectAddr + 0x20L) == expectedHelperH(),
                        "O20 before header allocation mutation");
                result = headerAddr;
                if (mutateBeforeHeader()) {
                    writeInt64(objectAddr + 0x20L, headerHAddr);
                }
            } else {
                note(false, "unexpected allocator invocation");
                result = allocationFallbackAddr;
            }
            events.add(new Event("allocate", size, result, 0L, 0L));
            return result;
        }

        public long constructChild(long storage, long freshH, int zero) {
            events.add(new Event("constructChild", storage, freshH, zero, childResultAddr));
            note(storage == firstStorageAddr, "helper storage");
            note(freshH == expectedHelperH(), "helper fresh O20");
            note(zero == 0, "helper R8D zero");
            writeInt64(firstStorageAddr, freshH);
            writeInt64(firstStorageAddr + 8L, 0x1122334455667700L + caseId);
            return childResultAddr;
        }

        public long getRegistry(long architecturalRcx) {
            events.add(new Event("getRegistry", architecturalRcx, registryAddr, 0L, 0L));
            note(architecturalRcx == address(0x54E0948L), "registry query explicit RCX");
            note(readPointer(objectAddr + 0x50L) == small(),
                    "O50 before query mutation");
            writeInt64(objectAddr + 0x50L, changedO50Addr);
            writeInt64(address(0x5434F38L), freshStringAddr);
            writeInt32(address(0x5434F48L), LENGTHS[caseId]);
            writeInt64(address(0x5434F50L), CAPACITIES[caseId]);
            return registryAddr;
        }

        public long findName(long registry, NativeIdlerConstruction.Descriptor knownDescriptorFields) {
            events.add(new Event("findName", registry, knownDescriptorFields.data(),
                    knownDescriptorFields.length(), Byte.toUnsignedInt(knownDescriptorFields.flag())));
            note(registry == registryAddr, "lookup registry result");
            note(knownDescriptorFields.data() == expectedNameData(), "unsigned capacity descriptor data");
            note(knownDescriptorFields.length() == LENGTHS[caseId], "fresh descriptor DWORD length");
            note(knownDescriptorFields.flag() == (byte) 0, "descriptor byte flag");
            writeInt64(address(0x5CBF858L),
                    finalGlobalPresent() ? globalReceiverAddr : 0L);
            return lookupResultAddr;
        }

        public void virtual30(long receiver, long lookupResult, long savedO50) {
            events.add(new Event("virtual30", receiver, lookupResult, savedO50, 0L));
            note(finalGlobalPresent(), "unexpected final virtual call");
            note(receiver == globalReceiverAddr, "fresh global receiver");
            note(lookupResult == lookupResultAddr, "lookup return passed to virtual call");
            note(savedO50 == small(), "saved O50 survives query mutation");
            note(readPointer(objectAddr + 0x50L) == changedO50Addr,
                    "query did mutate O50");
        }

        void verifyCompleted(long returnedObject) {
            check(returnedObject == objectAddr, "return must be entry O");
            check(allocationCount == 3, "three allocation calls");
            int expectedEvents = finalGlobalPresent() ? 7 : 6;
            check(events.size() == expectedEvents, "callback count");
            String[] order = {"allocate", "allocate", "constructChild", "allocate",
                "getRegistry", "findName", "virtual30"};
            for (int i = 0; i < expectedEvents; i++) {
                check(events.get(i).kind().equals(order[i]), "callback order index=" + i);
            }
            check(readPointer(objectAddr) == address(0x44BC418L), "O primary");
            check(readPointer(objectAddr + 0x18L) == address(0x54DF888L),
                    "O18 marker");
            check(readPointer(objectAddr + 0x20L) == expectedHeaderH(),
                    "final O20 after selected allocator mutations");
            check(readPointer(objectAddr + 0x28L) == childResultAddr,
                    "arbitrary child helper result published");
            check(childResultAddr != firstStorageAddr, "independent helper result");
            check(readPointer(objectAddr + 0x30L) == headerAddr, "O30 P2");
            check(readPointer(objectAddr + 0x48L) == address(0x54DF890L),
                    "O48 marker");
            check(readPointer(objectAddr + 0x50L) == changedO50Addr,
                    "final O50 mutation retained");
            check(readPointer(objectAddr + 0x68L) == address(0x54DF760L),
                    "O68 marker");
            check(readPointer(objectAddr + 0x80L) == address(0x54DF760L),
                    "O80 marker");
            check(readPointer(objectAddr + 0x88L) == 0L, "O88 zero");
            check(readPointer(objectAddr + 0x90L) == inputKAddr, "O90 entry K");
            long[] zeroOffsets = {8L, 0x10L, 0x38L, 0x40L, 0x58L, 0x60L, 0x70L, 0x78L};
            for (long offset : zeroOffsets) {
                check(readPointer(objectAddr + offset) == 0L,
                        "O zero field " + Long.toHexString(offset));
            }
            check(readPointer(firstStorageAddr) == expectedHelperH(),
                    "controlled helper payload");
            check(readPointer(firstStorageAddr + 8L)
                    == 0x1122334455667700L + caseId, "controlled helper marker");
            long[] headerWords = expectedHeaderWords(expectedHeaderH(), this);
            check(headerWords.length == 22, "all twenty-two P2 words");
            for (int i = 0; i < 22; i++) {
                check(readPointer(headerAddr + i * 8L) == headerWords[i],
                        "independent P2 header word " + i);
            }
            check(readPointer(address(0x5434F50L)) == CAPACITIES[caseId],
                    "capacity bits");
            check(readInt32(address(0x5434F48L)) == LENGTHS[caseId], "DWORD length bits");
            check(readPointer(address(0x5CBF858L))
                    == (finalGlobalPresent() ? globalReceiverAddr : 0L),
                    "lookup callback changed final global");
        }

        private long[] expectedHeaderWords(long freshH, NativeIdlerConstruction.Symbols symbols) {
            long[] w = new long[22];
            w[0] = freshH;
            w[1] = 0L;
            w[2] = 0L;
            w[3] = symbols.address(0x54e0928L);
            w[4] = 0L;
            w[5] = 0L;
            w[6] = symbols.address(0x54e0928L);
            w[7] = 0L;
            w[8] = 0L;
            w[9] = symbols.address(0x54e0928L);
            w[10] = 0L;
            w[11] = 0L;
            w[12] = symbols.address(0x54e0930L);
            w[13] = 0L;
            w[14] = 0L;
            w[15] = symbols.address(0x54e0938L);
            w[16] = 0L;
            w[17] = 0L;
            w[18] = symbols.address(0x54e0940L);
            w[19] = 0L;
            w[20] = 0L;
            w[21] = symbols.address(0x54e0948L);
            return w;
        }
    }

    // --- Test Method ---

    @Test
    public void testNativeIdlerConstructionMatrix() {
        int executed = 0;
        for (int id = 0; id < 8; id++) {
            Scenario scenario = new Scenario();
            scenario.prepare(id);

            // Create NativeTaskMemory adapter
            NativeTaskMemory memoryAdapter = new NativeTaskMemory() {
                @Override
                public long readPointer(long address) {
                    return scenario.readPointer(address);
                }
                @Override
                public int readInt32(long address) {
                    return scenario.readInt32(address);
                }
                @Override
                public void writeInt32(long address, int value) {
                    scenario.writeInt32(address, value);
                }
                @Override
                public void writeInt64(long address, long value) {
                    scenario.writeInt64(address, value);
                }
            };

            // Call the public facade
            long result = NativeIdlerConstruction.construct(
                scenario.objectAddr,
                scenario.initialHAddr,
                scenario.inputKAddr,
                memoryAdapter,
                scenario,
                scenario
            );

            // Verify
            scenario.verifyCompleted(result);
            executed++;
        }
        Assertions.assertEquals(8, executed, "Exactly eight existing construction scenarios");
    }
}
