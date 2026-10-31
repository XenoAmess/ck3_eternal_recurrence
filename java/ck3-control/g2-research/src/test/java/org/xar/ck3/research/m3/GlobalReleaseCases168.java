package org.xar.ck3.research.m3;

import java.util.List;
import java.util.ArrayList;

public final class GlobalReleaseCases168 {
    public record Pipeline(String id, long receiver, long rows, long alignment, long incomingR9,
            long selectorTarget, long wrapperTarget, List<ReleaseApi167.Word> initialWords,
            long tailResult, int expectedTailCalls, GlobalReleaseApi168.Registers expectedTail,
            long expectedResult) {}

    public static List<GlobalReleaseApi168.Scenario> units() {
        List<GlobalReleaseApi168.Scenario> list = new ArrayList<>();

        // U1: RDX=0, highbit RAX. No tail call. Result is incomingRAX.
        list.add(new GlobalReleaseApi168.Scenario(
            "U1-ZeroRDX-HighRAX",
            new GlobalReleaseApi168.Registers(0x1000L, 0L, 0x2000L, 0x3000L, 0x8000000000000001L),
            0L, 0, null, 0x8000000000000001L
        ));

        // U2: RDX=0, different highbit RAX. No tail call. Result is incomingRAX.
        list.add(new GlobalReleaseApi168.Scenario(
            "U2-ZeroRDX-DiffHighRAX",
            new GlobalReleaseApi168.Registers(0x1001L, 0L, 0x2001L, 0x3001L, 0x8000000000000002L),
            0L, 0, null, 0x8000000000000002L
        ));

        // U3: RDX!=0. Tail call to 40EC530. Expected tail: RCX=RDX, RDX=RDX, R8=R8, R9=R9, RAX=incomingRAX.
        // Inputs include distinct highbit/negative 64-bit values for all registers.
        list.add(new GlobalReleaseApi168.Scenario(
            "U3-NonZeroRDX-TailCall",
            new GlobalReleaseApi168.Registers(0x8000000000000003L, 0x8000000000000004L, 0x8000000000000005L, 0x8000000000000006L, 0x8000000000000007L),
            0x9000000000000001L, 1,
            new GlobalReleaseApi168.Registers(0x8000000000000004L, 0x8000000000000004L, 0x8000000000000005L, 0x8000000000000006L, 0x8000000000000007L),
            0x9000000000000001L
        ));

        // U4: RDX!=0. Tail call to 40EC530. Expected tail: RCX=RDX, RDX=RDX, R8=R8, R9=R9, RAX=incomingRAX.
        // Inputs include distinct highbit/negative 64-bit values for all registers.
        list.add(new GlobalReleaseApi168.Scenario(
            "U4-NonZeroRDX-DiffTailCall",
            new GlobalReleaseApi168.Registers(0x8000000000000008L, 0x8000000000000009L, 0x800000000000000AL, 0x800000000000000BL, 0x800000000000000CL),
            0x9000000000000002L, 1,
            new GlobalReleaseApi168.Registers(0x8000000000000009L, 0x8000000000000009L, 0x800000000000000AL, 0x800000000000000BL, 0x800000000000000CL),
            0x9000000000000002L
        ));

        return list;
    }

    public static List<Pipeline> pipelines() {
        List<Pipeline> list = new ArrayList<>();

        // P1: rows=0. Traverses 167 slot38+release10. 168 zeroRDX skips opaque 40EC530.
        // Result is incomingRAX (which equals returnedReceiver in this binding).
        long rec1 = 0x1000000000000001L;
        long sel1 = 0x2000000000000001L;
        long wrap1 = 0x3000000000000001L;
        long retRec1 = 0x4000000000000001L; // returnedReceiver
        long retVptr1 = 0x5000000000000001L; // returnedVptr

        List<ReleaseApi167.Word> words1 = List.of(
            new ReleaseApi167.Word(rec1, 0x6000000000000001L), // entryVptr
            new ReleaseApi167.Word(0x6000000000000001L + 0x38, sel1), // selectorTarget
            new ReleaseApi167.Word(rec1 + 0x408, retRec1), // returnedReceiver
            new ReleaseApi167.Word(retRec1, retVptr1), // returnedVptr
            new ReleaseApi167.Word(retVptr1 + 0x10, wrap1) // wrapperTarget
        );

        list.add(new Pipeline(
            "P1-Rows0-NoTail",
            rec1, 0L, 0x100L, 0x200L, sel1, wrap1, words1,
            0L, 0, null, retRec1
        ));

        // P2: rows nonzero highbit. Traverses 167 slot38+release10. 168 nonzeroRDX calls opaque 40EC530.
        // Expected tail: RCX=rows, RDX=rows, R8=alignment, R9=returnedVptr, RAX=returnedReceiver.
        long rec2 = 0x1000000000000002L;
        long sel2 = 0x2000000000000002L;
        long wrap2 = 0x3000000000000002L;
        long retRec2 = 0x4000000000000002L; // returnedReceiver
        long retVptr2 = 0x5000000000000002L; // returnedVptr
        long rows2 = 0x8000000000000001L; // nonzero highbit
        long align2 = 0x101L;
        long inR9_2 = 0x201L;
        long tailRes2 = 0x9000000000000001L; // opaque tailResult

        List<ReleaseApi167.Word> words2 = List.of(
            new ReleaseApi167.Word(rec2, 0x6000000000000002L), // entryVptr
            new ReleaseApi167.Word(0x6000000000000002L + 0x38, sel2), // selectorTarget
            new ReleaseApi167.Word(rec2 + 0x408, retRec2), // returnedReceiver
            new ReleaseApi167.Word(retRec2, retVptr2), // returnedVptr
            new ReleaseApi167.Word(retVptr2 + 0x10, wrap2) // wrapperTarget
        );

        GlobalReleaseApi168.Registers expTail2 = new GlobalReleaseApi168.Registers(
            rows2, rows2, align2, retVptr2, retRec2
        );

        list.add(new Pipeline(
            "P2-RowsNonZero-TailCall",
            rec2, rows2, align2, inR9_2, sel2, wrap2, words2,
            tailRes2, 1, expTail2, tailRes2
        ));

        return list;
    }
}