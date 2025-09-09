"""Author/admin API routes for managing storylets."""

import os
import json
import logging
import traceback
from typing import Dict, Any, cast
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Storylet, SessionVars
from ..models.schemas import SuggestReq, SuggestResp, StoryletIn, GenerateStoryletRequest, WorldDescription
from ..services.llm_service import llm_suggest_storylets, generate_world_storylets
from ..services.game_logic import auto_populate_storylets
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func

router = APIRouter()


@router.post('/suggest', response_model=SuggestResp)
def author_suggest(payload: SuggestReq):
    """Generate storylet suggestions using LLM."""
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


@router.post('/commit')
def author_commit(payload: SuggestResp, db: Session = Depends(get_db)):
    """Commit suggested storylets to the database."""
    count = 0
    for s in payload.storylets:
        # Normalize title for comparison
        normalized = (s.title or "").strip()
        exists = db.query(Storylet).filter(func.lower(Storylet.title) == func.lower(normalized)).first()
        if exists:
            # Skip duplicate
            continue
        row = Storylet(
            title=normalized,
            text_template=s.text_template,
            requires=s.requires,
            choices=s.choices,
            weight=s.weight
        )
        db.add(row)
        try:
            db.flush()
        except IntegrityError:
            # Another thread/process inserted a row with same title; skip it
            db.rollback()
            continue
        count += 1
    db.commit()
    
    # Auto-assign spatial coordinates to newly committed storylets
    if count > 0:
        from ..services.spatial_navigator import SpatialNavigator
        new_storylet_ids = []
        for storylet in db.query(Storylet).filter(Storylet.title.in_([s.title for s in payload.storylets])):
            new_storylet_ids.append(storylet.id)
        
        updates = SpatialNavigator.auto_assign_coordinates(db, new_storylet_ids)
        if updates > 0:
            print(f"📍 Auto-assigned coordinates to {updates} committed storylets")
    
    # Auto-improve storylets after adding new ones
    from ..services.auto_improvement import auto_improve_storylets, should_run_auto_improvement, get_improvement_summary
    
    if should_run_auto_improvement(count, "author-commit"):
        improvement_results = auto_improve_storylets(
            db=db, 
            trigger=f"author-commit ({count} storylets)",
            run_smoothing=True,
            run_deepening=True
        )
        
        return {
            "added": count,
            "auto_improvements": get_improvement_summary(improvement_results),
            "improvement_details": improvement_results
        }
    
    return {"added": count}


@router.post('/populate')
def populate_storylets(target_count: int = 20, db: Session = Depends(get_db)):
    """Auto-populate the database with AI-generated storylets."""
    # Validate target_count parameter
    if target_count < 1:
        raise HTTPException(status_code=400, detail="target_count must be at least 1")
    if target_count > 100:
        raise HTTPException(status_code=400, detail="target_count cannot exceed 100")
    
    try:
        added = auto_populate_storylets(db, target_count)
        current_count = db.query(Storylet).count()
        
        # Auto-assign spatial coordinates to any storylets that need them
        if added > 0:
            from ..services.spatial_navigator import SpatialNavigator
            updates = SpatialNavigator.auto_assign_coordinates(db)
            if updates > 0:
                print(f"📍 Auto-assigned coordinates to {updates} populated storylets")
        
        # Auto-improve storylets after population
        from ..services.auto_improvement import auto_improve_storylets, should_run_auto_improvement, get_improvement_summary
        
        base_response = {
            "success": True,
            "added": added,
            "total_storylets": current_count,
            "message": f"Added {added} new storylets. Total: {current_count}"
        }
        
        if should_run_auto_improvement(added, "populate-storylets"):
            improvement_results = auto_improve_storylets(
                db=db,
                trigger=f"populate-storylets ({added} storylets)",
                run_smoothing=True,
                run_deepening=True
            )
            
            base_response["auto_improvements"] = get_improvement_summary(improvement_results)
            base_response["improvement_details"] = improvement_results
        
        return base_response
        
    except Exception as e:
        logging.exception("Error populating storylets")
        raise HTTPException(status_code=500, detail={
            "error": str(e),
            "type": type(e).__name__
        })


@router.get("/debug")
def debug_game_state(db: Session = Depends(get_db)):
    """Debug endpoint to see current game state and storylet data."""
    try:
        # Get session variables
        session_vars = db.query(SessionVars).first()
        session_dict = cast(Dict[str, Any], session_vars.vars) if session_vars else {}
        
        # Get total storylets
        total_storylets = db.query(Storylet).count()
        
        # Get storylets that match current state  
        all_storylets = db.query(Storylet).all()
        
        return {
            "session_variables": session_dict,
            "total_storylets": total_storylets,
            "available_storylets": len(all_storylets),
            "sample_storylet_titles": [s.title for s in all_storylets[:5]]  # Show first 5
        }
    except Exception as e:
        return {"error": str(e)}


