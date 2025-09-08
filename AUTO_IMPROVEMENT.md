# Auto-Improvement System Documentation

## Overview

The WorldWeaver backend now includes an **automatic story improvement system** that runs whenever new storylets are added to the database. This system ensures that your storylet ecosystem remains healthy, connected, and engaging without manual intervention.

## What It Does

### 🔧 Story Smoothing
- **Fixes isolated locations**: Adds exit choices to connect disconnected areas
- **Eliminates dead-end variables**: Creates storylets that use variables being set but never required
- **Creates bidirectional paths**: Ensures players can navigate back from locations

### 🕳️ Story Deepening  
- **Adds bridge storylets**: Creates narrative transitions between abrupt storylet changes
- **Enhances choice previews**: Shows players where their choices will lead (→ Location)
- **Improves narrative coherence**: Ensures smooth story flow and meaningful consequences

## When It Runs

The auto-improvement system automatically triggers after storylets are added via:

- ✅ **World Generation** (`/author/generate-world`)
- ✅ **Author Commit** (`/author/commit`) 
- ✅ **Population** (`/author/populate`)
- ✅ **Intelligent Generation** (`/author/generate-intelligent`)
- ✅ **Targeted Generation** (`/author/generate-targeted`)
- ✅ **Contextual Generation** (during gameplay when storylets are low)
- ✅ **Auto-Population** (when storylets are automatically added)

## Configuration

### Triggering Conditions
The system uses smart triggering to avoid unnecessary processing:
- Runs when **1 or more** storylets are added
- Considers the **context** of addition (world generation, AI generation, etc.)
- Can be **disabled** by modifying the `should_run_auto_improvement()` function

### Algorithm Selection
You can control which algorithms run:
```python
auto_improve_storylets(
    db=db,
    trigger="your-trigger-name",
    run_smoothing=True,   # Enable/disable smoothing
    run_deepening=True    # Enable/disable deepening
)
```

## Example Output

When the system runs, you'll see responses like:
```json
{
  "added": 6,
  "auto_improvements": "🤖 Auto-improved (8 total): 🔧 Smoothing: 4 variable storylets, 3 return paths | 🕳️ Deepening: choice previews updated",
  "improvement_details": {
    "trigger": "world-generation (6 storylets)",
    "smoothing_results": {...},
    "deepening_results": {...},
    "total_improvements": 8,
    "success": true
  }
}
```

## Console Monitoring

Watch your server console for auto-improvement activity:
```
🤖 Auto-improvement triggered by: world-generation (6 storylets)
🔧 Running story smoothing...
✅ Smoothing complete: 7 fixes applied
🕳️ Running story deepening...
✅ Deepening complete: 1 improvements made
🎉 Auto-improvement complete! Total improvements: 8
```

## Benefits

1. **Transparent Navigation**: Players always know where choices lead
2. **Connected World**: No more isolated locations or dead-end variables  
3. **Engaging Flow**: Smooth narrative transitions and meaningful consequences
4. **Zero Maintenance**: Happens automatically without author intervention
5. **Scalable Content**: System grows more robust as more storylets are added

## Technical Details

### Core Components
- `auto_improvement.py`: Main coordination and triggering logic
- `story_smoother.py`: Graph analysis and structural fixes
- `story_deepener.py`: Narrative flow enhancement and choice previews

### Safety Features
- **Error Isolation**: Auto-improvement failures don't break storylet creation
- **Dry Run Mode**: Available for testing without database changes
- **Logging**: Full audit trail of improvements made
- **Smart Triggering**: Only runs when meaningful improvements are possible

## Customization

To modify the auto-improvement behavior:

1. **Change triggers**: Edit `should_run_auto_improvement()` in `auto_improvement.py`
2. **Adjust algorithms**: Modify `StorySmoother` or `StoryDeepener` classes
3. **Disable for endpoint**: Set `run_smoothing=False` or `run_deepening=False`
4. **Add new triggers**: Call `auto_improve_storylets()` from new code paths

The system is designed to be **opt-out rather than opt-in** - it assumes you want healthy storylet ecosystems by default!
