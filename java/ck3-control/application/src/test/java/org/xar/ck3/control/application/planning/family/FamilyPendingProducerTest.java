package org.xar.ck3.control.application.planning.family;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.planning.family.FamilyJson.*;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.family.FamilyMarriageIntent;
import org.xar.ck3.control.application.action.family.FamilyMarriageSendExpectation;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.writer.DomainBodies.Slot;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Actual pure pending producer -> JSON -> original domain/result consumer. No Native or writer qualification is claimed. */
final class FamilyPendingProducerTest {
    private static final FamilyPorts.BridgeIdentity BRIDGE = new FamilyPorts.BridgeIdentity(77, "20261023000000.000000+000");
    private static Obj json(String raw) { return decode(raw.getBytes(StandardCharsets.UTF_8)); }
    private static Obj snapshot() { return json("{\"snapshot_id\":\"native-1\",\"revision\":1,\"native_revision\":1,\"date_raw\":100,\"episode_run_id\":\"ep\",\"paused\":true,\"map_ready\":true,\"played_character\":{\"character_id\":1}}"); }
    private static Obj ledger(Slot slot) { return obj("schema", t(FamilyDomainSource.schema(slot)), "pending", Nil.INSTANCE, "resolved", Nil.INSTANCE); }
    private static FamilyPendingProducer.State state() { return new FamilyPendingProducer.State(ledger(Slot.FAMILY), ledger(Slot.CHILD_MATRILINEAL), ledger(Slot.DEFAULT_MARRIAGE)); }
    private static FamilyNativePreparation.MaterializedSend send() {return new FamilyNativePreparation.MaterializedSend(1,4,java.util.OptionalLong.of(3),java.util.OptionalLong.of(2),java.util.OptionalLong.empty(),5,
            new ExactRef("D:/fixture/family-before-read.json",1,"c".repeat(64)));}
    private static Obj plan() {
        Obj legal = json("{\"native_revision\":1,\"query_sequence\":7,\"exact_ck3_build\":\"1.20.0.4\",\"observed_first_heir_character_id\":3,\"native_legal_candidates\":[{\"candidate_character_id\":2,\"recipient_matchmaker_character_id\":4}]}");
        Obj relation = json("{\"status\":\"available\",\"bilateral_verified\":true,\"native_revision\":1,\"heir_character_id\":3,\"betrothed_character_id\":null,\"primary_spouse_character_id\":null,\"spouse_character_ids\":[]}");
        Obj diagnostic = json("{\"selected_candidate_character_id\":2,\"native_revision\":1,\"legality_query_sequence\":7,\"date_raw\":100,\"episode_run_id\":\"ep\",\"exact_ck3_build\":\"1.20.0.4\",\"source_projection_schema\":\"xar.ck3.first-heir-candidate-alliance-projection.v1\",\"rows\":[{\"candidate_character_id\":2,\"recipient_character_id\":4,\"recipient_matchmaker_character_id\":4,\"rejection_reasons\":[],\"heir_betrothed_character_id\":null,\"heir_primary_spouse_character_id\":null,\"heir_spouse_count\":0,\"possible_alliance_pairs\":[{\"first_character_id\":1,\"second_character_id\":4,\"already_allied\":false,\"both_have_realm_data\":true,\"would_attempt_if_accepted\":true}]}]}");
        Obj selected=object(array(diagnostic.get("rows")).getFirst()).with("matrilineal_option_selected",new Bool(false));
        diagnostic=diagnostic.with("rows",rows(List.of(selected)));
        return obj("schema",t(FamilyMarriagePreparationReview.SCHEMA),"selected_step", t(FamilyPendingProducer.Branch.HEIR.operation().value()), "family_marriage_legality", legal,
                "family_marriage_current_relationship", relation, "family_marriage_private_diagnostic", diagnostic,
                "family_marriage_projection",obj("rows",rows(List.of(obj("candidate_character_id",n(2)),obj("candidate_character_id",n(5)),obj("candidate_character_id",n(6)),obj("candidate_character_id",n(7)),obj("candidate_character_id",n(8))))),
                "family_marriage_choice", json("{\"candidate_character_id\":2,\"realm_alliance_attempt_if_accepted\":true}"));
    }
    private static ActionCommand command(Obj plan) {
        var source = new G2Source("fixture-family-machine", "2026-10-23T18:00:00Z", "1.20.0.4", new ExactRef("D:/fixture/family-source.json", 1, "a".repeat(64)));
        var before = new ObservationIdentity(source.machineId(), new GameGeneration(123, new PythonOnlyUInt64(new BigInteger("133700000000000001"))),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.ONE, BigInteger.ONE, BigInteger.valueOf(100)), "native-1", BigInteger.ONE, "ep"), 1);
        var expected = FamilyMarriageSendExpectation.expected(before,source,3,2);
        Obj intent=new FamilyMarriageIntent(FamilyMarriageIntent.Route.FIRST_HEIR,1,3,2,4,false,List.of(2,5,6,7,8),Optional.of(plan)).toJson();
        return new ActionCommand("family-fixture-1", before, source, "session-family", FamilyPendingProducer.Branch.HEIR.operation(), intent, expected,
                new JointBudgetSelector.Claims(Set.of(), Set.of(BigInteger.valueOf(4)), Set.of(BigInteger.ONE, BigInteger.TWO, BigInteger.valueOf(3), BigInteger.valueOf(4)), Set.of("first-heir-marriage:3")),
                Instant.parse("2026-10-23T18:00:30Z"));
    }
    @Test void producedPendingRoundtripsIntoOriginalResultConsumerWithoutPreproposalMaterialCredit() {
        ActionCommand original = command(plan()), roundtrip = ActionCodec.decodeCommand(ActionCodec.encodeCommand(original));
        var output = FamilyPendingProducer.produce(roundtrip, snapshot(), BRIDGE, state(),plan(),send());
        byte[] serialized = ContinuityJson.canonical(OpportunityJson.toNode(output.body()), ContinuityJson.DOMAIN_MAX_BYTES);
        Obj body = FamilyDomainSource.validate(Slot.FAMILY, serialized);
        assertEquals(output.body(), body); assertEquals(new Bool(false), output.pending().get("material_result"));
        assertEquals(t("may_have_submitted"), output.pending().get("submission_state"));
        assertEquals(t("basis_only_unpriced"), object(output.pending().get("selected_value_projection")).get("child_dynasty_prediction_status"));
        Obj read = json("{\"status\":\"marriage\",\"material_result\":true,\"heir_character_id\":3,\"candidate_character_id\":2,\"post_native_revision\":2}");
        Obj resolved = FamilyResultReducer.reduce(FamilyPorts.Query.FAMILY_RESULT, body, obj("pending", output.pending(), "cold", new Bool(false)), read, BRIDGE, integer(snapshot().get("date_raw")));
        assertEquals(Nil.INSTANCE, resolved.get("pending"));
        assertEquals(output.pending(), object(resolved.get("resolved")).get("source_pending"));
        FamilyDomainSource.validate(Slot.FAMILY, ContinuityJson.canonical(OpportunityJson.toNode(resolved), ContinuityJson.DOMAIN_MAX_BYTES));
    }
    @Test void pendingOrMissingOriginalDomainNeverPermitsAnotherProposal() {
        var first = FamilyPendingProducer.produce(command(plan()), snapshot(), BRIDGE, state(),plan(),send());
        var unresolved = new FamilyPendingProducer.State(first.body(), state().matrilineal(), state().childDefault());
        assertThrows(IllegalArgumentException.class, () -> FamilyPendingProducer.produce(command(plan()), snapshot(), BRIDGE, unresolved,plan(),send()));
        Obj missing = obj("schema", t(FamilyDomainSource.schema(Slot.FAMILY)), "resolved", Nil.INSTANCE);
        assertThrows(IllegalArgumentException.class, () -> FamilyPendingProducer.produce(command(plan()), snapshot(), BRIDGE,
                new FamilyPendingProducer.State(missing, state().matrilineal(), state().childDefault()),plan(),send()));
    }
    @Test void changedNativeFramePairAndDuplicateFinalRowsAreRejected() {
        assertThrows(IllegalArgumentException.class, () -> FamilyPendingProducer.produce(command(plan()), snapshot().with("native_revision", n(2)), BRIDGE, state(),plan(),send()));
        Obj changed = plan().with("family_marriage_choice", object(plan().get("family_marriage_choice")).with("candidate_character_id", new Bool(true)));
        assertThrows(IllegalArgumentException.class, () -> FamilyPendingProducer.produce(command(changed), snapshot(), BRIDGE, state(),changed,send()));
        Obj legal = object(plan().get("family_marriage_legality")); Value row = array(legal.get("native_legal_candidates")).get(0);
        Obj duplicate = plan().with("family_marriage_legality", legal.with("native_legal_candidates", rows(List.of(row, row))));
        assertThrows(IllegalArgumentException.class, () -> FamilyPendingProducer.produce(command(duplicate), snapshot(), BRIDGE, state(),duplicate,send()));
    }
    @Test void pendingUsesFreshPreparedSequenceRatherThanImmutableOldPlanningProof() {
        Obj old=plan(),fresh=old.with("family_marriage_legality",object(old.get("family_marriage_legality")).with("query_sequence",n(91)))
            .with("family_marriage_private_diagnostic",object(old.get("family_marriage_private_diagnostic")).with("legality_query_sequence",n(91)));
        ActionCommand command=command(old);
        var output=FamilyPendingProducer.produce(command,snapshot(),BRIDGE,state(),fresh,send());
        assertEquals(n(91),object(output.pending().get("selected_value_projection")).get("source_legality_query_sequence"));
        assertEquals(n(7),object(FamilyMarriageIntent.fromJson(command.arguments()).planningProof().orElseThrow().get("family_marriage_legality")).get("query_sequence"));
        assertThrows(IllegalArgumentException.class,()->FamilyPendingProducer.produce(command,snapshot(),BRIDGE,state(),obj("plan",old),send()));
        Obj changedRoles=fresh.with("family_marriage_choice",object(fresh.get("family_marriage_choice")).with("candidate_character_id",n(5)));
        assertThrows(IllegalArgumentException.class,()->FamilyPendingProducer.produce(command,snapshot(),BRIDGE,state(),changedRoles,send()));
    }
    @Test void educationSendDoesNotExpectAnImmediateGuardianRelation() {
        var expected = FamilyCommands.expected(new OperationKey("initiate-character-interaction-ordinary-v1"), obj("child_full_id", n(2), "guardian_full_id", n(3)), obj());
        assertTrue(expected.contains(new ExpectedBoolean(new FieldKey("outbound_request_effect_observed"), true)));
        assertFalse(expected.stream().anyMatch(value -> value.field().value().equals("guardian_relation_present")));
    }
    @Test void actualFiveRoleSenderContextRoundtripsAndPrivateRedirectOrUnsupportedArityAreRejected() {
        var actual=send();assertEquals(actual,FamilyNativePreparation.MaterializedSend.fromJson(actual.toJson()));
        var output=FamilyPendingProducer.produce(command(plan()),snapshot(),BRIDGE,state(),plan(),actual);
        assertEquals(actual.toJson(),output.pending().get("native_send_context"));
        assertEquals(t(FamilyNativePreparation.MaterializedSend.SCHEMA),output.pending().get("java_preparation_schema"));
        var redirected=new FamilyNativePreparation.MaterializedSend(9,4,actual.secondaryActorId(),actual.secondaryRecipientId(),actual.intermediaryId(),5,actual.beforeRead());
        assertThrows(IllegalArgumentException.class,()->FamilyPendingProducer.produce(command(plan()),snapshot(),BRIDGE,state(),plan(),redirected));
        for(Obj malformed:List.of(actual.toJson().with("sender_id",new Bool(true)),actual.toJson().with("role_arity",n(6)),
                actual.toJson().with("role_arity",Nil.INSTANCE),actual.toJson().with("sixth_role_id",n(7))))
            assertThrows(IllegalArgumentException.class,()->FamilyNativePreparation.MaterializedSend.fromJson(malformed));
    }
}
