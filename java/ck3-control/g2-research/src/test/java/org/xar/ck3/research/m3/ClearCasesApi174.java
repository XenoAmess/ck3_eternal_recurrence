package org.xar.ck3.research.m3;
import java.util.List;
/** Test data only: hooks are controlled callee effects, not original Native actions. */
public final class ClearCasesApi174 {
    private ClearCasesApi174() { }
    public enum Event { DESTROY, CLEANUP }
    public record Word(long address,int width,long bits) { }
    public record Hook(Event event,int ordinal,List<Word> changes) { }
    public record Scenario(String id,boolean throughConsumer,long observedCode,long selectedCode,
        long singletonReturn,long receiver,RegistrationClearApi174.Limits limits,
        List<Word> initialWords,List<Hook> hooks,RegistrationClearApi174.Completion expected,
        List<String> expectedEvents,List<Word> expectedFinalWords) { }
}
