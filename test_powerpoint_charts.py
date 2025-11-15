#!/usr/bin/env python3
"""
Test PowerPoint chart support in document_parsers module.
"""

from pathlib import Path
from document_parsers import create_powerpoint_from_slides

def test_powerpoint_charts():
    """Test PowerPoint chart creation."""
    
    print("🧪 Testing PowerPoint Chart Support")
    print("=" * 50)
    
    # Test file
    test_file = Path("test_powerpoint_with_charts.pptx")
    
    # Create presentation with various chart types
    slides_data = [
        {
            "title": "AI Market Growth Analysis",
            "content": [
                "Data-Driven Insights",
                "Presented by: Glenn Mossy",
                "Date: November 15, 2024"
            ],
            "layout": "title"
        },
        {
            "title": "AI Market Size (2020-2024)",
            "layout": "blank",
            "chart": {
                "type": "column",
                "chart_title": "Global AI Market Size (Billions USD)",
                "categories": ["2020", "2021", "2022", "2023", "2024"],
                "series": [
                    {
                        "name": "Market Size",
                        "values": [50.1, 62.5, 86.9, 136.6, 184.0]
                    }
                ]
            }
        },
        {
            "title": "AI Adoption by Industry",
            "layout": "blank",
            "chart": {
                "type": "bar",
                "chart_title": "AI Adoption Rate by Industry (%)",
                "categories": ["Healthcare", "Finance", "Retail", "Manufacturing", "Tech"],
                "series": [
                    {
                        "name": "Adoption Rate",
                        "values": [45, 62, 38, 51, 78]
                    }
                ]
            }
        },
        {
            "title": "LLM Model Performance Trends",
            "layout": "blank",
            "chart": {
                "type": "line",
                "chart_title": "Model Performance Over Time (Benchmark Score)",
                "categories": ["GPT-3", "GPT-3.5", "GPT-4", "Claude 2", "Claude 3"],
                "series": [
                    {
                        "name": "Performance Score",
                        "values": [65, 72, 86, 80, 90]
                    }
                ]
            }
        },
        {
            "title": "AI Investment Distribution",
            "layout": "blank",
            "chart": {
                "type": "pie",
                "chart_title": "AI Investment by Category (2024)",
                "categories": ["Research", "Infrastructure", "Applications", "Training", "Other"],
                "series": [
                    {
                        "name": "Investment %",
                        "values": [25, 30, 20, 15, 10]
                    }
                ]
            }
        },
        {
            "title": "Generative AI vs Traditional AI",
            "layout": "blank",
            "chart": {
                "type": "column",
                "chart_title": "Investment Comparison (Billions USD)",
                "categories": ["2020", "2021", "2022", "2023", "2024"],
                "series": [
                    {
                        "name": "Generative AI",
                        "values": [2.5, 5.2, 12.8, 28.5, 45.0]
                    },
                    {
                        "name": "Traditional AI",
                        "values": [47.6, 57.3, 74.1, 108.1, 139.0]
                    }
                ]
            }
        },
        {
            "title": "Key Insights",
            "content": [
                "AI market growing at 38% CAGR",
                "Generative AI adoption accelerating rapidly",
                "Tech sector leads in AI implementation",
                "Investment shifting toward generative AI applications"
            ]
        },
        {
            "title": "Future Projections",
            "layout": "blank",
            "chart": {
                "type": "line",
                "chart_title": "Projected AI Market Growth (2025-2030)",
                "categories": ["2025", "2026", "2027", "2028", "2029", "2030"],
                "series": [
                    {
                        "name": "Total AI Market",
                        "values": [250, 340, 460, 620, 830, 1100]
                    },
                    {
                        "name": "Generative AI",
                        "values": [65, 105, 165, 255, 385, 550]
                    }
                ]
            }
        }
    ]
    
    print("\n1. Creating PowerPoint with charts...")
    try:
        create_powerpoint_from_slides(
            slides_data=slides_data,
            output_path=test_file,
            title="AI Market Growth Analysis with Charts"
        )
        print(f"✅ Created: {test_file} ({test_file.stat().st_size} bytes)")
        print(f"✅ Slides: {len(slides_data)}")
        print(f"✅ Charts: 6 (column, bar, line, pie)")
    except Exception as e:
        print(f"❌ Failed to create PowerPoint: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 50)
    print("✅ PowerPoint with charts created successfully!")
    print(f"\nTest file: {test_file}")
    print("\nChart types demonstrated:")
    print("  - Column chart (market size)")
    print("  - Bar chart (industry adoption)")
    print("  - Line chart (performance trends)")
    print("  - Pie chart (investment distribution)")
    print("  - Multi-series column chart (comparison)")
    print("  - Multi-series line chart (projections)")
    
    return True

if __name__ == "__main__":
    import sys
    success = test_powerpoint_charts()
    sys.exit(0 if success else 1)
