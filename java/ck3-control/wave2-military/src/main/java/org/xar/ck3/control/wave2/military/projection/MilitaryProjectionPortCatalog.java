package org.xar.ck3.control.wave2.military.projection;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.ArrayList;
import java.util.EnumSet;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionOperation;
import org.xar.ck3.control.contracts.projection.ProjectionPort;
import org.xar.ck3.control.contracts.projection.ProjectionPortCatalog;
import org.xar.ck3.control.contracts.projection.RegisteredProjection;
import org.xar.ck3.control.wave2.military.actualcontact.ContactProjectionPorts;
import org.xar.ck3.control.wave2.military.warresults.WarWindowProjectionPorts;
import org.xar.ck3.control.wave2.military.monthlyloss.SupplyProjectionPorts;
import org.xar.ck3.control.wave2.military.refuge.ConsumerTransferProjectionPort;
import org.xar.ck3.control.wave2.military.coalition.CoalitionRiskJsonAdapter;
import org.xar.ck3.control.wave2.military.coalition.PrewarCoalition;
import org.xar.ck3.control.wave2.military.declarationcontract.DeclarationContract;
import org.xar.ck3.control.wave2.military.holycost.HolyCostJsonAdapter;
import org.xar.ck3.control.wave2.military.holycost.HolyCostObservation;
import org.xar.ck3.control.wave2.military.prewaradmission.OrdinaryPrewarAdmission;
import org.xar.ck3.control.wave2.military.prewaradmission.PrewarAdmissionCodec;
import org.xar.ck3.control.wave2.military.prewaradmission.PrewarAdmissionInput;

/** Existing complete pure policies inside the one host. No query, Game or writer capability enters these ports. */
public final class MilitaryProjectionPortCatalog implements ProjectionPortCatalog {
    public MilitaryProjectionPortCatalog() { }

    @Override public List<RegisteredProjection> registrations() {
        var result = new ArrayList<>(List.of(
                RegisteredProjection.of(new CataloguePort()), RegisteredProjection.of(new HolySelectedPort()),
                RegisteredProjection.of(new HolyContextPort()), RegisteredProjection.of(new CoalitionNormalizePort()),
                RegisteredProjection.of(new CoalitionRiskPort()), RegisteredProjection.of(new PrewarPort())));
        result.addAll(MovementProjectionPorts.registrations());
        result.addAll(ArmyProjectionPorts.registrations());
        result.addAll(ContactProjectionPorts.registrations(new ContactProjectionPorts.Operations(
                ProjectionOperation.MILITARY_ARMY_INVENTORY, ProjectionOperation.MILITARY_ROUTE_WINDOW,
                ProjectionOperation.MILITARY_ROUTE_STEP, ProjectionOperation.MILITARY_ACTUAL_SCOPE,
                ProjectionOperation.MILITARY_ACTUAL_QUERY)));
        result.addAll(StockProjectionPorts.registrations(new StockProjectionPorts.Operations(
                ProjectionOperation.MILITARY_UPDATER_WRITES, ProjectionOperation.MILITARY_STOCK_SUPPLY,
                ProjectionOperation.MILITARY_NEXT_FLEET_RATE, ProjectionOperation.MILITARY_CALLBACK_SUPPLY_RISK,
                ProjectionOperation.MILITARY_CALLBACK_SOLDIER_EFFECTS)));
        result.add(RegisteredProjection.of(new ConsumerTransferProjectionPort()));
        result.addAll(CombatCommanderProjectionPorts.registrations(new CombatCommanderProjectionPorts.Operations(
                ProjectionOperation.MILITARY_COMBAT_ROLES_NORMALIZE, ProjectionOperation.MILITARY_COMBAT_ROLES_PROJECT,
                ProjectionOperation.MILITARY_COMMANDER_QUALITY_PROPOSE, ProjectionOperation.MILITARY_COMMANDER_QUALITY_ADMIT_OBSERVED,
                ProjectionOperation.MILITARY_COMMANDER_QUALITY_PLAN, ProjectionOperation.MILITARY_COMMANDER_QUALITY_PLAN_NEXT)));
        result.addAll(WarWindowProjectionPorts.registrations(new WarWindowProjectionPorts.Operations(
                ProjectionOperation.MILITARY_WAR_RESULTS_PLAN, ProjectionOperation.MILITARY_WAR_OVERVIEW_PLAN,
                ProjectionOperation.MILITARY_WAR_RESULTS_PRESENCE, ProjectionOperation.MILITARY_WAR_OVERVIEW_PRESENCE,
                ProjectionOperation.MILITARY_WAR_RESULTS_QUERY_FRAME, ProjectionOperation.MILITARY_WAR_OVERVIEW_QUERY_FRAME,
                ProjectionOperation.MILITARY_WAR_RESULTS_NORMALIZE, ProjectionOperation.MILITARY_WAR_RESULTS_SOURCE_OWNER,
                ProjectionOperation.MILITARY_DEJURE_BASELINE_NORMALIZE, ProjectionOperation.MILITARY_WAR_EXIT_TERMS_NORMALIZE)));
        result.addAll(SupplyProjectionPorts.registrations(ProjectionOperation.MILITARY_SUPPLY_CONSUMER));
        result.addAll(HolyConsumerPorts.registrations(new HolyConsumerPorts.Operations(
                ProjectionOperation.MILITARY_HOLY_REINFORCEMENT, ProjectionOperation.MILITARY_HOLY_HIRE)));
        var operations = EnumSet.noneOf(ProjectionOperation.class);
        for (RegisteredProjection registration : result) {
            if (!operations.add(registration.operation())) {
                throw new IllegalStateException("duplicate military operation: " + registration.operation());
            }
        }
        return List.copyOf(result);
    }

