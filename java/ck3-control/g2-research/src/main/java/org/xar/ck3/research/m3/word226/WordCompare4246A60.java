package org.xar.ck3.research.m3.word226;

import org.xar.ck3.research.m3.word226.WordCompare226Api;

/**
 * Exact-width address operations for supplied storage; no process attachment.
 * This class implements the contract for the 44-byte NORMAL44 body at 0x4246a60.
 */
public final class WordCompare4246A60 implements WordCompare226Api {

    public WordCompare4246A60() {
    }

    @Override
    public WordCompare226Api.Result execute(WordCompare226Api.Memory memory, long rcx, long rdx, long r8) {
        // Entry: test r8,r8; jne 0x4246a7d (loop start/continue check)
        // If r8 == 0: xor eax,eax (eax=0); ret.
        // Result: difference32=0, remainingR8=0, finalRightCursor=original rdx, finalReadsOccurred=false.
        if (r8 == 0L) {
            return new WordCompare226Api.Result(
                0,
                0L,
                rdx,
                0,
                false
            );
        }

        // Nonzero count path.
        // The source logic decrements R8 before the first loop test (sub r8,0x1; jne ...).
        // We simulate the loop structure exactly as per the 17 instructions.

        long currentRcx = rcx;
        long currentRdx = rdx;
        long currentR8 = r8;

        // Decrement before loop entry check (matches 'sub r8,0x1' at 0x4246a7d if jumping from initial test,
        // but actually the flow is: test r8 -> if 0 ret. If not 0, fall through to 0x4246a68?
        // Wait, looking at disassembly:
        // 4246a60: test r8,r8
        // 4246a63: jne 0x4246a7d  -> If r8 != 0, jump to 0x4246a7d.
        // 0x4246a7d: sub r8,0x1
        // 0x4246a81: jne 0x4246a68 -> If r8 != 0 after sub, jump to 0x4246a68 (loop body start).
        // If r8 == 0 after sub, fall through to 0x4246a83 (final read block).

        // So for r8=1:
        // test r8 (1) -> jne 0x4246a7d.
        // sub r8 -> 0.
        // jne 0x4246a68 -> false (0 is not nonzero), fall through to 0x4246a83.
        // 0x4246a83: movzx eax, WORD[rcx]
        // 0x4246a86: movzx ecx, WORD[rdx]
        // 0x4246a89: sub eax, ecx
        // 0x4246a8b: ret

        // For r8=2:
        // test r8 (2) -> jne 0x4246a7d.
        // sub r8 -> 1.
        // jne 0x4246a68 -> true, jump to 0x4246a68.
        // 0x4246a68: movzx eax, WORD[rcx]
        // 0x4246a6b: test ax,ax
        // 0x4246a6e: je 0x4246a83 -> If left word is 0, jump to final read block.
        // 0x4246a70: cmp ax, WORD[rdx]
        // 0x4246a73: jne 0x4246a83 -> If mismatch, jump to final read block.
        // 0x4246a75: add rcx, 0x2
        // 0x4246a79: add rdx, 0x2
        // 0x4246a7d: sub r8, 0x1
        // 0x4246a81: jne 0x4246a68 -> Loop back if r8 != 0.

        // The loop body at 0x4246a68 checks the CURRENT left word. If it is 0, it breaks to final.
        // If it is not 0, it compares with current right word. If mismatch, breaks to final.
        // If match, advances pointers and decrements count, then loops.

        // We must implement this exact control flow.

        // Initial decrement happens at 0x4246a7d which is reached via the first JNE.
        currentR8 = currentR8 - 1L;

        // Check if we should enter the loop body (0x4246a68) or go to final (0x4246a83)
        // The instruction at 0x4246a81 is 'jne 0x4246a68'. This tests the result of 'sub r8,0x1'.
        // If r8 != 0, jump to 0x4246a68.
        // If r8 == 0, fall through to 0x4246a83.

        while (currentR8 != 0L) {
            // 0x4246a68: movzx eax, WORD PTR [rcx]
            int leftWord = memory.readWord16(currentRcx);

            // 0x4246a6b: test ax,ax
            // 0x4246a6e: je 0x4246a83
            if (leftWord == 0) {
                // Break to final read block
                break;
            }

            // 0x4246a70: cmp ax, WORD PTR [rdx]
            int rightWord = memory.readWord16(currentRdx);

            // 0x4246a73: jne 0x4246a83
            if (leftWord != rightWord) {
                // Break to final read block
                break;
            }

            // 0x4246a75: add rcx, 0x2
            currentRcx = currentRcx + 2L;
            // 0x4246a79: add rdx, 0x2
            currentRdx = currentRdx + 2L;

            // 0x4246a7d: sub r8, 0x1
            currentR8 = currentR8 - 1L;

            // 0x4246a81: jne 0x4246a68
            // Loop continues if currentR8 != 0
        }

        // Final block: 0x4246a83
        // 0x4246a83: movzx eax, WORD PTR [rcx]
        int finalLeftWord = memory.readWord16(currentRcx);

        // 0x4246a86: movzx ecx, WORD PTR [rdx]
        int finalRightWord = memory.readWord16(currentRdx);

        // 0x4246a89: sub eax, ecx
        int difference32 = finalLeftWord - finalRightWord;

        // Result construction
        // remainingR8 is currentR8 (which is 0 if loop finished normally, or whatever it was if broken early?
        // Wait, if we break early from the loop (leftWord==0 or mismatch), we jump to 0x4246a83.
        // The 'sub r8,0x1' at 0x4246a7d is NOT executed in the break paths.
        // So currentR8 retains the value it had at the start of the iteration that broke.
        // However, the contract says: "remaining actual full64".
        // If we break at 0x4246a6e (je 0x4246a83), we haven't decremented r8 for this iteration yet.
        // The decrement happens at 0x4246a7d, which is AFTER the comparison and pointer advance.
        // So if we break, currentR8 is the count remaining BEFORE the decrement of the current step.

        return new WordCompare226Api.Result(
            difference32,
            currentR8,
            currentRdx,
            finalRightWord,
            true
        );
    }
}