package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.NativeEffectRegistry;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.contracts.ExactRef;

/** Registry-to-fact metadata integration only. No fixture can grant physical SAVE or native qualification. */
final class RootControlClassificationTest {
    private static final ExactRef PREPARATION=new ExactRef("D:/fixture/save-preparation.java",1,"a".repeat(64));
    private static final ExactRef DECODER=new ExactRef("D:/fixture/save-poststate.java",1,"b".repeat(64));
    private static final ExactRef REPLAY=new ExactRef("D:/fixture/save-replay.java",1,"c".repeat(64));
    private static RootExecutableBindings.ActionBinding save() {
        var effect=new NativeEffectRegistry.Binding(RootSaveRuntime.OPERATION,PREPARATION,
                command->{throw new AssertionError("metadata fixture must not prepare a live SAVE");},
                (command,attempt,dispatch)->{throw new AssertionError("metadata fixture must not observe Native");});
        return new RootExecutableBindings.ActionBinding(effect,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,
                Optional.of("game.command.save-checkpoint"),DECODER);
    }
    private static RootExecutableBindings catalog(RootExecutableBindings.ActionBinding save) {
        var replay=new NativeRecordedEvidenceVerifier.Binding(RootSaveRuntime.OPERATION,REPLAY,
                (head,receipt,archive)->{throw new AssertionError("metadata fixture grants no archived SAVE settlement");});
        var catalog=RootExecutableBindings.freeze(List.of(save),RootReadContractCatalog.staticOnly(List.of()),List.of(),
                List.of(replay),List.of(),List.of(),8);
        catalog.requireCompleteArchiveCoverage();return catalog;
    }
    @Test void actualInstalledSaveIdentityBecomesSystemControlWithoutAnInventedBusinessDomain() {
        var save=save();var actual=catalog(save);
        var result=RootPlanningDomainCatalog.classifyControl(actual,save,RootSaveRuntime.OPERATION).orElseThrow();
        assertInstanceOf(RootPlanningInputsFactory.SystemControl.class,result);
        assertEquals(RootPlanningInputsFactory.ControlKind.CHECKPOINT_SAVE,((RootPlanningInputsFactory.SystemControl)result).kind());
        assertSame(save.effect(),actual.actualActionBinding(RootSaveRuntime.OPERATION).orElseThrow());
    }
    @Test void sameOperationAndSourceBytesCannotReplaceTheInstalledHandlerIdentity() {
        var original=save();var foreign=save();var actual=catalog(original);
        assertThrows(IllegalArgumentException.class,()->RootPlanningDomainCatalog.classifyControl(actual,foreign,RootSaveRuntime.OPERATION));
        assertSame(original.effect(),actual.actualActionBinding(RootSaveRuntime.OPERATION).orElseThrow());
    }
    @Test void similarlyNamedUninstalledOperationDoesNotBecomeSystemControl() {
        var save=save();var actual=catalog(save);
        assertTrue(RootPlanningDomainCatalog.classifyControl(actual,save,new OperationKey("save-checkpoint-copy")).isEmpty());
        assertTrue(actual.actualActionBinding(new OperationKey("save-checkpoint-copy")).isEmpty());
    }
}

