package org.xar.ck3.research.m1;

import java.util.List;
import java.util.HashSet;
import java.util.Set;
import org.xar.ck3.research.m1.GovernmentSharedComposition168Fixture.MemoryImage;
import org.xar.ck3.research.m1.GovernmentFull193172CaseApi.Case;
import org.xar.ck3.research.m1.GovernmentFull193172CaseBook;
import org.xar.ck3.research.m1.GovernmentFull193172Composition;
import org.xar.ck3.research.m1.GovernmentRowResolve164Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

public final class GovernmentFull193174JavaWire {
    private static final long B = 0x1_0000_0000L;
    private static final long E = 0x7000_0008L;
    private static final long ROW = 0x4000_0000L;
    private static final long CTX = 0x5000_0000L;
    private static final long MGR = B + 0x5DC1390L;
    private static final long ROWS = 0x8000_0000L;
    private static final long Q = 0x8000_0020L;
    private static final long DATA = 0x8200_0003L;
    private static final long TABLE = 0x9000_0000L;
    private static final long HIT = 0xA000_3000L;
    private static final long INLINE_BUCKET = 0x9000_32B8L;
    private static final long COLLISION_BUCKET = 0x9000_4BD8L;
    private static final long NEXT_BUCKET = 0x9000_4BF0L;
    private static final long RETURN = 0x1234_5678_7654_3210L;
    private static final long OTHER = 0xB000_4000L;

    private GovernmentFull193174JavaWire() { }

    public static void main(String[] args) {
        if (args.length != 0) throw new AssertionError("no arguments");
        List<Case> cases = GovernmentFull193172CaseBook.cases();
        if (cases.size() != 2) throw new AssertionError("exact two cases");
        Set<String> seen=new HashSet<>();
        for(Case c:cases) {
            if(!seen.add(c.name()))throw new AssertionError("duplicate case "+c.name());
            emit(c);
        }
    }

