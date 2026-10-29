package org.xar.ck3.control.continuity;

import java.util.HashSet;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;

/** Pure event-chain projection from already captured small documents.
 * File identities, source indexes and writer-lock recheck stay with the original reader/writer.
 */
public final class ContinuityHistory {
    public static final int MAX_CONTINUITY_EVENTS = 256;
    private ContinuityHistory() { }
    public record Preview(ContinuityState head, List<ContinuityEvent> events, boolean snapshotNeedsRecovery) {
        public Preview { java.util.Objects.requireNonNull(head); events = List.copyOf(events); }
        public String headDigest() { return ContinuityJson.digest(head.toJson()); }
        public int ledgerWrites() { return 0; }
    }
    public static Preview preview(ContinuityState anchor, ContinuityState snapshot, List<byte[]> eventDocuments) {
        java.util.Objects.requireNonNull(anchor); java.util.Objects.requireNonNull(snapshot);
        eventDocuments = List.copyOf(eventDocuments);
        // Existing range(256) requires the absent next-event observation before exhausting the loop.
        StrictJson.require(eventDocuments.size() < MAX_CONTINUITY_EVENTS, "continuity event chain exceeds finite bound");
        StrictJson.require(snapshot.machineId().equals(anchor.machineId())
                && snapshot.sequence() >= anchor.sequence(), "canonical snapshot cannot precede anchor");
        boolean matched = snapshot.sequence() == anchor.sequence();
        if (matched) { StrictJson.require(ContinuityJson.same(snapshot.toJson(), anchor.toJson()), "same sequence snapshot differs"); }
        ContinuityState head = anchor;
        List<ContinuityEvent> events = new java.util.ArrayList<>(); Set<String> sources = new HashSet<>();
        java.util.Map<Long,byte[]> originals=new java.util.HashMap<>();
        for (byte[] document : eventDocuments) {
            ContinuityEvent event = ContinuityEvent.fromJson(
                    ContinuityJson.parseObject(document, ContinuityJson.LEDGER_MAX_BYTES), head);
            StrictJson.require(sources.add(event.sourceKey()), "committed evidence ID reused");
            if(EpisodeWindow.BEGIN_KIND.equals(event.kind())){
                EpisodeWindow.Begin begin=EpisodeWindow.begin(new org.xar.ck3.control.continuity.writer.WriterContracts.Request(event.kind(),event.details(),List.of()));
                requireAncestor(events,originals,begin.lifecycleSequence(),begin.lifecycleEventIdentity(),begin.lifecycleEventRef());
            }else if(EpisodeWindow.BASELINE_KIND.equals(event.kind())){
                EpisodeWindow.Baseline baseline=EpisodeWindow.baseline(new org.xar.ck3.control.continuity.writer.WriterContracts.Request(event.kind(),event.details(),List.of()));
                EpisodeWindow.CommittedBegin begin=baseline.begin();
                ContinuityEvent actualBegin=requireAncestor(events,originals,begin.sequence(),begin.eventIdentity(),begin.eventRef());
                StrictJson.require(actualBegin.kind().equals(EpisodeWindow.BEGIN_KIND)
                        &&ContinuityJson.digest(actualBegin.after().toJson()).equals(begin.headDigest())
                        &&ContinuityJson.same(ContinuityJson.parseObject(actualBegin.details(),ContinuityJson.DOCUMENT_MAX_BYTES),begin.begin().request().detailsObject()),
                        "BASELINE must retain its exact actual earlier BEGIN state/details");
            }
            originals.put(event.sequence(),document.clone());
            events.add(event); head = event.after();
            if (head.sequence() == snapshot.sequence()) {
                StrictJson.require(ContinuityJson.same(snapshot.toJson(), head.toJson()), "snapshot differs from its committed event");
                matched = true;
            }
        }
        StrictJson.require(matched, "snapshot has no exact committed lineage from anchor");
        return new Preview(head, events, head.sequence() != snapshot.sequence());
    }
    private static ContinuityEvent requireAncestor(List<ContinuityEvent> events,java.util.Map<Long,byte[]> originals,long sequence,String identity,
            org.xar.ck3.control.contracts.ExactRef reference){
        ContinuityEvent event=events.stream().filter(row->row.sequence()==sequence).findFirst()
                .orElseThrow(()->new org.xar.ck3.control.contracts.ContractViolationException("actual original episode ancestor event must remain in the finite chain"));
        byte[] raw=originals.get(sequence);String digest;
        try{digest=java.util.HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(raw));}
        catch(java.security.NoSuchAlgorithmException impossible){throw new IllegalStateException(impossible);}
        StrictJson.require(event.identity().equals(identity)&&reference.bytes()==raw.length&&reference.sha256().equals(digest),
                "episode ancestor event reference differs from its exact actual original bytes");return event;
    }
}
