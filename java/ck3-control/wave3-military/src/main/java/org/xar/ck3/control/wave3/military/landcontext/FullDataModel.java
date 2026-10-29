package org.xar.ck3.control.wave3.military.landcontext;

import java.util.List;
import java.util.Objects;

/** Complete normalized DATA dependency of Province contributors; not the q-only numeric projection. */
public final class FullDataModel {
    private FullDataModel() {}
    public enum Coverage { AVAILABLE, PARTIAL, UNAVAILABLE }
    public enum RecordStatus { AVAILABLE, UNAVAILABLE }
    public record CharacterRole(Coverage status, int armyRegimentId, int nativeCarmyId,
                                Integer arrgArmyId140, Integer characterRawId148, Integer resolvedCharacterId,
                                Integer extensionArmyIdF4, Integer extensionArrgIdF8, Long characterMagic1c,
                                Boolean resolutionUsedFallback, Boolean nativeCharacterPredicate,
                                Boolean characterExtensionPresent, boolean sameArrgInstanceAfter,
                                String unavailableReason) {
        public CharacterRole {
            Objects.requireNonNull(status);
            require(armyRegimentId != -1 && nativeCarmyId != -1, "Character role parent identity differs");
            require(characterMagic1c == null || characterMagic1c >= 0 && characterMagic1c <= 0xffff_ffffL,
                    "Character magic must be uint32/null");
            if (Boolean.TRUE.equals(nativeCharacterPredicate)) {
                require(Long.valueOf(0x4368_6172L).equals(characterMagic1c)
                        && resolvedCharacterId != null && resolvedCharacterId != -1 && resolutionUsedFallback != null,
                        "true Character predicate lacks resolved native identity");
            }
            if (Boolean.FALSE.equals(resolutionUsedFallback)) require(Objects.equals(resolvedCharacterId, characterRawId148),
                    "direct Character generation differs");
            if (Boolean.FALSE.equals(characterExtensionPresent)) require(extensionArmyIdF4 == null && extensionArrgIdF8 == null,
                    "absent Character extension has values");
            if (Integer.valueOf(-1).equals(characterRawId148)) require(Boolean.FALSE.equals(nativeCharacterPredicate)
                    && resolvedCharacterId == null, "absent Character association invented a role");
            if (status == Coverage.AVAILABLE) {
                require(unavailableReason == null && sameArrgInstanceAfter && Integer.valueOf(nativeCarmyId).equals(arrgArmyId140)
                        && characterRawId148 != null && nativeCharacterPredicate != null, "available Character role is incomplete");
                if (Boolean.TRUE.equals(nativeCharacterPredicate)) {
                    require(characterExtensionPresent != null, "available Character extension presence unknown");
                    if (characterExtensionPresent) require(extensionArmyIdF4 != null && extensionArrgIdF8 != null,
                            "available Character extension is incomplete");
                }
            } else require(unavailableReason != null && !unavailableReason.isEmpty(), "unavailable Character role requires reason");
        }
    }
    public record DataRecord(RecordStatus status, String unavailableReason, int recordIndex, int persistentRegimentId,
                             int chunkIndex, Integer currentSoldiers, Integer maximumSoldiers,
                             Integer effectiveCurrentSoldiers, Integer stateRaw, Boolean nativeCanReplenish,
                             Boolean nativeChunkCanReplenish, Long monthlyFractionRaw, Long preparedFractionRaw,
                             int monthlyFractionScale, int preparedFractionScale, Integer chunkArmyRegimentId) {
        public DataRecord {
            Objects.requireNonNull(status);
            require(monthlyFractionScale == 100_000 && preparedFractionScale == 100_000, "native DATA fraction scale differs");
            if (status == RecordStatus.AVAILABLE) {
                require(unavailableReason == null && currentSoldiers != null && maximumSoldiers != null
                        && effectiveCurrentSoldiers != null && stateRaw != null && nativeCanReplenish != null
                        && nativeChunkCanReplenish != null && monthlyFractionRaw != null && preparedFractionRaw != null,
                        "native available full DATA record is incomplete");
            } else require(unavailableReason != null && !unavailableReason.isEmpty(), "native unavailable DATA record requires reason");
        }
    }
    public record Snapshot(int armyRegimentId, Coverage status, Integer nativeDataRecordCount,
                            String unavailableReason, List<DataRecord> records, Boolean nativeLossWriterSkipped,
                            String lossWriterAdmissionUnavailableReason, CharacterRole characterRole) {
        public Snapshot {
            Objects.requireNonNull(status); records = List.copyOf(records);
            require(nativeDataRecordCount == null || nativeDataRecordCount >= 0, "native DATA count cannot be negative");
            if (status == Coverage.AVAILABLE || status == Coverage.PARTIAL) require(nativeDataRecordCount != null
                    && nativeDataRecordCount == records.size(), "native DATA stored count/order is incomplete");
            require(status != Coverage.AVAILABLE || unavailableReason == null, "available DATA reason must be null");
            require(unavailableReason == null || !unavailableReason.isEmpty(), "native DATA reason must be nonempty/null");
            require(lossWriterAdmissionUnavailableReason == null || !lossWriterAdmissionUnavailableReason.isEmpty(),
                    "loss writer admission reason must be nonempty/null");
            require(nativeLossWriterSkipped == null || lossWriterAdmissionUnavailableReason == null,
                    "available loss writer admission value has a reason");
            for (int index = 0; index < records.size(); index++) {
                DataRecord record = records.get(index);
                require(record.recordIndex() == index, "native DATA record order differs");
                if (record.status() == RecordStatus.AVAILABLE && record.chunkArmyRegimentId() != null) {
                    require(record.chunkArmyRegimentId() == armyRegimentId, "available DATA chunk association differs");
                }
                if (status == Coverage.AVAILABLE) require(record.status() == RecordStatus.AVAILABLE,
                        "complete DATA snapshot contains unavailable record");
            }
            if (characterRole != null) {
                require(characterRole.armyRegimentId() == armyRegimentId, "Character role parent identity differs");
                if (characterRole.nativeCharacterPredicate() != null && nativeLossWriterSkipped != null) {
                    require(characterRole.nativeCharacterPredicate().equals(nativeLossWriterSkipped),
                            "same-query Character predicates disagree");
                }
            }
        }
    }
    private static void require(boolean condition, String message) {
        if (!condition) throw new IllegalArgumentException(message);
    }
}