    private static void emit(Case c) {
        String name = c.name();
        if (!"full193-inline-byte80-tail-unlocked-hit".equals(name) && !"full193-heap-fourbytes-block-reader-collision-hit".equals(name)) {
            throw new AssertionError("unhandled case name " + name);
        }
        boolean inline = name.startsWith("full193-inline");
        boolean heap = name.startsWith("full193-heap");
        if (inline == heap) throw new AssertionError("duplicate/unhandled case");

        GovernmentRowResolve164Api.Result r = GovernmentFull193172Composition.execute(
                c.entry(), c.memory(), c.delegate(), c.lookupBudget(), c.resolveBudget(), c.hashBudget(), c.ownedMxcsrAtHash());

        c.delegate().done(c.expectedGsReads());
        c.resolveBudget().done();
        c.hashBudget().done();

        VolatileBits v = r.volatileBits();
        NonvolatileBits n = r.nonvolatileBits();
        MemoryImage m = c.memory();

        String id = inline ? "inline80" : "heap4";
        StringBuilder sb = new StringBuilder("case=").append(id);

        append(sb, id, "ret.rip", sym(r.returnRipBits()));
        append(sb, id, "ret.rsp", sym(r.callerRspBits()));
        append(sb, id, "v.rax", hexQword(v.raxBits()));
        append(sb, id, "v.rcx", hexQword(v.rcxBits()));
        append(sb, id, "v.rdx", hexQword(v.rdxBits()));
        append(sb, id, "v.r8", hexQword(v.r8Bits()));
        append(sb, id, "v.r9", hexQword(v.r9Bits()));
        append(sb, id, "v.r10", sym(v.r10Bits()));
        append(sb, id, "v.r11", hexQword(v.r11Bits()));
        append128(sb, id, "xmm0", v.xmm0());
        append128(sb, id, "xmm1", v.xmm1());
        append128(sb, id, "xmm2", v.xmm2());
        append128(sb, id, "xmm3", v.xmm3());
        append128(sb, id, "xmm4", v.xmm4());
        append128(sb, id, "xmm5", v.xmm5());
        append(sb, id, "n.rbx", hexQword(n.rbxBits()));
        append(sb, id, "n.rbp", hexQword(n.rbpBits()));
        append(sb, id, "n.rsi", hexQword(n.rsiBits()));
        append(sb, id, "n.rdi", hexQword(n.rdiBits()));
        append(sb, id, "n.r12", hexQword(n.r12Bits()));
        append(sb, id, "n.r13", hexQword(n.r13Bits()));
        append(sb, id, "n.r14", hexQword(n.r14Bits()));
        append(sb, id, "n.r15", hexQword(n.r15Bits()));
        append128(sb, id, "xmm6", n.xmm6());

        append(sb, id, "mem.row.q0", sym(m.readQword(ROW)));
        append(sb, id, "mem.row.d8", hexDword(m.readDword(ROW + 8)));
        append(sb, id, "mem.row.dc", hexDword(m.readDword(ROW + 0xC)));
        append(sb, id, "mem.manager.q30", sym(m.readQword(MGR + 0x30)));
        append(sb, id, "mem.manager.d3c", hexDword(m.readDword(MGR + 0x3C)));
        append(sb, id, "mem.manager.d48", hexDword(m.readDword(MGR + 0x48)));
        append(sb, id, "mem.string.q10", hexQword(m.readQword(Q + 0x10)));
        append(sb, id, "mem.string.q18", hexQword(m.readQword(Q + 0x18)));
        if (inline) {
            append(sb, id, "mem.string.data", hexByte(m.readUnsignedByte(Q)));
        } else {
            append(sb, id, "mem.string.data", hexDword(m.readDword(DATA)));
        }
        append(sb, id, "mem.context.mode", hexByte(m.readUnsignedByte(CTX + 0xEE0)));
        append(sb, id, "mem.context.mask", hexDword(m.readDword(CTX + 0x18C)));
        append(sb, id, "mem.context.table", sym(m.readQword(CTX + 0x180)));
        append(sb, id, "mem.hit.magic", hexDword(m.readDword(HIT + 0x38)));

        append(sb, id, "stack.ret", sym(m.readQword(E)));
        append(sb, id, "stack.m08", hexQword(m.readQword(E - 8)));
        append(sb, id, "stack.p08", hexQword(m.readQword(E + 8)));
        append(sb, id, "stack.p10", hexQword(m.readQword(E + 0x10)));
        append(sb, id, "stack.m30", sym(m.readQword(E - 0x30)));
        append(sb, id, "stack.m28", hexQword(m.readQword(E - 0x28)));
        append(sb, id, "stack.m38", hexQword(m.readQword(E - 0x38)));
        append(sb, id, "stack.m60", sym(m.readQword(E - 0x60)));
        append(sb, id, "stack.m58", hexQword(m.readQword(E - 0x58)));
        append(sb, id, "stack.m50", sym(m.readQword(E - 0x50)));
        append(sb, id, "stack.m48", sym(m.readQword(E - 0x48)));
        append(sb, id, "stack.m40", hexQword(m.readQword(E - 0x40)));
        append(sb, id, "stack.m18", hexDword(m.readDword(E - 0x18)));

        if (inline) {
            append(sb, id, "bucket0.d4", hexDword(m.readDword(INLINE_BUCKET + 4)));
            append(sb, id, "bucket0.d8", hexDword(m.readDword(INLINE_BUCKET + 8)));
            append(sb, id, "bucket0.dc", hexDword(m.readDword(INLINE_BUCKET + 0xC)));
            append(sb, id, "bucket0.q10", sym(m.readQword(INLINE_BUCKET + 0x10)));
        } else {
            append(sb, id, "mem.context.counter", hexDword(m.readDword(CTX + 0xEA0)));
            append(sb, id, "bucket0.d4", hexDword(m.readDword(COLLISION_BUCKET + 4)));
            append(sb, id, "bucket0.d8", hexDword(m.readDword(COLLISION_BUCKET + 8)));
            append(sb, id, "bucket0.dc", hexDword(m.readDword(COLLISION_BUCKET + 0xC)));
            append(sb, id, "bucket0.q10", sym(m.readQword(COLLISION_BUCKET + 0x10)));
            append(sb, id, "bucket1.d4", hexDword(m.readDword(NEXT_BUCKET + 4)));
            append(sb, id, "bucket1.d8", hexDword(m.readDword(NEXT_BUCKET + 8)));
            append(sb, id, "bucket1.dc", hexDword(m.readDword(NEXT_BUCKET + 0xC)));
            append(sb, id, "bucket1.q10", sym(m.readQword(NEXT_BUCKET + 0x10)));
        }

        System.out.println(sb);
    }

    private static void append(StringBuilder sb, String id, String field, String value) {
        sb.append(' ').append(field).append('=').append(value);
    }

    private static void append128(StringBuilder sb, String id, String reg, Bits128 b) {
        append(sb, id, reg + ".lo", hexQword(b.lowBits()));
        append(sb, id, reg + ".hi", hexQword(b.highBits()));
    }

    private static String sym(long value) {
        if (value == ROW) return "ROW";
        if (value == CTX) return "CTX";
        if (value == MGR) return "MGR";
        if (value == ROWS) return "ROWS";
        if (value == Q) return "Q";
        if (value == DATA) return "DATA";
        if (value == TABLE) return "TABLE";
        if (value == HIT) return "HIT";
        if (value == RETURN) return "RETURN";
        if (value == OTHER) return "OTHER";
        if (value == INLINE_BUCKET) return "BUCKET0";
        if (value == COLLISION_BUCKET) return "BUCKET0";
        if (value == NEXT_BUCKET) return "BUCKET1";
        if (value == E) return "SP+0";
        if (value == E + 8) return "SP+8";
        if (value >= E - 0x100 && value <= E + 0x100) {
            long delta = value - E;
            if (delta >= 0) return "SP+" + Long.toHexString(delta).toUpperCase();
            return "SP-" + Long.toHexString(-delta).toUpperCase();
        }
        if (value >= B && value < B + 0x6000000L) {
            return "IMG+" + Long.toHexString(value - B).toUpperCase();
        }
        return hexQword(value);
    }

    private static String hexQword(long value) {
        return String.format("%016X", value);
    }

    private static String hexDword(int value) {
        return String.format("%08X", value);
    }

    private static String hexByte(int value) {
        return String.format("%02X", value & 0xFF);
    }
}
