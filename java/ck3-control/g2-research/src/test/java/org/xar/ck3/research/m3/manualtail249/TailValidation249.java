package org.xar.ck3.research.m3.manualtail249;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.OptionalLong;
import java.util.function.LongConsumer;
import org.xar.ck3.research.m3.f8a8242.F8a8Api242;
import org.xar.ck3.research.m3.callee246.Callee68fcApi246;
import org.xar.ck3.research.m3.fa90245.Fa90Api245;
import org.xar.ck3.research.m3.fa90245.Fa90Target424FA90;
import org.xar.ck3.research.m3.tail249.Tail6670Api249;
import org.xar.ck3.research.m3.tail249.Tail4256670249;
import org.xar.ck3.research.m3.tail249.Tail6670FromFa90Binding249;
public final class TailValidation249 {
 private TailValidation249() { }
 private static int checks,groups,events,ramEvents,ports,opaqueEffects,atomicEvents;
 private static void check(boolean b,String label){checks++;if(!b)throw new AssertionError(label);}
 private static String h(long v){return Long.toUnsignedString(v,16);}
 private static String rw(String k,long a,long v){return k+":"+h(a)+":"+h(v);}
 private static final class Ram implements Callee68fcApi246.Memory {
  final Map<Long,Byte> bytes=new HashMap<>();final List<String> trace=new ArrayList<>();LongConsumer afterAtomic;int atomicCalls;
  private long raw(long a,int w){long v=0;for(int n=0;n<w;n++){Byte b=bytes.get(a+n);if(b==null)throw new AssertionError("unmapped "+h(a+n));v|=(b.longValue()&255L)<<(8*n);}return v;}
  private void store(long a,int w,long v){for(int n=0;n<w;n++)bytes.put(a+n,(byte)(v>>>(8*n)));}
  void seed8(long a,int v){check((v&~255)==0,"seed8 width");store(a,1,v);}
  void seed32(long a,int v){store(a,4,Integer.toUnsignedLong(v));}
  void seed64(long a,long v){store(a,8,v);}
  void effect32(long a,int v){trace.add(rw("E32",a,Integer.toUnsignedLong(v)));store(a,4,Integer.toUnsignedLong(v));}
  void effect64(long a,long v){trace.add(rw("E64",a,v));store(a,8,v);}
  Map<Long,Byte> snapshot(){return Map.copyOf(bytes);}
  @Override public long readPointer(long a){long v=raw(a,8);trace.add(rw("R64",a,v));return v;}
  @Override public int readInt32(long a){long v=raw(a,4);trace.add(rw("R32",a,v));return (int)v;}
  @Override public void writeInt32(long a,int v){trace.add(rw("W32",a,Integer.toUnsignedLong(v)));store(a,4,Integer.toUnsignedLong(v));}
  @Override public void writeInt64(long a,long v){trace.add(rw("W64",a,v));store(a,8,v);}
  @Override public void writeInt16(long a,int v){trace.add(rw("W16",a,v&65535L));store(a,2,v);}
  @Override public void atomicAddInt32(long a,int delta){long before=raw(a,4),after=(before+Integer.toUnsignedLong(delta))&0xFFFFFFFFL;store(a,4,after);atomicCalls++;trace.add("A32:"+h(a)+":"+h(Integer.toUnsignedLong(delta))+":"+h(before)+":"+h(after));if(afterAtomic!=null)afterAtomic.accept(a);}
 }
 private abstract static class TailBase implements Tail6670Api249.Ports {
  @Override public void tail4256874(Callee68fcApi246.Memory m,long site,long rcx,long rdx,long rax,long r8){throw new AssertionError("unexpected tail");}
 }
 private abstract static class PortsBase implements Fa90Api245.Ports {
  @Override public void call42568fc(F8a8Api242.Memory m,long site,long rcx,long rdx,long rax){throw new AssertionError("unexpected first");}
  @Override public void call42566fc(F8a8Api242.Memory m,long site,long rcx,long rax){throw new AssertionError("unexpected second");}
  @Override public void call4256670(F8a8Api242.Memory m,long site,long rcx,OptionalLong rdx,OptionalLong rax){throw new AssertionError("unexpected third fallback");}
 }
 private static void expectedWrite(Map<Long,Byte> m,long a,int w,long v){for(int n=0;n<w;n++)m.put(a+n,(byte)(v>>>(8*n)));}
 private static void tailEvent(Ram m,long site,long rcx,long rdx,long rax,long r8){m.trace.add("T:"+h(site)+":"+h(rcx)+":"+h(rdx)+":"+h(rax)+":"+h(r8));}
 private static void sameException(Runnable work,RuntimeException marker,String label){try{work.run();}catch(RuntimeException actual){check(actual==marker,label);return;}throw new AssertionError("no original exception "+label);}
 private static void rejected(Runnable work,String label){try{work.run();}catch(RuntimeException actual){checks++;return;}throw new AssertionError("not rejected "+label);}
 private static void complete(Ram m,List<String> expected,Map<Long,Byte> finalBytes,String label){check(m.trace.equals(expected),label+" expected="+expected+" actual="+m.trace);check(m.snapshot().equals(finalBytes),label+" finalbytes");groups++;events+=m.trace.size();for(String event:m.trace){if(event.startsWith("A32:"))atomicEvents++;if(event.startsWith("R")||event.startsWith("W")||event.startsWith("A32:"))ramEvents++;else if(event.startsWith("E"))opaqueEffects++;else ports++;}}

