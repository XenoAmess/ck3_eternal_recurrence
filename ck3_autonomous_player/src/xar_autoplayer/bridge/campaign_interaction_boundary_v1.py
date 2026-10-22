"""Typed native notification boundary; never chooses or clears an interaction."""
from __future__ import annotations
from dataclasses import dataclass
import math
from typing import Literal,NotRequired,TypedDict

class FailedAdvancePauseV1(TypedDict):
    original_error_type: str
    original_error: str
    status: Literal['NOT_ADMITTED','ALREADY_PAUSED_OBSERVED','FULL_PAUSED_FRAME_OBSERVED','PAUSE_NOT_PROVEN']
    pause_attempted: bool
    original_deadline: float
    business_credit: Literal[False]
    date_raw: NotRequired[int]
    pause_error_type: NotRequired[str]
    pause_error: NotRequired[str]

class ControlPlanFailureHoldV1(TypedDict):
    schema: Literal['ck3-control-plan-failure-hold-v1']
    control_plan: str
    original_error_type: str
    original_error: str
    original_hold_deadline: float
    consumed_control_plan_preserved: Literal[True]
    mutation_replayed: Literal[False]
    business_pass: Literal[False]
    normal_close_qualified: Literal[False]

def control_plan_failure_hold_v1(control_plan: str,error: Exception,deadline: float) -> ControlPlanFailureHoldV1:
    if type(control_plan) is not str or not control_plan or '\0' in control_plan:
        raise ValueError('Actual consumed control path required')
    if not isinstance(error,Exception):raise ValueError('Original ordinary control exception required')
    if type(deadline) not in (int,float) or not math.isfinite(deadline) or deadline<=0:
        raise ValueError('Original finite hold deadline required')
    return {'schema':'ck3-control-plan-failure-hold-v1','control_plan':control_plan,
            'original_error_type':type(error).__name__,'original_error':str(error),'original_hold_deadline':float(deadline),
            'consumed_control_plan_preserved':True,'mutation_replayed':False,'business_pass':False,
            'normal_close_qualified':False}

def integer(value: object, minimum: int=1, maximum: int=2**64-1) -> int:
    if type(value) is not int or not isinstance(value,int) or not minimum<=value<=maximum:
        raise ValueError('Exact bounded native identity integer required')
    return value

@dataclass(frozen=True)
class PendingNotificationV1:
    instance_id: int
    sender_character_id: int
    auto_accept_notification: bool

    @classmethod
    def parse(cls,value: object) -> PendingNotificationV1 | None:
        if value is None:return None
        if not isinstance(value,dict) or set(value)!={'instance_id','sender_character_id','auto_accept_notification','source'}:
            raise ValueError('Exact native pending notification required')
        automatic=value.get('auto_accept_notification')
        if value.get('source')!='native' or type(automatic) is not bool or not isinstance(automatic,bool):
            raise ValueError('Native source and exact notification boolean required')
        return cls(integer(value.get('instance_id'),maximum=2**32-1),
                   integer(value.get('sender_character_id'),maximum=2**32-2),automatic)

def pending_instance_v1(value: object) -> int | None:
    parsed=PendingNotificationV1.parse(value)
    return None if parsed is None else parsed.instance_id

def owner_identities_match_v1(source: object,current: object,*,allow_actor_change: bool=False,
                              allowed_interaction_instance: int | None=None) -> bool:
    """Permit one newly observed notification, preserving every actual owner field."""
    try:
        if type(allow_actor_change) is not bool:raise ValueError('Exact actor policy required')
        if not isinstance(source,(tuple,list)) or not isinstance(current,(tuple,list)) or len(source)!=8 or len(current)!=8:
            raise ValueError('Complete in-memory owner identity required')
        for identity in (source,current):
            for index,minimum,maximum in ((0,1,2**32-1),(1,1,2**64-1),(2,1,2**31-1),
                                          (3,0,2**31-1),(4,1,5),(6,1,2**32-1)):
                integer(identity[index],minimum=minimum,maximum=maximum)
            if type(identity[5]) is not str or not identity[5] or '\0' in identity[5]:
                raise ValueError('Exact original pipe required')
        previous=PendingNotificationV1.parse(source[7]);pending=PendingNotificationV1.parse(current[7])
        indices=(0,1,3,4,5,6) if allow_actor_change else (0,1,2,3,4,5,6)
        if any(source[index]!=current[index] for index in indices):return False
        if allowed_interaction_instance is None:return previous==pending
        instance=integer(allowed_interaction_instance,maximum=2**32-1)
        return pending is not None and pending.instance_id==instance and (previous is None or previous==pending)
    except ValueError:
        return False
