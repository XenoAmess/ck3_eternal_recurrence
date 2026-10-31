package org.xar.ck3.research.m5;
import java.util.HashMap;
import java.util.Map;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.*;
import org.xar.ck3.research.m5.GovernmentCrtCallee186WitnessApi.*;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

public final class GovernmentCrtCallee186WitnessRunner {
 private GovernmentCrtCallee186WitnessRunner() { }
 public static int verifyAll(Book book) { int count=0;for(var witness:book.witnesses()){verify(witness);count++;}return count; }
 public static void verify(Witness witness) {
  Session s=new Session(witness);
  NormalReturn actual=switch(witness.subject()) {
   case CALLEE -> GovernmentCrtCallee186.execute(witness.entry(),s.memory,s);
   case CALLER_3F24 -> GovernmentCrtBoundary185.execute3F24(witness.entry(),s.memory,GovernmentCrtCallee186Calls.bind(witness.entry().imageBaseBits(),s.memory,s));
  };
  equal(witness,"full normal return",witness.expected(),actual);
  equal(witness,"complete final byte map",witness.expectedFinalBytes(),s.bytes);
  equal(witness,"complete event cursor",witness.events().size(),s.cursor);
 }
 private static void equal(Witness w,String field,Object expected,Object actual) {
  if(!expected.equals(actual))throw new AssertionError(w.name()+" "+field+": expected="+expected+" actual="+actual);
 }
 private static void byteValues(Map<Long,Integer> bytes) {
  for(var entry:bytes.entrySet())if(entry.getValue()==null||entry.getValue()<0||entry.getValue()>255)throw new AssertionError("Not an unsigned byte at "+entry.getKey());
 }
 private static final class Session implements Calls {
  final Witness witness; final Map<Long,Integer> bytes; final MemoryImpl memory; int cursor;
  Session(Witness witness) { this.witness=witness;byteValues(witness.memorySeed());bytes=new HashMap<>(witness.memorySeed());memory=new MemoryImpl(bytes); }
  @Override public VolatileBits invoke(Call call) {
   if(cursor>=witness.events().size())throw new AssertionError(witness.name()+" unexpected call "+call);
   CallStep event=witness.events().get(cursor++);
   equal(witness,"full call frame",event.expected(),call);
   equal(witness,"complete bytes before call",event.expectedMemoryBefore(),bytes);
   byteValues(event.mutation());bytes.putAll(event.mutation());return event.normalPost();
  }
  @Override public NormalReturn tail(Tail transfer) {throw new AssertionError(witness.name()+" unexpected tail "+transfer);}
  @Override public long readGsQword58() {throw new AssertionError(witness.name()+" unexpected GS");}
 }
    static final class MemoryImpl implements Memory {
        private final Map<Long, Integer> map;
        MemoryImpl(Map<Long, Integer> map) { this.map = map; }

        private int getByte(long addr) {
            Integer v = map.get(addr);
            if (v == null) throw new AssertionError("Missing byte at " + Long.toHexString(addr));
            return v;
        }

        private void putByte(long addr, int val) {
            map.put(addr, val & 0xFF);
        }

        @Override
        public int readDword(long addressBits) {
            long a = addressBits;
            int b0 = getByte(a);
            int b1 = getByte(a + 1);
            int b2 = getByte(a + 2);
            int b3 = getByte(a + 3);
            return (b0) | (b1 << 8) | (b2 << 16) | (b3 << 24);
        }

        @Override
        public long readQword(long addressBits) {
            long a = addressBits;
            long v = 0;
            for (int i = 0; i < 8; i++) {
                v |= ((long) getByte(a + i)) << (i * 8);
            }
            return v;
        }

        @Override
        public int readUnsignedByte(long addressBits) {
            return getByte(addressBits);
        }

        @Override
        public void writeDword(long addressBits, int valueBits) {
            long a = addressBits;
            putByte(a, valueBits);
            putByte(a + 1, valueBits >>> 8);
            putByte(a + 2, valueBits >>> 16);
            putByte(a + 3, valueBits >>> 24);
        }

        @Override
        public int lockedXaddDword(long addressBits, int addendBits) {
            throw new UnsupportedOperationException("Atomic operations not supported");
        }

        @Override
        public void writeQword(long addressBits, long valueBits) {
            long a = addressBits;
            for (int i = 0; i < 8; i++) {
                putByte(a + i, (int) (valueBits >>> (i * 8)));
            }
        }

        @Override
        public void writeByte(long addressBits, int lowByteBits) {
            putByte(addressBits, lowByteBits);
        }

        @Override
        public Bits128 read128(long addressBits) {
            long a = addressBits;
            long low = 0;
            for (int i = 0; i < 8; i++) {
                low |= ((long) getByte(a + i)) << (i * 8);
            }
            long high = 0;
            for (int i = 0; i < 8; i++) {
                high |= ((long) getByte(a + 8 + i)) << (i * 8);
            }
            return new Bits128(low, high);
        }

        @Override
        public void write128(long addressBits, Bits128 valueBits) {
            long a = addressBits;
            long low = valueBits.lowBits();
            long high = valueBits.highBits();
            for (int i = 0; i < 8; i++) {
                putByte(a + i, (int) (low >>> (i * 8)));
            }
            for (int i = 0; i < 8; i++) {
                putByte(a + 8 + i, (int) (high >>> (i * 8)));
            }
        }
    }


}
