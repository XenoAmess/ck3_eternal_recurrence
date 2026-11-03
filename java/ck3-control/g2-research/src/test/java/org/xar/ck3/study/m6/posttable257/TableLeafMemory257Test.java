package org.xar.ck3.study.m6.posttable257;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.TreeMap;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Entry;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.study.m6.poststate240.PostState240Api;

/**
 * Four new source-only Memory witnesses, independently frozen from the complete held69B.
 * No normal-vector suite, candidate implementation, typedStopped or hardware-fault model.
 * Selected alias is row1: key at entrySP, value at entrySP+4, RET consumes their sharedQWORD.
 * The earlier equal-address row0 alias is unselected and is not executed here.
 * Owner has not compiled or run this source.
 */
public final class TableLeafMemory257Test {
    private static final long IMAGE = 0x0000000140000000L;
    private static final long TABLE = 0x0000000144423A60L;
    private static final long ORDINARY_SP = 0x00000000001A0008L;
    private static final long ALIAS_SP = 0x0000000144423A68L;
    private static final QueueFp604Api.Mxcsr MXCSR =
            new QueueFp604Api.Mxcsr(0x5F85, 0xFFC5);
    private static final VolatileBits MATCH_INPUT_V = new VolatileBits(
            0xF0E1D2C3B4A59687L, 0xA1B2C3D413579BDFL, 0x2233445566778899L, 0x33445566778899AAL, 0x445566778899AABBL, 0x5566778899AABBCCL, 0x66778899AABBCCDDL,
            new Bits128(0x0102030405060708L, 0x1112131415161718L),
            new Bits128(0x2122232425262728L, 0x3132333435363738L),
            new Bits128(0x4142434445464748L, 0x5152535455565758L),
            new Bits128(0x6162636465666768L, 0x7172737475767778L),
            new Bits128(0x8182838485868788L, 0x9192939495969798L),
            new Bits128(0xA1A2A3A4A5A6A7A8L, 0xB1B2B3B4B5B6B7B8L));
    private static final VolatileBits MISS_INPUT_V = new VolatileBits(
            0xF0E1D2C3B4A59687L, 0xA1B2C3D4DEADBEEFL, 0x2233445566778899L, 0x33445566778899AAL, 0x445566778899AABBL, 0x5566778899AABBCCL, 0x66778899AABBCCDDL,
            new Bits128(0x0102030405060708L, 0x1112131415161718L),
            new Bits128(0x2122232425262728L, 0x3132333435363738L),
            new Bits128(0x4142434445464748L, 0x5152535455565758L),
            new Bits128(0x6162636465666768L, 0x7172737475767778L),
            new Bits128(0x8182838485868788L, 0x9192939495969798L),
            new Bits128(0xA1A2A3A4A5A6A7A8L, 0xB1B2B3B4B5B6B7B8L));
    private static final VolatileBits ALIAS_INPUT_V = new VolatileBits(
            0xF0E1D2C3B4A59687L, 0xA1B2C3D480000005L, 0x2233445566778899L, 0x33445566778899AAL, 0x445566778899AABBL, 0x5566778899AABBCCL, 0x66778899AABBCCDDL,
            new Bits128(0x0102030405060708L, 0x1112131415161718L),
            new Bits128(0x2122232425262728L, 0x3132333435363738L),
            new Bits128(0x4142434445464748L, 0x5152535455565758L),
            new Bits128(0x6162636465666768L, 0x7172737475767778L),
            new Bits128(0x8182838485868788L, 0x9192939495969798L),
            new Bits128(0xA1A2A3A4A5A6A7A8L, 0xB1B2B3B4B5B6B7B8L));
    private static final VolatileBits ALIAS_EXPECTED_V = new VolatileBits(
            0x0000000000000001L, 0xA1B2C3D480000005L, 0x0000000144423A68L, 0x0000000000000008L, 0x0000000144423A60L, 0x5566778899AABBCCL, 0x66778899AABBCCDDL,
            new Bits128(0x0102030405060708L, 0x1112131415161718L),
            new Bits128(0x2122232425262728L, 0x3132333435363738L),
            new Bits128(0x4142434445464748L, 0x5152535455565758L),
            new Bits128(0x6162636465666768L, 0x7172737475767778L),
            new Bits128(0x8182838485868788L, 0x9192939495969798L),
            new Bits128(0xA1A2A3A4A5A6A7A8L, 0xB1B2B3B4B5B6B7B8L));
    private static final NonvolatileBits INPUT_N = new NonvolatileBits(
            0x7000000000000001L, 0x7000000000000002L, 0x7000000000000003L, 0x7000000000000004L, 0xFEDCBA9800000057L, 0x7000000000000006L, 0x7000000000000007L, 0x7000000000000008L,
            new Bits128(0xC1C2C3C4C5C6C7C8L, 0xD1D2D3D4D5D6D7D8L));