@router.post("/generate-intelligent")
def generate_intelligent_storylets(
    request: GenerateStoryletRequest,
    db: Session = Depends(get_db)
):
    """
    Generate storylets using AI learning and gap analysis.
    
    This endpoint uses the storylet analyzer to generate targeted,
    coherent storylets that fill identified gaps in the story flow.
    """
    try:
        # Get current session state
        session_vars = db.query(SessionVars).first()
        current_vars: Dict[str, Any] = {}
        if session_vars:
            current_vars = cast(Dict[str, Any], session_vars.vars or {})
        
        # Generate storylets using enhanced AI learning
        from ..services.llm_service import generate_learning_enhanced_storylets
        storylets = generate_learning_enhanced_storylets(
            db=db,
            current_vars=current_vars,
            n=request.count or 3
        )
        
        if not storylets:
            return {"error": "No storylets generated"}
        
        # Save to database
        created_storylets = []
        for data in storylets:
            # Validate required fields
            if not all(key in data for key in ["title", "text_template", "requires", "choices", "weight"]):
                continue
            # Skip duplicates by title (case-insensitive)
            normalized = (data.get("title") or "").strip()
            exists = db.query(Storylet).filter(func.lower(Storylet.title) == func.lower(normalized)).first()
            if exists:
                continue
            storylet = Storylet(
                title=normalized,
                text_template=data["text_template"],
                requires=data["requires"],
                choices=data["choices"],
                weight=float(data["weight"])
            )
            db.add(storylet)
            try:
                db.flush()
            except IntegrityError:
                db.rollback()
                continue
            created_storylets.append({
                "title": storylet.title,
                "text_template": storylet.text_template,
                "requires": data["requires"],
                "choices": data["choices"],
                "weight": storylet.weight
            })
        
        db.commit()
        
        # Auto-assign spatial coordinates to newly created storylets
        if created_storylets:
            from ..services.spatial_navigator import SpatialNavigator
            new_storylet_ids = []
            for storylet in db.query(Storylet).filter(Storylet.title.in_([s["title"] for s in created_storylets])):
                new_storylet_ids.append(storylet.id)
            
            updates = SpatialNavigator.auto_assign_coordinates(db, new_storylet_ids)
            if updates > 0:
                print(f"📍 Auto-assigned coordinates to {updates} intelligent storylets")
        
        # Auto-improve storylets after intelligent generation
        from ..services.auto_improvement import auto_improve_storylets, should_run_auto_improvement, get_improvement_summary
        
        base_response = {
            "message": f"Generated {len(created_storylets)} intelligent storylets",
            "storylets": created_storylets,
            "ai_context": "Used storylet analysis to create targeted, coherent content"
        }
        
        if should_run_auto_improvement(len(created_storylets), "intelligent-generation"):
            improvement_results = auto_improve_storylets(
                db=db,
                trigger=f"intelligent-generation ({len(created_storylets)} storylets)",
                run_smoothing=True,
                run_deepening=True
            )
            
            base_response["auto_improvements"] = get_improvement_summary(improvement_results)
            base_response["improvement_details"] = improvement_results
        
        return base_response
        
    except Exception as e:
        db.rollback()
        return {"error": f"Failed to generate intelligent storylets: {str(e)}"}


@router.get("/storylet-analysis")
def get_storylet_analysis(db: Session = Depends(get_db)):
    """
    Get comprehensive storylet analysis and recommendations.
    
    This endpoint provides detailed analysis of the storylet ecosystem,
    including gaps, successful patterns, and improvement priorities.
    """
    try:
        from ..services.storylet_analyzer import (
            analyze_storylet_gaps,
            generate_gap_recommendations,
            get_ai_learning_context
        )
        
        # Run comprehensive analysis
        gap_analysis = analyze_storylet_gaps(db)
        
        # Extract data for recommendations
        missing_setters = set(gap_analysis.get("missing_connections", []))
        unused_setters = set(gap_analysis.get("unused_setters", []))
        location_flow = gap_analysis.get("location_analysis", {})
        danger_distribution = gap_analysis.get("danger_distribution", {})
        
        recommendations = generate_gap_recommendations(
            missing_setters, unused_setters, location_flow, danger_distribution
        )
        learning_context = get_ai_learning_context(db)
        
        return {
            "gap_analysis": gap_analysis,
            "recommendations": recommendations,
            "ai_learning_context": learning_context,
            "summary": {
                "total_gaps": len(gap_analysis.get("missing_connections", [])),
                "top_priority": recommendations[0]["suggestion"] if recommendations else "No urgent issues",
                "connectivity_health": learning_context.get("world_state_analysis", {}).get("connectivity_health", 0)
            }
        }
        
    except Exception as e:
        return {"error": f"Failed to analyze storylets: {str(e)}"}


