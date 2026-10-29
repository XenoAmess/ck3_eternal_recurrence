package org.xar.ck3.control.wave2.military.armyselector;

import static org.xar.ck3.control.wave2.military.armyselector.ArmySelectorModel.*;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.xar.ck3.control.replenishment.ReplenishmentPolicy;

/** Single extracted ordered physical loop, shared by the established selector and rich Army service. */
public final class OrderedRefillPhysicalCore {
    private OrderedRefillPhysicalCore() { }
    public record Permission(Boolean permitted,String basis) { }
    public record Decision(int physicalIndex,int ordinal,boolean predicate,String permissionBasis,boolean qualified,int calculatedQ) { }
    public record Write(int physicalIndex,int ordinal,int q,int beforeCurrent,int beforeMaximum,int afterCurrent,int afterMaximum,boolean pairCleared) { }
    public record Receipt(Occurrence occurrence,long preparedFraction,boolean admitted,List<Integer> qBuffer,List<Decision> decisions,List<Write> writes) {
        public Receipt {qBuffer=List.copyOf(qBuffer);decisions=List.copyOf(decisions);writes=List.copyOf(writes);}
    }
    public record Physical(int persistentId,int chunkIndex,Chunk chunk) { }
    public record Result(boolean rosterObserved,Map<Integer,List<Chunk>> physical,List<Receipt> receipts,Set<Integer> failedPersistentIds,List<String> missingInputs) {
        public Result {
            var copy=new LinkedHashMap<Integer,List<Chunk>>();physical.forEach((id,chunks)->copy.put(id,List.copyOf(chunks)));
            physical=java.util.Collections.unmodifiableMap(copy);receipts=List.copyOf(receipts);failedPersistentIds=Set.copyOf(failedPersistentIds);missingInputs=List.copyOf(missingInputs);
        }
        public boolean ready(){return rosterObserved&&missingInputs.isEmpty();}
        public List<Physical> finalChunks(){
            List<Physical> result=new ArrayList<>();physical.forEach((id,chunks)->{
                if(!failedPersistentIds.contains(id)&&chunks.size()==7)for(Chunk chunk:chunks)result.add(new Physical(id,chunk.physicalIndex(),chunk));
            });return List.copyOf(result);
        }
    }
    public static Result project(OrderedInputs inputs) {
        if(inputs.occurrenceCount()==null)return new Result(false,Map.of(),List.of(),Set.of(),List.of("native_persistent_occurrence_roster"));
        Map<Integer,List<Chunk>> physical=new LinkedHashMap<>();Map<Integer,Long> fractions=new LinkedHashMap<>();
        for(Persistent persistent:inputs.persistents()){physical.put(persistent.persistentId(),new ArrayList<>(persistent.chunks()));fractions.put(persistent.persistentId(),persistent.fraction());}
        Set<Integer> failed=new LinkedHashSet<>();Set<String> missing=new LinkedHashSet<>();List<Receipt> receipts=new ArrayList<>();
        for(Occurrence occurrence:inputs.occurrences()) {
            int identity=occurrence.persistentId();if(failed.contains(identity))continue;
            List<Chunk> chunks=physical.get(identity);Long fraction=fractions.get(identity);
            if(chunks==null||chunks.size()!=7||fraction==null){missing.add("persistent:"+identity+":complete_seven_and_prepared");failed.add(identity);continue;}
            int[] requests=new int[7];boolean admitted=false;List<Decision> decisions=new ArrayList<>();
            for(Chunk chunk:chunks) {
                Permission permission=fraction<=0?new Permission(false,"prepared_nonpositive"):predicate(chunk);
                if(permission.permitted()==null){missing.add("persistent:"+identity+":chunk:"+chunk.physicalIndex()+":"+permission.basis());failed.add(identity);break;}
                int effective=chunk.state()==3&&chunk.current()==0?chunk.maximum():chunk.current();
                var calculation=ReplenishmentPolicy.sameInputChunkQ(chunk.maximum(),effective,fraction,permission.permitted());
                if(calculation.nativeCoreChunkQualifies()) {
                    if(chunk.ordinal()<0||chunk.ordinal()>=7){missing.add("persistent:"+identity+":native_q_buffer_slot:"+chunk.ordinal());failed.add(identity);break;}
                    requests[chunk.ordinal()]=calculation.sameInputQ();admitted=true;
                }
                decisions.add(new Decision(chunk.physicalIndex(),chunk.ordinal(),permission.permitted(),permission.basis(),calculation.nativeCoreChunkQualifies(),calculation.sameInputQ()));
            }
            if(failed.contains(identity))continue;
            List<Chunk> after=new ArrayList<>(chunks);List<Write> writes=new ArrayList<>();
            if(admitted)for(int index=0;index<after.size();index++) {
                Chunk chunk=after.get(index);
                if(chunk.ordinal()<0||chunk.ordinal()>=7){missing.add("persistent:"+identity+":native_q_buffer_read:"+chunk.ordinal());failed.add(identity);break;}
                Chunk written=chunk.withPair(chunk.current()+requests[chunk.ordinal()],chunk.maximum());Boolean clear=cleanup(written);
                if(clear==null){missing.add("persistent:"+identity+":chunk:"+chunk.physicalIndex()+":raw_owner_cleanup_context");failed.add(identity);break;}
                Chunk result=clear?written.withPair(0,0):written;after.set(index,result);
                writes.add(new Write(chunk.physicalIndex(),chunk.ordinal(),requests[chunk.ordinal()],chunk.current(),chunk.maximum(),result.current(),result.maximum(),clear));
            }
            if(failed.contains(identity))continue;
            physical.put(identity,after);receipts.add(new Receipt(occurrence,fraction,admitted,java.util.Arrays.stream(requests).boxed().toList(),decisions,writes));
        }
        return new Result(true,physical,receipts,failed,new ArrayList<>(missing));
    }
    public static Permission predicate(Chunk c) {
        if(c.maximum()==0||c.current()>=c.maximum())return new Permission(false,"current_maximum");
        if(c.origin788()==null)return new Permission(null,"origin_province_788_raw");
        if(c.origin788()!=-1)return new Permission(false,"origin_province_788_raw");
        if(c.state()==3)return new Permission(c.current()>0,"state3_current");
        if(c.origin73c()==null)return new Permission(null,"origin_province_73c_raw");
        if(c.origin73c()!=-1)return new Permission(false,"origin_province_73c_raw");
        if(c.associatedMagic()==null||c.associatedRegimentId()==null)return new Permission(null,"native_associated_arrg_resolution");
        if(c.associatedMagic()!=0x41725267L||c.associatedRegimentId()==-1)return new Permission(true,"invalid_native_arrg");
        if(c.armyByte1d4()==null)return new Permission(null,"army_byte_1d4_raw");if(c.armyByte1d4()!=0)return new Permission(false,"army_byte_1d4_raw");
        if(c.armyByte1ec()==null)return new Permission(null,"army_byte_1ec_raw");if(c.armyByte1ec()!=0)return new Permission(false,"army_byte_1ec_raw");
        if(c.inCombat()==null)return new Permission(null,"native_army_in_combat");if(c.inCombat())return new Permission(false,"held_native_army_in_combat");
        if(c.unit170()==null)return new Permission(null,"unit_170_raw");if(c.unit170()>0)return new Permission(false,"unit_170_raw");
        if(c.provinceMagic()!=null&&c.provinceMagic()!=0x50726f76L)return new Permission(false,"invalid_position_province");
        if(c.positionOwner()!=null&&c.positionOwner().equals(c.positionHolder()))return new Permission(true,"same_resolved_position_owner_holder");
        return new Permission(c.positionEligible(),"held_native_unit_position_context");
    }
    public static Boolean cleanup(Chunk c) {
        if(c.current()<c.maximum()||c.armyRegimentId()!=-1||c.exclusionByte()!=0)return false;
        if(c.ownerGuard()!=null&&c.ownerGuard()!=0)return false;if(c.ownerGuard()==null||c.ownerMagic()==null)return null;
        return c.ownerMagic()!=0x4744624fL;
    }
}