    private TableLeafMemory257Test() { }

    public static void main(String[] args) {
        if (args.length == 0) {
            firstKeyFailure();
            firstValueFailure();
            missRetFailure();
            selectedRowAlias();
        } else if (args.length == 1) {
            switch (args[0]) {
                case "first-key" -> firstKeyFailure();
                case "first-value" -> firstValueFailure();
                case "miss-ret" -> missRetFailure();
                case "row-alias" -> selectedRowAlias();
                default -> throw new IllegalArgumentException("Unknown Memory257 selector");
            }
        } else {
            throw new IllegalArgumentException("Expected no args or one Memory257 selector");
        }
        System.out.println("Selected independent TableLeaf Memory257 cases passed");
    }

    private static void firstKeyFailure() {
        Ram ram = firstMatchRam();
        RuntimeException ordinary = new IllegalStateException("first-key257");
        ram.inject("R4", TABLE, ordinary);
        expectSameOrdinary(input(ORDINARY_SP, MATCH_INPUT_V), ram, ordinary, List.of(
            new Read("R4", 0x0000000144423A60L, null)), 0);
    }

    private static void firstValueFailure() {
        Ram ram = firstMatchRam();
        RuntimeException ordinary = new IllegalStateException("first-value257");
        ram.inject("R4", 0x0000000144423A64L, ordinary);
        expectSameOrdinary(input(ORDINARY_SP, MATCH_INPUT_V), ram, ordinary, List.of(
            new Read("R4", 0x0000000144423A60L, 0x13579BDFL),
            new Read("R4", 0x0000000144423A64L, null)), 0);
    }

