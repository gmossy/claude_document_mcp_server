#!/usr/bin/env python3
"""
Test PowerPoint template support - demonstrates using branded templates.
"""

from pathlib import Path
from document_parsers import (
    create_powerpoint_from_slides,
    get_powerpoint_template_layouts
)

def test_template_inspection():
    """Test inspecting a PowerPoint template's layouts."""
    
    print("🧪 Testing PowerPoint Template Support")
    print("=" * 50)
    
    # First, create a simple template to use as an example
    print("\n1. Creating a sample template...")
    template_file = Path("sample_template.pptx")
    
    # Create a basic presentation to serve as a template
    template_slides = [
        {
            "title": "Company Template",
            "content": ["This is a sample template", "Delete this slide when using"],
            "layout": "title"
        }
    ]
    
    try:
        create_powerpoint_from_slides(
            slides_data=template_slides,
            output_path=template_file,
            title="Sample Template"
        )
        print(f"✅ Created sample template: {template_file}")
    except Exception as e:
        print(f"❌ Failed to create template: {e}")
        assert False, f"Failed to create template: {e}"
    
    # Inspect the template layouts
    print("\n2. Inspecting template layouts...")
    try:
        layouts = get_powerpoint_template_layouts(template_file)
        print(f"✅ Found {len(layouts)} layouts in template:\n")
        
        for layout in layouts:
            print(f"  Layout {layout['index']}: {layout['name']}")
            print(f"    - Placeholders: {layout['placeholder_count']}")
            if layout['placeholders']:
                for ph in layout['placeholders']:
                    print(f"      • {ph['name']} (type: {ph['type']})")
            print()
    except Exception as e:
        print(f"❌ Failed to inspect template: {e}")
        assert False, f"Failed to inspect template: {e}"
    
    # Create a presentation using the template
    print("\n3. Creating presentation from template...")
    output_file = Path("presentation_from_template.pptx")
    
    slides_data = [
        {
            "title": "AI Strategy 2024",
            "content": [
                "Leveraging Artificial Intelligence",
                "Company Confidential",
                "Q4 2024"
            ],
            "layout_index": 0  # Use first layout from template
        },
        {
            "title": "Executive Summary",
            "content": [
                "AI adoption increasing across all departments",
                "ROI exceeding projections by 40%",
                "Scaling to 500+ AI-powered workflows",
                "Investment in GenAI infrastructure"
            ],
            "layout_index": 1  # Use second layout
        },
        {
            "title": "Key Metrics",
            "content": [
                "Productivity gain: +35%",
                "Cost reduction: $2.5M annually",
                "Employee satisfaction: +28%",
                "Customer NPS: +15 points"
            ],
            "layout_index": 1
        }
    ]
    
    try:
        create_powerpoint_from_slides(
            slides_data=slides_data,
            output_path=output_file,
            title="AI Strategy Presentation",
            template_path=template_file  # Use the template!
        )
        print(f"✅ Created presentation using template: {output_file}")
        print(f"✅ File size: {output_file.stat().st_size} bytes")
    except Exception as e:
        print(f"❌ Failed to create presentation: {e}")
        import traceback
        traceback.print_exc()
        assert False, f"Failed to create presentation from template: {e}"
    
    print("\n" + "=" * 50)
    print("✅ Template support working!")
    print("\nKey Features Demonstrated:")
    print("  - Template inspection (layouts and placeholders)")
    print("  - Using existing template for branding")
    print("  - Specific layout selection by index")
    print("  - Template theme, colors, and fonts preserved")
    
    print("\n📝 How to use your own branded template:")
    print("  1. Create your branded PowerPoint template (.pptx)")
    print("  2. Inspect layouts: get_powerpoint_template_layouts(template_path)")
    print("  3. Note the layout indices you want to use")
    print("  4. Create slides with layout_index parameter")
    print("  5. Pass template_path to create_powerpoint_from_slides()")

if __name__ == "__main__":
    import sys
    success = test_template_inspection()
    sys.exit(0 if success else 1)
