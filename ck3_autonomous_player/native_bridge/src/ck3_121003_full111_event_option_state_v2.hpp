#pragma once

#include "xar_bridge/ck3_121003_full111_event_option_v2.hpp"
#include <algorithm>
#include <limits>

namespace xar::ck3_121003::build26785313::full111_event_effect {
using Action = Full111EventOptionAction267V2;
using Request = Full111EventOptionRequest267V2;
using Target = Full111EventOptionTarget267V2;
using Lineage = Full111EventOptionLineage267V2;

struct Owner {
    std::uintptr_t game = 0, jomini = 0;
    std::uint64_t connection = 0, ticket = 0;
    friend bool operator==(const Owner &, const Owner &) = default;
};
inline bool LaterOnOwner(const Owner &after, const Owner &before) noexcept {
    return before.game && before.jomini && before.connection && before.ticket &&
        after.game == before.game && after.jomini == before.jomini &&
        after.connection == before.connection && after.ticket > before.ticket;
}
inline bool SameCore(const ck3_1210::CoreSnapshotPrefix &a, const ck3_1210::CoreSnapshotPrefix &b) noexcept {
    return a.clock.date_raw == b.clock.date_raw && a.clock.speed == b.clock.speed &&
        a.clock.paused == b.clock.paused && a.local_player_id == b.local_player_id &&
        a.map_ready == b.map_ready && a.has_played_character == b.has_played_character &&
        a.played_character_id == b.played_character_id && a.played_character_alive == b.played_character_alive;
}

struct Evidence {
    Lineage lineage;
    ck3_1210::CoreSnapshotPrefix core;
    Owner owner;
    std::uint64_t wall = 0, mono = 0;
};
struct Lease {
    Evidence evidence;
    Target target;
};
struct Claim {
    Lease lease;
    bool dispatched = false;
};

class State {
public:
    const std::optional<Lease> &active_lease() const noexcept { return lease_; }

    bool accepts_renderer(const Request &request, const Evidence &renderer, const Owner &owner) const noexcept {
        return request.lineage == renderer.lineage && LaterOnOwner(owner, renderer.owner) &&
            SameCore(request.expected, renderer.core) && request.deadline_unix_ms == renderer.wall;
    }

    bool prepare(const Request &request, const Evidence &renderer, const Owner &owner, std::uint64_t mono) {
        if (!accepts_renderer(request, renderer, owner) || prior_instance(request.target, owner) ||
            unresolved() || sequence_ == (std::numeric_limits<std::uint64_t>::max)()) return false;
        if (lease_ && lease_->evidence.lineage.renderer_request_id == request.lineage.renderer_request_id &&
            lease_->evidence.owner.connection == owner.connection) return false;
        auto lineage = request.lineage;
        lineage.prepare_request_id = request.request_id;
        lineage.lease_sequence = sequence_ + 1;
        lease_ = Lease{{std::move(lineage), request.expected, owner, renderer.wall, mono}, request.target};
        ++sequence_;
        return true;
    }

    bool accepts_selection(const Request &request, const Owner &owner) const noexcept {
        if (!lease_ || unresolved() || prior_instance(request.target, owner)) return false;
        const auto &evidence = lease_->evidence;
        return request.lineage == evidence.lineage && request.target == lease_->target &&
            LaterOnOwner(owner, evidence.owner) && SameCore(request.expected, evidence.core) &&
            request.deadline_unix_ms == evidence.wall;
    }

    Claim *preclaim(const Request &request, const Owner &owner) {
        if (!accepts_selection(request, owner) || already_claimed(request.request_id) ||
            sequence_ == (std::numeric_limits<std::uint64_t>::max)()) return nullptr;
        auto claim = *lease_;
        claim.evidence.owner = owner;
        claim.evidence.lineage.effect_request_id = request.request_id;
        claim.evidence.lineage.claim_sequence = sequence_ + 1;
        claims_.push_back({std::move(claim), false});
        lease_.reset();
        open_claim_ = true;
        ++sequence_;
        return &claims_.back();
    }

    const Claim *known_claim_for_read(const Request &request, const Owner &owner) const noexcept {
        if (claims_.empty()) return nullptr;
        const auto &claim = claims_.back();
        return claim.dispatched && request.target == claim.lease.target &&
            request.lineage == claim.lease.evidence.lineage && LaterOnOwner(owner, claim.lease.evidence.owner) &&
            SameCore(request.expected, claim.lease.evidence.core) ? &claim : nullptr;
    }

    bool already_claimed(std::string_view id) const noexcept {
        return std::any_of(claims_.begin(), claims_.end(), [&](const Claim &claim) {
            return claim.lease.evidence.lineage.effect_request_id == id;
        });
    }

    void close_known_claim() noexcept { open_claim_ = false; }
private:
    bool unresolved() const noexcept { return open_claim_; }
    bool prior_instance(const Target &target, const Owner &owner) const noexcept {
        return std::any_of(claims_.begin(), claims_.end(), [&](const Claim &claim) {
            return claim.lease.evidence.owner.game == owner.game &&
                claim.lease.evidence.owner.jomini == owner.jomini &&
                claim.lease.target.instance_id == target.instance_id;
        });
    }
    std::optional<Lease> lease_;
    std::vector<Claim> claims_;
    std::uint64_t sequence_ = 0;
    bool open_claim_ = false;
};
}
