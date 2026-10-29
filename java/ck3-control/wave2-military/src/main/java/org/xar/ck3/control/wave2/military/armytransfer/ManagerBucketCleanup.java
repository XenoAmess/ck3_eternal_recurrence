package org.xar.ck3.control.wave2.military.armytransfer;

import java.util.ArrayList;
import java.util.List;
import java.util.Objects;

/** Sole pure modulo30/pointer bucket kernel shared by manager and assault cleanup. */
public final class ManagerBucketCleanup {
    public record Row(int storedIndex,Integer observedArmyId,Boolean nativeSameCleanupPointer) { }
    public record Input(Integer resolvedArmyId,Boolean usedFallback,Integer selectedBucketIndex,List<Row> rows) {
        public Input { rows=rows==null?null:List.copyOf(rows); }
    }
    public record Result(boolean ready,Integer resolvedArmyId,Boolean usedFallback,Integer selectedBucketIndex,
            List<Row> before,List<Row> after,List<Integer> removedStoredIndices,List<String> missingInputs) {
        public Result { before=before==null?null:List.copyOf(before);after=after==null?null:List.copyOf(after);removedStoredIndices=List.copyOf(removedStoredIndices);missingInputs=List.copyOf(missingInputs); }
    }
    private ManagerBucketCleanup() { }
    public static Result project(Input input) {
        Objects.requireNonNull(input);boolean operands=input.resolvedArmyId()!=null&&input.usedFallback()!=null&&input.selectedBucketIndex()!=null
                &&input.selectedBucketIndex()==Integer.toUnsignedLong(input.resolvedArmyId())%30;
        boolean rowsReady=input.rows()!=null;
        if(rowsReady)for(int index=0;index<input.rows().size();index++){Row row=input.rows().get(index);rowsReady&=row.storedIndex()==index&&row.nativeSameCleanupPointer()!=null;}
        if(!operands||!rowsReady)return new Result(false,operands?input.resolvedArmyId():null,operands?input.usedFallback():null,
                operands?input.selectedBucketIndex():null,null,null,List.of(),List.of("second_resolution_and_selected_bucket_pointer_occurrences"));
        List<Row> after=new ArrayList<>();List<Integer> removed=new ArrayList<>();
        for(Row row:input.rows())if(Boolean.TRUE.equals(row.nativeSameCleanupPointer()))removed.add(row.storedIndex());else after.add(row);
        return new Result(true,input.resolvedArmyId(),input.usedFallback(),input.selectedBucketIndex(),input.rows(),after,removed,List.of());
    }
}
