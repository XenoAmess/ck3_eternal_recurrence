package org.xar.ck3.control.application.effects;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.JsonToken;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HexFormat;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.function.Consumer;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.capabilities.religion.PlayerHolyOrderContext;
import org.xar.ck3.control.nativebridge.capabilities.religion.PlayerHolyOrderContextRead;
import org.xar.ck3.control.nativebridge.capabilities.religion.PlayerReligionContext;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Mandatory actual C++ fixture outputs. Missing corpus is NOT EXECUTED/RED, never a skipped or synthetic native PASS. */
final class ArmyWarWindowProducerTest {
    @TempDir Path temporary;
    private int counter;
    private ObjectNode sourceMap;
    private static final Set<String> TARGETS = Set.of(
            "xar_ck3_12003_holy_order_war_eligibility_test", "xar_ck3_12003_holy_order_service_lifecycle_test",
            "xar_ck3_12003_holy_order_troop_association_test", "xar_ck3_12003_holy_order_hire_cost_context_test",
            "xar_ck3_12003_holy_order_current_reinforcement_test");
    record Sample(String target, byte[] originalFrame) {
        Sample { originalFrame = originalFrame.clone(); }
        @Override public byte[] originalFrame() { return originalFrame.clone(); }
    }
    private record FixtureOwner(String value) {
        FixtureOwner {
            StrictJson.require(value != null && !value.isBlank() && value.length() <= 128
                    && value.chars().noneMatch(c -> c < 32 || c == 127), "finite actual fixture owner required");
        }
        static FixtureOwner from(JsonNode value) { return new FixtureOwner(StrictJson.text(value)); }
    }
    private record FixtureOwnership(FixtureOwner owner, ObjectNode terminal, ObjectNode request) { }

