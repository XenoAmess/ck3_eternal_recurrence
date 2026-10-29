package org.xar.ck3.control.service.root;

import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.RootExecutableBindings;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyObserverSampling;
import static org.junit.jupiter.api.Assertions.*;

/** Actual installed binding/replay object identity; software metadata grants no Native dispatch. */
final class RootObserverSamplingClassificationTest {
    private static List<RootExecutableBindings.ActionBinding> actions() {
        return List.of(RootAubControlClassificationTest.action(ArmyObserverSampling.ENABLE),
                RootAubControlClassificationTest.action(ArmyObserverSampling.DISABLE));
    }
    @Test void bothActualInstalledActionsClassifyAsResearchControlOnly() {
        var controls=actions();var actual=RootAubControlClassificationTest.catalog(controls);
        for(var action:controls) {
            var result=assertInstanceOf(RootPlanningInputsFactory.SystemControl.class,
                    RootPlanningDomainCatalog.classifySamplingControl(actual,controls,actual.archivedBindings(),
                            action.effect().operation()).orElseThrow());
            assertEquals(RootPlanningInputsFactory.ControlKind.OBSERVER_SAMPLING_CONTROL,result.kind());
            assertNotEquals(RootPlanningInputsFactory.ControlKind.CHECKPOINT_SAVE,result.kind());
        }
        assertTrue(RootPlanningDomainCatalog.classifySamplingControl(actual,controls,actual.archivedBindings(),
                new OperationKey(ArmyObserverSampling.QUERY)).isEmpty());
        assertTrue(RootPlanningDomainCatalog.classifySamplingControl(actual,controls,actual.archivedBindings(),
                RootSaveRuntime.OPERATION).isEmpty());
    }
    @Test void equalNamesCannotReplaceTheInstalledActionOrReplayObject() {
        var controls=actions();var actual=RootAubControlClassificationTest.catalog(controls);
        for(int index=0;index<2;index++) {
            var changed=new ArrayList<>(controls);
            changed.set(index,RootAubControlClassificationTest.action(controls.get(index).effect().operation().value()));
            assertThrows(IllegalArgumentException.class,()->RootPlanningDomainCatalog.classifySamplingControl(
                    actual,changed,actual.archivedBindings(),new OperationKey(ArmyObserverSampling.ENABLE)));
        }
        var changed=new ArrayList<>(actual.archivedBindings());var original=changed.getFirst();
        changed.set(0,new NativeRecordedEvidenceVerifier.Binding(original.operation(),original.definitionSource(),
                (head,receipt,archive)->{throw new AssertionError("metadata test cannot verify Native evidence");}));
        assertThrows(IllegalArgumentException.class,()->RootPlanningDomainCatalog.classifySamplingControl(
                actual,controls,changed,new OperationKey(ArmyObserverSampling.ENABLE)));
    }
    @Test void partialOrDuplicateRostersCannotClassifyAnyOperation() {
        var controls=actions();var actual=RootAubControlClassificationTest.catalog(controls);
        assertThrows(IllegalArgumentException.class,()->RootPlanningDomainCatalog.classifySamplingControl(
                actual,controls.subList(0,1),actual.archivedBindings(),new OperationKey(ArmyObserverSampling.ENABLE)));
        assertThrows(IllegalArgumentException.class,()->RootPlanningDomainCatalog.classifySamplingControl(
                actual,List.of(controls.getFirst(),controls.getFirst()),actual.archivedBindings(),
                new OperationKey(ArmyObserverSampling.ENABLE)));
    }
}