@router.post("/generate-targeted")
def generate_targeted_storylets(db: Session = Depends(get_db)):
    """
    Generate storylets specifically targeting identified gaps.
    
    This endpoint creates storylets that address the most critical
    connectivity gaps in the current storylet ecosystem.
    """
    try:
        from ..services.storylet_analyzer import generate_targeted_storylets
        
        # Generate targeted storylets to fill gaps
        storylets = generate_targeted_storylets(db, max_storylets=5)
        
        if not storylets:
            return {"message": "No critical gaps identified - storylet ecosystem is healthy!"}
        
        # Save to database
        created_storylets = []
        for data in storylets:
            # Validate required fields
            if not all(key in data for key in ["title", "text_template", "requires", "choices", "weight"]):
                continue
            # Skip duplicates by title (case-insensitive)
            normalized = (data.get("title") or "").strip()
            exists = db.query(Storylet).filter(func.lower(Storylet.title) == func.lower(normalized)).first()
            if exists:
                continue
            storylet = Storylet(
                title=normalized,
                text_template=data["text_template"],
                requires=data["requires"],
                choices=data["choices"],
                weight=float(data["weight"])
            )
            db.add(storylet)
            try:
                db.flush()
            except IntegrityError:
                db.rollback()
                continue
            created_storylets.append({
                "title": storylet.title,
                "text_template": storylet.text_template,
                "requires": data["requires"],
                "choices": data["choices"],
                "weight": storylet.weight
            })
        
        db.commit()
        
        # Auto-assign spatial coordinates to newly created storylets
        if created_storylets:
            from ..services.spatial_navigator import SpatialNavigator
            new_storylet_ids = []
            for storylet in db.query(Storylet).filter(Storylet.title.in_([s["title"] for s in created_storylets])):
                new_storylet_ids.append(storylet.id)
            
            updates = SpatialNavigator.auto_assign_coordinates(db, new_storylet_ids)
            if updates > 0:
                print(f"📍 Auto-assigned coordinates to {updates} targeted storylets")
        
        # Auto-improve storylets after targeted generation
        from ..services.auto_improvement import auto_improve_storylets, should_run_auto_improvement, get_improvement_summary
        
        base_response = {
            "message": f"Generated {len(created_storylets)} targeted storylets",
            "storylets": created_storylets,
            "targeting_info": "These storylets specifically address connectivity gaps and flow issues"
        }
        
        if should_run_auto_improvement(len(created_storylets), "targeted-generation"):
            improvement_results = auto_improve_storylets(
                db=db,
                trigger=f"targeted-generation ({len(created_storylets)} storylets)",
                run_smoothing=True,
                run_deepening=True
            )
            
            base_response["auto_improvements"] = get_improvement_summary(improvement_results)
            base_response["improvement_details"] = improvement_results
        
        return base_response
        
    except Exception as e:
        db.rollback()
        return {"error": f"Failed to generate targeted storylets: {str(e)}"}


