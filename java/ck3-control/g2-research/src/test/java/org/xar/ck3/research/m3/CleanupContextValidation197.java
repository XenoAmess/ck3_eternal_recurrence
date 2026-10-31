package org.xar.ck3.research.m3;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.control.g2.common.nativecore.task.captured.RequestE92780;
import org.xar.ck3.control.g2.common.nativecore.task.captured.m4cleanup.lower61.Lower61Inputs;
import org.xar.ck3.research.m3.CleanupContextBook197.Cell;
import org.xar.ck3.research.m3.CleanupContextBook197.Entry;
import org.xar.ck3.research.m3.CleanupContextBook197.Event;
import org.xar.ck3.research.m3.CleanupContextBook197.Expected;
import org.xar.ck3.research.m3.CleanupContextBook197.Kind;
import org.xar.ck3.research.m3.CleanupContextBook197.Scenario;

/** Owner mechanical byte-memory runner; literal expectations belong to the independent Book. */
public final class CleanupContextValidation197 {
    private CleanupContextValidation197() { }

    public static void main(String[] args) {
        List<Scenario> scenarios=CleanupContextBook197.cases();
        if(scenarios.isEmpty() || scenarios.size()>8) throw new AssertionError("197 finite Book size");
        int totalEvents=0, totalCalls=0, totalFinalCells=0;
        for(Scenario scenario:scenarios) {
            Script script=new Script(scenario);
            Expected observed;
            if(scenario.entry()==Entry.CORE) {
                if(scenario.expectedPlanPath().isEmpty()) throw new AssertionError("CORE path expectation missing");
                CleanupContext197Api.Result result=CleanupContext197.execute(scenario.moduleBase(),scenario.storage(),script,script);
                observed=switch(result.completion()) {
                    case RETURNED -> Expected.RETURNED;
                    case UNSUPPORTED_ERROR_BRANCH -> Expected.UNSUPPORTED_RESULT;
                };
                if(result.plan().path()!=scenario.expectedPlanPath().orElseThrow())
                    throw new AssertionError(scenario.id()+" Plan path mismatch");
            } else {
                if(scenario.expectedPlanPath().isPresent()) throw new AssertionError("Non-CORE path not externally exposed");
                MoveSlotCleanupContextBinding197 binding=MoveSlotCleanupContextBinding197.bind(scenario.moduleBase(),script,script);
                if(script.cursor!=0 || script.calls!=0) throw new AssertionError("Binding constructor observed input");
                if(scenario.entry()==Entry.MOVE_SLOT) {
                    if(scenario.storage()!=scenario.bucket()+8L) throw new AssertionError("Actual193 destination storage");
                    observed=Expected.RETURNED;
                    try {
                        MoveSlot193.move(script,binding,scenario.bucket(),scenario.probe(),scenario.hash(),scenario.sourceDescriptor());
                    } catch(IllegalStateException unsupported) {
                        if(unsupported.getMessage()==null || !unsupported.getMessage().contains("UNSUPPORTED_ERROR_BRANCH")) throw unsupported;
                        observed=Expected.THREW_UNSUPPORTED;
                    }
                } else if(scenario.entry()==Entry.FOREIGN_CALLBACK) {
                    Script foreign=new Script(scenario);
                    Map<Long,Byte> before=Map.copyOf(foreign.bytes);
                    boolean rejected=false;
                    try {
                        binding.call856050(foreign,scenario.storage());
                    } catch(IllegalArgumentException expected) {
                        rejected=true;
                    }
                    if(!rejected || foreign.cursor!=0 || foreign.calls!=0 || !before.equals(foreign.bytes))
                        throw new AssertionError("Foreign callback did not reject before touching foreign memory");
                    observed=Expected.THREW_FOREIGN;
                } else {
                    throw new AssertionError("Unexpected entry");
                }
            }
            if(observed!=scenario.expectedOutcome()) throw new AssertionError(scenario.id()+" software outcome "+observed);
            if(script.cursor!=scenario.expectedEvents().size()) throw new AssertionError(scenario.id()+" unconsumed events "+script.cursor);
            for(Cell cell:scenario.finalCells()) script.verify(cell);
            totalEvents+=script.cursor;
            totalCalls+=script.calls;
            totalFinalCells+=scenario.finalCells().size();
            System.out.println("197 id="+scenario.id()+" outcome="+observed+" events="+script.cursor
                    +" lowerCalls="+script.calls+" finalCells="+scenario.finalCells().size());
        }
        System.out.println("197 scenarios="+scenarios.size()+" events="+totalEvents+" lowerCalls="+totalCalls+" finalCells="+totalFinalCells);
    }

    private static final class Script implements CleanupContext197Api.Memory, Lower61Inputs.Calls {
        private final Scenario scenario;
        private final Map<Long,Byte> bytes=new HashMap<>();
        private int cursor;
        private int calls;

        Script(Scenario scenario) {
            this.scenario=scenario;
            for(Cell cell:scenario.initialCells()) seed(cell);
        }

