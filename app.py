from __future__ import annotations
import random
from datetime import datetime
from typing import Any, Dict, List, Optional, cast
import os, json, logging, traceback

from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import JSON, Column, DateTime, Float, Integer, String, Text, create_engine, func
from sqlalchemy.orm import Session, declarative_base, sessionmaker, scoped_session

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code
    with SessionLocal() as db:
        seed_if_empty(db)
    yield
    # Shutdown code
    # (none for now)

# FastAPI Setup
app = FastAPI(title = 'DwarfWeave Backend', version="0.1", lifespan=lifespan)

# During local dev, allow Twine page (often file://) to call us
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database Setup
engine = create_engine('sqlite:///dwarfweave.db', future=True)
SessionLocal = scoped_session(sessionmaker(bind=engine, autoflush=False, autocommit=False))
Base = declarative_base()

class Storylet(Base):
    __tablename__ = 'storylets'
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    text_template = Column(Text, nullable=False)
    requires = Column(JSON, default=dict)
    choices = Column(JSON, default=list)
    weight = Column(Float, default=1.0)
    
class SessionVars(Base):
    __tablename__ = 'session_vars'
    session_id = Column(String(64), primary_key=True)
    vars = Column(JSON, default=dict)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
Base.metadata.create_all(engine)

# Utilities
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
class SafeDict(dict):
    def __missing__(self, key):
        return '{' + key + '}'
    
def _norm_choices(c: Dict[str, Any]) -> ChoiceOut:
    label = c.get("label") or c.get("text") or "Continue"
    set_obj = c.get("set") or c.get("set_vars") or {}
    return ChoiceOut(label=label, set=set_obj)
    
def render(template: str, vars: Dict[str, Any]) -> str:
    return template.format_map(SafeDict(vars))

def meets_requirements(vars: Dict[str, Any], req: Dict[str, Any]) -> bool:
    """
    Simple matcher:
      - Plain equality: {'location': 'mineshaft'}
      - Booleans: {'has_pickaxe': True}
      - Numeric comparisons: {'danger': {'lte': 2}} (supports gte, gt, lte, lt, eq, ne)
    """
    
    for key, need in (req or {}).items():
        have = vars.get(key, None)
        if isinstance(need, dict):
            # numeric or comparable operators
            for op, val in need.items():
                if op == 'gte' and not (have is not None and have >= val): return False
                if op == 'gt'  and not (have is not None and have > val): return False
                if op == 'lte' and not (have is not None and have <= val): return False
                if op == 'lt'  and not (have is not None and have < val): return False
                if op == 'eq'  and not (have == val): return False
                if op == 'ne'  and not (have != val): return False
        else:
            if have != need:
                return False
    return True

def pick_storylet(db: Session, vars: Dict[str, Any]) -> Optional[Storylet]:
    all_rows = db.query(Storylet).all()
    eligible = [s for s in all_rows if meets_requirements(vars, cast(Dict[str, Any], s.requires or {}))]
    if not eligible:
        return None
    weights = [max(0.0, cast(float, s.weight or 0.0)) for s in eligible]
    return random.choices(eligible, weights=weights, k=1)[0]