    /** Narrow detached legacy JSON boundary; the complete domain validator runs in project, before domain construction. */
    private static final class RawValue {
        private final JsonNode value;
        RawValue(JsonNode value) {
            StrictJson.require(value != null, "required original JSON field missing");
            this.value = value.deepCopy();
        }
        JsonNode copy() { return value.deepCopy(); }
    }

    private record CatalogueInput(RawValue rows) { }
    private record HolySelectedInput(RawValue snapshot, String declarationId) { }
    private record HolyContextInput(RawValue context, RawValue snapshot, String declarationId, RawValue selected) { }
    private record CoalitionInput(RawValue domain, RawValue snapshot, RawValue declaration, RawValue receipt,
                                  String requestId, BigInteger expectedEpoch, RawValue policy) { }

    private static final class CataloguePort implements ProjectionPort<CatalogueInput, List<DeclarationContract.Choice>> {
        @Override public ProjectionOperation operation() { return ProjectionOperation.MILITARY_DECLARATION_CATALOGUE; }
        @Override public CatalogueInput decode(byte[] raw) {
            ObjectNode row = object(raw, Set.of("value"));
            return new CatalogueInput(new RawValue(row.get("value")));
        }
        @Override public List<DeclarationContract.Choice> project(CatalogueInput input) {
            return DeclarationContract.normalize(input.rows().copy());
        }
        @Override public byte[] encode(List<DeclarationContract.Choice> result) {
            return StrictJson.canonical(DeclarationContract.encode(result));
        }
    }

    private static final class HolySelectedPort implements ProjectionPort<HolySelectedInput, DeclarationContract.Choice> {
        @Override public ProjectionOperation operation() { return ProjectionOperation.MILITARY_HOLY_COST_SELECTED; }
        @Override public HolySelectedInput decode(byte[] raw) {
            ObjectNode row = object(raw, Set.of("snapshot", "declaration_id"));
            return new HolySelectedInput(new RawValue(row.get("snapshot")), StrictJson.text(row.get("declaration_id")));
        }
        @Override public DeclarationContract.Choice project(HolySelectedInput input) {
            return HolyCostJsonAdapter.selectedDeclaration(input.snapshot().copy(), input.declarationId());
        }
        @Override public byte[] encode(DeclarationContract.Choice result) {
            return StrictJson.canonical(HolyCostJsonAdapter.selectedJson(result));
        }
    }