    private static void missRetFailure() {
        Ram ram = missRam();
        RuntimeException ordinary = new IllegalStateException("fresh-ret257");
        ram.inject("R8", ORDINARY_SP, ordinary);
        expectSameOrdinary(input(ORDINARY_SP, MISS_INPUT_V), ram, ordinary, List.of(
            new Read("R4", 0x0000000144423A60L, 0x10000000L),
            new Read("R4", 0x0000000144423A68L, 0x10000001L),
            new Read("R4", 0x0000000144423A70L, 0x10000002L),
            new Read("R4", 0x0000000144423A78L, 0x10000003L),
            new Read("R4", 0x0000000144423A80L, 0x10000004L),
            new Read("R4", 0x0000000144423A88L, 0x10000005L),
            new Read("R4", 0x0000000144423A90L, 0x10000006L),
            new Read("R4", 0x0000000144423A98L, 0x10000007L),
            new Read("R4", 0x0000000144423AA0L, 0x10000008L),
            new Read("R4", 0x0000000144423AA8L, 0x10000009L),
            new Read("R4", 0x0000000144423AB0L, 0x1000000AL),
            new Read("R4", 0x0000000144423AB8L, 0x1000000BL),
            new Read("R4", 0x0000000144423AC0L, 0x1000000CL),
            new Read("R4", 0x0000000144423AC8L, 0x1000000DL),
            new Read("R4", 0x0000000144423AD0L, 0x1000000EL),
            new Read("R4", 0x0000000144423AD8L, 0x1000000FL),
            new Read("R4", 0x0000000144423AE0L, 0x10000010L),
            new Read("R4", 0x0000000144423AE8L, 0x10000011L),
            new Read("R4", 0x0000000144423AF0L, 0x10000012L),
            new Read("R4", 0x0000000144423AF8L, 0x10000013L),
            new Read("R4", 0x0000000144423B00L, 0x10000014L),
            new Read("R4", 0x0000000144423B08L, 0x10000015L),
            new Read("R4", 0x0000000144423B10L, 0x10000016L),
            new Read("R4", 0x0000000144423B18L, 0x10000017L),
            new Read("R4", 0x0000000144423B20L, 0x10000018L),
            new Read("R4", 0x0000000144423B28L, 0x10000019L),
            new Read("R4", 0x0000000144423B30L, 0x1000001AL),
            new Read("R4", 0x0000000144423B38L, 0x1000001BL),
            new Read("R4", 0x0000000144423B40L, 0x1000001CL),
            new Read("R4", 0x0000000144423B48L, 0x1000001DL),
            new Read("R4", 0x0000000144423B50L, 0x1000001EL),
            new Read("R4", 0x0000000144423B58L, 0x1000001FL),
            new Read("R4", 0x0000000144423B60L, 0x10000020L),
            new Read("R4", 0x0000000144423B68L, 0x10000021L),
            new Read("R4", 0x0000000144423B70L, 0x10000022L),
            new Read("R4", 0x0000000144423B78L, 0x10000023L),
            new Read("R4", 0x0000000144423B80L, 0x10000024L),
            new Read("R4", 0x0000000144423B88L, 0x10000025L),
            new Read("R4", 0x0000000144423B90L, 0x10000026L),
            new Read("R4", 0x0000000144423B98L, 0x10000027L),
            new Read("R4", 0x0000000144423BA0L, 0x10000028L),
            new Read("R4", 0x0000000144423BA8L, 0x10000029L),
            new Read("R4", 0x0000000144423BB0L, 0x1000002AL),
            new Read("R4", 0x0000000144423BB8L, 0x1000002BL),
            new Read("R4", 0x0000000144423BC0L, 0x1000002CL),
            new Read("R8", 0x00000000001A0008L, null)), 1);
    }

    /** No returned V/N/SP, snapshot or Outcome is synthesized for an ordinary failure. */
    private static void expectSameOrdinary(PostState240Api.Input input, Ram ram,
            RuntimeException ordinary, List<Read> expectedReads, int expectedRetAttempts) {
        Map<Long, Integer> before = new TreeMap<>(ram.bytes);
        try {
            new TableDwordLeaf257().execute(input, ram);
            throw new AssertionError("Ordinary Memory exception was swallowed or converted to Outcome");
        } catch (RuntimeException actual) {
            same(ordinary, actual, "original ordinary Memory exception");
        }
        equal(expectedReads, ram.reads, "complete attempted/successful read prefix");
        equalLong(expectedRetAttempts, ram.retAttempts, "fresh QWORD RET attempts");
        equalLong(0, ram.writeAttempts, "no Memory writes");
        equal(before, ram.bytes, "entire owned RAM unchanged after ordinary exception");
    }