@router.post("/generate-world")
def generate_world_from_description(
    world_description: WorldDescription,
    db: Session = Depends(get_db)
):
    """Generate a complete storylet ecosystem from a world description."""
    try:
        # Clear existing storylets for fresh start
        existing_count = db.query(Storylet).count()
        if existing_count > 0:
            db.query(Storylet).delete()
            db.commit()
            print(f"🗑️ Cleared {existing_count} existing storylets")
        
        # Generate world-specific storylets using AI
        storylets = generate_world_storylets(
            description=world_description.description,
            theme=world_description.theme,
            player_role=world_description.player_role,
            key_elements=world_description.key_elements,
            tone=world_description.tone,
            count=world_description.storylet_count
        )
        
        # Add to database
        created_storylets = []
        for storylet_data in storylets:
            # Normalize title and skip duplicates early
            normalized = (storylet_data.get("title") or "").strip()
            exists = db.query(Storylet).filter(func.lower(Storylet.title) == func.lower(normalized)).first()
            if exists:
                continue
            storylet = Storylet(
                title=normalized,
                text_template=storylet_data["text"],
                choices=storylet_data["choices"],
                requires=storylet_data.get("requires", {}),
                weight=storylet_data.get("weight", 1.0)
            )
            db.add(storylet)
            try:
                db.flush()
            except IntegrityError:
                db.rollback()
                continue
            created_storylets.append({
                "title": storylet.title,
                "text_template": storylet.text_template,
                "requires": storylet_data.get("requires", {}),
                "choices": storylet_data["choices"],
                "weight": storylet.weight
            })
        
        # Analyze the generated world to create a perfect starting storylet
        generated_locations = set()
        generated_themes = set()
        
        for storylet_data in storylets:
            # Extract locations from requirements
            requires = storylet_data.get("requires", {})
            if "location" in requires:
                generated_locations.add(requires["location"])
            
            # Extract themes from titles and content
            title_lower = storylet_data["title"].lower()
            text_lower = storylet_data["text"].lower()
            
            # Identify key themes
            if any(word in title_lower or word in text_lower for word in ["forge", "craft", "create", "build"]):
                generated_themes.add("crafting")
            if any(word in title_lower or word in text_lower for word in ["market", "trade", "vendor", "buy", "sell"]):
                generated_themes.add("commerce")
            if any(word in title_lower or word in text_lower for word in ["ancient", "artifact", "old", "relic"]):
                generated_themes.add("history")
            if any(word in title_lower or word in text_lower for word in ["danger", "threat", "risk", "escape"]):
                generated_themes.add("danger")
            if any(word in title_lower or word in text_lower for word in ["clan", "rival", "family", "group"]):
                generated_themes.add("social")
        
        # Generate a contextual starting storylet
        from ..services.llm_service import generate_starting_storylet
        starting_storylet_data = generate_starting_storylet(
            world_description=world_description,
            available_locations=list(generated_locations),
            world_themes=list(generated_themes)
        )
        
        # Create the dynamic starting storylet
        starting_storylet = Storylet(
            title=starting_storylet_data["title"],
            text_template=starting_storylet_data["text"],
            choices=starting_storylet_data["choices"],
            requires={},  # No requirements - always accessible
            weight=2.0    # Higher weight to be chosen more often
        )
        db.add(starting_storylet)
        created_storylets.append({
            "title": starting_storylet.title,
            "text_template": starting_storylet.text_template,
            "requires": {},
            "choices": starting_storylet.choices,
            "weight": starting_storylet.weight
        })
        
        db.commit()
        
        # Get the IDs of newly created storylets for spatial assignment
        new_storylet_ids = []
        for storylet in db.query(Storylet).filter(Storylet.title.in_([s["title"] for s in created_storylets])):
            new_storylet_ids.append(storylet.id)
        
        # Assign spatial positions to the generated storylets
        from ..services.spatial_navigator import SpatialNavigator
        try:
            spatial_nav = SpatialNavigator(db)
            positions = spatial_nav.assign_spatial_positions(created_storylets)
            print(f"📍 Assigned spatial positions to {len(positions)} storylets")
            
            # Auto-assign coordinates to any storylets that still need them
            additional_updates = SpatialNavigator.auto_assign_coordinates(db, new_storylet_ids)
            if additional_updates > 0:
                print(f"📍 Auto-assigned coordinates to {additional_updates} additional storylets")
                
        except Exception as e:
            print(f"⚠️ Warning: Could not assign spatial positions: {e}")
            # Try just the auto-assignment as fallback
            try:
                updates = SpatialNavigator.auto_assign_coordinates(db, new_storylet_ids)
                if updates > 0:
                    print(f"📍 Fallback: Auto-assigned coordinates to {updates} storylets")
            except Exception as e2:
                print(f"⚠️ Fallback also failed: {e2}")
        
        print(f"🌍 Generated world with {len(generated_locations)} locations: {', '.join(generated_locations)}")
        print(f"🎭 Identified themes: {', '.join(generated_themes)}")
        
        # Auto-improve storylets after world generation
        from ..services.auto_improvement import auto_improve_storylets, should_run_auto_improvement, get_improvement_summary
        
        total_storylets = len(storylets) + 1
        base_response = {
            "success": True,
            "message": f"🎉 Generated {total_storylets} storylets for your {world_description.theme} world!",
            "storylets_created": total_storylets,
            "theme": world_description.theme,
            "player_role": world_description.player_role,
            "tone": world_description.tone,
            "storylets": created_storylets[:3]  # Return first 3 as preview
        }
        
        if should_run_auto_improvement(total_storylets, "world-generation"):
            improvement_results = auto_improve_storylets(
                db=db,
                trigger=f"world-generation ({total_storylets} storylets)",
                run_smoothing=True,
                run_deepening=True
            )
            
            base_response["auto_improvements"] = get_improvement_summary(improvement_results)
            base_response["improvement_details"] = improvement_results
            
            print(f"🤖 {get_improvement_summary(improvement_results)}")
        
        return base_response
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"World generation failed: {str(e)}")
