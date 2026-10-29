package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.action.NativeStepDiscriminator.RiteCreation;

/** Exact installed metadata only. Software handlers cannot prepare, observe or qualify a Game. */
final class RootRiteControlClassificationTest {
    private static List<RootExecutableBindings.ActionBinding> actions() {
        var actions=new ArrayList<RootExecutableBindings.ActionBinding>();
        for(RiteCreation selector:RiteCreation.values())if(selector!=RiteCreation.PREVIEW)
            actions.add(RootAubControlClassificationTest.action(selector.operationKey().value()));
        return List.copyOf(actions);
    }
    @Test void everyInstalledRiteActionIsControlAndPreviewRemainsARead() {
        var controls=actions();var actual=RootAubControlClassificationTest.catalog(controls);
        assertEquals(7,controls.size());
        for(var binding:controls) {
            var classification=assertInstanceOf(RootPlanningInputsFactory.SystemControl.class,
                    RootPlanningDomainCatalog.classifyRiteControl(actual,controls,actual.archivedBindings(),binding.effect().operation()).orElseThrow());
            assertEquals(RootPlanningInputsFactory.ControlKind.RITE_CREATION_CONTROL,classification.kind());
            assertNotEquals(RootPlanningInputsFactory.ControlKind.CHECKPOINT_SAVE,classification.kind());
        }
        assertTrue(RootPlanningDomainCatalog.classifyRiteControl(actual,controls,actual.archivedBindings(),RiteCreation.PREVIEW.operationKey()).isEmpty());
        assertTrue(RootPlanningDomainCatalog.classifyRiteControl(actual,controls,actual.archivedBindings(),RootSaveRuntime.OPERATION).isEmpty());
    }
    @Test void sameSelectorAndSourceCannotReplaceAnyActualInstalledHandler() {
        var controls=actions();var actual=RootAubControlClassificationTest.catalog(controls);
        for(int i=0;i<controls.size();i++) {
            var changed=new ArrayList<>(controls);
            changed.set(i,RootAubControlClassificationTest.action(controls.get(i).effect().operation().value()));
            assertThrows(IllegalArgumentException.class,()->RootPlanningDomainCatalog.classifyRiteControl(
                    actual,changed,actual.archivedBindings(),RiteCreation.OPEN_CREATE_DRAFT.operationKey()));
        }
    }
    @Test void equivalentReplayBodyCannotReplaceTheActualInstalledVerifier() {
        var controls=actions();var actual=RootAubControlClassificationTest.catalog(controls);
        var copies=new ArrayList<>(actual.archivedBindings());var original=copies.get(0);
        copies.set(0,new org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier.Binding(
                original.operation(),original.definitionSource(),(head,receipt,archive)->{
                    throw new AssertionError("metadata never verifies Native evidence");
                }));
        assertThrows(IllegalArgumentException.class,()->RootPlanningDomainCatalog.classifyRiteControl(
                actual,controls,copies,RiteCreation.OPEN_CREATE_DRAFT.operationKey()));
    }
    @Test void partialDuplicateReadAndSimilarLiteralRostersNeverReceiveAuthority() {
        var controls=actions();var actual=RootAubControlClassificationTest.catalog(controls);
        var partial=controls.subList(0,6);
        assertThrows(IllegalArgumentException.class,()->RootPlanningDomainCatalog.classifyRiteControl(
                actual,partial,actual.archivedBindings(),RiteCreation.OPEN_CREATE_DRAFT.operationKey()));
        var duplicate=new ArrayList<>(controls);duplicate.set(6,controls.get(0));
        assertThrows(IllegalArgumentException.class,()->RootPlanningDomainCatalog.classifyRiteControl(
                actual,duplicate,actual.archivedBindings(),RiteCreation.OPEN_CREATE_DRAFT.operationKey()));
        var read=new ArrayList<>(controls);read.set(6,RootAubControlClassificationTest.action(RiteCreation.PREVIEW.operationKey().value()));
        assertThrows(IllegalArgumentException.class,()->RootPlanningDomainCatalog.classifyRiteControl(
                actual,read,actual.archivedBindings(),RiteCreation.OPEN_CREATE_DRAFT.operationKey()));
        assertTrue(RootPlanningDomainCatalog.classifyRiteControl(actual,controls,actual.archivedBindings(),
                new OperationKey(RiteCreation.OPEN_CREATE_DRAFT.operationKey().value()+"-copy")).isEmpty());
        assertTrue(RootPlanningDomainCatalog.classifyRiteControl(RootAubControlClassificationTest.catalog(List.of()),
                List.of(),List.of(),RiteCreation.OPEN_CREATE_DRAFT.operationKey()).isEmpty());
    }
}