    private static final class HolyContextPort implements ProjectionPort<HolyContextInput, HolyCostObservation> {
        @Override public ProjectionOperation operation() { return ProjectionOperation.MILITARY_HOLY_COST_NORMALIZE; }
        @Override public HolyContextInput decode(byte[] raw) {
            ObjectNode row = object(raw, Set.of("value", "snapshot", "declaration_id", "selected_declaration"));
            return new HolyContextInput(new RawValue(row.get("value")), new RawValue(row.get("snapshot")),
                    StrictJson.text(row.get("declaration_id")), new RawValue(row.get("selected_declaration")));
        }
        @Override public HolyCostObservation project(HolyContextInput input) {
            return HolyCostJsonAdapter.normalize(input.context().copy(), input.snapshot().copy(),
                    input.declarationId(), input.selected().copy());
        }
        @Override public byte[] encode(HolyCostObservation result) { return StrictJson.canonical(HolyCostJsonAdapter.encode(result)); }
    }

    private static final class CoalitionNormalizePort implements ProjectionPort<CoalitionReceiptProjectionBranch.Request, CoalitionReceiptProjectionBranch.Result> {
        @Override public ProjectionOperation operation() { return ProjectionOperation.MILITARY_COALITION_NORMALIZE; }
        @Override public CoalitionReceiptProjectionBranch.Request decode(byte[] raw) { return CoalitionReceiptProjectionBranch.decode(raw); }
        @Override public CoalitionReceiptProjectionBranch.Result project(CoalitionReceiptProjectionBranch.Request input) {
            return CoalitionReceiptProjectionBranch.project(input);
        }
        @Override public byte[] encode(CoalitionReceiptProjectionBranch.Result result) { return CoalitionReceiptProjectionBranch.encode(result); }
    }

    private static final class CoalitionRiskPort implements ProjectionPort<CoalitionInput, CoalitionRiskJsonAdapter.Assessment> {
        @Override public ProjectionOperation operation() { return ProjectionOperation.MILITARY_COALITION_RISK; }
        @Override public CoalitionInput decode(byte[] raw) { return coalitionInput(raw, true); }
        @Override public CoalitionRiskJsonAdapter.Assessment project(CoalitionInput input) {
            return CoalitionRiskJsonAdapter.assess(input.domain().copy(), input.snapshot().copy(), input.declaration().copy(),
                    input.receipt().copy(), input.requestId(), input.expectedEpoch(), input.policy().copy());
        }
        @Override public byte[] encode(CoalitionRiskJsonAdapter.Assessment result) {
            return StrictJson.canonical(result.riskJson());
        }
    }

    private static final class PrewarPort implements ProjectionPort<PrewarAdmissionInput, OrdinaryPrewarAdmission.Result> {
        @Override public ProjectionOperation operation() { return ProjectionOperation.MILITARY_PREWAR_ADMISSION; }
        @Override public PrewarAdmissionInput decode(byte[] raw) {
            ObjectNode row = object(raw, Set.of("snapshot", "declaration"));
            return PrewarAdmissionCodec.decodeLegacyContainer(row.get("snapshot"), row.get("declaration"));
        }
        @Override public OrdinaryPrewarAdmission.Result project(PrewarAdmissionInput input) {
            return OrdinaryPrewarAdmission.assess(input);
        }
        @Override public byte[] encode(OrdinaryPrewarAdmission.Result result) { return OrdinaryPrewarAdmission.encodeResult(result); }
    }

    private static CoalitionInput coalitionInput(byte[] raw, boolean risk) {
        Set<String> fields = risk
                ? Set.of("value", "snapshot", "expected_declaration", "expected_request_binding", "expected_request_id", "expected_capture_epoch", "policy")
                : Set.of("value", "snapshot", "expected_declaration", "expected_request_binding", "expected_request_id", "expected_capture_epoch");
        ObjectNode row = object(raw, fields);
        JsonNode epoch = row.get("expected_capture_epoch");
        BigInteger expectedEpoch = epoch.isNull() ? null : StrictJson.integer(epoch, BigInteger.ONE, StrictJson.UINT64_MAX);
        return new CoalitionInput(new RawValue(row.get("value")), new RawValue(row.get("snapshot")),
                new RawValue(row.get("expected_declaration")), new RawValue(row.get("expected_request_binding")),
                StrictJson.text(row.get("expected_request_id")), expectedEpoch,
                new RawValue(risk ? row.get("policy") : StrictJson.object().nullNode()));
    }

    private static ObjectNode object(byte[] raw, Set<String> fields) { return StrictJson.object(StrictJson.parse(raw), fields); }
}

