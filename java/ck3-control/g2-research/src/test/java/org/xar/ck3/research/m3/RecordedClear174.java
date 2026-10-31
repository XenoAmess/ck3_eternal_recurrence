package org.xar.ck3.research.m3;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/** Owned fixture observation, unrelated to a Native or Game execution receipt. */
public final class RecordedClear174 {
    private RecordedClear174() { }
    @FunctionalInterface public interface Checks {
        void check(boolean good,String reason);
    }
    public record Observation(RegistrationClearApi174.Completion completion,List<String> events,
        Map<Long,ClearCasesApi174.Word> finalWords,Map<ClearCasesApi174.Hook,Integer> appliedHooks) { }
    public static Map<Long,ClearCasesApi174.Word> words(List<ClearCasesApi174.Word> words) {
        Map<Long,ClearCasesApi174.Word> result=new LinkedHashMap<>();
        for(ClearCasesApi174.Word word:words) {
            if(word.width()!=4&&word.width()!=8)throw new AssertionError("fixture word width");
            long bits=word.width()==4?Integer.toUnsignedLong((int)word.bits()):word.bits();
            if(result.putIfAbsent(word.address(),new ClearCasesApi174.Word(word.address(),word.width(),bits))!=null)
                throw new AssertionError("duplicate fixture word");
        }
        return Map.copyOf(result);
    }
}
