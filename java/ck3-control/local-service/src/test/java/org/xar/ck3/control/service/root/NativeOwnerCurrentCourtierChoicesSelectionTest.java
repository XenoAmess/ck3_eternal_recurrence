package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.CurrentCourtierChoices;
import org.xar.ck3.control.nativebridge.CurrentCourtierChoicesSource;
import org.xar.ck3.control.nativebridge.CurrentCourtierChoicesResult;
import org.xar.ck3.control.nativebridge.CurrentCourtierControls;
import org.xar.ck3.control.nativebridge.CurrentCourtierConfigurationSource;
import org.xar.ck3.control.nativebridge.CurrentLetterResult;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Java DATA boundaries only; these constructors do not mint private Transport authority or Native credit. */
final class NativeOwnerCurrentCourtierChoicesSelectionTest {
    private static ObjectNode config(boolean select,String product,String catalog) {
        var n=StrictJson.object().put("schema","xar.native-owner-snapshot-config/v34")
                .put("mode",select?"current_courtier_choice_select":"current_courtier_choices_query")
                .put("product",product).put("catalog",catalog).put("overall_timeout_seconds",120)
                .put("read_timeout_seconds",20).put("maximum_frames_per_operation",128);
        n.putObject("owner_descriptor").put("path","D:/courtier-choices-DATA/owner.json").put("bytes",1).put("sha256","0".repeat(64));
        if(select)n.put("choice_key","target_trait");return n;
    }
    private static ObjectNode select(){return config(true,"main","other");}
    private static CoreFrame.Prefix core(int date){return new CoreFrame.Prefix(date,1,true,0,true,true,42,true);}
    private static List<Optional<Long>> values(){return List.of(Optional.of(31L),Optional.of(0L),Optional.of(7L),Optional.of(8L),Optional.of(9L),Optional.of(10L),Optional.of(11L),Optional.of(12L),Optional.of(0L),Optional.of(777L));}
    private static CurrentCourtierConfigurationSource.Configuration raw(List<Optional<Long>> v){return new CurrentCourtierConfigurationSource.Configuration(v.get(0),v.get(1),v.get(2),v.get(3),v.get(4),v.get(5),v.get(6),v.get(7),v.get(8),v.get(9));}
    private static CurrentCourtierChoicesSource.Row row(String token,String key,boolean selected,boolean admitted){return new CurrentCourtierChoicesSource.Row(token,key,true,true,selected,admitted);}
    private static CurrentCourtierChoicesSource present(CurrentCourtierControls.Product p,CurrentCourtierChoices.Catalog c,List<CurrentCourtierChoicesSource.Row> rows,CurrentCourtierConfigurationSource.Configuration raw){return new CurrentCourtierChoicesSource(p,c,true,true,true,true,true,true,true,true,Optional.of(rows.size()),rows,Optional.of(raw));}
    private static CurrentCourtierChoicesSource ready(){return present(CurrentCourtierControls.Product.MAIN,CurrentCourtierChoices.Catalog.OTHER,List.of(row("tok_first","first_trait",false,true),row("tok_target","target_trait",false,true),row("tok_last","last_trait",false,true)),raw(values()));}
    private static CurrentCourtierChoicesResult frame(CurrentCourtierChoices.Action a,CurrentCourtierChoicesSource s,String token,int provider,int query,int date,int connection){
        boolean effect=a==CurrentCourtierChoices.Action.SELECT_CHOICE;
        return new CurrentCourtierChoicesResult(a,effect?CurrentCourtierChoicesResult.Status.CHOICE_DISPATCHED:CurrentCourtierChoicesResult.Status.AVAILABLE,effect,effect,true,
                BigInteger.valueOf(provider),BigInteger.valueOf(query),effect?BigInteger.ONE:BigInteger.ZERO,Optional.of(core(date)),
                Optional.of(new CurrentLetterResult.OwnerWitness(BigInteger.valueOf(connection),BigInteger.TWO,BigInteger.valueOf(3),4)),Optional.of(s),Optional.empty(),s.product(),s.catalog(),token);
    }
    private static CurrentCourtierChoicesResult query(CurrentCourtierChoicesSource s){return frame(CurrentCourtierChoices.Action.QUERY_CHOICES,s,"",1,2,1000,1);}
    private static NativeOwnerSnapshotMain268.CourtierChoicesConfig intent(){return NativeOwnerSnapshotMain268.currentCourtierChoicesConfig(select());}
    @Test void independentModesKeepExactProductsCataloguesAndKeyRoles()throws IOException {
        for(var p:CurrentCourtierControls.Product.values())for(var c:CurrentCourtierChoices.Catalog.values()) {
            var q=config(false,p.wire(),c.wire());var s=config(true,p.wire(),c.wire());
            var qi=NativeOwnerSnapshotMain268.currentCourtierChoicesConfig(q);var si=NativeOwnerSnapshotMain268.currentCourtierChoicesConfig(s);
            assertEquals(p,qi.product());assertEquals(c,si.catalog());assertTrue(qi.choiceKey().isEmpty());assertEquals("target_trait",si.choiceKey().orElseThrow());
            assertEquals(NativeOwnerSnapshotMain268.ObservationMode.CURRENT_COURTIER_CHOICES_QUERY,NativeOwnerSnapshotMain268.observationMode(q));
            assertEquals(NativeOwnerSnapshotMain268.ObservationMode.CURRENT_COURTIER_CHOICE_SELECT,NativeOwnerSnapshotMain268.observationMode(s));
        }
        for(String v:List.of("MAIN","main ","unknown"))assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(config(false,v,"other")));
        for(String v:List.of("OTHER","other ","traits",""))assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(config(false,"main",v)));
    }
    @Test void queryRejectsEvenNullKeyAndSelectRequiresExactAsciiData()throws IOException {
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(config(false,"main","other").putNull("choice_key")));
        var missing=select();missing.remove("choice_key");assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(missing));
        for(var n:List.of(select().putNull("choice_key"),select().put("choice_key",true),select().put("choice_key",1),select().put("choice_key",1.5)))assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(n));
        for(String k:List.of("","a".repeat(129)," trait","trait ","a/b","a+b","\u4eba"))assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(select().put("choice_key",k)));
        for(String k:List.of("a","A.b-c_9","z".repeat(128)))assertEquals(k,NativeOwnerSnapshotMain268.currentCourtierChoicesConfig(select().put("choice_key",k)).choiceKey().orElseThrow());
    }
    @Test void commonFilePinAndBoundsRejectCallerAuthorityOrMalformedTypes()throws IOException {
        var bad=select();((ObjectNode)bad.get("owner_descriptor")).put("bytes",true);
        for(var n:List.of(bad,select().put("owner_descriptor","D:/owner.json"),select().put("overall_timeout_seconds",601),select().put("read_timeout_seconds",61),select().put("maximum_frames_per_operation",0)))assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(n));
        for(String k:List.of("choice_token","token","ordinal","index","scope","action","expected_core","provider_generation","query_sequence","deadline","permission","execute_admissible","age","cost","configuration"))assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(select().put(k,1)),k);
        for(String k:List.of("schema","mode","owner_descriptor","overall_timeout_seconds","read_timeout_seconds","maximum_frames_per_operation","product","catalog")){var n=select();n.remove(k);assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(n));}
    }
    @Test void oldSchemasCannotBorrowCatalogueFieldsAndV33StillSelectsItsOwnSetting()throws IOException {
        for(int v=24;v<=33;v++){var n=select().put("schema","xar.native-owner-snapshot-config/v"+v);assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(n));}
        var old=select().put("schema","xar.native-owner-snapshot-config/v33").put("mode","current_courtier_configuration_query").put("setting","choose_female");old.remove("catalog");old.remove("choice_key");
        assertEquals(NativeOwnerSnapshotMain268.ObservationMode.CURRENT_COURTIER_CONFIGURATION_QUERY,NativeOwnerSnapshotMain268.observationMode(old));
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(old.deepCopy().put("catalog","other")));
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(config(false,"main","other").put("mode","current_courtier_choices_query_then_select")));
    }
    @Test void actualAbsenceAndActualZeroCountRemainDifferentReadonlySources()throws IOException {
        var absent=new CurrentCourtierChoicesSource(CurrentCourtierControls.Product.MAIN,CurrentCourtierChoices.Catalog.OTHER,true,false,false,false,false,false,false,false,Optional.empty(),List.of(),Optional.empty());
        var zero=present(CurrentCourtierControls.Product.MAIN,CurrentCourtierChoices.Catalog.OTHER,List.of(),raw(values()));
        NativeOwnerSnapshotMain268.requireCurrentCourtierChoicesQueryFrame(query(absent),core(1000),absent.product(),absent.catalog());
        NativeOwnerSnapshotMain268.requireCurrentCourtierChoicesQueryFrame(query(zero),core(1000),zero.product(),zero.catalog());
        assertTrue(absent.catalogCount().isEmpty());assertEquals(0,zero.catalogCount().orElseThrow());
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentCourtierChoicesRow(query(absent),intent()));assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentCourtierChoicesRow(query(zero),intent()));
        assertThrows(IllegalArgumentException.class,()->new CurrentCourtierChoicesSource(zero.product(),zero.catalog(),true,true,true,true,true,true,true,true,Optional.empty(),List.of(),Optional.of(raw(values()))));
        assertThrows(IllegalArgumentException.class,()->new CurrentCourtierChoicesSource(zero.product(),zero.catalog(),false,false,false,false,false,false,false,false,Optional.empty(),List.of(),Optional.empty()));
    }
    @Test void exactKeyBindsMiddleActualRowAndNeverFallsBackToFirstOrLast()throws IOException {
        var s=ready();var actual=NativeOwnerSnapshotMain268.requireCurrentCourtierChoicesRow(query(s),intent());assertEquals(s.rows().get(1),actual);
        var absent=NativeOwnerSnapshotMain268.currentCourtierChoicesConfig(select().put("choice_key","missing_trait"));assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentCourtierChoicesRow(query(s),absent));
        var disabled=present(s.product(),s.catalog(),List.of(row("tok_target","target_trait",false,false)),raw(values()));assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentCourtierChoicesRow(query(disabled),intent()));
        assertThrows(IllegalArgumentException.class,()->present(s.product(),s.catalog(),List.of(row("t1","same",false,false),row("t2","same",false,true)),raw(values())));
        assertThrows(IllegalArgumentException.class,()->present(s.product(),s.catalog(),List.of(row("same","a",false,false),row("same","b",false,true)),raw(values())));
    }
    @Test void oneWayAdmissionRequiresCompleteNumericDataWithoutNullToZero()throws IOException {
        var v=new ArrayList<>(values());v.set(9,Optional.empty());var partial=raw(v);assertFalse(partial.complete());
        var s=present(CurrentCourtierControls.Product.MAIN,CurrentCourtierChoices.Catalog.OTHER,List.of(row("t","target_trait",false,false)),partial);
        NativeOwnerSnapshotMain268.requireCurrentCourtierChoicesQueryFrame(query(s),core(1000),s.product(),s.catalog());
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentCourtierChoicesRow(query(s),intent()));
        assertThrows(IllegalArgumentException.class,()->present(s.product(),s.catalog(),List.of(row("t","target_trait",false,true)),partial));
        assertThrows(IllegalArgumentException.class,()->new CurrentCourtierChoicesSource.Row("t","target_trait",true,false,false,true));
    }
    @Test void tokenWholeSourceAndProductCatalogueDriftCannotQualifyDispatch()throws IOException {
        var s=ready();var q=query(s);var cfg=intent();
        NativeOwnerSnapshotMain268.requireCurrentCourtierChoicesDispatchFrame(q,frame(CurrentCourtierChoices.Action.SELECT_CHOICE,s,"tok_target",1,2,1000,1),cfg);
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentCourtierChoicesDispatchFrame(q,frame(CurrentCourtierChoices.Action.SELECT_CHOICE,s,"tok_last",1,2,1000,1),cfg));
        var v=new ArrayList<>(values());v.set(0,Optional.of(32L));var changed=present(s.product(),s.catalog(),s.rows(),raw(v));
        var reordered=present(s.product(),s.catalog(),List.of(s.rows().get(2),s.rows().get(1),s.rows().get(0)),raw(values()));
        var otherProduct=present(CurrentCourtierControls.Product.VIVHITE,s.catalog(),s.rows(),raw(values()));var otherCatalog=present(s.product(),CurrentCourtierChoices.Catalog.CULTURE,s.rows(),raw(values()));
        for(var drift:List.of(changed,reordered,otherProduct,otherCatalog))assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentCourtierChoicesDispatchFrame(q,frame(CurrentCourtierChoices.Action.SELECT_CHOICE,drift,"tok_target",1,2,1000,1),cfg));
    }
    @Test void staleCoreLeaseOwnerAndKnownZeroEffectRefusalNeverBecomeSuccess()throws IOException {
        var s=ready();var q=query(s);var cfg=intent();
        for(var d:List.of(frame(CurrentCourtierChoices.Action.SELECT_CHOICE,s,"tok_target",2,2,1000,1),frame(CurrentCourtierChoices.Action.SELECT_CHOICE,s,"tok_target",1,3,1000,1),frame(CurrentCourtierChoices.Action.SELECT_CHOICE,s,"tok_target",1,2,1001,1),frame(CurrentCourtierChoices.Action.SELECT_CHOICE,s,"tok_target",1,2,1000,2),q))assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentCourtierChoicesDispatchFrame(q,d,cfg));
        var refused=new CurrentCourtierChoicesResult(CurrentCourtierChoices.Action.SELECT_CHOICE,CurrentCourtierChoicesResult.Status.STALE_SOURCE,false,false,true,BigInteger.ONE,BigInteger.TWO,BigInteger.ONE,q.factsBefore(),q.owner(),q.source(),Optional.of("actual_stale_source_DATA"),s.product(),s.catalog(),"tok_target");
        assertFalse(refused.successful());assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentCourtierChoicesDispatchFrame(q,refused,cfg));
        for(var c:List.of(CurrentCourtierChoices.Catalog.CULTURE,CurrentCourtierChoices.Catalog.FAITH)) {
            var unavailable=new CurrentCourtierChoicesResult(CurrentCourtierChoices.Action.QUERY_CHOICES,CurrentCourtierChoicesResult.Status.UNAVAILABLE,false,false,true,BigInteger.ZERO,BigInteger.ZERO,BigInteger.ZERO,Optional.empty(),Optional.empty(),Optional.empty(),Optional.of("actual_unbound_model_DATA"),s.product(),c,"");
            assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentCourtierChoicesQueryFrame(unavailable,core(1000),s.product(),c));
        }
    }
    @Test void selectedToggleAndSignedRawBoundariesStayObservationsAfterVoidDispatch()throws IOException {
        var v=new ArrayList<>(values());v.set(0,Optional.of(Long.MIN_VALUE));v.set(9,Optional.of(Long.MAX_VALUE));
        var s=present(CurrentCourtierControls.Product.MAIN,CurrentCourtierChoices.Catalog.OTHER,List.of(row("tok_selected","target_trait",true,true)),raw(v));
        var q=query(s);var d=frame(CurrentCourtierChoices.Action.SELECT_CHOICE,s,"tok_selected",1,2,1000,1);
        assertTrue(NativeOwnerSnapshotMain268.requireCurrentCourtierChoicesRow(q,intent()).selected());NativeOwnerSnapshotMain268.requireCurrentCourtierChoicesDispatchFrame(q,d,intent());
        var encoded=StrictJson.parse(d.encode().bytes(),1<<20);var data=encoded.get("source").get("configuration");assertEquals(Long.toString(Long.MIN_VALUE),data.get("age").textValue());assertEquals(Long.toString(Long.MAX_VALUE),data.get("cost").textValue());
        for(String k:List.of("native_handled","creator_closed","courtier_created","selection_changed","new_date_observed","physical_save_confirmed"))assertFalse(encoded.get(k).booleanValue(),k);
    }
}