        private static void checkWidth(int width) {
            if(width!=1 && width!=2 && width!=4 && width!=8 && width!=16)
                throw new AssertionError("Unsupported fixture width "+width);
        }

        private void seed(Cell cell) {
            checkWidth(cell.byteWidth());
            if(cell.byteWidth()==16) {
                writeBytes(cell.address(),8,cell.low());
                writeBytes(cell.address()+8L,8,cell.high());
            } else writeBytes(cell.address(),cell.byteWidth(),cell.low());
        }

        private void verify(Cell cell) {
            checkWidth(cell.byteWidth());
            for(int i=0;i<cell.byteWidth();i++) {
                long address=cell.address()+i;
                Byte actual=bytes.get(address);
                long bits=i<8 ? cell.low():cell.high();
                byte expected=(byte)(bits >>> (8*(i&7)));
                if(actual==null || actual.byteValue()!=expected)
                    throw new AssertionError(scenario.id()+" final byte "+Long.toUnsignedString(address,16));
            }
        }

        private long readBytes(long address,int width) {
            long value=0;
            for(int i=0;i<width;i++) {
                Byte one=bytes.get(address+i);
                if(one==null) throw new AssertionError(scenario.id()+" unmapped read "+Long.toUnsignedString(address+i,16));
                value|=((long)one.byteValue() & 0xFFL) << (8*i);
            }
            return value;
        }

        private void writeBytes(long address,int width,long value) {
            for(int i=0;i<width;i++) bytes.put(address+i,(byte)(value >>> (8*i)));
        }

        private void observe(Kind kind,long address,long arg0,long arg1,long result) {
            Event actual=new Event(kind,address,arg0,arg1,result);
            if(cursor>=scenario.expectedEvents().size()) throw new AssertionError(scenario.id()+" unexpected event "+actual);
            Event expected=scenario.expectedEvents().get(cursor);
            if(!expected.equals(actual)) throw new AssertionError(scenario.id()+" event "+cursor+" expected="+expected+" actual="+actual);
            cursor++;
        }

        @Override public long readPointer(long address) {
            long value=readBytes(address,8);
            observe(Kind.READ_POINTER,address,0,0,value);
            return value;
        }

        @Override public int readInt32(long address) {
            int value=(int)readBytes(address,4);
            observe(Kind.READ_INT32,address,0,0,value);
            return value;
        }

        @Override public void writeInt32(long address,int value) {
            observe(Kind.WRITE_INT32,address,value,0,0);
            writeBytes(address,4,Integer.toUnsignedLong(value));
        }

        @Override public void writeInt64(long address,long value) {
            observe(Kind.WRITE_INT64,address,value,0,0);
            writeBytes(address,8,value);
        }

        @Override public int readUnsignedByte(long address) {
            int value=(int)readBytes(address,1);
            observe(Kind.READ_BYTE,address,0,0,value);
            return value;
        }

        @Override public void writeByte(long address,byte value) {
            observe(Kind.WRITE_BYTE,address,Byte.toUnsignedInt(value),0,0);
            writeBytes(address,1,Byte.toUnsignedInt(value));
        }

        @Override public void writeInt16(long address,short value) {
            observe(Kind.WRITE_INT16,address,value,0,0);
            writeBytes(address,2,Short.toUnsignedInt(value));
        }

        @Override public RequestE92780.Raw128 readRaw128(long address) {
            long low=readBytes(address,8), high=readBytes(address+8L,8);
            observe(Kind.READ_RAW128,address,low,high,0);
            return new RequestE92780.Raw128(low,high);
        }

        @Override public void writeRaw128(long address,RequestE92780.Raw128 value) {
            observe(Kind.WRITE_RAW128,address,value.low(),value.high(),0);
            writeBytes(address,8,value.low());
            writeBytes(address+8L,8,value.high());
        }

        @Override public int callSlot43DA748(Lower61Inputs.FirstCall known) {
            int bits=scenario.lowerReturns().firstCallBits();
            observe(Kind.FIRST_CALL,known.rcxRaw(),known.rdxRaw(),known.r8Raw(),Integer.toUnsignedLong(bits));
            calls++;
            return bits;
        }

        @Override public long call423B18C() {
            long destination=scenario.lowerReturns().failureCellAddress();
            observe(Kind.FAILURE_CELL,0,0,0,destination);
            calls++;
            return destination;
        }

        @Override public int callSlot43DA738() {
            int bits=scenario.lowerReturns().lastErrorBits();
            observe(Kind.LAST_ERROR,0,0,0,Integer.toUnsignedLong(bits));
            calls++;
            return bits;
        }

        @Override public int call423B0D4(long knownRcxRaw) {
            int bits=scenario.lowerReturns().mappedBits();
            observe(Kind.MAP_CODE,knownRcxRaw,0,0,Integer.toUnsignedLong(bits));
            calls++;
            return bits;
        }
    }
}
