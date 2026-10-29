package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.time.Instant;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.ServiceLoader;
import java.util.function.LongSupplier;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts;
import org.xar.ck3.control.application.driver.DriverActionHistoryPublisher;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.identity.OperatorPlayerSwitch;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.service.mcp.PublicServiceFailure;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Mandatory actual Root/native originals. Missing source inputs fail as NOT_RUN; no replacement issuer is manufactured. */
public final class RootPlayedCharacterActualEntryTest {
    public enum Scenario { NO_CAPABILITY,UNPAUSED_AND_WRONG_REVISION,WRONG_REVISION_AND_UNSUPPORTED_BUILD,
            UNSUPPORTED_BUILD,KNOWN_REJECTION,ZERO_DISPATCH,UNKNOWN_CODE,WRONG_TARGET_AFTER,DEAD_TARGET_AFTER,
            MISSING_AFTER_FIELD,SWITCHED,ALREADY_PLAYED_NO_REBIND,COLD_ORIGINAL,COLD_KNOWN_REJECTION }
    @FunctionalInterface public interface ColdOpen { ActualRoot reopen()throws Exception; }
    public record HistoryProducts(RootActionHistoryMaterialSourceFactory.Prepared prepared,DriverActionHistoryPublisher publisher){
        public HistoryProducts{Objects.requireNonNull(prepared);Objects.requireNonNull(publisher);}
    }
    public record ActualRoot(RootInstalledCatalog catalog,PublicBindings registry,Optional<HistoryProducts> history){
        public ActualRoot{Objects.requireNonNull(catalog);Objects.requireNonNull(registry);history=Objects.requireNonNull(history);}
    }
    public record Inputs(ActualRoot actual,RawJson originalCaller,Instant deadline,LongSupplier actualSetterPacketsWritten,
            Optional<ColdOpen> coldOpen){
        public Inputs{Objects.requireNonNull(actual);Objects.requireNonNull(originalCaller);Objects.requireNonNull(deadline);
            Objects.requireNonNull(actualSetterPacketsWritten);coldOpen=Objects.requireNonNull(coldOpen);}
    }
    public interface InputsProducer {Inputs open(Scenario scenario)throws Exception;}
    private static Inputs actual(Scenario scenario)throws Exception{
        var providers=ServiceLoader.load(InputsProducer.class).stream().toList();
        if(providers.size()!=1)throw new IllegalStateException("MISSING_ACTUAL_ROOT_PLAYED_CHARACTER_INPUTS_NOT_RUN: "+scenario);
        var input=Objects.requireNonNull(providers.getFirst().get().open(scenario));
        var catalog=input.actual().catalog();var title=catalog.additionalDomains().driverRegistry().titleClaims();
        title.requireContext(catalog.context());title.requireOwner(root(input.actual()));
        assertEquals(OperatorPlayerSwitch.Request.class,input.actual().registry().lookup(PublicMethod.SET_PLAYER_CHARACTER_V1).orElseThrow().requestType());
        OperatorPlayerSwitch.decode(input.originalCaller());return input;
    }
    private static RootApplicationSession root(ActualRoot actual){return assertInstanceOf(RootApplicationSession.class,actual.catalog().context().actions());}
    private static RawJson invoke(Inputs input)throws InterruptedException{
        return input.actual().registry().lookup(PublicMethod.SET_PLAYER_CHARACTER_V1).orElseThrow().invoke(PublicBindings.present(input.originalCaller()));
    }
    private static Optional<ActionReceipt> canonical(Inputs input,ActualRoot actual)throws Exception{
        var context=actual.catalog().context();var request=OperatorPlayerSwitch.decode(input.originalCaller());
        return root(actual).withPublicStandaloneRead(input.deadline(),same->context.core().actions().withFrozen(same,lease->{
            var matches=lease.snapshot().actions().stream().filter(receipt->receipt.command().operation().value().equals(request.step())
                    &&receipt.command().source().equals(context.source())).toList();
            assertTrue(matches.size()<=1,"actual isolated fixture retained multiple commands for the original caller");
            lease.assertCurrent();return matches.stream().findFirst();
        }));
    }
    private static void preSubmission(Scenario scenario,PublicServiceFailure.Kind kind,String message)throws Exception{
        var input=actual(scenario);long count=input.actualSetterPacketsWritten().getAsLong();
        var failure=assertThrows(PublicServiceFailure.class,()->invoke(input));assertEquals(kind,failure.kind());
        assertTrue(failure.getMessage().startsWith(message));assertEquals(count,input.actualSetterPacketsWritten().getAsLong());
        assertTrue(canonical(input,input.actual()).isEmpty());
    }
    @Test void actualCapabilityFaultPrecedesAnyNativeSubmission()throws Exception{
        preSubmission(Scenario.NO_CAPABILITY,PublicServiceFailure.Kind.UNSUPPORTED_STEP,
                "capability_not_available: selected backend cannot rebind the played character");
    }
    @Test void actualPausedMapGuardWinsOverWrongRevision()throws Exception{
        preSubmission(Scenario.UNPAUSED_AND_WRONG_REVISION,PublicServiceFailure.Kind.BRIDGE_UNAVAILABLE,
                "played-character rebind requires a paused map-ready snapshot");
    }
    @Test void actualWrongRevisionWinsOverUnsupportedOperatorBuild()throws Exception{
        preSubmission(Scenario.WRONG_REVISION_AND_UNSUPPORTED_BUILD,PublicServiceFailure.Kind.PRE_SUBMISSION_REVISION_MISMATCH,
                "played-character rebind revision mismatch: expected ");
    }
    @Test void actualUnsupportedExactBuildCannotSubmit()throws Exception{
        preSubmission(Scenario.UNSUPPORTED_BUILD,PublicServiceFailure.Kind.BRIDGE_UNAVAILABLE,
                "native played-character rebind requires the frozen exact build");
    }
    private static void verifyOriginal(Inputs input,ActualRoot actual,ActionReceipt receipt)throws Exception{
        var context=actual.catalog().context();
        root(actual).withPublicStandaloneRead(input.deadline(),same->{
            var archive=context.archive().withSession(same);var head=same.head();
            context.core().operatorAuthority().requireArchivedReceipt(context,same,receipt,archive);
            assertEquals(head,same.head());
            var command=ActionCodec.encodeCommand(receipt.command());assertEquals(receipt.command(),ActionCodec.decodeCommand(command));
            assertArrayEquals(command,ActionCodec.encodeCommand(ActionCodec.decodeCommand(command)));
            var bytes=ActionReceiptCodec.encodeReceipt(receipt,archive);assertEquals(receipt,ActionReceiptCodec.decodeReceipt(bytes,archive));
            assertArrayEquals(bytes,ActionReceiptCodec.encodeReceipt(ActionReceiptCodec.decodeReceipt(bytes,archive),archive));
            for(String field:List.of("version","sequence")){
                var wrong=(ObjectNode)StrictJson.parse(bytes,ActionReceiptCodec.MAXIMUM_RECEIPT_BYTES);wrong.put(field,true);
                assertThrows(RuntimeException.class,()->ActionReceiptCodec.decodeReceipt(StrictJson.canonical(wrong,ActionReceiptCodec.MAXIMUM_RECEIPT_BYTES),archive));
            }
            var missing=(ObjectNode)StrictJson.parse(bytes,ActionReceiptCodec.MAXIMUM_RECEIPT_BYTES);missing.remove("body_sha256");
            assertThrows(RuntimeException.class,()->ActionReceiptCodec.decodeReceipt(StrictJson.canonical(missing,ActionReceiptCodec.MAXIMUM_RECEIPT_BYTES),archive));
            context.adopted().authority().withFrozenFacts(same,frozen->{
                var known=assertInstanceOf(DriverSnapshotFacts.Known.class,frozen.state());
                var driver=known.driver().encode();assertArrayEquals(driver,DriverStateSnapshot.decodeComplete(driver).encode());return null;
            });
            if(receipt.state() instanceof ActionState.Settled settled&&settled.settlement() instanceof ActionState.OperatorRebound rebound){
                var completion=rebound.observation();var refs=completion.originals();
                var beforeDriver=archive.loadFullMaterial(refs.beforeDriver()).bytes();
                var afterDriver=archive.loadFullMaterial(refs.afterDriver()).bytes();
                var after=DriverStateSnapshot.decodeComplete(afterDriver);
                assertEquals(java.math.BigInteger.valueOf(completion.request().characterId()),after.session().actorId());
                assertEquals(completion.episodeRunId(),after.session().episodeRunId());
                if(completion.rebindPerformed()){
                    assertInstanceOf(DriverStateSnapshot.NullValue.class,after.successionExpectation());
                    var auxiliary=DriverJson.object(archive.loadFullMaterial(refs.afterAuxiliary()).bytes(),DriverJson.MAX_NATIVE_BYTES);
                    assertEquals(new OpportunityJson.Arr(List.of()),auxiliary.get("arrange_marriage_choices"));
                    for(String name:List.of("arrange_marriage_query_sequence","active_combat_retreat_token","succession_reconciliation"))
                        assertEquals(OpportunityJson.Nil.INSTANCE,auxiliary.get(name));
                }else{
                    assertArrayEquals(beforeDriver,afterDriver);
                    assertArrayEquals(archive.loadFullMaterial(refs.beforeAuxiliary()).bytes(),archive.loadFullMaterial(refs.afterAuxiliary()).bytes());
                }
            }
            assertFalse(receipt.visibleGameplay());assertFalse(receipt.eligibleAdvance());return null;
        });
    }
    @Test void actualKnownNativeRejectionAndZeroDispatchReplayOriginalsWithoutDriverRebind()throws Exception{
        for(Scenario scenario:List.of(Scenario.KNOWN_REJECTION,Scenario.ZERO_DISPATCH)){
            var input=actual(scenario);long before=input.actualSetterPacketsWritten().getAsLong();
            var failure=assertThrows(PublicServiceFailure.class,()->invoke(input));
            assertEquals(scenario==Scenario.KNOWN_REJECTION?PublicServiceFailure.Kind.NATIVE_COMMAND_REJECTED:PublicServiceFailure.Kind.BRIDGE_UNAVAILABLE,failure.kind());
            var receipt=canonical(input,input.actual()).orElseThrow();verifyOriginal(input,input.actual(),receipt);
            var context=input.actual().catalog().context();
            root(input.actual()).withPublicStandaloneRead(input.deadline(),same->{
                var head=same.head();context.core().operatorAuthority().requireOperatorWithoutRebind(context,same,receipt,context.archive().withSession(same));
                var history=input.actual().history().orElseThrow(()->new IllegalStateException("MISSING_ACTUAL_OPERATOR_HISTORY_PRODUCTS_NOT_RUN"));
                assertDoesNotThrow(()->RootOperatorNonRebindMaterialTest.assertActualCanonicalNonRebind(
                        history.prepared(),input.actual().catalog(),same,history.publisher(),receipt));
                assertEquals(head,same.head());return null;
            });
            assertEquals(scenario==Scenario.KNOWN_REJECTION?1:0,input.actualSetterPacketsWritten().getAsLong()-before);
        }
    }
    private static void unknownDoesNotReplay(Scenario scenario)throws Exception{
        var input=actual(scenario);assertThrows(PublicServiceFailure.class,()->invoke(input));
        var original=canonical(input,input.actual()).orElseThrow();assertFalse(original.settled());
        long count=input.actualSetterPacketsWritten().getAsLong();
        assertThrows(PublicServiceFailure.class,()->invoke(input));var after=canonical(input,input.actual()).orElseThrow();
        assertEquals(count,input.actualSetterPacketsWritten().getAsLong());assertEquals(original.command(),after.command());
        assertEquals(original.bodySha256(),after.bodySha256());assertEquals(ActionTransitions.attempt(original.state()),ActionTransitions.attempt(after.state()));
        var context=input.actual().catalog().context();root(input.actual()).withPublicStandaloneRead(input.deadline(),same->{
            assertThrows(RuntimeException.class,()->context.core().operatorAuthority().requireOperatorWithoutRebind(context,same,after,context.archive().withSession(same)));
            var history=input.actual().history().orElseThrow(()->new IllegalStateException("MISSING_ACTUAL_OPERATOR_HISTORY_PRODUCTS_NOT_RUN"));
            assertDoesNotThrow(()->RootOperatorNonRebindMaterialTest.assertActualUnknownNotQualified(
                    history.prepared(),input.actual().catalog(),same,history.publisher(),after));return null;
        });
    }
    @Test void actualUnknownNativeCodeCannotBecomeKnownRejectionOrTriggerAnotherSubmit()throws Exception{
        unknownDoesNotReplay(Scenario.UNKNOWN_CODE);
    }
    @Test void actualWrongDeadOrMissingAfterRemainsOriginalUnknownWithoutResubmission()throws Exception{
        for(Scenario scenario:List.of(Scenario.WRONG_TARGET_AFTER,Scenario.DEAD_TARGET_AFTER,Scenario.MISSING_AFTER_FIELD))unknownDoesNotReplay(scenario);
    }
    private static ActionReceipt completed(Inputs input,OperatorPlayerSwitch.NativeStatus expected)throws Exception{
        long before=input.actualSetterPacketsWritten().getAsLong();var result=invoke(input);
        RootPlayedCharacterPublicContract.requireResult(OperatorPlayerSwitch.decode(input.originalCaller()),result);
        var receipt=canonical(input,input.actual()).orElseThrow();
        var completion=assertInstanceOf(ActionState.OperatorRebound.class,
                assertInstanceOf(ActionState.Settled.class,receipt.state()).settlement()).observation();
        assertEquals(expected,completion.status());assertEquals(1,input.actualSetterPacketsWritten().getAsLong()-before);
        assertEquals(completion,OperatorPlayerSwitch.decodeCompletion(completion.encode()));
        verifyOriginal(input,input.actual(),receipt);return receipt;
    }
    @Test void actualSwitchedUsesIndependentLaterAfterAndPersistsTheSameRun()throws Exception{
        var input=actual(Scenario.SWITCHED);var receipt=completed(input,OperatorPlayerSwitch.NativeStatus.SWITCHED);
        var completion=((ActionState.OperatorRebound)((ActionState.Settled)receipt.state()).settlement()).observation();
        assertTrue(completion.afterRevision().compareTo(completion.request().expectedRevision())>0);
        assertTrue(completion.rebindPerformed());assertEquals(completion.beforeDriverVersion()+1,completion.afterDriverVersion());
    }
    @Test void actualAlreadyPlayedRetainsItsActualDriverWhenEpisodeActorAlreadyMatches()throws Exception{
        var input=actual(Scenario.ALREADY_PLAYED_NO_REBIND);var receipt=completed(input,OperatorPlayerSwitch.NativeStatus.ALREADY_PLAYED);
        var completion=((ActionState.OperatorRebound)((ActionState.Settled)receipt.state()).settlement()).observation();
        assertFalse(completion.rebindPerformed());assertEquals(completion.beforeDriverVersion(),completion.afterDriverVersion());
    }
    @Test void actualColdRootReopensOriginalCommandDriverReceiptAndSourceWithoutIssuingAnotherTarget()throws Exception{
        var input=actual(Scenario.COLD_ORIGINAL);var original=completed(input,OperatorPlayerSwitch.NativeStatus.SWITCHED);
        var reopened=input.coldOpen().orElseThrow(()->new IllegalStateException("MISSING_ACTUAL_COLD_OPERATOR_ROOT_INPUTS_NOT_RUN")).reopen();
        assertNotSame(input.actual().catalog().context(),reopened.catalog().context());
        long count=input.actualSetterPacketsWritten().getAsLong();
        var retained=canonical(input,reopened).orElseThrow();assertEquals(original,retained);verifyOriginal(input,reopened,retained);
        assertEquals(count,input.actualSetterPacketsWritten().getAsLong());
    }
    @Test void actualColdKnownRejectionUsesItsOriginalSourceWithoutCreatingFamilyMembership()throws Exception{
        var input=actual(Scenario.COLD_KNOWN_REJECTION);assertThrows(PublicServiceFailure.class,()->invoke(input));
        var original=canonical(input,input.actual()).orElseThrow();
        assertInstanceOf(ActionState.Rejected.class,assertInstanceOf(ActionState.Settled.class,original.state()).settlement());
        var reopened=input.coldOpen().orElseThrow(()->new IllegalStateException("MISSING_ACTUAL_COLD_OPERATOR_ROOT_INPUTS_NOT_RUN")).reopen();
        var retained=canonical(input,reopened).orElseThrow();assertEquals(original,retained);
        var history=reopened.history().orElseThrow(()->new IllegalStateException("MISSING_ACTUAL_COLD_OPERATOR_HISTORY_PRODUCTS_NOT_RUN"));
        long count=input.actualSetterPacketsWritten().getAsLong();
        root(reopened).withPublicStandaloneRead(input.deadline(),same->{
            assertDoesNotThrow(()->RootOperatorNonRebindMaterialTest.assertActualColdCanonicalNonRebind(
                    history.prepared(),reopened.catalog(),same,history.publisher(),retained));return null;
        });
        assertEquals(count,input.actualSetterPacketsWritten().getAsLong());
    }
}
