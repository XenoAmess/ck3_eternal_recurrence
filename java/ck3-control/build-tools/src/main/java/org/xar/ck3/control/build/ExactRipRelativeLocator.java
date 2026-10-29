package org.xar.ck3.control.build;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.HexFormat;
import java.util.List;
import static org.xar.ck3.control.build.RawWindowCaptureContract.*;
import static org.xar.ck3.control.build.RawWindowLocatorContract.*;

/** Pure bounded raw-pattern matcher, not an x64 disassembler. No I/O and no valid-instruction claim. */
final class ExactRipRelativeLocator {
    record Batch(List<Candidate> candidates, long scannedThroughFileOffset, boolean limitReached, boolean candidateScanComplete) {
        Batch { candidates = List.copyOf(candidates); }
    }
    private byte[] carry = new byte[0];
    private long received, nextStart;
    private boolean closed;
    Batch accept(byte[] actual, long segmentRelativeOffset, boolean end, int remainingCandidates) {
        require(!closed && segmentRelativeOffset == received && actual != null && actual.length <= CHUNK_BYTES
                && received + actual.length <= TEXT_BYTES && remainingCandidates > 0 && remainingCandidates <= MAX_CANDIDATES,
                "one ordered finite actual locator stream required");
        byte[] buffer = new byte[carry.length + actual.length];
        System.arraycopy(carry, 0, buffer, 0, carry.length); System.arraycopy(actual, 0, buffer, carry.length, actual.length);
        long base = received - carry.length; received += actual.length;
        List<Candidate> found = new ArrayList<>(); boolean limit = false;
        // Delay at most10 bytes of encoding and15 bytes of following context. Preserve15 bytes before each delayed start.
        while (end ? nextStart + 7 <= received : nextStart + 26 <= received) {
            int at = Math.toIntExact(nextStart - base); int rex = buffer[at] & 255, opcode = buffer[at + 1] & 255, modrm = buffer[at + 2] & 255;
            Operation operation = null; int length = 7;
            if (rex >= 0x48 && rex <= 0x4f && (modrm & 0xc7) == 5) {
                operation = switch (opcode) { case 0x8d -> Operation.LEA; case 0x8b -> Operation.LOAD; case 0x89 -> Operation.STORE; default -> null; };
                if (rex == 0x48 && opcode == 0xc7 && modrm == 5) { operation = Operation.STORE_IMMEDIATE32; length = 11; }
            }
            if (operation != null && nextStart + length <= received) {
                int displacement = littleInt(buffer, at + 3); long rva = TEXT_RVA + nextStart, targetRva = rva + length + displacement;
                Target target = targetRva == MANAGER_RVA ? Target.MANAGER : targetRva == QUEUE_RVA ? Target.QUEUE : null;
                if (target != null) {
                    int before = Math.min(15, at), after = Math.min(15, buffer.length - at - length);
                    found.add(new Candidate(TEXT_OFFSET + nextStart, rva, operation, length, displacement, target, targetRva,
                            hex(buffer, at, length), hex(buffer, at - before, before), hex(buffer, at + length, after),
                            before < 15, after < 15, Boundary.UNVALIDATED));
                    if (found.size() == remainingCandidates) { nextStart++; limit = true; closed = true; break; }
                }
            }
            nextStart++;
        }
        if (end && !limit) { nextStart = received; closed = true; }
        carry = Arrays.copyOfRange(buffer, Math.max(0, buffer.length - 40), buffer.length);
        return new Batch(found, TEXT_OFFSET + nextStart, limit, end && !limit && received == TEXT_BYTES);
    }
    private static String hex(byte[] value, int offset, int length) { return HexFormat.of().formatHex(value, offset, offset + length); }
}
