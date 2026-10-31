package org.xar.ck3.control.g2.m2.nativecode;

import java.util.List;
import static org.xar.ck3.control.g2.m2.nativecode.PendingSlotWitness188.*;
import static org.xar.ck3.control.g2.m2.nativecode.PendingSlotWitness188.Op.*;

/** Owner literal early branches directly from470B; no target execution generates expectations. */
public final class PendingSlotProducerFailureWitness188 {
    private PendingSlotProducerFailureWitness188() { }
    public static void main(String[] args) {
        var input=new PendingSlotProducer2A32770.Input(0x1000L,0x2000L,0xc000L,0xb000L,0xa000L,0x9000L,0x10000000L);
        run("initial-flag-no-phantom-read",input,List.of(
            e(R8,0x1048L,0x80),e(R64,0x15d1ec70L,0xfedcba9876543210L)
        ),0xfedcba9876543210L);
        run("grow-ALfalse-exact-target",input,List.of(
            e(R8,0x1048L,0),e(R8,0x1049L,0),e(R32,0x1040L,0xffffffL),e(R32,0x102cL,0x1000),
            c(GROW,0x1008L,0x2000,0),e(R64,0x15d1ec70L,0x8877665544332211L)
        ),0x8877665544332211L);
        run("page-ALfalse-fresh-head",input,List.of(
            e(R8,0x1048L,0),e(R8,0x1049L,0),e(R32,0x1040L,5),e(R32,0x1040L,5),
            c(PAGE,0x1008L,6,0),e(R64,0x15d1ec70L,0x8000000000000001L)
        ),0x8000000000000001L);
    }
}