    @Test void actualFixtureOwnerComesFromAllFivePinnedNativeTerminalsAndRequests() throws Exception {
        samples(); // The positive path must consume every actual C++ family and its original custody.
        ObjectNode corpus = object(StrictJson.parse(Files.readAllBytes(Path.of(required("xar.holyOrder.fixtureCorpus"))), StrictJson.EXPLICIT_MAX_BYTES));
        ObjectNode process = object(StrictJson.parse(pinned(ExactRef.fromJson(corpus.get("runs").get(0).get("receipt_ref"))), StrictJson.EXPLICIT_MAX_BYTES));
        FixtureOwnership original = ownership(process, corpus.get("machine_id"));
        FixtureOwner selected = FixtureOwner.from(map().get("owner"));
        FixtureOwner other = new FixtureOwner(selected.value() + "/different-executor");
        assertEquals(selected, original.owner());
        assertThrows(AssertionError.class, () -> requireSameFixtureOwner(other, original.terminal(), original.request()));
        ObjectNode wrongTerminal = original.terminal().deepCopy(); wrongTerminal.put("owner", other.value());
        assertThrows(AssertionError.class, () -> requireSameFixtureOwner(selected, wrongTerminal, original.request()));
        ObjectNode wrongRequest = original.request().deepCopy(); wrongRequest.put("owner", other.value());
        assertThrows(AssertionError.class, () -> requireSameFixtureOwner(selected, original.terminal(), wrongRequest));
        assertThrows(IllegalArgumentException.class, () -> FixtureOwner.from(StrictJson.object().put("owner", 7).get("owner")));
    }
    @Test void actualWholeCppProvidersReachStrictReadAndLosslessAllSubobserverModel() throws Exception {
        List<Sample> samples = samples();
        int seen = 0;
        for (Sample sample : samples) {
            ObjectNode packet = object(StrictJson.parse(sample.originalFrame(), StrictJson.EXPLICIT_MAX_BYTES));
            PlanningReadReceipt receipt = receipt(sample.originalFrame(), packet);
            var query = query(); var observation = query.contract().decode(receipt);
            assertTrue(query.contract().hasPureReplay());
            assertEquals(ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP, query.contract().guardMode());
            assertEquals(PlayerHolyOrderContextRead.flattened(observation),
                    PlayerHolyOrderContextRead.flattened(query.contract().replay(receipt)));
            ObjectNode original = object(packet.get("result").get("player_holy_order_context"));
            assertEquals(original, observation.context().encode(), "full actual native component changed; optional subobservers and occurrence order must survive");
            assertEquals(observation.context().encode(), PlayerHolyOrderContext.decode(observation.context().encode()).encode());
            ObjectNode normalized = PlayerHolyOrderContextRead.flattened(observation);
            assertEquals(original.get("rows"), normalized.get("rows"));
            assertEquals(receipt.request().before().frame().identity().player(), normalized.get("played_character_id").bigIntegerValue());
            assertEquals(receipt.request().before().frame().identity().nativeRevision(), normalized.get("queried_native_revision").bigIntegerValue());
            assertEquals(PlayerHolyOrderContextRead.OPERATION, query.contract().operation());
            seen++;
        }
        assertTrue(seen >= TARGETS.size(), "all five actual native provider families must be represented");
    }
    @Test void actualHolyProducerRegistersItsSameReadonlyContractAndReplaysOriginalPacketsThroughRootCatalog() throws Exception {
        var producer = query();
        ExactRef decoder = input("java_holy_order_read_decoder"); pinned(decoder);
        var installed = producer.installedRead(decoder);
        var catalog = new RootReadContractCatalog(List.of(installed), List.of());
        assertSame(producer.contract(), installed.contract()); assertEquals(decoder, installed.decoderSource());
        assertTrue(catalog.containsIdentity(producer.contract()));
        assertEquals(1, catalog.installed().size()); assertTrue(catalog.families().isEmpty());
        assertEquals(ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE, installed.contract().permissionMode());
        assertEquals(PlayerHolyOrderContextRead.PERMISSION, installed.contract().permissionKey());
        assertEquals(ReadContract.WireProfile.G2_PRIVATE_QUERY, installed.contract().wireProfile());
        assertEquals(ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP, installed.contract().guardMode());
        assertTrue(installed.contract().requiredCapability().isEmpty());
        assertEquals(sources().pythonProducer(), installed.contract().sourceRef());
        assertFalse(catalog.containsIdentity(query().contract()), "another reader is not the identical installed producer");
        assertThrows(IllegalArgumentException.class, () -> new RootReadContractCatalog(List.of(installed, installed), List.of()));
        for (Sample sample : samples()) {
            ObjectNode packet = object(StrictJson.parse(sample.originalFrame(), StrictJson.EXPLICIT_MAX_BYTES));
            PlanningReadReceipt original = receipt(sample.originalFrame(), packet);
            var actual = catalog.originalContract(producer.contract(), original.contractId()).orElseThrow();
            assertSame(producer.contract(), actual);
            var decoded = actual.decode(original);
            // Exact persistence codec roundtrip retains the original guards and original native packet; no new read is issued.
            ExactRef args = store("holy-order-arguments", OpportunityJson.encode(original.request().arguments()));
            var request = CommandOriginCodec.planningRequest(StrictJson.parse(StrictJson.canonical(
                    CommandOriginCodec.planningRequest(original.request(), args))), original.request().arguments());
            var before = CommandOriginCodec.planningGuard(StrictJson.parse(StrictJson.canonical(CommandOriginCodec.planningGuard(original.before()))));
            var after = CommandOriginCodec.planningGuard(StrictJson.parse(StrictJson.canonical(CommandOriginCodec.planningGuard(original.after()))));
            var restored = new PlanningReadReceipt(request, original.contractId(), original.requestId(), before, after, original.original());
            assertEquals(original, restored);
            assertEquals(PlayerHolyOrderContextRead.flattened(decoded), PlayerHolyOrderContextRead.flattened(actual.replay(restored)));
        }
    }
    @Test void wrongTypesFrameBuildIdentityAndCompletePacketCannotBecomeAnObservation() throws Exception {
        ObjectNode original = firstMilitaryFrame();
        List<Consumer<ObjectNode>> changes = List.of(
                frame -> component(frame).put("played_character_id", true),
                frame -> component(frame).put("played_character_id", component(frame).get("played_character_id").longValue() + 1),
                frame -> component(frame).put("date_raw", component(frame).get("date_raw").intValue() + 1),
                frame -> component(frame).put("capture_epoch", 0),
                frame -> component(frame).put("capture_epoch", "1"),
                frame -> component(frame).put("raw_scale", true),
                frame -> component(frame).put("available", 1),
                frame -> component(frame).put("schema", "another_schema"),
                frame -> firstMilitary(frame).put("holy_order_id", -1),
                frame -> firstMilitary(frame).put("rite_id", 4294967295L),
                frame -> firstMilitary(frame).put("employer_id", 1.0),
                frame -> terms(frame).put("can_hire", "true"),
                frame -> terms(frame).put("resource_costs_raw", 0),
                frame -> terms(frame).put("resource_scale", 1),
                frame -> terms(frame).put("can_hire_reasons_available", 1),
                frame -> terms(frame).put("can_afford_reasons_available", false).put("can_afford_reason_literal", "retained"),
                frame -> object(frame.get("result")).put("snapshot_revision", 1.0),
                frame -> object(frame.get("result")).put("date_raw", true),
                frame -> object(frame.get("result")).put("read_only", false),
                frame -> object(frame.get("result")).put("advertised", true),
                frame -> object(frame.get("result")).put("backend_id", "wrong"),
                frame -> object(frame.get("result")).put("domain_key", "wrong"),
                frame -> object(frame.get("result")).put("status", "submitted"),
                frame -> object(frame.get("result")).put("alias", 1));
        for (Consumer<ObjectNode> change : changes) {
            ObjectNode malformed = original.deepCopy(); change.accept(malformed);
            byte[] payload = StrictJson.canonical(malformed, StrictJson.EXPLICIT_MAX_BYTES);
            assertThrows(IllegalArgumentException.class, () -> PlayerHolyOrderContextRead.decode(receipt(payload, original)));
            assertThrows(IllegalArgumentException.class, () -> query().contract().replay(receipt(payload, original)));
        }
        var valid = receipt(StrictJson.canonical(original, StrictJson.EXPLICIT_MAX_BYTES), original);
        byte[] packet = valid.original().originalPacket(); packet[packet.length - 1] ^= 1;
        var badAck = new NativeActionPort.AckReceived(valid.requestId(), true, valid.original().originalResultToken(), valid.original().originalFrame(), packet);
        var changed = new PlanningReadReceipt(valid.request(), valid.contractId(), valid.requestId(), valid.before(), valid.after(), badAck);
        assertThrows(IllegalArgumentException.class, () -> PlayerHolyOrderContextRead.decode(changed));
        ObjectNode remapped = original.deepCopy();
        remapToFour(remapped);
        assertEquals("1.20.0.4", PlayerHolyOrderContextRead.decode(receipt(StrictJson.canonical(remapped, StrictJson.EXPLICIT_MAX_BYTES), remapped)).context().build().version(),
                "controlled schema/build remap is a codec case only; it is not a real .4/Game result");
    }
    @Test void originalSourceGateAndExactEmptyArgsRemainRequired() throws Exception {
        var query = query(); ObjectNode packet = firstMilitaryFrame(); var original = receipt(StrictJson.canonical(packet, StrictJson.EXPLICIT_MAX_BYTES), packet);
        assertEquals("{}", new String(query.contract().prepare(original.request(), "holy-source-gate").additionalFields().bytes(), java.nio.charset.StandardCharsets.UTF_8));
        var altered = new PlanningReadRequest(original.request().before(), original.request().source(), original.request().sessionId(), original.request().operation(),
                OpportunityJson.object(OpportunityJson.parse("{\"alias\":1}".getBytes(java.nio.charset.StandardCharsets.UTF_8)), "fixture"), original.request().deadline());
        assertThrows(IllegalArgumentException.class, () -> query.contract().prepare(altered, "holy-wrong-arguments"));
        var refs = sources();
        var wrong = new PlayerHolyOrderContextRead.Sources(new ExactRef(refs.pythonProducer().path(), refs.pythonProducer().bytes(), "0".repeat(64)),
                refs.pythonCostNormalizer(), refs.pythonReinforcementNormalizer(), refs.nativeMailbox(), refs.nativeWire(), refs.nativeContext(), refs.nativeReinforcement(), refs.nativeBuild4Binding());
        var bad = new PlayerHolyOrderContextRead(unusedReads(), wrong, (s, r) -> {});
        assertThrows(IllegalArgumentException.class, () -> bad.contract().prepare(original.request(), "holy-drifted-source"));
        assertThrows(IllegalArgumentException.class, () -> bad.contract().decode(original));
        assertTrue(bad.contract().hasPureReplay());
        assertEquals(PlayerHolyOrderContextRead.flattened(query.contract().decode(original)),
                PlayerHolyOrderContextRead.flattened(bad.contract().replay(original)),
                "the explicit archive parser does not execute source-file checks or a live query");
        var onlyHoly = ArmyWarWindowReads.Queries.forHolyHire(new ArmyWarWindowReads.Query<>(bad.contract(),
                value -> new RawJson(StrictJson.canonical(PlayerHolyOrderContextRead.flattened(value))), request -> new OpportunityJson.Obj(Map.of())));
        onlyHoly.require(new ArmyWarWindowReads.HolyHire(1));
        var selected = new ArmyWarWindowReads.HolyHire(1);
        var archivedContext = ArmyWarWindowReads.Request.fromReceipt(complete(original), selected, original);
        assertSame(bad.contract(), onlyHoly.get(ArmyWarWindowReads.View.HOLY_ORDER).contract(archivedContext));
        assertEquals(PlayerHolyOrderContextRead.flattened(query.contract().decode(original)),
                StrictJson.parse(onlyHoly.get(ArmyWarWindowReads.View.HOLY_ORDER).replay(archivedContext, original).normalized().bytes()));
        assertThrows(IllegalArgumentException.class, () -> onlyHoly.get(ArmyWarWindowReads.View.FINAL_CB_ROLES));
        assertThrows(IllegalArgumentException.class, () -> onlyHoly.require(new ArmyWarWindowReads.Window(ArmyWarWindowReads.WindowKind.RESULTS)));
    }
    @Test void actualWholeNativeAssociationsFeedSupplementWithoutPromotingEmployerSettlement() throws Exception {
        int checked=0;
        for(Sample sample:samples()) {
            ObjectNode packet=object(StrictJson.parse(sample.originalFrame(),StrictJson.EXPLICIT_MAX_BYTES));
            ObjectNode context=PlayerHolyOrderContextRead.flattened(query().contract().decode(receipt(sample.originalFrame(),packet)));
            BigInteger actor=context.get("played_character_id").bigIntegerValue();
            for(JsonNode row:context.withArray("rows")) {
                JsonNode association=row.path("military_terms").get("troop_association");
                if(association==null||!actor.equals(row.path("employer_id").bigIntegerValue())||!association.path("applies_to_player").asBoolean())continue;
                List<HolyHirePoststate.Member> members=new ArrayList<>();
                for(JsonNode member:association.path("rows"))members.add(new HolyHirePoststate.Member(member.get("regiment_id").bigIntegerValue(),
                        member.path("available").booleanValue(),member.path("regiment_resolved").booleanValue(),member.path("native_carmy_resolved").booleanValue(),
                        member.path("native_carmy_id").isNull()?Optional.empty():Optional.of(member.get("native_carmy_id").bigIntegerValue()),
                        member.path("combat_resolved").booleanValue(),member.path("combat_id").isNull()?Optional.empty():Optional.of(member.get("combat_id").bigIntegerValue())));
                var resolved=members.stream().filter(member->member.available()&&member.nativeArmyResolved()&&member.nativeArmyId().isPresent()).findFirst();
                if(resolved.isEmpty())continue;
                var status=association.path("available").booleanValue()?HolyHirePoststate.Status.AVAILABLE:HolyHirePoststate.Status.PARTIAL;
                var associated=new HolyHirePoststate.Association(status,members,status==HolyHirePoststate.Status.AVAILABLE?Optional.empty():Optional.of("partial native association"));
                // Control/soldiers are declared unit inputs here; the actual Strengths producer has its own complete corpus.
                var army=new HolyHirePoststate.Strength(BigInteger.valueOf(17),resolved.orElseThrow().nativeArmyId(),HolyHirePoststate.Quantity.value(BigInteger.valueOf(42)),true,Optional.of(BigInteger.valueOf(4444)),Optional.of(BigInteger.valueOf(460)));
                var troops=HolyHirePoststate.troops(associated,HolyHirePoststate.Status.AVAILABLE,List.of(army),Optional.empty());
                assertTrue(troops.usableArmyObserved());assertEquals(1,troops.materialArmies().size());
                assertEquals(resolved.orElseThrow().nativeArmyId().orElseThrow(),troops.materialArmies().getFirst().nativeArmyId());
                ObjectNode before=context.deepCopy();
                for(JsonNode candidate:before.withArray("rows"))if(candidate.get("holy_order_id").equals(row.get("holy_order_id"))) {
                    ObjectNode order=object(candidate);order.putNull("employer_id");
                    ObjectNode terms=object(order.get("military_terms"));terms.put("available",true).put("can_hire",true).put("can_afford",true);
                }
                var employer=NativeArmyWarWindowEffects.holy(new ArmyWarWindowReads.HolyHire(row.get("holy_order_id").longValue()),actor,before,context).orElseThrow();
                assertEquals("holy_order_employer_relationship_only",employer.get("postcondition_scope").textValue());
                assertFalse(employer.get("payment_observed").booleanValue());assertFalse(employer.get("public_cunit_availability_observed").booleanValue());
                assertEquals(context,PlayerHolyOrderContextRead.flattened(query().contract().replay(receipt(sample.originalFrame(),packet))));
                checked++;
            }
        }
        assertTrue(checked>0,"the actual Native troop-association corpus must contain a resolved player-associated member");
    }

