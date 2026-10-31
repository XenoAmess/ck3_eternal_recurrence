package org.xar.ck3.control.g2.m2.nativecode;

import java.util.List;
import org.xar.ck3.control.g2.m2.nativecode.PendingContextTailWitness271Api.*;

/** Independent finite literals from the complete original 129 bytes, with controlled opaque effects. */
public final class PendingContextTailWitnessBook271 {
    private PendingContextTailWitnessBook271() { }
    private static Step mem(Kind kind,long address,long value) {
        return new Step(kind,address,value,List.of(),0L,List.of());
    }
    public static List<Scene> scenes() {
        long d0=0xA100000000000010L,s0=0xB200000000000020L;
        Scene empty=new Scene("null-object",d0,s0,
                List.of(new Cell(s0,8,0L),new Cell(d0,8,0xFFFFFFFF00000001L)),
                List.of(mem(Kind.R64,s0,0L),mem(Kind.W64,d0,0L)),d0,
                List.of(new Cell(s0,8,0L),new Cell(d0,8,0L)));
        long dest=0x8100000000000100L,source=0x8200000000000200L,object=0x8300000000000300L;
        long table=0x8400000000000400L,entry=0x8500000000000500L,vtable=0x8600000000000600L;
        long target=0x8700000000000700L,captured=0xF123456789ABCDEFL;
        long changed=0xE23456789ABCDEF0L,written=0xFEDCBA9876543210L;
        long slot=table+255L*64L+0x38L;
        Scene success=new Scene("raw-ff-captured-source-pointer",dest,source,
                List.of(new Cell(source,8,object),new Cell(object+0x26F8L,1,0xFFL),
                        new Cell(source+0x330L,8,captured),new Cell(dest,8,0xAAAAAAAA55555555L),
                        new Cell(slot,8,entry),new Cell(entry,8,vtable),new Cell(vtable+0x10L,8,target)),
                List.of(mem(Kind.R64,source,object),mem(Kind.R8,object+0x26F8L,0xFFL),
                        mem(Kind.R64,source+0x330L,captured),
                        new Step(Kind.HELPER,0L,0L,List.of(dest,source),table,
                                List.of(new Cell(source+0x330L,8,changed))),
                        mem(Kind.R64,slot,entry),mem(Kind.R64,entry,vtable),mem(Kind.R64,vtable+0x10L,target),
                        new Step(Kind.VIRTUAL,0L,0L,List.of(target,entry,dest,captured),0L,
                                List.of(new Cell(dest,8,written)))),dest,
                List.of(new Cell(source,8,object),new Cell(object+0x26F8L,1,0xFFL),
                        new Cell(source+0x330L,8,changed),new Cell(dest,8,written),
                        new Cell(slot,8,entry),new Cell(entry,8,vtable),new Cell(vtable+0x10L,8,target)));
        return List.of(empty,success);
    }
}
