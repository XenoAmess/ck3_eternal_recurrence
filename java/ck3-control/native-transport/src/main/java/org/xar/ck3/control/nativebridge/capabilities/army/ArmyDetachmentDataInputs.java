package org.xar.ck3.control.nativebridge.capabilities.army;

import java.util.List;

/** Complete observed DATA seed. Boxed nulls are explicit native unknowns, not missing keys or zero operands. */
public record ArmyDetachmentDataInputs(State state,boolean selectionReady,boolean rosterReady,Long currentDateStorageRaw64,
        String primaryReceiverIdentity,String canonicalPendingVtableIdentity,String readyPendingCallbackIdentity,
        List<Candidate> candidateOccurrences,List<Incoming> incoming) {
    public ArmyDetachmentDataInputs { candidateOccurrences=List.copyOf(candidateOccurrences);incoming=List.copyOf(incoming); }
    public enum Status { AVAILABLE,PARTIAL,UNAVAILABLE }
    public enum Selection { REGISTRY_FULL_ID,NATIVE_FALLBACK }
    public record State(Status status,boolean ready,String unavailableReason) { }
    /** The DATA source contract observes these fields without granting a stronger resolution readiness rule. */
    public record Resolution(State state,Long requestedFullId,Boolean registryLoaded,Long registryCapacity,Long registryIndex,
            String indexedIdentity,Long indexedFullId,Selection selection,Boolean usedFallback,String objectIdentity,Long selectedFullId) { }
    public record Candidate(State state,int nativeIndex,Long rawFullId,Resolution resolution,Long magic14,Boolean incomingValid,Integer incomingIndex) { }
    public record Incoming(State state,int nativeIndex,String arrgIdentity,Long arrgFullId,Long armyFullId140,Long unitFullId124,
            Resolution armyResolution,Resolution unitResolution,String passedProvinceIdentity,String dataPointerIdentity,Integer dataCount,
            String capturedCursorIdentity,String capturedEndIdentity,boolean dataReady,Long characterFullId148,Resolution characterResolution,
            Boolean characterPointer1b8Present,String characterPointer1b8Identity,List<DataOccurrence> dataOccurrences,List<PhysicalChunk> physicalChunks,
            List<Association> associationInputs,List<Owner> ownerInputs,List<DateInput> dateInputs,Pending pending) {
        public Incoming { dataOccurrences=List.copyOf(dataOccurrences);physicalChunks=List.copyOf(physicalChunks);
            associationInputs=List.copyOf(associationInputs);ownerInputs=List.copyOf(ownerInputs);dateInputs=List.copyOf(dateInputs); }
    }
    public record DataOccurrence(State state,int nativeIndex,String recordIdentity,Long rawRegiFullId,Integer dataOrdinal,
            String heldFallbackRegiIdentity,Resolution resolution,Long magic14,Boolean identityValid,Boolean physicalChunkPresent,Integer physicalChunkIndex) { }
    public record PhysicalChunk(State state,int nativeIndex,String chunkIdentity,Integer maximum00,Integer current04,Long owner08,
            Integer ordinal0c,Long association10,Integer flag14,Long date1cRaw64) { }
    public record Association(State state,Long requestedFullId,Resolution arrgResolution,Long armyFullId140,Resolution armyResolution,
            Long unitFullId124,Resolution unitResolution,Long characterFullId174,Resolution characterResolution,String contextPointerIdentity,Long contextCount0c) { }
    public record Owner(State state,Long requestedFullId,Resolution resolution,Integer state138,String definitionIdentity,Long definitionMagic38,
            String originIdentity,Long originMagic85c) { }
    public record DateInput(State state,Long associationFullId,Long ownerFullId,String unitIdentity,String sourceOriginIdentity,
            Long sourceOriginMagic85c,String capitalOriginIdentity,Long capitalOriginMagic85c,Long outputDateRaw64,String basis) { }
    public record Pending(State state,String headerIdentity,String bufferIdentity,Integer capacity08,Integer count0c,String allocatorIdentity,List<PendingRecord> records) {
        public Pending { records=List.copyOf(records); }
    }
    public record PendingRecord(State state,int nativeIndex,String recordIdentity,String vtableIdentity,String slot0TargetIdentity,Long owner08,Integer ordinal0c) { }
}
