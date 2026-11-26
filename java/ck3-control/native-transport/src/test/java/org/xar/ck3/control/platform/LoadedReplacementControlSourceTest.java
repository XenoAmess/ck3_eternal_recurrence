package org.xar.ck3.control.platform;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Original replacement-control DATA only; no decoder in these tests can construct a loaded role. */
final class LoadedReplacementControlSourceTest {
    private static final String PARENT="public-restore-43f7a45b4dd038c190740f7295641372d148cc43a79400415583d51cad6164fe";
    private static final String CHILD="replacement-475fd1a5e5a67a41a994a84f1311d960b32af36ff952dedcc27355bfb43dc9b2";
    private static ExactRef reference(String leaf){return new ExactRef("D:/control-data/"+leaf,32,"f".repeat(64));}
    private static ObjectNode original(){
        var row=StrictJson.object().put("schema","xar.java-game-replacement/v1")
                .put("parent_lifecycle_intent_id",PARENT)
                .put("phase","EXITED_SOURCE_NEW_HELLO_ACCEPTED_MAP_NOT_YET_VERIFIED")
                .put("old_pid",145132).put("old_birth_decimal","134388549310428814");
        row.set("save",reference("checkpoint.ck3").toJson());
        row.set("stop_evidence",reference("exited-original.json").toJson());
        row.set("launch_evidence",reference("new-hello-event.json").toJson());return row;
    }
    private static RootProcessAttach.LoadedReplacementControl decode(ObjectNode row)throws IOException {
        return RootProcessAttach.decodeLoadedReplacementControl(StrictJson.canonical(row,65536));
    }
    @Test void originalSnakeCaseControlRetainsParentBirthAndAllThreeExactReferences()throws Exception {
        var decoded=decode(original());
        assertEquals(PARENT,decoded.parentId());assertEquals(CHILD,JavaGameLifecycle.replacementRequestId(decoded.parentId()));
        assertEquals(145132,decoded.previous().pid());assertEquals("134388549310428814",decoded.previous().creationFiletime().value().toString());
        assertEquals(reference("checkpoint.ck3"),decoded.save());assertEquals(reference("exited-original.json"),decoded.stopped());
        assertEquals(reference("new-hello-event.json"),decoded.launched());
        assertEquals(decoded,decode(original()),"wire DATA equality does not recreate an actual private replacement capability");
    }
    @Test void incompleteUnknownAndUnrelatedPhasesCannotEnterLoadedSource()throws Exception {
        for(String phase:java.util.List.of("ENTERED","OLD_EXIT_PROVED_NEW_LAUNCH_ENTERED","UNKNOWN","NEW_HELLO_ACCEPTED_MAP_NOT_YET_VERIFIED")){
            var changed=original();changed.put("phase",phase);assertThrows(IOException.class,()->decode(changed),phase);
        }
        var nullPhase=original();nullPhase.putNull("phase");assertThrows(IOException.class,()->decode(nullPhase));
        var wrongSchema=original();wrongSchema.put("schema","xar.java-game-replacement/v2");assertThrows(IOException.class,()->decode(wrongSchema));
    }
    @Test void birthAndPidCannotBeCoercedFromNumbersBooleansOrNoncanonicalStrings()throws Exception {
        var numericBirth=original();numericBirth.put("old_birth_decimal",134388549310428814L);assertThrows(IOException.class,()->decode(numericBirth));
        for(String birth:java.util.List.of("0134388549310428814","0","18446744073709551616")){
            var changed=original();changed.put("old_birth_decimal",birth);assertThrows(IOException.class,()->decode(changed),birth);
        }
        var booleanPid=original();booleanPid.put("old_pid",true);assertThrows(IOException.class,()->decode(booleanPid));
        var fractionalPid=original();fractionalPid.put("old_pid",145132.0);
        assertThrows(IOException.class,()->RootProcessAttach.decodeLoadedReplacementControl(
                org.xar.ck3.control.build.ControlBuild.strictMapper().writeValueAsBytes(fractionalPid)));
        var oversizedPid=original();oversizedPid.put("old_pid",4294967296L);assertThrows(IOException.class,()->decode(oversizedPid));
    }
    @Test void camelAliasesMissingReferencesAndExtraPermissionFieldsAreRejected()throws Exception {
        var camel=original();camel.set("parentLifecycleIntentId",camel.remove("parent_lifecycle_intent_id"));assertThrows(IOException.class,()->decode(camel));
        for(String field:java.util.List.of("save","stop_evidence","launch_evidence")){
            var absent=original();absent.remove(field);assertThrows(IOException.class,()->decode(absent),field);
            var explicitNull=original();explicitNull.putNull(field);assertThrows(IOException.class,()->decode(explicitNull),field);
        }
        var extra=original();extra.put("may_create",true);assertThrows(IOException.class,()->decode(extra));
        var changedRef=original();((ObjectNode)changedRef.get("save")).put("bytes",true);assertThrows(IOException.class,()->decode(changedRef));
    }
    @Test void importedControlRoundTripsActualProducerAndKeepsTheSeparateProof()throws Exception {
        byte[] bytes=producedImported("EXITED_SOURCE_NEW_HELLO_ACCEPTED_MAP_NOT_YET_VERIFIED",reference("new-hello-event.json"));
        var exact=RootProcessAttach.decodeImportedLoadedControl(bytes,bytes.clone());
        assertEquals(PARENT,exact.replacement().parentId());
        assertEquals(50372,exact.replacement().previous().pid());
        assertEquals("134401544348311914",exact.replacement().previous().creationFiletime().value().toString());
        assertEquals(reference("staged.ck3"),exact.replacement().save());
        assertEquals(reference("exited-original.json"),exact.replacement().stopped());
        assertEquals(reference("new-hello-event.json"),exact.replacement().launched());
        assertEquals(reference("transfer-original.json"),exact.transferProof());
        assertThrows(IOException.class,()->RootProcessAttach.decodeLoadedReplacementControl(bytes));
    }

