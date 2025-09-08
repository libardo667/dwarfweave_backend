"""
Storylet Map Visualizer
Creates a visual graph of storylet connections and navigation flow.
"""

import sqlite3
import json
from collections import defaultdict, Counter
import webbrowser
import tempfile
import os


def get_storylets_from_db():
    """Get all storylets from the database."""
    conn = sqlite3.connect('worldweaver.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, title, text_template, requires, choices, weight 
        FROM storylets
    """)
    
    storylets = []
    for row in cursor.fetchall():
        storylet = {
            'id': row[0],
            'title': row[1],
            'text': row[2][:50] + '...' if len(row[2]) > 50 else row[2],
            'requires': json.loads(row[3]) if row[3] else {},
            'choices': json.loads(row[4]) if row[4] else [],
            'weight': row[5]
        }
        storylets.append(storylet)
    
    conn.close()
    return storylets


def analyze_connections(storylets):
    """Analyze location connections and variable flow."""
    locations = set()
    location_storylets = defaultdict(list)
    location_connections = defaultdict(set)
    variables_required = set()
    variables_set = Counter()
    dead_end_variables = set()
    
    # Extract locations and analyze variable flow
    for storylet in storylets:
        # Get location requirement
        location = storylet['requires'].get('location', 'No Location')
        locations.add(location)
        location_storylets[location].append(storylet)
        
        # Track required variables
        for var in storylet['requires'].keys():
            variables_required.add(var)
        
        # Analyze choices for location changes and variable setting
        for choice in storylet['choices']:
            choice_sets = choice.get('set', {})
            
            # Track variables being set
            for var, value in choice_sets.items():
                variables_set[var] += 1
                
            # Track location connections
            new_location = choice_sets.get('location')
            if new_location and new_location != location:
                location_connections[location].add(new_location)
    
    # Find dead-end variables (set but never required)
    all_set_vars = set(variables_set.keys())
    dead_end_variables = all_set_vars - variables_required
    
    return {
        'locations': locations,
        'location_storylets': location_storylets,
        'location_connections': location_connections,
        'variables_required': variables_required,
        'variables_set': dict(variables_set),
        'dead_end_variables': dead_end_variables
    }


def generate_html_map(storylets, analysis):
    """Generate an HTML visualization of the storylet map."""
    
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>WorldWeaver Storylet Map</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        body {{ 
            font-family: 'Segoe UI', sans-serif; 
            margin: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            min-height: 100vh;
        }}
        .container {{ 
            max-width: 1200px; 
            margin: 0 auto; 
            background: rgba(255,255,255,0.1);
            padding: 20px;
            border-radius: 15px;
            backdrop-filter: blur(10px);
        }}
        .header {{ 
            text-align: center; 
            margin-bottom: 30px; 
        }}
        .stats {{ 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); 
            gap: 20px; 
            margin-bottom: 30px; 
        }}
        .stat-box {{ 
            background: rgba(255,255,255,0.1); 
            padding: 15px; 
            border-radius: 10px; 
            border: 1px solid rgba(255,255,255,0.2);
        }}
        .stat-title {{ 
            font-weight: bold; 
            margin-bottom: 10px; 
            color: #feca57;
        }}
        .location-graph {{ 
            background: rgba(255,255,255,0.05); 
            border-radius: 10px; 
            padding: 20px; 
            margin: 20px 0;
        }}
        .location-node {{ 
            background: rgba(46, 204, 113, 0.2);
            border: 2px solid #2ecc71;
            border-radius: 8px;
            padding: 10px;
            margin: 10px;
            display: inline-block;
            min-width: 150px;
            text-align: center;
        }}
        .isolated-location {{ 
            background: rgba(231, 76, 60, 0.2);
            border-color: #e74c3c;
        }}
        .connection-arrow {{ 
            color: #feca57;
            font-weight: bold;
        }}
        .dead-vars {{ 
            background: rgba(231, 76, 60, 0.2);
            border: 1px solid #e74c3c;
            border-radius: 5px;
            padding: 10px;
            margin-top: 10px;
        }}
        .storylet-list {{
            max-height: 200px;
            overflow-y: auto;
            font-size: 0.9em;
        }}
        .storylet-item {{
            margin: 5px 0;
            padding: 5px;
            background: rgba(255,255,255,0.1);
            border-radius: 3px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🗺️ WorldWeaver Storylet Map</h1>
            <p>Visual analysis of storylet connections and navigation flow</p>
        </div>
        
        <div class="stats">
            <div class="stat-box">
                <div class="stat-title">📊 Overview</div>
                <div>Total Storylets: {len(storylets)}</div>
                <div>Total Locations: {len(analysis['locations'])}</div>
                <div>Location Connections: {sum(len(conns) for conns in analysis['location_connections'].values())}</div>
            </div>
            
            <div class="stat-box">
                <div class="stat-title">🔗 Variable Flow</div>
                <div>Variables Required: {len(analysis['variables_required'])}</div>
                <div>Variables Set: {len(analysis['variables_set'])}</div>
                <div>Dead-End Variables: {len(analysis['dead_end_variables'])}</div>
            </div>
            
            <div class="stat-box">
                <div class="stat-title">🚨 Navigation Issues</div>
                <div>Isolated Locations: {len([loc for loc in analysis['locations'] if loc not in analysis['location_connections'] and not any(loc in conns for conns in analysis['location_connections'].values())])}</div>
                <div>One-Way Connections: {sum(1 for conns in analysis['location_connections'].values() for conn in conns if conn not in analysis['location_connections'])}</div>
            </div>
        </div>
"""

    # Location Graph
    html_content += """
        <div class="location-graph">
            <h3>🌍 Location Network</h3>
            <p>Green = Connected locations, Red = Isolated locations</p>
"""
    
    # Show each location and its connections
    for location in sorted(analysis['locations']):
        connections = analysis['location_connections'].get(location, set())
        is_isolated = len(connections) == 0 and not any(location in conns for conns in analysis['location_connections'].values())
        
        node_class = "isolated-location" if is_isolated else "location-node"
        
        html_content += f"""
            <div class="{node_class}">
                <strong>{location}</strong><br>
                <small>{len(analysis['location_storylets'][location])} storylets</small>
                {f'<br><span class="connection-arrow">→ {", ".join(connections)}</span>' if connections else ''}
                
                <div class="storylet-list">
"""
        
        # List storylets in this location
        for storylet in analysis['location_storylets'][location]:
            html_content += f'<div class="storylet-item">📖 {storylet["title"]}</div>'
        
        html_content += """
                </div>
            </div>
"""

    # Dead-end variables warning
    if analysis['dead_end_variables']:
        html_content += f"""
            <div class="dead-vars">
                <strong>⚠️ Dead-End Variables</strong><br>
                These variables are set by choices but never required by any storylet:<br>
                <em>{', '.join(analysis['dead_end_variables'])}</em>
            </div>
"""

    html_content += """
        </div>
        
        <div class="stat-box">
            <div class="stat-title">💡 Recommendations</div>
            <ul>
                <li>Add location-changing choices to isolated locations</li>
                <li>Create storylets that require the dead-end variables</li>
                <li>Ensure each location has multiple entry/exit points</li>
                <li>Add "travel" storylets that connect distant locations</li>
            </ul>
        </div>
    </div>
</body>
</html>
"""
    
    return html_content


def main():
    """Generate and display the storylet map."""
    print("🗺️ Generating WorldWeaver Storylet Map...")
    
    # Get data
    storylets = get_storylets_from_db()
    if not storylets:
        print("❌ No storylets found in database!")
        return
    
    # Analyze connections
    analysis = analyze_connections(storylets)
    
    # Generate HTML
    html_content = generate_html_map(storylets, analysis)
    
    # Save to temp file and open
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
        f.write(html_content)
        temp_file = f.name
    
    print(f"✅ Map generated: {temp_file}")
    print("🌐 Opening in browser...")
    
    # Open in browser
    webbrowser.open(f'file://{os.path.abspath(temp_file)}')
    
    # Print summary
    print(f"""
🗺️ STORYLET MAP SUMMARY:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 {len(storylets)} storylets across {len(analysis['locations'])} locations
🔗 {sum(len(conns) for conns in analysis['location_connections'].values())} location connections
⚠️  {len(analysis['dead_end_variables'])} dead-end variables: {', '.join(analysis['dead_end_variables'])}
🚨 Navigation issues detected - see browser for visual analysis
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")


if __name__ == "__main__":
    main()