    @Test void independentHolyEmployerTransitionGivesNoPaymentOrUsableUnitCredit() throws Exception {
        // The before/after variant below is explicitly controlled. Whole native provider decoding is exercised above.
        ObjectNode packet = firstMilitaryFrame(); ObjectNode beforePacket = packet.deepCopy(), afterPacket = packet.deepCopy();
        ObjectNode beforeRow = firstMilitary(beforePacket), afterRow = firstMilitary(afterPacket);
        BigInteger actor = component(packet).get("played_character_id").bigIntegerValue();
        long selectedId = beforeRow.get("holy_order_id").longValue();
        beforeRow.putNull("employer_id"); afterRow.put("employer_id", actor);
        object(beforeRow.get("military_terms")).put("available", true).putNull("unavailable_reason").put("can_hire", true).put("can_afford", true);
        // Remove only additive employer-scoped fields from these controlled historical-format variants; full current variants remain covered by original corpus.
        for (ObjectNode row : List.of(beforeRow, afterRow)) {
            ObjectNode terms = object(row.get("military_terms"));
            terms.remove(List.of("current_reinforcement_v1", "service_lifecycle", "troop_association"));
        }
        var before = PlayerHolyOrderContextRead.flattened(PlayerHolyOrderContextRead.decode(receipt(StrictJson.canonical(beforePacket, StrictJson.EXPLICIT_MAX_BYTES), beforePacket)));
        var after = PlayerHolyOrderContextRead.flattened(PlayerHolyOrderContextRead.decode(receipt(StrictJson.canonical(afterPacket, StrictJson.EXPLICIT_MAX_BYTES), afterPacket)));
        var material = NativeArmyWarWindowEffects.holy(new ArmyWarWindowReads.HolyHire(selectedId), actor, before, after).orElseThrow();
        assertEquals("holy_order_employer_relationship_only", material.get("postcondition_scope").textValue());
        assertFalse(material.get("payment_observed").booleanValue());
        assertFalse(material.get("public_cunit_availability_observed").booleanValue());
        assertTrue(NativeArmyWarWindowEffects.holy(new ArmyWarWindowReads.HolyHire(selectedId), actor, before, before).isEmpty());
        assertTrue(NativeArmyWarWindowEffects.holy(new ArmyWarWindowReads.HolyHire(selectedId), actor, after, after).isEmpty());
        ObjectNode absent = after.deepCopy(); absent.putArray("rows");
        assertTrue(NativeArmyWarWindowEffects.holy(new ArmyWarWindowReads.HolyHire(selectedId), actor, before, absent).isEmpty());
        ObjectNode duplicate = after.deepCopy(); ((com.fasterxml.jackson.databind.node.ArrayNode) duplicate.get("rows")).add(firstMilitary(afterPacket).deepCopy());
        assertThrows(IllegalArgumentException.class, () -> NativeArmyWarWindowEffects.holy(new ArmyWarWindowReads.HolyHire(selectedId), actor, before, duplicate));
    }
    @Test void actualHolyTopFlowsThroughIndependentPendingProducerAndPureReplayWithEmployerOnlyCredit() throws Exception {
        // Controlled variants of the actual C++ TOP corpus exercise source contracts, not live Game qualification.
        ObjectNode beforePacket=firstMilitaryFrame(),afterPacket=beforePacket.deepCopy();
        var beforeRow=firstMilitary(beforePacket);var afterRow=firstMilitary(afterPacket);
        BigInteger actor=component(beforePacket).get("played_character_id").bigIntegerValue();long selectedId=beforeRow.get("holy_order_id").longValue();
        beforeRow.putNull("employer_id");afterRow.put("employer_id",actor);
        terms(beforePacket).put("available",true).putNull("unavailable_reason").put("can_hire",true).put("can_afford",true);
        for(var row:List.of(beforeRow,afterRow))object(row.get("military_terms")).remove(List.of("current_reinforcement_v1","service_lifecycle","troop_association"));
        var ordinary=receipt(StrictJson.canonical(beforePacket,StrictJson.EXPLICIT_MAX_BYTES),beforePacket);
        var afterRaw=receipt(StrictJson.canonical(afterPacket,StrictJson.EXPLICIT_MAX_BYTES),afterPacket);
        var afterRequest=new PlanningReadRequest(afterRaw.request().before(),ordinary.request().source(),ordinary.request().sessionId(),afterRaw.request().operation(),afterRaw.request().arguments(),ordinary.request().deadline());
        var afterBinding=new GuardEvidence(afterRequest.before(),afterRequest.source(),afterRequest.sessionId(),afterRaw.before().binding().connectionGeneration(),afterRequest.operation(),
                afterRaw.before().binding().nativeEvidence(),afterRaw.before().binding().capabilityEvidence(),"controlled-same-source-after",afterRaw.before().binding().observedAt(),afterRequest.deadline());
        var afterGuard=new PlanningReadGuard(afterBinding,true,true,true,afterRaw.before().originalBindingSha256());
        var afterOriginal=new PlanningReadReceipt(afterRequest,afterRaw.contractId(),afterRaw.requestId(),afterGuard,afterGuard,afterRaw.original());
        var frame=complete(afterOriginal);var selected=new ArmyWarWindowReads.HolyHire(selectedId);
        var call=new org.xar.ck3.control.nativebridge.capabilities.army.ArmyCalls.Hire(
                org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod.HIRE_HOLY_ORDER_V1,
                new org.xar.ck3.control.nativebridge.capabilities.army.ArmyCalls.Revision(
                    new org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.Present<>(ordinary.request().before().frame().revision())),
                new org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.HireId(selectedId));
        ExactRef preflight=store("unqualified-preflight-data",StrictJson.canonical(CommandOriginCodec.planningGuard(ordinary.before())));
        var outer=new org.xar.ck3.control.nativebridge.capabilities.army.ArmyOrdinaryActionArguments(selected.kind(),
                org.xar.ck3.control.nativebridge.capabilities.army.ArmyCallCodec.encode(call),List.of(preflight));
        var expected=NativeArmyWarWindowEffects.expected(ordinary.request().before(),ordinary.request().source(),selected.operation(),outer.raw());
        var command=new ActionCommand("holy-original-data",ordinary.request().before(),ordinary.request().source(),ordinary.request().sessionId(),selected.operation(),outer.encode(),expected,
                new JointBudgetSelector.Claims(Set.of(),Set.of(),Set.of(),Set.of()),ordinary.request().deadline());
        var prior=ordinary.before().binding();
        var guard=new GuardEvidence(command.before(),command.source(),command.sessionId(),prior.connectionGeneration(),selected.operation(),prior.nativeEvidence(),prior.capabilityEvidence(),
                "unqualified-holy-source-data",prior.observedAt(),command.deadline());
        var prepared=new NativeRequest("hire-holy-order-v1",Optional.of("game.command.hire-holy-order-v1"),
                new RawJson(StrictJson.canonical(StrictJson.object().put("holy_order_id",selectedId))));
        var attempt=new ActionState.Attempt("original-holy-hire-request",prior.observedAt(),guard,prepared);
        var lost=new NativeActionPort.Unknown(attempt.requestId(),"controlled lost response",new byte[]{1},Optional.empty());
        var pending=new ActionReceipt(1,2,command,ActionCodec.bodySha256(command),new ActionState.Unknown(Optional.of(attempt),Optional.of(lost),"controlled source DATA",List.of()));
        ExactRef driver=store("unqualified-driver-data",new byte[]{'{','}'});
        var evidence=new ReconciliationIdentity.Evidence(frame.originalEvidence(),afterOriginal.before().binding().capabilityEvidence(),
                store("unqualified-heartbeat-data",new byte[]{1}),store("unqualified-manifest-data",new byte[]{2}),driver,store("unqualified-source-data",new byte[]{3}));
        // The actual writer/archive membership is covered by HolyOrderReconciliationFamilyAdmissionTest; this reference is DATA only.
        var identity=ReconciliationIdentity.fromCanonical(pending,frame.identity(),frame.source(),frame.sessionId(),frame.connectionGeneration(),
                store("unqualified-pending-command-data",ActionCodec.encodeCommand(command)),driver,evidence,frame.observedAt());
        var request=PlanningReadRequest.newReconciliation(identity,PlayerHolyOrderContextRead.OPERATION,new OpportunityJson.Obj(Map.of()),command.deadline());
        var binding=new GuardEvidence(request.origin(),frame.source(),frame.sessionId(),frame.connectionGeneration(),request.operation(),frame.originalEvidence(),identity.capabilityEvidence(),
                "unqualified-holy-reconciliation-data",frame.observedAt(),request.deadline(),identity.supportingEvidence());
        var readGuard=new PlanningReadGuard(binding,new PlanningReadGuard.Reconciliation(),identity.bindingSha256());
        var original=new PlanningReadReceipt(request,PlayerHolyOrderContextRead.RECONCILIATION_CONTRACT_ID,afterOriginal.requestId(),readGuard,readGuard,afterOriginal.original());
        int[] queries={0};
        var readPort=new PlanningReadPort(){
            @Override public <T>PlanningReadResult<T> read(ReadContract<T> contract,PlanningReadRequest actual){
                assertEquals(request,actual);assertEquals(PlayerHolyOrderContextRead.RECONCILIATION_CONTRACT_ID,contract.contractId());queries[0]++;
                var wire=contract.prepare(actual,"independent-data-query");assertEquals(PlayerHolyOrderContextRead.STEP,wire.step());assertTrue(wire.requiredCapability().isEmpty());assertEquals("{}",new String(wire.additionalFields().bytes(),java.nio.charset.StandardCharsets.UTF_8));
                return new PlanningReadResult.Known<>(contract.decode(original),original,preflight);
            }
        };
        var producer=new PlayerHolyOrderContextRead(readPort,sources(),(s,r)->assertEquals(identity,r.origin().requireReconciliation()));
        var catalog=new RootReadContractCatalog(List.of(producer.installedRead(input("java_holy_order_read_decoder")),
                producer.reconciliationInstalledRead(input("java_holy_order_read_decoder"))),List.of());
        assertTrue(catalog.containsIdentity(producer.contract()));assertTrue(catalog.containsIdentity(producer.reconciliationContract()));
        PlayerHolyOrderContextRead.requireCanonicalReconciliation(pending,attempt,identity,producer.reconciliationContract(),request);
        var query=new ArmyWarWindowReads.Query<PlayerHolyOrderContextRead.Observation>(PlayerHolyOrderContextRead.OPERATION,
                scope->scope.reconciliation().isPresent()?producer.reconciliationContract():producer.contract(),
                value->new RawJson(StrictJson.canonical(PlayerHolyOrderContextRead.flattened(value))),scope->new OpportunityJson.Obj(Map.of()));
        var scope=new ArmyWarWindowReads.Request(frame,selected,request.deadline(),Optional.of(identity));
        assertInstanceOf(PlanningReadResult.Known.class,query.read(readPort,scope));assertEquals(1,queries[0]);
        var requestRef=store("reconciliation-arguments",OpportunityJson.encode(request.arguments()));
        var restoredRequest=CommandOriginCodec.planningRequest(StrictJson.parse(StrictJson.canonical(CommandOriginCodec.planningRequest(request,requestRef))),request.arguments());
        var restoredGuard=CommandOriginCodec.planningGuard(StrictJson.parse(StrictJson.canonical(CommandOriginCodec.planningGuard(readGuard))));
        var restored=new PlanningReadReceipt(restoredRequest,original.contractId(),original.requestId(),restoredGuard,restoredGuard,original.original());
        var normalized=object(StrictJson.parse(query.replay(ArmyWarWindowReads.Request.fromReceipt(frame,selected,restored),restored).normalized().bytes()));
        assertEquals(1,queries[0],"pure archive replay cannot query or repeat the original hire");
        var before=PlayerHolyOrderContextRead.flattened(PlayerHolyOrderContextRead.decode(ordinary));
        assertTrue(NativeArmyWarWindowEffects.canCollect(selected,selected.operation(),lost));
        var effect=NativeArmyWarWindowEffects.holy(selected,actor,before,normalized).orElseThrow();
        assertFalse(effect.get("payment_observed").booleanValue());assertFalse(effect.get("public_cunit_availability_observed").booleanValue());
        assertEquals("holy_order_employer_relationship_only",effect.get("postcondition_scope").textValue());assertFalse(pending.settled());
        assertThrows(IllegalArgumentException.class,()->producer.contract().replay(restored));
        var wrong=new PlanningReadReceipt(restoredRequest,PlayerHolyOrderContextRead.CONTRACT_ID,original.requestId(),restoredGuard,restoredGuard,original.original());
        assertThrows(IllegalArgumentException.class,()->producer.reconciliationContract().replay(wrong));
    }
    @Test void invitedOrOldWarAbsentDoesNotBecomeAnAllyJoin() {
        BigInteger actor = BigInteger.valueOf(41); int war = Integer.MIN_VALUE + 7, recipient = 52;
        var selected = new ArmyWarWindowReads.CallAlly(war, recipient);
        ObjectNode before = family(actor, recipient, war, "absent"), invited = family(actor, recipient, war, "absent");
        object(invited.path("alliance_obligations").path("first_wars").get(0)).put("recipient_was_called", true);
        assertTrue(NativeArmyWarWindowEffects.ally(selected, actor, before, invited).isEmpty(), "was_called/ACK is not membership");
        ObjectNode joined = family(actor, recipient, war, "attacker");
        assertEquals("same_selected_active_war_actual_participant_side",
                NativeArmyWarWindowEffects.ally(selected, actor, before, joined).orElseThrow().get("postcondition_scope").textValue());
        ObjectNode absent = family(actor, recipient, war, "absent"); object(absent.get("alliance_obligations")).putArray("first_wars");
        assertTrue(NativeArmyWarWindowEffects.ally(selected, actor, before, absent).isEmpty(), "old war absent cannot establish invitation success or war victory");
        assertTrue(NativeArmyWarWindowEffects.ally(selected, actor, before, family(actor, recipient, war + 0x01000000, "attacker")).isEmpty(), "same index other generation is another war");
        ObjectNode wrong = family(actor, recipient, war, "attacker"); object(wrong.get("alliance_obligations")).put("first_character_id", 42);
        assertThrows(IllegalArgumentException.class, () -> NativeArmyWarWindowEffects.ally(selected, actor, before, wrong));
    }
    @Test void fixedWindowNegativeOwnerProofIsUiOnlyAndCannotUseCloseAck() {
        var selected = new ArmyWarWindowReads.Window(ArmyWarWindowReads.WindowKind.RESULTS);
        ObjectNode before = fixedWindow(true, true), absent = fixedWindow(false, false);
        ObjectNode result = NativeArmyWarWindowEffects.window(selected, before, absent).orElseThrow();
        assertFalse(result.get("war_outcome_observed").booleanValue()); assertFalse(result.get("terms_observed").booleanValue());
        assertTrue(NativeArmyWarWindowEffects.window(selected, absent, absent).isEmpty(), "preexisting absence is no close action credit");
        ObjectNode incomplete = absent.deepCopy(); incomplete.put("root_observation_source", "guarded_registered_top_level");
        assertThrows(IllegalArgumentException.class, () -> NativeArmyWarWindowEffects.window(selected, before, incomplete));
        ObjectNode ack = absent.deepCopy(); ack.put("operation", "close").put("closure_verified", true).put("dispatch_attempted", true);
        assertThrows(IllegalArgumentException.class, () -> NativeArmyWarWindowEffects.window(selected, before, ack));
        ObjectNode forgedTicket = absent.deepCopy();
        object(forgedTicket.path("native_command_result").get("war_results_window_owner_receipt")).put("completed_sequence", true);
        assertThrows(IllegalArgumentException.class, () -> NativeArmyWarWindowEffects.window(selected, before, forgedTicket));
    }
    @Test void unsignedFamilyReferencesRetainTheCompleteSignedPublicRawBits() {
        BigInteger actor = BigInteger.valueOf(41);
        int recipient = Integer.MIN_VALUE + 13, war = Integer.MIN_VALUE + 7;
        var selected = new ArmyWarWindowReads.CallAlly(war, recipient);
        ObjectNode before = family(actor, recipient, war, "absent"), after = family(actor, recipient, war, "attacker");
        ObjectNode material = NativeArmyWarWindowEffects.ally(selected, actor, before, after).orElseThrow();
        assertEquals(Integer.toUnsignedLong(war), material.get("war_id").longValue());
        assertEquals(Integer.toUnsignedLong(recipient), material.get("recipient_character_id").longValue());
        assertTrue(NativeArmyWarWindowEffects.ally(selected, actor, before,
                family(actor, recipient, war + 0x01000000, "attacker")).isEmpty());
        assertTrue(NativeArmyWarWindowEffects.ally(selected, actor, before,
                family(actor, recipient, war, "absent")).isEmpty());
        ObjectNode signedAlias = after.deepCopy();
        object(signedAlias.get("alliance_obligations")).put("second_character_id", recipient);
        assertThrows(IllegalArgumentException.class, () -> NativeArmyWarWindowEffects.ally(selected, actor, before, signedAlias));
        assertThrows(IllegalArgumentException.class, () -> new ArmyWarWindowReads.CallAlly(-1, recipient));
        assertThrows(IllegalArgumentException.class, () -> new ArmyWarWindowReads.CallAlly(war, -1));
    }