def seed_if_empty(db: Session):
    if db.query(Storylet).count() > 0:
        return
    seeds: List[Storylet] = [
        Storylet(
            title="A Dark Cave",
            text_template="You find yourself at the entrance of a dark cave. The air is damp and you can hear faint sounds from within.",
            requires={"location": "forest", "has_torch": True},
            choices=[
                {"text": "Enter the cave", "set_vars": {"location": "cave_entrance"}},
                {"text": "Go back to the forest", "set_vars": {"location": "forest"}}
            ],
            weight=1.0
        ),
        Storylet(
            title="Mysterious Stranger",
            text_template="A mysterious stranger approaches you in the market. They seem to be in a hurry and glance around nervously.",
            requires={"location": "market"},
            choices=[
                {"text": "Talk to the stranger", "set_vars": {"met_stranger": True}},
                {"text": "Ignore and walk away", "set_vars": {}}
            ],
            weight=1.0
        ),
        Storylet(
            title="Abandoned Hut",
            text_template="You stumble upon an abandoned hut. It looks old and worn, but there might be something useful inside.",
            requires={"location": "forest"},
            choices=[
                {"text": "Enter the hut", "set_vars": {"location": "hut_interior"}},
                {"text": "Continue through the forest", "set_vars": {"location": "deep_forest"}}
            ],
            weight=1.0
        ),
        Storylet(
            title="Hidden Treasure",
            text_template="You discover a hidden treasure chest buried under some leaves. It looks ancient and valuable.",
            requires={"location": "cave_entrance", "has_key": True},
            choices=[
                {"text": "Open the chest", "set_vars": {"found_treasure": True}},
                {"text": "Leave it alone", "set_vars": {}}
            ],
            weight=1.0
        ),
        Storylet(
            title="Glittering Vein",
            text_template="⛏️ {name} spots a glittering vein in the rock. Danger: {danger}. The air smells like iron.",
            requires={"danger": {"lte": 1}},
            choices=[
                {"label": "Chip at the vein", "set": {"ore": {"inc": 1}, "danger": {"inc": 1}}},
                {"label": "Mark it for later", "set": {"notes": "Marked a vein", "danger": {"inc": 0}}},
            ],
            weight=2.0,
        ),
        Storylet(
            title="Shaky Beam",
            text_template="🪵 A support beam groans. {name} freezes. Danger: {danger}.",
            requires={"danger": {"gte": 1}},
            choices=[
                {"label": "Brace the beam", "set": {"danger": {"dec": 1}}},
                {"label": "Sprint past",    "set": {"danger": {"inc": 1}}},
            ],
            weight=1.5,
        ),
        Storylet(
            title="Where’s My Pickaxe?",
            text_template="🔍 {name} pats their belt. No pickaxe! Danger: {danger}.",
            requires={"has_pickaxe": False},
            choices=[
                {"label": "Search tool rack", "set": {"has_pickaxe": True}},
                {"label": " improvise with a rock", "set": {"danger": {"inc": 1}}},
            ],
            weight=1.0,
        ),
    ]
    db.add_all(seeds)
    db.commit()
    
def apply_choice_set(vars: Dict[str, Any], set_obj: Dict[str, Any]) -> Dict[str, Any]:
    """
    Applies the 'set' dict semantics used in choices. Supports:
        - direct assignment: {'has_pickaxe': True, "notes": "Msg"}
        - numeric inc/dec: {'ore': {'inc': 1}, 'danger': {'dec': 1}}
    (This is here for future use; right now the client applies sets. Server can apply too if you want.)
    """
    out = dict(vars)
    for key, val in (set_obj or {}).items():
        if isinstance(val, dict) and ("inc" in val or 'dec' in val):
            curr = out.get(key, 0)
            out[key] = curr + int(val.get("inc", 0)) - int(val.get('dec', 0))
        else:
            out[key] = val
    return out

