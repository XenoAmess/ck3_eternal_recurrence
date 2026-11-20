package org.xar.ck3.control.nativebridge.capabilities.registry;

import java.math.BigInteger;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactCk3Build;

/** Redacted current-root index DATA only: no widget addresses, complete tree or action authority. */
public sealed interface GuiRootIndexFrame permits GuiRootIndexFrame.Partial, GuiRootIndexFrame.Unavailable {
    String STEP = "query-scripted-gui-root-index-v1";
    String SCHEMA = "ck3.scripted_gui_root_index.v1";
    String REQUEST_SCHEMA = "ck3.scripted_gui_root_index_request.v1";
    String BACKEND = "ck3-1.21.0.3-native-headless-main-thread";
    ExactCk3Build BUILD = ExactCk3Build.CK3_121003_STEAM_26785313;
    Set<String> FIELDS = Set.of("step", "schema", "game_version", "executable_sha256", "adapter_id", "backend",
            "status", "root_index_available", "application_main_observed", "source_abi_pins_verified", "addresses_redacted",
            "complete_snapshot", "complete_gui_tree", "control_actions_available", "core_frame", "root_index", "owner_witness", "unavailable_reason");
    CoreFrame coreFrame();
    default ExactCk3Build build() { return BUILD; }

    record IndexStats(int entryCount, int materializedRootCount, int emptyEntryCount) {
        public IndexStats {
            RegistryJson.require(entryCount >= 0 && entryCount <= 4096 && materializedRootCount >= 0
                    && materializedRootCount <= 4096 && emptyEntryCount >= 0 && emptyEntryCount <= 4096
                    && materializedRootCount + emptyEntryCount == entryCount, "bounded root-index counts must partition entries");
        }
    }
    record OwnerWitness(BigInteger connectionGeneration, BigInteger ticketSequence, BigInteger pumpEpoch, long threadId) {
        public OwnerWitness {
            for (BigInteger value : java.util.List.of(connectionGeneration, ticketSequence, pumpEpoch))
                RegistryJson.require(value.signum() > 0 && value.compareTo(RegistryJson.U64) <= 0, "positive uint64 owner witness required");
            RegistryJson.require(threadId >= 1 && threadId <= 0xffff_ffffL, "positive uint32 owner thread required");
        }
    }
    record Partial(CoreFrame.Partial coreFrame, IndexStats rootIndex, OwnerWitness ownerWitness) implements GuiRootIndexFrame {
        public Partial { requireExpectedCore(coreFrame); Objects.requireNonNull(rootIndex); Objects.requireNonNull(ownerWitness); }
    }
    record Unavailable(CoreFrame.Unavailable coreFrame, String reason) implements GuiRootIndexFrame {
        public Unavailable {
            Objects.requireNonNull(coreFrame);
            RegistryJson.require(coreFrame.build() == BUILD && reason != null && !reason.isEmpty()
                    && reason.equals(coreFrame.reason()), "atomic unavailable root-index/core reasons required");
        }
    }
    static void requireExpectedCore(CoreFrame.Partial frame) {
        Objects.requireNonNull(frame); var p = frame.prefix();
        RegistryJson.require(frame.build() == BUILD && p.paused() && p.mapReady() && p.localPlayerId() >= 0
                && p.hasPlayedCharacter() && p.playedCharacterId() != -1 && p.playedCharacterAlive(),
                "current267 paused living Core required for root-index query");
    }
    static GuiRootIndexFrame decode(RawJson original) {
        var row = RegistryJson.object(original); RegistryJson.keys(row, FIELDS);
        RegistryJson.require(STEP.equals(RegistryJson.text(row.get("step"))) && SCHEMA.equals(RegistryJson.text(row.get("schema")))
                && BUILD.matches(RegistryJson.text(row.get("game_version")), RegistryJson.text(row.get("executable_sha256")))
                && BUILD.coreFrameAdapterId().equals(RegistryJson.text(row.get("adapter_id")))
                && BACKEND.equals(RegistryJson.text(row.get("backend"))), "root-index exact source tuple mismatch");
        RegistryJson.require(RegistryJson.bool(row.get("addresses_redacted")) && !RegistryJson.bool(row.get("complete_snapshot"))
                && !RegistryJson.bool(row.get("complete_gui_tree")) && !RegistryJson.bool(row.get("control_actions_available")),
                "root-index DATA cannot expand to addresses, full snapshots, GUI trees or controls");
        CoreFrame core = CoreFrame.decodeObject(RegistryJson.object(row.get("core_frame")));
        RegistryJson.require(core.build() == BUILD, "nested Core source differs from root-index source");
        boolean available = RegistryJson.bool(row.get("root_index_available"));
        boolean main = RegistryJson.bool(row.get("application_main_observed"));
        boolean pins = RegistryJson.bool(row.get("source_abi_pins_verified"));
        if (!available) {
            RegistryJson.require("unavailable".equals(RegistryJson.text(row.get("status"))) && !pins
                    && core instanceof CoreFrame.Unavailable && row.get("root_index").isNull() && row.get("owner_witness").isNull(),
                    "unavailable index must retain null root/witness and unavailable Core");
            var absent = (CoreFrame.Unavailable) core;
            RegistryJson.require(main == absent.applicationMainObserved(), "unavailable main-owner flag differs from nested Core");
            return new Unavailable(absent, RegistryJson.text(row.get("unavailable_reason")));
        }
        RegistryJson.require("partial".equals(RegistryJson.text(row.get("status"))) && main && pins
                && core instanceof CoreFrame.Partial && row.get("unavailable_reason").isNull(), "root-index partial evidence missing");
        var root = RegistryJson.object(row.get("root_index"));
        RegistryJson.keys(root, Set.of("entry_count", "materialized_root_count", "empty_entry_count", "all_entries_current_context"));
        RegistryJson.require(RegistryJson.bool(root.get("all_entries_current_context")), "foreign-context entries cannot form a current index");
        var owner = RegistryJson.object(row.get("owner_witness"));
        RegistryJson.keys(owner, Set.of("connection_generation", "ticket_sequence", "pump_epoch", "thread_id"));
        return new Partial((CoreFrame.Partial) core,
                new IndexStats(RegistryJson.int32(root.get("entry_count")), RegistryJson.int32(root.get("materialized_root_count")), RegistryJson.int32(root.get("empty_entry_count"))),
                new OwnerWitness(witness(owner.get("connection_generation")), witness(owner.get("ticket_sequence")), witness(owner.get("pump_epoch")),
                        RegistryJson.integer(owner.get("thread_id"), BigInteger.ONE, BigInteger.valueOf(0xffff_ffffL)).longValueExact()));
    }
    private static BigInteger witness(com.fasterxml.jackson.databind.JsonNode value) {
        String token = RegistryJson.text(value);
        RegistryJson.require(token.matches("[1-9][0-9]{0,19}"), "canonical positive uint64 witness string required");
        BigInteger result = new BigInteger(token);
        RegistryJson.require(result.compareTo(RegistryJson.U64) <= 0, "owner witness exceeds uint64"); return result;
    }
}