    @Test void frameScopedContractsRouteBeforeAfterAndPureArchiveWithoutRelabelingReceipts() throws Exception {
        // Controlled router contracts exercise exact scope selection; this is not a new native execution or qualification.
        ObjectNode beforePacket = firstMilitaryFrame(), afterPacket = beforePacket.deepCopy();
        object(afterPacket.get("result")).put("snapshot_revision",
                beforePacket.path("result").path("snapshot_revision").bigIntegerValue().add(BigInteger.ONE));
        PlanningReadReceipt before = scopedReceipt(beforePacket), after = scopedReceipt(afterPacket);
        var beforeFrame = complete(before); var afterFrame = complete(after);
        var selected = new ArmyWarWindowReads.HolyHire(1);
        int[] callbacks = {0, 0, 0};
        ReadContract<String> beforeContract = routingContract(before.contractId(), callbacks);
        ReadContract<String> afterContract = routingContract(after.contractId(), callbacks);
        var query = new ArmyWarWindowReads.Query<String>(PlayerHolyOrderContextRead.OPERATION,
                request -> {
                    if (request.frame().equals(beforeFrame)) return beforeContract;
                    if (request.frame().equals(afterFrame)) return afterContract;
                    throw new IllegalArgumentException("no actual fixture contract for this frame");
                }, value -> new RawJson(StrictJson.canonical(StrictJson.object().put("contract", value))),
                request -> new OpportunityJson.Obj(Map.of()));
        List<ReadContract<?>> routed = new ArrayList<>();
        PlanningReadPort capture = new PlanningReadPort() {
            @Override public <T> PlanningReadResult<T> read(ReadContract<T> contract, PlanningReadRequest request) {
                routed.add(contract);
                assertEquals(request.before().equals(beforeFrame.identity()) ? before.contractId() : after.contractId(), contract.contractId());
                return new PlanningReadResult.Unavailable<>("software-only routing capture; no native query", Optional.empty());
            }
        };
        query.read(capture, beforeFrame, selected, before.request().deadline());
        query.read(capture, afterFrame, selected, after.request().deadline());
        assertSame(beforeContract, routed.get(0)); assertSame(afterContract, routed.get(1));
        var beforeContext = ArmyWarWindowReads.Request.fromReceipt(beforeFrame, selected, before);
        var afterContext = ArmyWarWindowReads.Request.fromReceipt(afterFrame, selected, after);
        assertEquals(before.contractId(), StrictJson.parse(query.decode(beforeContext, before).normalized().bytes()).get("contract").textValue());
        assertEquals(after.contractId(), StrictJson.parse(query.replay(afterContext, after).normalized().bytes()).get("contract").textValue());
        assertEquals(0, callbacks[0], "archive never prepares or dispatches");
        assertEquals(1, callbacks[1], "pure replay never calls the live decoder");
        assertEquals(1, callbacks[2]);
        var wronglyFixed = new ArmyWarWindowReads.Query<>(beforeContract,
                value -> new RawJson(StrictJson.canonical(StrictJson.object().put("contract", value))),
                request -> new OpportunityJson.Obj(Map.of()));
        assertThrows(IllegalArgumentException.class, () -> wronglyFixed.replay(afterContext, after));
        assertThrows(IllegalArgumentException.class, () -> ArmyWarWindowReads.Request.fromReceipt(beforeFrame, selected, after));
        var wrongDeadline = new ArmyWarWindowReads.Request(afterFrame, selected, after.request().deadline().plusSeconds(1));
        assertThrows(IllegalArgumentException.class, () -> query.replay(wrongDeadline, after));
        var wrongArguments = new ArmyWarWindowReads.Query<String>(PlayerHolyOrderContextRead.OPERATION,
                request -> afterContract, value -> new RawJson(StrictJson.canonical(StrictJson.object().put("contract", value))),
                request -> new OpportunityJson.Obj(Map.of("alias", new OpportunityJson.IntegerValue(BigInteger.ONE))));
        assertThrows(IllegalArgumentException.class, () -> wrongArguments.replay(afterContext, after));
        assertEquals(0, callbacks[0]); assertEquals(1, callbacks[1]); assertEquals(1, callbacks[2]);
    }
    @Test void archivedReconciliationKeepsItsOriginalIdentityAndNeverBorrowsGameplayReadiness() throws Exception {
        // Pure data/router regression. These constructors grant no canonical writer membership or actual query permission.
        ObjectNode packet = firstMilitaryFrame();
        PlanningReadReceipt original = receipt(StrictJson.canonical(packet, StrictJson.EXPLICIT_MAX_BYTES), packet);
        var frame = complete(original);
        ExactRef retainedDriver = store("retained-driver", "{}".getBytes(java.nio.charset.StandardCharsets.UTF_8));
        var evidence = new ReconciliationIdentity.Evidence(frame.originalEvidence(), original.before().binding().capabilityEvidence(),
                store("heartbeat", "heartbeat".getBytes(java.nio.charset.StandardCharsets.UTF_8)),
                store("manifest", "manifest".getBytes(java.nio.charset.StandardCharsets.UTF_8)), retainedDriver,
                store("qualification", "qualification".getBytes(java.nio.charset.StandardCharsets.UTF_8)));
        var pending = new ReconciliationIdentity.Pending("controlled-route-action", "b".repeat(64), "original-pending-request",
                frame.identity(), store("pending", "pending".getBytes(java.nio.charset.StandardCharsets.UTF_8)), retainedDriver);
        var identity = new ReconciliationIdentity(frame.identity(), frame.source(), frame.sessionId(), frame.connectionGeneration(),
                pending, evidence, frame.observedAt());
        var selected = new ArmyWarWindowReads.HolyHire(1);
        var context = new ArmyWarWindowReads.Request(frame, selected, original.request().deadline(), Optional.of(identity));
        PlanningReadRequest request = context.planning(PlayerHolyOrderContextRead.OPERATION, new OpportunityJson.Obj(Map.of()));
        assertEquals(identity, request.origin().requireReconciliation());
        assertThrows(IllegalStateException.class, request::before);
        var binding = new GuardEvidence(request.origin(), frame.source(), frame.sessionId(), frame.connectionGeneration(),
                request.operation(), frame.originalEvidence(), identity.capabilityEvidence(), "software-reconciliation-only",
                frame.observedAt(), request.deadline(), identity.supportingEvidence());
        var guard = new PlanningReadGuard(binding, new PlanningReadGuard.Reconciliation(), identity.bindingSha256());
        String id = "software-only/reconciliation/" + frame.identity().frame().revision();
        PlanningReadReceipt archived = new PlanningReadReceipt(request, id, original.requestId(), guard, guard, original.original());
        // Use the exact public persistence codec, including its distinct reconciliation guard shape.
        ExactRef argumentsRef = store("reconciliation-arguments", OpportunityJson.encode(request.arguments()));
        var requestJson = StrictJson.parse(StrictJson.canonical(CommandOriginCodec.planningRequest(request, argumentsRef)));
        var guardJson = StrictJson.parse(StrictJson.canonical(CommandOriginCodec.planningGuard(guard)));
        var roundTripRequest = CommandOriginCodec.planningRequest(requestJson, request.arguments());
        var roundTripGuard = CommandOriginCodec.planningGuard(guardJson);
        assertEquals(request, roundTripRequest); assertEquals(guard, roundTripGuard);
        archived = new PlanningReadReceipt(roundTripRequest, id, original.requestId(), roundTripGuard, roundTripGuard, original.original());
        final PlanningReadReceipt originalArchive = archived;
        var restored = ArmyWarWindowReads.Request.fromReceipt(frame, selected, originalArchive);
        assertEquals(identity, restored.reconciliation().orElseThrow());
        assertThrows(IllegalStateException.class, guard::paused);
        int[] callbacks = {0, 0, 0};
        ReadContract<String> actual = routingContract(id, callbacks, ReadContract.GuardMode.RECONCILIATION_OBSERVATION);
        var query = new ArmyWarWindowReads.Query<String>(request.operation(), value -> actual,
                value -> new RawJson(StrictJson.canonical(StrictJson.object().put("contract", value))),
                value -> new OpportunityJson.Obj(Map.of()));
        assertEquals(id, StrictJson.parse(query.replay(restored, originalArchive).normalized().bytes()).get("contract").textValue());
        assertEquals(0, callbacks[0]); assertEquals(0, callbacks[1]); assertEquals(1, callbacks[2]);
        var gameplay = new ArmyWarWindowReads.Request(frame, selected, request.deadline());
        assertThrows(IllegalArgumentException.class, () -> query.replay(gameplay, originalArchive));
        ReadContract<String> wrongPhase = routingContract(id, callbacks);
        var badQuery = new ArmyWarWindowReads.Query<String>(request.operation(), value -> wrongPhase,
                value -> new RawJson(StrictJson.canonical(StrictJson.object().put("contract", value))),
                value -> new OpportunityJson.Obj(Map.of()));
        assertThrows(IllegalArgumentException.class, () -> badQuery.replay(restored, originalArchive));
        var wrongBinding = new PlanningReadGuard(binding, new PlanningReadGuard.Reconciliation(), frame.fullBindingSha256());
        var changed = new PlanningReadReceipt(request, id, original.requestId(), wrongBinding, wrongBinding, original.original());
        assertThrows(IllegalArgumentException.class, () -> ArmyWarWindowReads.Request.fromReceipt(frame, selected, changed));
        assertEquals(0, callbacks[0]); assertEquals(0, callbacks[1]); assertEquals(1, callbacks[2]);
    }