def llm_suggest_storylets(n: int, themes: List[str], bible: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Placeholder for LLM integration to suggest new storylets.
    For now, returns some hardcoded examples.
    """
    
    if not os.getenv("OPENAI_API_KEY"):
        base = [
            {
                "title": "Creak in the Dark",
                "text_template": "👂 {name} hears a faint creak behind the support beam. Danger: {danger}.",
                "requires": {"danger": {"lte": 1}},
                "choices": [
                    {"label": "Probe with pick", "set": {"danger": {"inc": 1}}},
                    {"label": "Wedge a shim",    "set": {"danger": {"dec": 1}}},
                ],
                "weight": 1.2,
            },
            {
                "title": "Mushroom Cache",
                "text_template": "🍄 A pale cluster of cave mushrooms glows softly.",
                "requires": {"has_pickaxe": True},
                "choices": [
                    {"label": "Harvest carefully", "set": {"food": {"inc": 1}}},
                    {"label": "Leave them be",     "set": {}},
                ],
                "weight": 1.0,
            },
        ]
        return base[:max(1, int(n or 1))]
        
    # Call OpenAI API
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    sys = (
        "You are an interactive fiction storylet generator. "
        "Output STRICT JSON with a top-level key 'storylets' (array). "
        "Each storylet must have: title, text_template, requires, choices, weight. "
        "choices is an array of objects with {label, set}. "
        "The 'set' supports direct assignment (booleans/strings/numbers) and numeric inc/dec like "
        "{\"danger\": {\"inc\": 1}}. Use ONLY qualities/items mentioned in the bible."
    )
    user = {
        "n": n,
        "themes": themes,
        "bible": bible,
        "example_choices": [
            {"label": "Brace the beam", "set": {"danger": {"dec": 1}}},
            {"label": "Sprint past",    "set": {"danger": {"inc": 1}}}
        ],
    }

    resp = client.chat.completions.create(
        model=os.getenv("MODEL", "gpt-4o-mini"),
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": sys},
            {"role": "user", "content": json.dumps(user)},
        ],
        temperature=0.7,
    )
    data = json.loads(resp.choices[0].message.content or "{}")
    return data.get("storylets", [])

# API Models
class NextReq(BaseModel):
    session_id: str
    vars: Dict[str, Any]
    
class ChoiceOut(BaseModel):
    label: str
    set: Dict[str, Any] = {}
    
class NextResp(BaseModel):
    text: str
    choices: List[ChoiceOut]
    vars: Dict[str, Any]
    
class StoryletIn(BaseModel):
    title: str = Field(..., max_length=200)
    text_template: str
    requires: Dict[str, Any] = Field(default_factory=dict)
    choices: List[Dict[str, Any]] = Field(default_factory=list)
    weight: float = 1.0
    
    # Accept both {"label", "set"} and {"text", "set_vars"}; normalize to label/set
    @field_validator('choices', mode='before')
    @classmethod
    def _normalize_choices(cls, v):
        out = []
        for c in (v or []):
            label = (c.get("label") or c.get("text") or "Continue")
            set_obj = (c.get("set") or c.get("set_vars") or {})
            out.append({"label": label, "set": set_obj})
        return out
    
class SuggestReq(BaseModel):
    n: int = 3
    themes: List[str] = Field(default_factory=list)
    bible: Dict[str, Any] = Field(default_factory=dict)
    
class SuggestResp(BaseModel):
    storylets: List[StoryletIn]

# Routes
@app.get('/health')
def health():
    return {'ok': True, "time": datetime.utcnow().isoformat() + "Z"}

# @app.on_event("start_up")
# def on_startup():
#     with SessionLocal() as db:
#         seed_if_empty(db)
        
@app.post('/api/next', response_model=NextResp)
def api_next(payload: NextReq, db: Session = Depends(get_db)):
    #1 persist/merge session vars
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
    # # Ensure some defaults
    # vars_now.setdefault("name", "Adventurer")
    # vars_now.setdefault("danger", 0)
    # vars_now.setdefault("has_pickaxe", True)
    
    #2 pick a storylet
    story = pick_storylet(db, vars_now)
    if story is None:
        text="🕯️ The tunnel is quiet. Nothing compelling meets the eye."
        out = NextResp(text=text, choices=[ChoiceOut(label='Wait', set={})], vars=vars_now)
        # save back
        row.vars = out.vars  # type: ignore
        db.commit()
        return out
    
    #3 render text and ship choices as is
    text = render(cast(str, story.text_template), vars_now)
    choices = [_norm_choices(c) for c in cast(List[Dict[str, Any]], story.choices or [])]
    out = NextResp(text=text, choices=choices, vars=vars_now)
    
    #4 save vars (unchanged here; your Twine client mutates on click)
    row.vars = out.vars  # type: ignore
    db.commit()
    return out

@app.post('/author/suggest', response_model=SuggestResp)
def author_suggest(payload: SuggestReq):
    # bible can include allowed qualities/items, setting details, etc. so the model stays on rails
    # example bible structure you can POST:
    # example_bible = {
    #     "allowed_qualities": ["brave", "smart", "kind"],
    #     "allowed_items": ["sword", "shield", "potion"],
    #     "setting_details": {
    #         "location": "forest",
    #         "time_of_day": "morning"
    #     }
    # }
    
    try:
        raw = llm_suggest_storylets(payload.n, payload.themes or [], payload.bible or {})
        items = [StoryletIn(**r) for r in (raw or [])]
        # extreme fallback if model returns nothing
        if not items:
            items = [StoryletIn(
                title="Model returned no storylets",
                text_template="The model did not return any storylets. Try adjusting the prompt or your API key.",
                requires={},
                choices=[{"label": "Ok", "set": {}}],
                weight=1.0
            )]
        return SuggestResp(storylets=items)
    except Exception as e:
        logging.exception("Error in LLM suggest")
        raise HTTPException(status_code=500, detail={
            "error": str(e),
            "type": type(e).__name__,
            "trace": traceback.format_exc().splitlines()[-3:]
        })

@app.post('/author/commit')
def author_commit(payload: SuggestResp, db: Session = Depends(get_db)):
    # Here you would implement the logic to commit the suggested storylets
    count = 0
    for s in payload.storylets:
        row = Storylet(
            title=s.title,
            text_template=s.text_template,
            requires=s.requires,
            choices=s.choices,
            weight=s.weight
        )
        db.add(row)
        count += 1
    db.commit()
    return {"added": count}