    private static void selectedRowAlias() {
        Ram ram = new Ram();
        ram.seed(0x0000000144423A60L, 4, 0x13579BDFL);
        ram.seed(0x0000000144423A64L, 4, 0x2468ACE0L);
        ram.seed(0x0000000144423A68L, 8, 0x0000000180000005L);
        Map<Long, Integer> before = new TreeMap<>(ram.bytes);
        QueueFp604Api.Outcome result = new TableDwordLeaf257().execute(
                input(ALIAS_SP, ALIAS_INPUT_V), ram);
        QueueFp604Api.Normal expected = new QueueFp604Api.Normal(
                new FullCopy437Api.CallResult(new NormalReturn(
                        ALIAS_EXPECTED_V, 0x0000000180000005L, 0x0000000144423A70L,
                        INPUT_N), true), MXCSR);
        equal(expected, result, "whole represented normal state / explicit DF / partial MXCSR");
        equal(List.of(
            new Read("R4", 0x0000000144423A60L, 0x13579BDFL),
            new Read("R4", 0x0000000144423A68L, 0x80000005L),
            new Read("R4", 0x0000000144423A6CL, 0x00000001L),
            new Read("R8", 0x0000000144423A68L, 0x0000000180000005L)), ram.reads, "key0/key1/value1/fresh64RET width-sensitive alias");
        equalLong(1, ram.retAttempts, "exactly one fresh RET read");
        equalLong(0, ram.writeAttempts, "alias source owns no write");
        equal(before, ram.bytes, "shared row bytes unchanged");
        equalLong(8, ALIAS_SP & 15L, "controlled entry alignment; no native admission claimed");
    }

    private static PostState240Api.Input input(long sp, VolatileBits v) {
        return new PostState240Api.Input(
                new Entry(IMAGE, sp, v, INPUT_N), true, MXCSR, 0xD257L);
    }

    private static Ram firstMatchRam() {
        Ram ram = new Ram();
        ram.seed(0x0000000144423A60L, 4, 0x13579BDFL);
        ram.seed(0x0000000144423A64L, 4, 0x2468ACE0L);
        ram.seed(0x00000000001A0008L, 8, 0x0000000140456780L);
        return ram;
    }