    private ReadContract<String> routingContract(String id, int[] callbacks) throws Exception {
        return routingContract(id, callbacks, ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP);
    }
    private ReadContract<String> routingContract(String id, int[] callbacks, ReadContract.GuardMode guardMode) throws Exception {
        return new ReadContract<>(id, PlayerHolyOrderContextRead.OPERATION, Optional.empty(), PlayerHolyOrderContextRead.PERMISSION,
                ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE, ReadContract.WireProfile.G2_PRIVATE_QUERY,
                guardMode, input("python_holy_context"),
                (request, requestId) -> { callbacks[0]++; throw new AssertionError("router fixture must never prepare a native request"); },
                receipt -> { callbacks[1]++; return receipt.contractId(); },
                receipt -> { callbacks[2]++; return receipt.contractId(); });
    }
    private PlanningReadReceipt scopedReceipt(ObjectNode packet) throws Exception {
        String id = "software-only/holy-frame/" + packet.path("result").path("snapshot_revision").bigIntegerValue();
        return receipt(StrictJson.canonical(packet, StrictJson.EXPLICIT_MAX_BYTES), packet, id);
    }
    private static org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete complete(PlanningReadReceipt receipt) {
        var guard = receipt.before();
        return new org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete(receipt.request().before(),
                receipt.request().source(), receipt.request().sessionId(), guard.binding().connectionGeneration(),
                new OpportunityJson.Obj(Map.of()), guard.binding().nativeEvidence(), guard.binding().observedAt(), guard.originalBindingSha256());
    }