    @Test void importedEnteredTornNullAliasedAndOversizedControlsRemainIneligible()throws Exception {
        String accepted="EXITED_SOURCE_NEW_HELLO_ACCEPTED_MAP_NOT_YET_VERIFIED";
        byte[] valid=producedImported(accepted,reference("new-hello-event.json"));
        byte[] entered=producedImported("EXITED_SOURCE_ACCEPTED_SAVED_LAUNCH_ENTERED",null);
        assertThrows(IOException.class,()->RootProcessAttach.decodeImportedLoadedControl(entered,entered));
        assertThrows(IOException.class,()->RootProcessAttach.decodeImportedLoadedControl(entered,valid));
        assertThrows(IOException.class,()->RootProcessAttach.decodeImportedLoadedControl(valid,entered));
        byte[] other=producedImported(accepted,reference("different-hello-event.json"));
        assertThrows(IOException.class,()->RootProcessAttach.decodeImportedLoadedControl(valid,other));
        for(var field:java.util.List.of("save","stop_evidence","launch_evidence","imported_save_transfer")){
            var row=(ObjectNode)StrictJson.parse(valid);
            row.putNull(field);
            byte[] absent=StrictJson.canonical(row,65536);
            assertThrows(IOException.class,()->RootProcessAttach.decodeImportedLoadedControl(absent,absent),field);
        }
        var alias=(ObjectNode)StrictJson.parse(valid);
        alias.set("importedSaveTransfer",alias.remove("imported_save_transfer"));
        byte[] camel=StrictJson.canonical(alias,65536);
        assertThrows(IOException.class,()->RootProcessAttach.decodeImportedLoadedControl(camel,camel));
        byte[] oversized=java.util.Arrays.copyOf(valid,65537);
        assertThrows(IOException.class,()->RootProcessAttach.decodeImportedLoadedControl(oversized,oversized));
    }

    private static byte[] producedImported(String phase,ExactRef launch)throws Exception {
        // Exercise the real private producer DTO and mapper without constructing any Game or lifecycle authority.
        var producer=Class.forName(JavaGameLifecycle.class.getName()+"$ImportedReplacementControl");
        var constructor=producer.getDeclaredConstructor(String.class,String.class,String.class,long.class,String.class,
                org.xar.ck3.control.build.ControlBuild.FileRef.class,ExactRef.class,ExactRef.class,ExactRef.class);
        constructor.setAccessible(true);
        var ref=reference("staged.ck3");
        var stage=new org.xar.ck3.control.build.ControlBuild.FileRef(ref.path(),ref.bytes(),ref.sha256());
        var row=constructor.newInstance(org.xar.ck3.control.application.checkpoint.RestoreCheckpointService.IMPORTED_REPLACEMENT_SCHEMA,
                PARENT,phase,50372L,"134401544348311914",stage,reference("exited-original.json"),launch,reference("transfer-original.json"));
        return org.xar.ck3.control.build.ControlBuild.strictMapper().writeValueAsBytes(row);
    }

}
