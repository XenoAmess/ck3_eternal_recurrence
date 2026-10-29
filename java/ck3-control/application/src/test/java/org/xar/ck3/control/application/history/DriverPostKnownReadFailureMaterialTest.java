package org.xar.ck3.control.application.history;

import static org.junit.jupiter.api.Assertions.*;
import java.util.*;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.history.DriverPostKnownReadFailureMaterial.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Closed DATA codec only. These source-reference values grant no archive, Source, installed
 * contract, Native attempt, actual Known, candidate, history publication or Root permission.
 */
public final class DriverPostKnownReadFailureMaterialTest {
    private static ExactRef dataSource(int index){return new ExactRef("unqualified-source-data-"+index+".java",1,"a".repeat(64));}
    private static Obj without(Obj value,String key){var fields=new LinkedHashMap<String,Value>(value.members());fields.remove(key);return new Obj(fields);}
    @Test public void finiteComputationCausesAndExactErrorSpellingRoundTripAsData(){
        for(Kind kind:Kind.values()){
            var failure=new Failure(kind,"IllegalStateException","actual fixed pure verifier diagnostic",List.of(dataSource(1)));
            assertEquals(kind==Kind.ARMY_EXPLICIT_PROJECT?0:1,kind.requiredEarlierReads());
            assertEquals("IllegalStateException: actual fixed pure verifier diagnostic",failure.error());
            assertEquals(failure,DriverPostKnownReadFailureMaterial.fromJson(DriverJson.object(DriverJson.encode(failure.toJson()),DriverJson.MAX_NATIVE_BYTES)));
            var empty=new Failure(kind,"IllegalStateException","",failure.sourceClosure());
            assertEquals("IllegalStateException: ",empty.error());
            assertEquals(empty,DriverPostKnownReadFailureMaterial.fromJson(empty.toJson()));
        }
    }
    @Test public void closedVersionFieldsTypesAndFiniteKindsAreValidatedBeforeAnyCustody(){
        var original=new Failure(Kind.ARMY_AUTO_CORE_COMPARE,"IllegalStateException","mismatch",List.of(dataSource(1))).toJson();
        for(String name:List.of("schema","kind","failure_type","message","source_closure")){
            assertThrows(IllegalArgumentException.class,()->DriverPostKnownReadFailureMaterial.fromJson(without(original,name)));
        }
        for(Value value:List.<Value>of(new Bool(false),new IntegerValue(java.math.BigInteger.ONE),Nil.INSTANCE)){
            for(String name:List.of("schema","kind","failure_type","message","source_closure")){
                assertThrows(IllegalArgumentException.class,()->DriverPostKnownReadFailureMaterial.fromJson(original.with(name,value)));
            }
        }
        assertThrows(IllegalArgumentException.class,()->DriverPostKnownReadFailureMaterial.fromJson(original.with("kind",new Text("NATIVE_FAILED_ATTEMPT"))));
        assertThrows(IllegalArgumentException.class,()->DriverPostKnownReadFailureMaterial.fromJson(original.with("schema",new Text("xar.driver-post-known-read-failure/v0"))));
        assertThrows(IllegalArgumentException.class,()->DriverPostKnownReadFailureMaterial.fromJson(original.with("unknown",new Bool(true))));
        assertThrows(IllegalArgumentException.class,()->new Failure(Kind.ARMY_EXPLICIT_PROJECT,"illegal.class","detail",List.of(dataSource(1))));
        assertThrows(NullPointerException.class,()->new Failure(Kind.ARMY_EXPLICIT_PROJECT,"IllegalStateException",null,List.of(dataSource(1))));
    }
    @Test public void completeDistinctVerifierClosureIsPreservedWithoutGrantingItsQualification(){
        var refs=new ArrayList<ExactRef>();for(int i=1;i<=256;i++)refs.add(dataSource(i));
        var failure=new Failure(Kind.ARMY_AUTO_CORE_COMPARE,"IllegalStateException","all sources",refs);
        refs.clear();assertEquals(256,failure.sourceClosure().size());
        assertEquals(failure,DriverPostKnownReadFailureMaterial.fromJson(failure.toJson()));
        assertThrows(UnsupportedOperationException.class,()->failure.sourceClosure().clear());
        assertThrows(IllegalArgumentException.class,()->new Failure(failure.kind(),failure.failureType(),failure.message(),List.of()));
        assertThrows(IllegalArgumentException.class,()->new Failure(failure.kind(),failure.failureType(),failure.message(),List.of(dataSource(1),dataSource(1))));
        var tooMany=new ArrayList<>(failure.sourceClosure());tooMany.add(dataSource(257));
        assertThrows(IllegalArgumentException.class,()->new Failure(failure.kind(),failure.failureType(),failure.message(),tooMany));
        assertEquals("IOError",new StorageDiagnostic("IOError","archive unavailable").failureType());
        assertEquals(dataSource(1),new Queued(dataSource(1)).originalRow());
    }
}
