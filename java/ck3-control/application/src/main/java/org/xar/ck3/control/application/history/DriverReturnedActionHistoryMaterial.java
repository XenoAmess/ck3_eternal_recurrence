package org.xar.ck3.control.application.history;

import java.util.Objects;
import java.util.Optional;
import java.util.regex.Pattern;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.contracts.StrictJson;

/** Shared original selector fields only. Parsing grants no action, history, current frame or retry authority. */
public final class DriverReturnedActionHistoryMaterial {
    public enum Kind { HALT,SPLIT_HALF,MERGE }
    public sealed interface StructuralCall permits Halt,SplitHalf,Merge {
        Kind kind();int source();OperationKey operation();
    }
    public record Halt(int source) implements StructuralCall {
        public Halt {unit(source);}
        public Kind kind(){return Kind.HALT;}
        public OperationKey operation(){return new OperationKey("halt-army-"+source);}
    }
    public record SplitHalf(int source) implements StructuralCall {
        public SplitHalf {unit(source);}
        public Kind kind(){return Kind.SPLIT_HALF;}
        public OperationKey operation(){return new OperationKey("split-army-half-"+source);}
    }
    public record Merge(int destination,int source) implements StructuralCall {
        public Merge {unit(destination);unit(source);StrictJson.require(destination!=source,"merge subjects must differ");}
        public Kind kind(){return Kind.MERGE;}
        public OperationKey operation(){return new OperationKey("merge-armies-"+destination+"-with-"+source);}
    }
    private static final Pattern HALT=Pattern.compile("halt-army-(0|[1-9][0-9]*)");
    private static final Pattern SPLIT=Pattern.compile("split-army-half-(0|[1-9][0-9]*)");
    private static final Pattern MERGE=Pattern.compile("merge-armies-(0|[1-9][0-9]*)-with-(0|[1-9][0-9]*)");
    private DriverReturnedActionHistoryMaterial(){ }
    /** The sole canonical parser. Native structural adapters map these fields to their own typed call. */
    public static Optional<StructuralCall> parse(OperationKey operation){
        Objects.requireNonNull(operation);String text=operation.value();
        try{
            var halt=HALT.matcher(text);if(halt.matches())return Optional.of(new Halt(Integer.parseInt(halt.group(1))));
            var split=SPLIT.matcher(text);if(split.matches())return Optional.of(new SplitHalf(Integer.parseInt(split.group(1))));
            var merge=MERGE.matcher(text);if(merge.matches())return Optional.of(new Merge(Integer.parseInt(merge.group(1)),Integer.parseInt(merge.group(2))));
        }catch(IllegalArgumentException outside){return Optional.empty();}
        return Optional.empty();
    }
    private static void unit(int value){StrictJson.require(value>=0,"public CUnit must be 0..2147483647");}
}
