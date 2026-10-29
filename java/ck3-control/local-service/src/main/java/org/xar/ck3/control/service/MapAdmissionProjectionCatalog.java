package org.xar.ck3.control.service;

import java.util.List;
import org.xar.ck3.control.contracts.CampaignMapAdmission;
import org.xar.ck3.control.contracts.CampaignMapAdmissionComposer;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionOperation;
import org.xar.ck3.control.contracts.projection.ProjectionPort;
import org.xar.ck3.control.contracts.projection.ProjectionPortCatalog;
import org.xar.ck3.control.contracts.projection.RegisteredProjection;

/** The original shared map producer remains the only map composition implementation. */
public final class MapAdmissionProjectionCatalog implements ProjectionPortCatalog {
    @Override public List<RegisteredProjection> registrations() { return List.of(RegisteredProjection.of(new MapPort())); }
    private static final class MapPort implements ProjectionPort<CampaignMapAdmission, CampaignMapAdmission> {
        @Override public ProjectionOperation operation() { return ProjectionOperation.MAP_ADMISSION_COMPOSE; }
        @Override public CampaignMapAdmission decode(byte[] raw) {
            return CampaignMapAdmission.fromJson(StrictJson.parse(CampaignMapAdmissionComposer.compose(raw)));
        }
        @Override public CampaignMapAdmission project(CampaignMapAdmission input) { return input; }
        @Override public byte[] encode(CampaignMapAdmission result) { return result.toCanonicalBytes(); }
        @Override public int outputMaximumBytes() { return StrictJson.OUTPUT_MAX_BYTES; }
    }
}