 @FunctionalInterface private interface FirstHook {void call(F8a8Api242.Memory m,long site,long rcx,long rdx,long rax);}
 @FunctionalInterface private interface SecondHook {void call(F8a8Api242.Memory m,long site,long rcx,long rax);}
 private static final class Fallback implements Fa90Api245.Ports {
  private final FirstHook first;private final SecondHook second;
  Fallback(FirstHook first,SecondHook second){this.first=first;this.second=second;}
  @Override public void call42568fc(F8a8Api242.Memory m,long site,long rcx,long rdx,long rax){first.call(m,site,rcx,rdx,rax);}
  @Override public void call42566fc(F8a8Api242.Memory m,long site,long rcx,long rax){second.call(m,site,rcx,rax);}
  @Override public void call4256670(F8a8Api242.Memory m,long site,long rcx,OptionalLong rdx,OptionalLong rax){throw new AssertionError("unexpected THIRD fallback");}
 }
 private static final class TailProbe implements Tail6670Api249.Ports {
  private final Ram ram;private final Tail6670Api249.Ports observer;
  TailProbe(Ram ram,Tail6670Api249.Ports observer){this.ram=ram;this.observer=observer;}
  @Override public void tail4256874(Callee68fcApi246.Memory m,long site,long rcx,long rdx,long rax,long r8){check(m==ram,"tail same original Memory");tailEvent(ram,site,rcx,rdx,rax,r8);observer.tail4256874(m,site,rcx,rdx,rax,r8);}
 }
 private static void direct139(){
  {
   Ram m=new Ram();
  m.seed64(0x10L,0xAABBCCDDFFFFFFFFL);
  m.seed64(0xE0L,0x0L);
  m.seed64(0xF0L,0x0L);
  m.seed64(0xE8L,0x0L);
  m.seed64(0x100L,0x0L);
  m.seed64(0x120L,0xCAFEBABEDEADBEEFL);
   for(int i=0;i<6;i++){m.seed64(0x28L+0x20L*i,0x542F498L);m.seed64(0x20L+0x20L*i,0);}
   m.seed8(0x0F,0xA5);m.seed8(0xF8,0x5A);
  Map<Long,Byte> expected=new HashMap<>(m.snapshot());
  expectedWrite(expected,0x10L,4,0x0L);
   RuntimeException marker=new RuntimeException("original opaque tail");int[] calls={0};
   TailProbe tail=new TailProbe(m,(memory,site,rcx,rdx,rax,r8)->{
    check(site==0x42566F6L&&rcx==0xCAFEBABEDEADBEEFL&&rdx==0x542F498L&&rax==0xF8&&r8==0,"zero entry four full tail knowns");
    calls[0]++;throw marker;
   });
   sameException(()->Tail4256670249.execute(m,tail,new Tail6670Api249.Input(0,0)),marker,"opaque tail exception original identity");
   check(calls[0]==1&&m.atomicCalls==1,"zero entry still one unconditional INC and tail");
   complete(m,ZERO_TRACE,expected,"zero entry and full opaque tail");
  }
  {
   Ram m=new Ram();
  m.seed64(0x1010L,0x11223344FFFFFFFFL);
  m.seed64(0x10E0L,0x10F0L);
  m.seed64(0x10F0L,0x2000L);
  m.seed64(0x2001L,0xABCDEF01FFFFFFFFL);
  m.seed64(0x10E8L,0x1100L);
  m.seed64(0x1100L,0x3FFFL);
  m.seed64(0x4000L,0xCAFEBABE80000000L);
  m.seed64(0x1028L,0x0L);
  m.seed64(0x1038L,0x1020L);
  m.seed64(0x1020L,0x0L);
  m.seed64(0x1030L,0x6000L);
  m.seed64(0x6000L,0xDEADBEEF7FFFFFFFL);
  m.seed64(0x1048L,0x10542F498L);
  m.seed64(0x1040L,0x1L);
  m.seed64(0x1050L,0x0L);
  m.seed64(0x1068L,0x0L);
  m.seed64(0x1078L,0x1088L);
  m.seed64(0x1060L,0x0L);
  m.seed64(0x1088L,0x10542F498L);
  m.seed64(0x1098L,0x8000L);
  m.seed64(0x8000L,0x11223344FFFFFFFFL);
  m.seed64(0x1080L,0x0L);
  m.seed64(0x10A8L,0x10542F498L);
  m.seed64(0x10A0L,0x0L);
  m.seed64(0x10C8L,0x0L);
  m.seed64(0x10D8L,0x0L);
  m.seed64(0x10C0L,0x0L);
  m.seed64(0x1120L,0x0L);
   m.seed8(0x100F,0xA5);m.seed8(0x2000,0xB6);m.seed8(0x2009,0xC7);m.seed8(0x4008,0xD8);
  Map<Long,Byte> expected=new HashMap<>(m.snapshot());
  expectedWrite(expected,0x1010L,4,0x0L);
  expectedWrite(expected,0x10F0L,4,0x2001L);
  expectedWrite(expected,0x2001L,4,0x0L);
  expectedWrite(expected,0x1100L,4,0x4000L);
  expectedWrite(expected,0x4000L,4,0x80000001L);
  expectedWrite(expected,0x1020L,4,0x1L);
  expectedWrite(expected,0x6000L,4,0x80000000L);
  expectedWrite(expected,0x1088L,4,0x542F499L);
  expectedWrite(expected,0x8000L,4,0x0L);
   int[] calls={0};
   TailProbe tail=new TailProbe(m,(memory,site,rcx,rdx,rax,r8)->{
    check(site==0x42566F6L&&rcx==0&&rdx==0&&rax==0x10F8&&r8==0,"last reached zero candidate overwrites sentinel and RCX0 still tail");calls[0]++;
   });
   Tail4256670249.execute(m,tail,new Tail6670Api249.Input(0x100000000L,0x1000));
   check(calls[0]==1&&m.atomicCalls==9,"rich exact 9 single atomics");
   complete(m,RICH_TRACE,expected,"interleaved aliases and six independent guards");
  }
 }