    private static Ram missRam() {
        Ram ram = new Ram();
        ram.seed(0x0000000144423A60L, 4, 0x10000000L);
        ram.seed(0x0000000144423A64L, 4, 0x60000000L);
        ram.seed(0x0000000144423A68L, 4, 0x10000001L);
        ram.seed(0x0000000144423A6CL, 4, 0x60000001L);
        ram.seed(0x0000000144423A70L, 4, 0x10000002L);
        ram.seed(0x0000000144423A74L, 4, 0x60000002L);
        ram.seed(0x0000000144423A78L, 4, 0x10000003L);
        ram.seed(0x0000000144423A7CL, 4, 0x60000003L);
        ram.seed(0x0000000144423A80L, 4, 0x10000004L);
        ram.seed(0x0000000144423A84L, 4, 0x60000004L);
        ram.seed(0x0000000144423A88L, 4, 0x10000005L);
        ram.seed(0x0000000144423A8CL, 4, 0x60000005L);
        ram.seed(0x0000000144423A90L, 4, 0x10000006L);
        ram.seed(0x0000000144423A94L, 4, 0x60000006L);
        ram.seed(0x0000000144423A98L, 4, 0x10000007L);
        ram.seed(0x0000000144423A9CL, 4, 0x60000007L);
        ram.seed(0x0000000144423AA0L, 4, 0x10000008L);
        ram.seed(0x0000000144423AA4L, 4, 0x60000008L);
        ram.seed(0x0000000144423AA8L, 4, 0x10000009L);
        ram.seed(0x0000000144423AACL, 4, 0x60000009L);
        ram.seed(0x0000000144423AB0L, 4, 0x1000000AL);
        ram.seed(0x0000000144423AB4L, 4, 0x6000000AL);
        ram.seed(0x0000000144423AB8L, 4, 0x1000000BL);
        ram.seed(0x0000000144423ABCL, 4, 0x6000000BL);
        ram.seed(0x0000000144423AC0L, 4, 0x1000000CL);
        ram.seed(0x0000000144423AC4L, 4, 0x6000000CL);
        ram.seed(0x0000000144423AC8L, 4, 0x1000000DL);
        ram.seed(0x0000000144423ACCL, 4, 0x6000000DL);
        ram.seed(0x0000000144423AD0L, 4, 0x1000000EL);
        ram.seed(0x0000000144423AD4L, 4, 0x6000000EL);
        ram.seed(0x0000000144423AD8L, 4, 0x1000000FL);
        ram.seed(0x0000000144423ADCL, 4, 0x6000000FL);
        ram.seed(0x0000000144423AE0L, 4, 0x10000010L);
        ram.seed(0x0000000144423AE4L, 4, 0x60000010L);
        ram.seed(0x0000000144423AE8L, 4, 0x10000011L);
        ram.seed(0x0000000144423AECL, 4, 0x60000011L);
        ram.seed(0x0000000144423AF0L, 4, 0x10000012L);
        ram.seed(0x0000000144423AF4L, 4, 0x60000012L);
        ram.seed(0x0000000144423AF8L, 4, 0x10000013L);
        ram.seed(0x0000000144423AFCL, 4, 0x60000013L);
        ram.seed(0x0000000144423B00L, 4, 0x10000014L);
        ram.seed(0x0000000144423B04L, 4, 0x60000014L);
        ram.seed(0x0000000144423B08L, 4, 0x10000015L);
        ram.seed(0x0000000144423B0CL, 4, 0x60000015L);
        ram.seed(0x0000000144423B10L, 4, 0x10000016L);
        ram.seed(0x0000000144423B14L, 4, 0x60000016L);
        ram.seed(0x0000000144423B18L, 4, 0x10000017L);
        ram.seed(0x0000000144423B1CL, 4, 0x60000017L);
        ram.seed(0x0000000144423B20L, 4, 0x10000018L);
        ram.seed(0x0000000144423B24L, 4, 0x60000018L);
        ram.seed(0x0000000144423B28L, 4, 0x10000019L);
        ram.seed(0x0000000144423B2CL, 4, 0x60000019L);
        ram.seed(0x0000000144423B30L, 4, 0x1000001AL);
        ram.seed(0x0000000144423B34L, 4, 0x6000001AL);
        ram.seed(0x0000000144423B38L, 4, 0x1000001BL);
        ram.seed(0x0000000144423B3CL, 4, 0x6000001BL);
        ram.seed(0x0000000144423B40L, 4, 0x1000001CL);
        ram.seed(0x0000000144423B44L, 4, 0x6000001CL);
        ram.seed(0x0000000144423B48L, 4, 0x1000001DL);
        ram.seed(0x0000000144423B4CL, 4, 0x6000001DL);
        ram.seed(0x0000000144423B50L, 4, 0x1000001EL);
        ram.seed(0x0000000144423B54L, 4, 0x6000001EL);
        ram.seed(0x0000000144423B58L, 4, 0x1000001FL);
        ram.seed(0x0000000144423B5CL, 4, 0x6000001FL);
        ram.seed(0x0000000144423B60L, 4, 0x10000020L);
        ram.seed(0x0000000144423B64L, 4, 0x60000020L);
        ram.seed(0x0000000144423B68L, 4, 0x10000021L);
        ram.seed(0x0000000144423B6CL, 4, 0x60000021L);
        ram.seed(0x0000000144423B70L, 4, 0x10000022L);
        ram.seed(0x0000000144423B74L, 4, 0x60000022L);
        ram.seed(0x0000000144423B78L, 4, 0x10000023L);
        ram.seed(0x0000000144423B7CL, 4, 0x60000023L);
        ram.seed(0x0000000144423B80L, 4, 0x10000024L);
        ram.seed(0x0000000144423B84L, 4, 0x60000024L);
        ram.seed(0x0000000144423B88L, 4, 0x10000025L);
        ram.seed(0x0000000144423B8CL, 4, 0x60000025L);
        ram.seed(0x0000000144423B90L, 4, 0x10000026L);
        ram.seed(0x0000000144423B94L, 4, 0x60000026L);
        ram.seed(0x0000000144423B98L, 4, 0x10000027L);
        ram.seed(0x0000000144423B9CL, 4, 0x60000027L);
        ram.seed(0x0000000144423BA0L, 4, 0x10000028L);
        ram.seed(0x0000000144423BA4L, 4, 0x60000028L);
        ram.seed(0x0000000144423BA8L, 4, 0x10000029L);
        ram.seed(0x0000000144423BACL, 4, 0x60000029L);
        ram.seed(0x0000000144423BB0L, 4, 0x1000002AL);
        ram.seed(0x0000000144423BB4L, 4, 0x6000002AL);
        ram.seed(0x0000000144423BB8L, 4, 0x1000002BL);
        ram.seed(0x0000000144423BBCL, 4, 0x6000002BL);
        ram.seed(0x0000000144423BC0L, 4, 0x1000002CL);
        ram.seed(0x0000000144423BC4L, 4, 0x6000002CL);
        ram.seed(0x00000000001A0008L, 8, 0x0000000140456780L);
        return ram;
    }

