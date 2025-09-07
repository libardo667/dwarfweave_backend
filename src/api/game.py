"""Main game API routes."""

import logging
import traceback
from typing import Any, Dict, List, cast
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import SessionVars, Storylet
from ..models.schemas import NextReq, NextResp, ChoiceOut
from ..services.game_logic import pick_storylet, render

router = APIRouter()


def _norm_choices(c: Dict[str, Any]) -> ChoiceOut:
    """Normalize choice dictionary to ChoiceOut model."""
    label = c.get("label") or c.get("text") or "Continue"
    set_obj = c.get("set") or c.get("set_vars") or {}
    return ChoiceOut(label=label, set=set_obj)


@router.post('/next', response_model=NextResp)
def api_next(payload: NextReq, db: Session = Depends(get_db)):
    """Get the next storylet for a session."""
    # 1. Persist/merge session vars
    row = db.get(SessionVars, payload.session_id)
    if row is None:
        row = SessionVars(session_id=payload.session_id, vars=payload.vars)
        db.add(row)
        db.commit()
        db.refresh(row)
    else:
        # merge client vars over stored vars
        merged = dict(cast(Dict[str, Any], row.vars or {}))
        merged.update(payload.vars or {})
        row.vars = merged  # type: ignore
        db.commit()
        db.refresh(row)
        
    vars_now = dict(cast(Dict[str, Any], row.vars or {}))
    
    # 2. Pick a storylet
    story = pick_storylet(db, vars_now)
    if story is None:
        text = "🕯️ The tunnel is quiet. Nothing compelling meets the eye."
        out = NextResp(text=text, choices=[ChoiceOut(label='Wait', set={})], vars=vars_now)
        # save back
        row.vars = out.vars  # type: ignore
        db.commit()
        return out
    
    # 3. Render text and ship choices as is
    text = render(cast(str, story.text_template), vars_now)
    choices = [_norm_choices(c) for c in cast(List[Dict[str, Any]], story.choices or [])]
    out = NextResp(text=text, choices=choices, vars=vars_now)
    
    # 4. Save vars (unchanged here; your Twine client mutates on click)
    row.vars = out.vars  # type: ignore
    db.commit()
    return out