 private static void actualFa90Protocol249(){
  Ram m=new Ram();
  m.seed64(0x1090L,0x2000L);
  m.seed64(0x205C5DCD8L,0x4000L);
  m.seed64(0x5010L,0xAABBCCDD00000007L);
  m.seed64(0x50E0L,0x0L);
  m.seed64(0x50F0L,0x0L);
  m.seed64(0x50E8L,0x0L);
  m.seed64(0x5100L,0x0L);
  m.seed64(0x5120L,0x1234L);
  m.seed64(0x50C8L,0x20542F498L);
  m.seed64(0x50C0L,0x1L);
  m.seed64(0x50D0L,0xFEDCBA9876543210L);
  m.seed64(0xFEDCBA9876543210L,0x998877667FFFFFFFL);
  m.seed32(0x3010L,(int)0x0L);
  for(int i=0;i<5;i++){m.seed64(0x5028L+0x20L*i,0x20542F498L);m.seed64(0x5020L+0x20L*i,0);}
  m.seed8(0x108F,0xA5);m.seed8(0x500F,0xB6);m.seed8(0xFEDCBA9876543218L,0xC7);
  Map<Long,Byte> expected=new HashMap<>(m.snapshot());
  expectedWrite(expected,0x5010L,4,0x0L);
  expectedWrite(expected,0xFEDCBA9876543210L,4,0x80000000L);
  expectedWrite(expected,0x1090L,8,0x5000L);
  expectedWrite(expected,0x5120L,8,0x0L);
  int[] first={0},second={0},tails={0};
  Fallback fallback=new Fallback((memory,site,rcx,rdx,rax)->{
   check(memory==m,"actual first original RAM");check(site==0x424FAACL&&rcx==0x2000&&rdx==0x5000&&rax==0xFEDCBA9876543210L,"actual first exact received knowns");
   first[0]++;m.trace.add("P:first:424faac:2000:5000:fedcba9876543210");m.effect64(0x1090,0x3000);
  },(memory,site,rcx,rax)->{
   check(memory==m,"actual second original RAM");check(site==0x424FAD3L&&rcx==0x3000&&rax==0x20542F330L,"actual second fresh selected RCX and known LEA");
   second[0]++;m.trace.add("P:second:424fad3:3000:20542f330");m.effect32(0x5010,-1);m.effect64(0x5120,0);
  });
  TailProbe tail=new TailProbe(m,(memory,site,rcx,rdx,rax,r8)->{
   check(site==0x42566F6L&&rcx==0&&rdx==0xFEDCBA9876543210L&&rax==0x50F8&&r8==0,"actual new third full current tail protocol");tails[0]++;
  });
  Fa90Api245.Ports bound=Tail6670FromFa90Binding249.bind(0x200000000L,m,tail,fallback);
  Fa90Target424FA90.execute(m,bound,new Fa90Api245.Input(0x200000000L,0x1000,0x5000,0xFEDCBA9876543210L));
  check(first[0]==1&&second[0]==1&&tails[0]==1&&m.atomicCalls==2,"actual first/second/third exactly once and leaf2INC");
  complete(m,CHAIN_TRACE,expected,"actual Fa90 cleanup before new third leaf");
 }