    /** null value means an injected ordinary exception before any value is returned. */
    private record Read(String operation, long addressBits, Long valueBits) { }

    /**
     * Strict plain byte RAM. Reads never change data or route control through side effects.
     * The only injected behavior is the requested ordinary exception at an explicit access.
     */
    private static final class Ram implements GovernmentCrtBoundary185Api.Memory {
        private final Map<Long, Integer> bytes = new TreeMap<>();
        private final List<Read> reads = new ArrayList<>();
        private String failingOperation;
        private long failingAddress;
        private RuntimeException ordinary;
        private int retAttempts;
        private int writeAttempts;

        void inject(String operation, long address, RuntimeException failure) {
            failingOperation = operation;
            failingAddress = address;
            ordinary = failure;
        }

        void seed(long address, int width, long value) {
            for (int i = 0; i < width; i++) {
                bytes.put(address + i, (int) ((value >>> (8 * i)) & 0xFFL));
            }
        }

        private long peek(long address, int width) {
            long value = 0;
            for (int i = 0; i < width; i++) {
                Integer oneByte = bytes.get(address + i);
                if (oneByte == null) throw new AssertionError(
                        "Unseeded owned byte " + Long.toHexString(address + i));
                value |= ((long) oneByte) << (8 * i);
            }
            return value;
        }

        private long read(String operation, long address, int width) {
            if (operation.equals("R8")) retAttempts++;
            if (ordinary != null && operation.equals(failingOperation) && address == failingAddress) {
                reads.add(new Read(operation, address, null));
                throw ordinary;
            }
            long value = peek(address, width);
            reads.add(new Read(operation, address, value));
            return value;
        }

        @Override public int readDword(long address) {
            return (int) read("R4", address, 4);
        }

        @Override public long readQword(long address) {
            return read("R8", address, 8);
        }

        private AssertionError unexpectedWrite() {
            writeAttempts++;
            return new AssertionError("Unexpected write: held leaf has no store");
        }

        @Override public void writeDword(long address, int value) {
            throw unexpectedWrite();
        }

        @Override public void writeQword(long address, long value) {
            throw unexpectedWrite();
        }

        @Override public void writeByte(long address, int value) {
            throw unexpectedWrite();
        }

        @Override public void write128(long address, Bits128 value) {
            throw unexpectedWrite();
        }

        @Override public int lockedXaddDword(long address, int addend) {
            throw unexpectedWrite();
        }

        @Override public int readUnsignedByte(long address) {
            throw new AssertionError("Unexpected byte read");
        }

        @Override public Bits128 read128(long address) {
            throw new AssertionError("Unexpected 128-bit read");
        }
    }

    private static void equal(Object expected, Object actual, String label) {
        if (!Objects.equals(expected, actual)) throw new AssertionError(
                label + "\nexpected=" + expected + "\nactual=" + actual);
    }

    private static void equalLong(long expected, long actual, String label) {
        if (expected != actual) throw new AssertionError(label + ": expected="
                + Long.toHexString(expected) + " actual=" + Long.toHexString(actual));
    }

    private static void same(Object expected, Object actual, String label) {
        if (expected != actual) throw new AssertionError(label + ": exception identity changed");
    }
}
