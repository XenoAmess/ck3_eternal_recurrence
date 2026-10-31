package org.xar.ck3.research.m3;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;

/** Owned Java fixture: source-derived literals, never a Native or Game action. */
public final class ClearValidation174 {
    private static int semanticChecks,fixtureChecks;
    private ClearValidation174() { }
    private static void fixture(boolean good,String reason) {
        fixtureChecks++;
        if(!good)throw new AssertionError(reason);
    }
    private static void semantic(boolean good,String reason) {
        semanticChecks++;
        if(!good)throw new AssertionError(reason);
    }
    private static String h(long bits) { return Long.toUnsignedString(bits,16); }
    public static void main(String[] args) {
        List<ClearCasesApi174.Scenario> cases=ClearCases174.cases();
        fixture(cases.size()==8,"eight independent cases");
        for(ClearCasesApi174.Scenario scenario:cases) {
            List<String> events=new ArrayList<>();
            OwnedMemory memory=new OwnedMemory(scenario.initialWords(),events);
            Probe probe=new Probe(scenario,memory,events);
            RegistrationClearApi174.Completion completion=scenario.throughConsumer()
                ? SecondRegistrationConsumer174.invoke(memory,probe,probe,
                    scenario.observedCode(),scenario.selectedCode(),scenario.limits())
                : RegistrationClear174.clear(memory,probe,scenario.receiver(),scenario.limits());
            RecordedClear174.Observation observed=new RecordedClear174.Observation(completion,
                List.copyOf(events),memory.snapshot(),Map.copyOf(probe.applied));
            ClearVerification174.verify(scenario,observed,ClearValidation174::semantic);
            System.out.println(scenario.id()+"|"+completion+"|"+String.join(";",events));
        }
        System.out.println("cases="+cases.size()+" semantic_checks="+semanticChecks
            +" fixture_checks="+fixtureChecks+" Native_execution=0 Game_actions=0 old_green_rerun=0");
    }
    private static final class OwnedMemory implements NativeTaskMemory {
        private final Map<Long,ClearCasesApi174.Word> words=new HashMap<>();
        private final List<String> events;
        private OwnedMemory(List<ClearCasesApi174.Word> initial,List<String> events) {
            words.putAll(RecordedClear174.words(initial));this.events=events;
        }
        private ClearCasesApi174.Word cell(long address,int width) {
            ClearCasesApi174.Word word=words.get(address);
            fixture(word!=null,"mapped fixture word "+h(address));
            fixture(word.width()==width,"exact fixture width "+h(address));
            return word;
        }
        public long readPointer(long address) {
            events.add("R64:"+h(address));return cell(address,8).bits();
        }
        public int readInt32(long address) {
            events.add("R32:"+h(address));return (int)cell(address,4).bits();
        }
        public void writeInt32(long address,int bits) {
            cell(address,4);events.add("W32:"+h(address)+":"+Integer.toUnsignedString(bits,16));
            words.put(address,new ClearCasesApi174.Word(address,4,Integer.toUnsignedLong(bits)));
        }
        public void writeInt64(long address,long bits) {
            cell(address,8);events.add("W64:"+h(address)+":"+h(bits));
            words.put(address,new ClearCasesApi174.Word(address,8,bits));
        }
        private void silent(ClearCasesApi174.Word update) {
            cell(update.address(),update.width());
            long bits=update.width()==4?Integer.toUnsignedLong((int)update.bits()):update.bits();
            words.put(update.address(),new ClearCasesApi174.Word(update.address(),update.width(),bits));
        }
        private Map<Long,ClearCasesApi174.Word> snapshot() { return Map.copyOf(words); }
    }
    private static final class Probe implements RegistrationClearApi174.Ports,RegistrationClearApi174.Singleton {
        private final ClearCasesApi174.Scenario scenario;
        private final OwnedMemory memory;
        private final List<String> events;
        private final Map<ClearCasesApi174.Hook,Integer> applied=new HashMap<>();
        private int destroys,cleanups,singletons;
        private Probe(ClearCasesApi174.Scenario scenario,OwnedMemory memory,List<String> events) {
            this.scenario=scenario;this.memory=memory;this.events=events;
        }
        private void apply(ClearCasesApi174.Event event,int ordinal) {
            for(ClearCasesApi174.Hook hook:scenario.hooks()) {
                if(hook.event()==event&&hook.ordinal()==ordinal) {
                    fixture(applied.getOrDefault(hook,0)==0,"hook once");
                    for(ClearCasesApi174.Word update:hook.changes())memory.silent(update);
                    applied.merge(hook,1,Integer::sum);
                }
            }
        }
        public void destroyRow(NativeTaskMemory observedMemory,long pointee,long row) {
            fixture(observedMemory==memory,"destroy memory identity");
            destroys++;fixture(destroys<=scenario.limits().maxFirstRows(),"bounded destroy callbacks");
            events.add("DESTROY:"+h(pointee)+":"+h(row));
            apply(ClearCasesApi174.Event.DESTROY,destroys);
        }
        public void cleanupField(NativeTaskMemory observedMemory,long field) {
            fixture(observedMemory==memory,"cleanup memory identity");
            cleanups++;
            fixture((long)cleanups<=2L*scenario.limits().maxCleanupRows(),"bounded cleanup callbacks");
            events.add("CLEANUP:"+h(field));apply(ClearCasesApi174.Event.CLEANUP,cleanups);
        }
        public long get() {
            fixture(++singletons==1,"singleton once");
            events.add("SINGLETON:"+h(scenario.singletonReturn()));return scenario.singletonReturn();
        }
    }
}
