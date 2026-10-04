"""Offline popup lifecycle oracle, not a CK3 interpreter or live attestation.

The UI callback keeps value context; its actor resolves to CURRENT variables.
This deliberately models the defect that passing an old Proposal object to the
controller would miss. All real mutations remain in the independent controller.
"""

from dataclasses import dataclass

from school_consent_model import ConsentController, Proposal, Rejected


@dataclass(frozen=True)
class EventContext:
    actor: str
    school: str
    serial: int
    terms_revision: int
    nonce: int

    @classmethod
    def capture(cls, proposal: Proposal) -> "EventContext":
        return cls(proposal.actor, proposal.moving_rite, proposal.serial,
                   proposal.terms_revision, proposal.callback_nonce)


def dispatch(controller: ConsentController, context: EventContext, respondent: str,
             action: str, *, school: str | None = None,
             new_faith_id: str | None = None):
    # Resolve current state through the saved actor, as CK3 scope variables do.
    active = [proposal for proposal in controller.proposals.values()
              if proposal.actor == context.actor
              and proposal.phase in {"ballot", "consent", "confirmed"}
              and controller.world.schools[proposal.moving_rite].proposal_owner == context.actor]
    if len(active) != 1:
        raise Rejected("Event actor has no unique current proposal")
    proposal = active[0]
    if EventContext.capture(proposal) != context:
        raise Rejected("Event context refers to another proposal generation")
    if action != "expire":
        controller._current(proposal)
    elif controller.world.day < proposal.deadline:
        raise Rejected("Expiry has not reached its captured deadline")
    if action in {"source_sign", "commit", "cancel", "expire"}:
        if respondent != proposal.actor or not controller.world.members[respondent].player:
            raise Rejected("Initiator popup belongs to another character")
    if action in {"source_vote_yes", "source_vote_no", "target_vote_yes", "target_vote_no"}:
        rite = controller.world.members[respondent].rite
        if (action.startswith("source_") and rite != proposal.moving_rite
                or action.startswith("target_") and rite == proposal.moving_rite):
            raise Rejected("Ballot belongs to the other side")
        controller.vote(proposal, respondent, action.endswith("yes"), context.terms_revision)
    elif action in {"player_yes", "player_no"}:
        controller.consent_player(proposal, respondent, action.endswith("yes"))
    elif action == "source_sign":
        controller.sign_school(proposal, proposal.moving_rite, respondent)
    elif action == "receiving_sign":
        controller.sign_receiving(proposal, respondent)
    elif action == "receiving_refuse":
        main = controller.world.faiths[proposal.receiving_faith].main if proposal.receiving_faith else None
        if not main or proposal.nominees.get(main) != respondent or proposal.moving_rite not in proposal.representative_signatures:
            raise Rejected("Not the receiving representative of this signed round")
        controller.cancel(proposal, rejected=True)
    elif action in {"holder_yes", "holder_no"}:
        if school is None:
            raise Rejected("Holder response needs its captured receiving school")
        controller.endorse_holder(proposal, school, respondent, action.endswith("yes"))
    elif action in {"receiving_head_yes", "receiving_head_no"}:
        controller.consent_head(proposal, "receiving", respondent, action.endswith("yes"))
    elif action in {"source_head_yes", "source_head_no"}:
        controller.consent_head(proposal, "source", respondent, action.endswith("yes"))
    elif action in {"peaceful_yes", "peaceful_no"}:
        controller.consent_old_faith(proposal, respondent, action.endswith("yes"))
    elif action == "commit":
        return controller.commit(proposal, new_faith_id)
    elif action in {"cancel", "expire"}:
        controller.cancel(proposal, rejected=False)
    else:
        raise Rejected("Unknown event callback")
    return proposal