    private static ObjectNode family(BigInteger actor, int recipient, int war, String recipientSide) {
        ObjectNode n = StrictJson.object(), alliance = n.putObject("alliance_obligations").put("status", "available")
                .put("first_character_id", actor).put("second_character_id", Integer.toUnsignedLong(recipient));
        alliance.putArray("first_wars").addObject().put("war_id", Integer.toUnsignedLong(war)).put("caller_character_id", actor)
                .put("recipient_character_id", Integer.toUnsignedLong(recipient)).put("caller_side", "attacker").put("recipient_side", recipientSide)
                .put("recipient_was_called", false).put("native_complete_can_send", true);
        return n;
    }
    private static ObjectNode fixedWindow(boolean present, boolean visible) {
        BigInteger ticket = new BigInteger("9007199254740993");
        ObjectNode n = StrictJson.object().put("operation", "query").put("window_name", "war_results").put("available", true)
                .put("root_observed", true).put("post_observed", true).put("scope_unchanged", true).put("application_owner_thread_verified", true)
                .put("dispatch_attempted", false).put("dispatch_invoked", false).put("native_handled", false).put("closure_verified", false)
                .put("window_present", present).put("effective_visible", visible).put("post_window_present", present).put("post_effective_visible", visible)
                .put("root_observation_source", "guarded_top_level_and_complete_owner_tree").put("post_observation_source", "guarded_top_level_and_complete_owner_tree")
                .put("ticket_sequence", ticket).put("request_id", "actual-read-fixture");
        n.putObject("native_command_result").putObject("war_results_window_owner_receipt").put("ticket_sequence", ticket)
                .put("executor_started_sequence", ticket).put("completed_sequence", ticket).put("request_id", "actual-read-fixture");
        return n;
    }
    @Test void unknownWindowOrHireSubmissionIsCollectedFromActualStateWithoutResending() throws java.io.IOException {
        var holy = new ArmyWarWindowReads.HolyHire(0x81000003L);
        var window = new ArmyWarWindowReads.Window(ArmyWarWindowReads.WindowKind.RESULTS);
        var ally = new ArmyWarWindowReads.CallAlly(7, 52);
        var declaration = new ArmyWarWindowReads.Declaration("52-1--1");
        NativeActionPort.Unknown unknown = new NativeActionPort.Unknown("original-request", "response timeout", new byte[]{1}, Optional.empty());
        assertTrue(NativeArmyWarWindowEffects.canCollect(holy, holy.operation(), unknown));
        assertTrue(NativeArmyWarWindowEffects.canCollect(window, window.operation(), unknown));
        assertTrue(NativeArmyWarWindowEffects.canCollect(ally, ally.operation(), unknown));
        assertFalse(NativeArmyWarWindowEffects.canCollect(declaration, declaration.operation(), unknown),
                "original declaration acceptance cannot be inferred from a new war");
        ObjectNode result = StrictJson.object().put("step", window.operation().value()).put("accepted", false);
        ObjectNode frame = StrictJson.object().put("type", "command_result").put("protocol_version", 1)
                .put("request_id", "original-request").put("ok", true); frame.set("result", result);
        byte[] payload = StrictJson.canonical(frame);
        var verificationPending = new NativeActionPort.AckReceived("original-request", true,
                Optional.of(new RawJson(StrictJson.canonical(result))), new RawJson(payload), NativeWire.packet(payload));
        assertTrue(NativeArmyWarWindowEffects.canCollect(window, window.operation(), verificationPending),
                "a close verification_pending ACK can later resolve through the independent qualified window query");
        var zero = new NativeActionPort.RejectedBeforeDispatch("original-request",
                new NativeActionPort.ZeroDispatchProof(NativeActionPort.ZeroDispatchStage.BEFORE_WRITE, 0, "not written", Optional.empty()));
        assertFalse(NativeArmyWarWindowEffects.canCollect(holy, holy.operation(), zero));
        // Permission to collect is not success: an unchanged state remains pending in the identical material projector.
        assertTrue(NativeArmyWarWindowEffects.window(window, fixedWindow(true, true), fixedWindow(true, true)).isEmpty());
    }
    private PlayerHolyOrderContextRead query() throws Exception { return new PlayerHolyOrderContextRead(unusedReads(), sources(), (sources, request) -> {}); }
    private static PlanningReadPort unusedReads() {
        return new PlanningReadPort() {
            @Override public <T> PlanningReadResult<T> read(ReadContract<T> contract, PlanningReadRequest request) { throw new AssertionError("this source test never dispatches a native query"); }
        };
    }
    private PlayerHolyOrderContextRead.Sources sources() throws Exception {
        return new PlayerHolyOrderContextRead.Sources(input("python_holy_context"), input("python_holy_cost"), input("python_holy_reinforcement"),
                input("native_holy_mailbox"), input("native_holy_wire"), input("native_holy_context"), input("native_holy_reinforcement"), input("native_holy_build4"));
    }
    private ObjectNode map() throws Exception {
        if (sourceMap == null) {
            byte[] body = Files.readAllBytes(Path.of(required("xar.armyWarWindow.sourceMap")));
            assertEquals(required("xar.armyWarWindow.sourceMapSha256"), sha(body), "actual Army war/window source map drift");
            sourceMap = object(StrictJson.parse(body, StrictJson.EXPLICIT_MAX_BYTES));
            assertEquals("xar.java-phase1.army-war-window-source-map/v1", sourceMap.path("schema").textValue());
            FixtureOwner.from(sourceMap.get("owner"));
        }
        return sourceMap;
    }
    private ExactRef input(String key) throws Exception { return ExactRef.fromJson(map().path("input_refs").get(key)); }
    private List<Sample> samples() throws Exception {
        byte[] bytes = Files.readAllBytes(Path.of(required("xar.holyOrder.fixtureCorpus")));
        assertEquals(required("xar.holyOrder.fixtureCorpusSha256"), sha(bytes), "actual whole native fixture corpus drift");
        ObjectNode corpus = object(StrictJson.parse(bytes, StrictJson.EXPLICIT_MAX_BYTES));
        StrictJson.object(corpus, Set.of("schema", "machine_id", "source_map_ref", "native_environment_ref", "native_source_snapshot_ref", "runs"));
        assertEquals("xar.ck3.holy-order-native-fixture-corpus/v1", corpus.path("schema").textValue());
        ExactRef mapRef = ExactRef.fromJson(corpus.get("source_map_ref"));
        assertEquals(required("xar.armyWarWindow.sourceMapSha256"), mapRef.sha256()); pinned(mapRef);
        pinned(ExactRef.fromJson(corpus.get("native_environment_ref"))); pinned(ExactRef.fromJson(corpus.get("native_source_snapshot_ref")));
        assertTrue(corpus.path("machine_id").isTextual() && !corpus.path("machine_id").textValue().isBlank());
        assertTrue(corpus.path("runs").isArray());
        var seen = new java.util.HashSet<String>(); List<Sample> out = new ArrayList<>();
        for (JsonNode value : corpus.get("runs")) {
            ObjectNode run = StrictJson.object(value, Set.of("target", "source_ref", "executable_ref", "receipt_ref", "output_ref"));
            String target = StrictJson.text(run.get("target")); assertTrue(TARGETS.contains(target) && seen.add(target));
            ExactRef source = ExactRef.fromJson(run.get("source_ref"));
            assertEquals(ExactRef.fromJson(map().path("fixture_sources").get(target)), source); pinned(source);
            ExactRef exe = ExactRef.fromJson(run.get("executable_ref")); pinned(exe);
            ObjectNode process = object(StrictJson.parse(pinned(ExactRef.fromJson(run.get("receipt_ref"))), StrictJson.EXPLICIT_MAX_BYTES));
            ownership(process, corpus.get("machine_id"));
            assertEquals(corpus.get("machine_id"), process.get("machine_id")); assertEquals(target, process.path("target").textValue());
            assertTrue(process.path("exit_code").isIntegralNumber()); assertEquals(BigInteger.ZERO, process.get("exit_code").bigIntegerValue());
            assertTrue(process.path("timed_out").isBoolean()); assertFalse(process.get("timed_out").booleanValue());
            assertTrue(process.path("actual_game_actions").isIntegralNumber()); assertEquals(BigInteger.ZERO, process.get("actual_game_actions").bigIntegerValue());
            assertEquals(exe, ExactRef.fromJson(process.get("executable_ref")));
            byte[] output = pinned(ExactRef.fromJson(run.get("output_ref")));
            List<byte[]> originalPackets = extractPackets(output); assertFalse(originalPackets.isEmpty(), "actual provider output has no complete packets: " + target);
            for (byte[] packet : originalPackets) out.add(new Sample(target, packet));
        }
        assertEquals(TARGETS, seen, "one required current subobserver family was omitted");
        return List.copyOf(out);
    }
    private FixtureOwnership ownership(ObjectNode process, JsonNode machine) throws Exception {
        assertEquals("xar.native-fixture-owned-process/v1", process.path("schema").textValue());
        ObjectNode terminal = object(StrictJson.parse(pinned(ExactRef.fromJson(process.get("original_terminal_ref"))), StrictJson.EXPLICIT_MAX_BYTES));
        ObjectNode request = object(StrictJson.parse(pinned(ExactRef.fromJson(terminal.get("request_ref"))), StrictJson.EXPLICIT_MAX_BYTES));
        assertEquals(machine, terminal.get("machine_id"));
        FixtureOwner actual = requireSameFixtureOwner(FixtureOwner.from(map().get("owner")), terminal, request);
        return new FixtureOwnership(actual, terminal, request);
    }
    private static FixtureOwner requireSameFixtureOwner(FixtureOwner selected, ObjectNode terminal, ObjectNode request) {
        assertEquals("xar.shared-owned-command-terminal/v2", terminal.path("schema").textValue());
        assertEquals("xar.shared-owned-command-spec/v2", request.path("schema").textValue());
        assertEquals(terminal.get("machine_id"), request.get("machine_id"));
        FixtureOwner actual = FixtureOwner.from(terminal.get("owner"));
        assertEquals(actual, FixtureOwner.from(request.get("owner")), "actual native terminal owner differs from its pinned original request");
        assertEquals(selected, actual, "source map must name the actual executor of every original native run");
        return actual;
    }
    private static List<byte[]> extractPackets(byte[] output) throws Exception {
        // Exact raw object slices preserve original serializer tokens/escapes, not a re-encoded manifest DTO.
        List<byte[]> packets = new ArrayList<>();
        try (var parser = new JsonFactory().createParser(output)) {
            assertEquals(JsonToken.START_OBJECT, parser.nextToken());
            while (parser.nextToken() != JsonToken.END_OBJECT) {
                String field = parser.currentName(); JsonToken token = parser.nextToken();
                if (!field.equals("samples")) { parser.skipChildren(); continue; }
                assertEquals(JsonToken.START_ARRAY, token);
                while (parser.nextToken() != JsonToken.END_ARRAY) {
                    assertEquals(JsonToken.START_OBJECT, parser.currentToken()); int begin = Math.toIntExact(parser.currentTokenLocation().getByteOffset());
                    parser.skipChildren(); int end = Math.toIntExact(parser.currentLocation().getByteOffset());
                    packets.add(Arrays.copyOfRange(output, begin, end));
                }
            }
            assertNull(parser.nextToken(), "trailing provider output");
        }
        return List.copyOf(packets);
    }
    private ObjectNode firstMilitaryFrame() throws Exception {
        for (Sample sample : samples()) {
            ObjectNode frame = object(StrictJson.parse(sample.originalFrame(), StrictJson.EXPLICIT_MAX_BYTES));
            if (component(frame).path("available").asBoolean() && component(frame).path("rows").isArray())
                for (JsonNode row : component(frame).get("rows"))
                    if (row.path("is_military").asBoolean() && row.path("military_terms").path("available").asBoolean()) return frame;
        }
        throw new IllegalStateException("NOT EXECUTED: actual corpus has no complete military context");
    }
    private PlanningReadReceipt receipt(byte[] originalPayload, ObjectNode reference) throws Exception {
        return receipt(originalPayload, reference, PlayerHolyOrderContextRead.CONTRACT_ID);
    }
    private PlanningReadReceipt receipt(byte[] originalPayload, ObjectNode reference, String actualContractId) throws Exception {
        ObjectNode result = object(reference.get("result")), context = object(result.get("player_holy_order_context"));
        BigInteger actor = context.get("played_character_id").bigIntegerValue(), date = result.get("date_raw").bigIntegerValue(), revision = result.get("snapshot_revision").bigIntegerValue();
        Instant now = Instant.now(); G2Source source = new G2Source("software-fixture-machine", now.toString(), "actual-cpp-holy-order-fixture", input("python_holy_context"));
        var frame = new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(actor, revision, date), "holy-order-software-fixture", revision.add(BigInteger.ONE), "fixture-episode");
        var identity = new ProposalLifecycle.ObservationIdentity(source.machineId(), new GameGeneration(42, new PythonOnlyUInt64(BigInteger.ONE)), frame, 1);
        var request = new PlanningReadRequest(identity, source, "fixture-session", PlayerHolyOrderContextRead.OPERATION, new OpportunityJson.Obj(Map.of()), now.plusSeconds(60));
        ObjectNode hello = StrictJson.object().put("type", "hello").put("protocol_version", 1).put("pid", 42).put("connection_generation", 11)
                .put("bridge_version", "software-fixture").put("expected_ck3_sha256", result.get("executable_sha256").textValue()).put("game_adapter_id", "native-fixture")
                .put("game_adapter_status", "ready").put("ck3_build_match", true); hello.putArray("capabilities");
        ExactRef helloRef = store("hello", NativeWire.packet(StrictJson.canonical(hello)));
        byte[] packet = NativeWire.packet(originalPayload); ExactRef original = store("query", packet);
        var binding = new GuardEvidence(identity, source, request.sessionId(), BigInteger.valueOf(11), request.operation(), original, helloRef, "software-fixture-only", now, now.plusSeconds(60));
        var guard = new PlanningReadGuard(binding, true, true, true, "a".repeat(64));
        ObjectNode parsed = object(StrictJson.parse(originalPayload, StrictJson.EXPLICIT_MAX_BYTES));
        var ack = new NativeActionPort.AckReceived(reference.get("request_id").textValue(), true,
                Optional.of(new RawJson(StrictJson.canonical(parsed.get("result"), StrictJson.EXPLICIT_MAX_BYTES))), new RawJson(originalPayload), packet);
        return new PlanningReadReceipt(request, actualContractId, reference.get("request_id").textValue(), guard, guard, ack);
    }
    private ExactRef store(String prefix, byte[] bytes) throws Exception { Path p = temporary.resolve(prefix + (++counter) + ".packet"); Files.write(p, bytes); return new ExactRef(p.toString(), bytes.length, sha(bytes)); }
    private static byte[] pinned(ExactRef ref) throws Exception { byte[] b = Files.readAllBytes(Path.of(ref.path())); assertEquals(ref.bytes(), b.length); assertEquals(ref.sha256(), sha(b)); return b; }
    private static String sha(byte[] b) throws Exception { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(b)); }
    private static String required(String key) { String value = System.getProperty(key); if (value == null || value.isBlank()) throw new IllegalStateException("NOT EXECUTED: actual original HolyOrder input missing: " + key); return value; }
    private static ObjectNode object(JsonNode n) { assertNotNull(n); assertTrue(n.isObject()); return (ObjectNode) n; }
    private static ObjectNode component(ObjectNode frame) { return object(frame.get("result").get("player_holy_order_context")); }
    private static ObjectNode firstMilitary(ObjectNode frame) { for (JsonNode row : component(frame).get("rows")) if (row.path("is_military").asBoolean() && row.path("military_terms").path("available").asBoolean()) return object(row); throw new IllegalArgumentException("complete military row required"); }
    private static ObjectNode terms(ObjectNode frame) { return object(firstMilitary(frame).get("military_terms")); }
    private static void remapToFour(ObjectNode frame) {
        ObjectNode result = object(frame.get("result")), context = component(frame);
        result.put("game_version", PlayerReligionContext.Build.CROZIER4.version()).put("executable_sha256", PlayerReligionContext.Build.CROZIER4.sha256())
                .put("backend_id", "ck3-1.20.0.4-native-player-holy-order-context-v1");
        context.put("game_version", PlayerReligionContext.Build.CROZIER4.version()).put("executable_sha256", PlayerReligionContext.Build.CROZIER4.sha256())
                .put("schema", "ck3_12004_player_holy_order_context_v1");
    }
}