 private static final List<String> ZERO_TRACE=List.of(
  "A32:10:1:ffffffff:0",
  "R64:e0:0",
  "R64:f0:0",
  "R64:e8:0",
  "R64:100:0",
  "R64:28:542f498",
  "R64:20:0",
  "R64:48:542f498",
  "R64:40:0",
  "R64:68:542f498",
  "R64:60:0",
  "R64:88:542f498",
  "R64:80:0",
  "R64:a8:542f498",
  "R64:a0:0",
  "R64:c8:542f498",
  "R64:c0:0",
  "R64:120:cafebabedeadbeef",
  "T:42566f6:cafebabedeadbeef:542f498:f8:0");
 private static final List<String> RICH_TRACE=List.of(
  "A32:1010:1:ffffffff:0",
  "R64:10e0:10f0",
  "A32:10f0:1:2000:2001",
  "R64:10f0:2001",
  "A32:2001:1:ffffffff:0",
  "R64:10e8:1100",
  "A32:1100:1:3fff:4000",
  "R64:1100:4000",
  "A32:4000:1:80000000:80000001",
  "R64:1028:0",
  "R64:1038:1020",
  "A32:1020:1:0:1",
  "R64:1020:1",
  "R64:1030:6000",
  "A32:6000:1:7fffffff:80000000",
  "R64:1048:10542f498",
  "R64:1040:1",
  "R64:1050:0",
  "R64:1068:0",
  "R64:1078:1088",
  "A32:1088:1:542f498:542f499",
  "R64:1060:0",
  "R64:1088:10542f499",
  "R64:1098:8000",
  "A32:8000:1:ffffffff:0",
  "R64:1080:0",
  "R64:10a8:10542f498",
  "R64:10a0:0",
  "R64:10c8:0",
  "R64:10d8:0",
  "R64:10c0:0",
  "R64:1120:0",
  "T:42566f6:0:0:10f8:0");
 private static final List<String> CHAIN_TRACE=List.of(
  "R64:1090:2000",
  "P:first:424faac:2000:5000:fedcba9876543210",
  "E64:1090:3000",
  "R64:1090:3000",
  "R64:205c5dcd8:4000",
  "R32:3010:0",
  "P:second:424fad3:3000:20542f330",
  "E32:5010:ffffffff",
  "E64:5120:0",
  "W64:1090:5000",
  "A32:5010:1:ffffffff:0",
  "R64:50e0:0",
  "R64:50f0:0",
  "R64:50e8:0",
  "R64:5100:0",
  "R64:5028:20542f498",
  "R64:5020:0",
  "R64:5048:20542f498",
  "R64:5040:0",
  "R64:5068:20542f498",
  "R64:5060:0",
  "R64:5088:20542f498",
  "R64:5080:0",
  "R64:50a8:20542f498",
  "R64:50a0:0",
  "R64:50c8:20542f498",
  "R64:50c0:1",
  "R64:50d0:fedcba9876543210",
  "A32:fedcba9876543210:1:7fffffff:80000000",
  "R64:5120:0",
  "T:42566f6:0:fedcba9876543210:50f8:0");
 private static final List<String> PROTOCOL_TRACE=List.of(
  "P:first:123456789abcdef0:8000000000000001:ffffffffffffffff:fedcba9876543210",
  "P:second:ffffffffffffffff:fedcba9876543210:8000000000000000",
  "P:firstThrow:ffffffffffffffff:0:8000000000000000:ffffffffffffffff",
  "P:secondThrow:8000000000000000:ffffffffffffffff:0");
 private static void atomicException249(){
  Ram m=new Ram();m.seed64(0x2010,0x1234567800000001L);m.seed64(0x20E0,0x3000);m.seed64(0x3000,0xAABBCCDDFFFFFFFFL);
  Map<Long,Byte> expected=new HashMap<>(m.snapshot());expectedWrite(expected,0x2010,4,2);expectedWrite(expected,0x3000,4,0);
  RuntimeException marker=new RuntimeException("original atomic after-store failure");
  m.afterAtomic=address->{if(address==0x3000)throw marker;};
  sameException(()->Tail4256670249.execute(m,new TailBase(){},new Tail6670Api249.Input(0,0x2000)),marker,"single atomic prefix exception identity");
  check(m.atomicCalls==2,"exact two atomics before failure");
  complete(m,List.of("A32:2010:1:1:2","R64:20e0:3000","A32:3000:1:ffffffff:0"),expected,"atomic exception source prefix");
 }
 private static void protocol249(){
  Ram captured=new Ram(),foreign=new Ram();TailBase forbiddenTail=new TailBase(){};PortsBase forbiddenFallback=new PortsBase(){};
  rejected(()->Tail6670FromFa90Binding249.bind(0,null,forbiddenTail,forbiddenFallback),"null captured");
  rejected(()->Tail6670FromFa90Binding249.bind(0,captured,null,forbiddenFallback),"null child");
  rejected(()->Tail6670FromFa90Binding249.bind(0,captured,forbiddenTail,null),"null fallback");
  Fa90Api245.Ports guarded=Tail6670FromFa90Binding249.bind(0,captured,forbiddenTail,forbiddenFallback);
  rejected(()->guarded.call4256670(foreign,0x424FAE7L,0,OptionalLong.empty(),OptionalLong.empty()),"third foreign before effects");
  rejected(()->guarded.call4256670(captured,0x424FAE6L,0,OptionalLong.empty(),OptionalLong.empty()),"third site before effects");
  check(captured.trace.isEmpty()&&foreign.trace.isEmpty()&&captured.bytes.isEmpty()&&foreign.bytes.isEmpty(),"active/factory zero RAM");
  RuntimeException firstFailure=new RuntimeException("first passive original"),secondFailure=new RuntimeException("second passive original");
  int[] first={0},second={0};
  Fallback fallback=new Fallback((memory,site,rcx,rdx,rax)->{
   check(memory==foreign,"passive first exact foreign identity");first[0]++;
   if(first[0]==1){
    check(site==0x123456789ABCDEF0L&&rcx==0x8000000000000001L&&rdx==-1L&&rax==0xFEDCBA9876543210L,"passive first full64 bits");captured.trace.add("P:first:123456789abcdef0:8000000000000001:ffffffffffffffff:fedcba9876543210");
   }else{
    check(first[0]==2&&site==-1L&&rcx==0&&rdx==Long.MIN_VALUE&&rax==-1L,"passive first throw bits");captured.trace.add("P:firstThrow:ffffffffffffffff:0:8000000000000000:ffffffffffffffff");throw firstFailure;
   }
  },(memory,site,rcx,rax)->{
   check(memory==foreign,"passive second exact foreign identity");second[0]++;
   if(second[0]==1){
    check(site==-1L&&rcx==0xFEDCBA9876543210L&&rax==Long.MIN_VALUE,"passive second full64 bits");captured.trace.add("P:second:ffffffffffffffff:fedcba9876543210:8000000000000000");
   }else{
    check(second[0]==2&&site==Long.MIN_VALUE&&rcx==-1L&&rax==0,"passive second throw bits");captured.trace.add("P:secondThrow:8000000000000000:ffffffffffffffff:0");throw secondFailure;
   }
  });
  Fa90Api245.Ports bound=Tail6670FromFa90Binding249.bind(0,captured,forbiddenTail,fallback);
  Map<Long,Byte> expected=new HashMap<>(captured.snapshot());
  bound.call42568fc(foreign,0x123456789ABCDEF0L,0x8000000000000001L,-1L,0xFEDCBA9876543210L);
  bound.call42566fc(foreign,-1L,0xFEDCBA9876543210L,Long.MIN_VALUE);
  sameException(()->bound.call42568fc(foreign,-1L,0,Long.MIN_VALUE,-1L),firstFailure,"first original passive exception identity");
  sameException(()->bound.call42566fc(foreign,Long.MIN_VALUE,-1L,0),secondFailure,"second original passive exception identity");
  check(first[0]==2&&second[0]==2,"passive callbacks each exactly two separate invocations");
  check(foreign.trace.isEmpty()&&foreign.bytes.isEmpty()&&foreign.atomicCalls==0&&captured.atomicCalls==0,"passive no RAM/child effect");
  complete(captured,PROTOCOL_TRACE,expected,"qualification and precise passive fallback");
 }
 public static void main(String[] args){direct139();atomicException249();actualFa90Protocol249();protocol249();check(groups==5&&events==90&&ramEvents==78&&ports==9&&opaqueEffects==3&&atomicEvents==14,"all current scenario counts");System.out.println("TAIL249_PASS groups="+groups+" orderedEvents="+events+" RAM="+ramEvents+" Ports="+ports+" OpaqueEffects="+opaqueEffects+" AtomicEvents="+atomicEvents+" mixedChecks="+checks+" Native=0 Game=0");}
}
