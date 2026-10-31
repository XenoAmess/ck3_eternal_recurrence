package org.xar.ck3.control.g2.m2.nativecode;

import java.util.ArrayList;
import java.util.List;
import static org.xar.ck3.control.g2.m2.nativecode.PendingSlotWitness188.*;
import static org.xar.ck3.control.g2.m2.nativecode.PendingSlotWitness188.Op.*;

/** Owner literal callback sequences, not a second implementation of the producer. */
public final class PendingSlotProducerSuccessWitness188 {
    private PendingSlotProducerSuccessWitness188() { }
    private static final long MODULE=0x100000000L;
    private static final PendingSlotProducer2A32770.Input INPUT=new PendingSlotProducer2A32770.Input(
        0x1000L,0x2000L,0xc000L,0xb000L,0xa000L,0x9000L,MODULE);
    private static void add(List<Step> result,Step... values) { result.addAll(List.of(values)); }
    /** Literal expected writes of the supplied real459B callee at this new caller edge.
     * The witness never invokes initialize to generate its expectations; produce must do the work.
     */
    private static void initializerWrites(List<Step> result,long component) {
        long[][] qwords={
            {0x18,0xf},{0,0},{0x78,0},{0x88,0},{0x90,0xf},{0x98,0},{0xa8,0},{0xb0,0xf},
            {0xb8,0},{0xc8,0},{0xd0,0xf},{0xd8,0},{0xe0,0},{0xe8,0x1054e62d8L},{0x1e8,component+0x78},
            {0x10,0},{0x20,0},{0x30,0},{0x38,0xf},{0x40,0},{0x50,0},{0x58,0xf},{0x60,0},{0x68,0},
            {0x70,0x1054e62d8L},{0xf0,0},{0x100,0},{0x108,0xf},{0x110,0},{0x120,0},{0x128,0xf},
            {0x130,0},{0x140,0},{0x148,0xf},{0x150,0},{0x158,0},{0x160,0x1054e62d8L},
            {0x168,0},{0x178,0},{0x180,0xf},{0x188,0},{0x198,0},{0x1a0,0xf},{0x1a8,0},{0x1b8,0},
            {0x1c0,0xf},{0x1c8,0},{0x1d0,0},{0x1d8,0x1054e62d8L},{0x1e0,component},{0x1f0,0},
            {0x200,0},{0x208,0xf},{0x210,0},{0x220,0},{0x228,0xf},{0x230,0},{0x240,0},{0x248,0xf},{0x250,-1L}
        };
        for(long[] qword:qwords) result.add(e(W64,component+qword[0],qword[1]));
        add(result,e(W32,component+0x258,0xffffffffL),e(W8,component+0x25c,0),
            e(W32,component+0x260,0),e(W8,component+0x264,1));
    }
    public static void main(String[] args) { normalFreshTables(); growAndGenerationWrap(); }
    private static void normalFreshTables() {
        long object=0x10000000000015c8L;
        List<Step> steps=new ArrayList<>();
        add(steps,
            e(R8,0x1048L,0),e(R8,0x1049L,0),e(R32,0x1040L,1),e(R32,0x1040L,1),c(PAGE,0x1008L,2,1),
            e(R64,0x1008L,0x5000L),e(R64,0x5000L,0x1000000000001000L),e(R64,0x1020L,0x6000L),
            e(R32,0x6010L,2),e(W32,0x1040L,2),e(R32,0x6010L,3),e(W32,0x6034L,0xffffffL),
            e(R64,0x1020L,0x7000L),e(W32,0x7010L,0xffffffL),e(R64,0x1020L,0x8000L),
            e(R32,0x103cL,10),e(W32,0x103cL,11),e(W8,0x104aL,1),e(R32,object+0x10,0x2a123456L),
            e(W64,0x8018L,object),e(R32,0x1038L,0xffffffffL),e(W32,0x1038L,1),
            e(R32,0x9000L,1),e(R8,0xa000L,2),e(R8,0xb000L,1),e(R32,0xc000L,0xdeadbeefL),
            e(W32,object+0x10,0xffffffffL),e(W32,object+0x14,0x4368496eL),
            e(W64,object,0x104759250L),e(W64,object+8,0x104759288L),c(COPY,object+0x18,0x2000L,0)
        );
        initializerWrites(steps,0x1000000000001918L);
        add(steps,e(W32,object+0x5b8,0),e(W32,object+0x5bc,0xdeadbeefL),e(R32,0x22e8L,0xffffffffL),
            e(W32,object+0x5c0,0),e(W8,object+0x5c4,1),e(W8,object+0x5c5,0),e(W8,object+0x5c6,1),
            e(W32,object+0x10,0x2b000001L));
        run("normal-fresh-next-and-three-tables",INPUT,steps,object);
    }
    private static void growAndGenerationWrap() {
        long object=0x7000000000000b90L;
        List<Step> steps=new ArrayList<>();
        add(steps,
            e(R8,0x1048L,0),e(R8,0x1049L,0),e(R32,0x1040L,0xffffffL),e(R32,0x102cL,4),c(GROW,0x1008L,8,1),
            e(R32,0x1040L,2),c(PAGE,0x1008L,3,1),e(R64,0x1008L,0x5000L),e(R64,0x5000L,0x7000000000000000L),
            e(R64,0x1020L,0x6000L),e(R32,0x6020L,0xffffffL),e(W32,0x1040L,0xffffffL),e(R32,0x6020L,0xffffffL),
            e(R32,0x103cL,0xffffffffL),e(W32,0x103cL,0),e(W8,0x104aL,1),e(R32,object+0x10,0xff123456L),
            e(W64,0x6028L,object),e(R32,0x1038L,3),
            e(R32,0x9000L,2),e(R8,0xa000L,1),e(R8,0xb000L,2),e(R32,0xc000L,0x80000000L),
            e(W32,object+0x10,0xffffffffL),e(W32,object+0x14,0x4368496eL),
            e(W64,object,0x104759250L),e(W64,object+8,0x104759288L),c(COPY,object+0x18,0x2000L,0)
        );
        initializerWrites(steps,0x7000000000000ee0L);
        add(steps,e(W32,object+0x5b8,0),e(W32,object+0x5bc,0x80000000L),e(R32,0x22e8L,0),
            e(W32,object+0x5c0,1),e(W8,object+0x5c4,0),e(W8,object+0x5c5,1),e(W8,object+0x5c6,0),
            e(W32,object+0x10,2));
        run("grow-success-wrap-generation-and-count",INPUT,steps,object);
    }
}
