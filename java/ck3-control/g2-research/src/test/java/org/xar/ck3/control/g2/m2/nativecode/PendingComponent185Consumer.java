package org.xar.ck3.control.g2.m2.nativecode;
import java.io.*;
import java.nio.file.*;
import java.util.*;
import java.util.HexFormat;

public final class PendingComponent185Consumer {
    public static void main(String[] args) throws Exception {
        if (args.length != 1) throw new IllegalArgumentException("missing path");
        List<String> lines = Files.readAllLines(Path.of(args[0]));
        if (lines.size() != 2) throw new IllegalStateException("expected 2 rows");
        int corePassCount = 0;
        int adapterPassCount = 0;
        for (int i = 0; i < 2; i++) {
            String line = lines.get(i);
            if (line.isEmpty()) throw new IllegalStateException("empty line");
            String[] parts = line.split("\t");
            if (parts.length != 7) throw new IllegalStateException("bad row fields");
            if (!parts[0].equals("CASE")) throw new IllegalStateException("bad case tag");
            if (!parts[1].equals(String.valueOf(i))) throw new IllegalStateException("bad index");
            long component = Long.parseUnsignedLong(parts[2], 16);
            long literal = Long.parseUnsignedLong(parts[3], 16);
            long rax = Long.parseUnsignedLong(parts[4], 16);
            if (rax != component) throw new IllegalStateException("rax mismatch");
            byte[] before = HexFormat.of().parseHex(parts[5]);
            byte[] after = HexFormat.of().parseHex(parts[6]);
            if (before.length != 704 || after.length != 704) throw new IllegalStateException("bad RAM length");
            long moduleBase = literal - 0x54E62D8L;

            byte[] clone = before.clone();
            Memory mem = new Memory(clone, component);
            long ret = PendingComponentInit2756120.initialize(mem, component, moduleBase);
            if (ret != component) throw new IllegalStateException("core return mismatch");
            if (!Arrays.equals(clone, after)) throw new IllegalStateException("core RAM mismatch");
            corePassCount++;

            byte[] clone2 = before.clone();
            Memory mem2 = new Memory(clone2, component);
            long pending = component - 0x350;
            PendingSlotComponentCall2A328D0.initializeSelectedSlotComponent(mem2, pending, moduleBase);
            if (!Arrays.equals(clone2, after)) throw new IllegalStateException("adapter RAM mismatch");
            adapterPassCount++;
        }
        System.out.println("nativeRows=2 corePassCount=" + corePassCount + " adapterPassCount=" + adapterPassCount);
    }

    private static class Memory implements PendingComponentInit2756120.Memory {
        private final byte[] buf;
        private final long base;
        Memory(byte[] buf, long base) { this.buf = buf; this.base = base; }
        private int idx(long addr, int width) {
            long off = addr - base;
            if (off < 0 || off > 0x280L - width) throw new IndexOutOfBoundsException();
            return 32 + (int)off;
        }
        public void write8(long address, int value) {
            int i = idx(address, 1);
            buf[i] = (byte)value;
        }
        public void write32(long address, int value) {
            int i = idx(address, 4);
            buf[i] = (byte)value;
            buf[i+1] = (byte)(value >>> 8);
            buf[i+2] = (byte)(value >>> 16);
            buf[i+3] = (byte)(value >>> 24);
        }
        public void write64(long address, long value) {
            int i = idx(address, 8);
            buf[i] = (byte)value;
            buf[i+1] = (byte)(value >>> 8);
            buf[i+2] = (byte)(value >>> 16);
            buf[i+3] = (byte)(value >>> 24);
            buf[i+4] = (byte)(value >>> 32);
            buf[i+5] = (byte)(value >>> 40);
            buf[i+6] = (byte)(value >>> 48);
            buf[i+7] = (byte)(value >>> 56);
        }
    }
}
