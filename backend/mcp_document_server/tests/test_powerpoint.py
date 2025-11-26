#!/usr/bin/env python3
"""
Test PowerPoint support in document_parsers module.
"""

from pathlib import Path
from document_parsers import (
    extract_text_from_powerpoint,
    create_powerpoint_from_slides,
    extract_text_from_file
)

def test_powerpoint_support():
    """Test PowerPoint extraction and creation."""
    
    print("🧪 Testing PowerPoint Support")
    print("=" * 50)
    
    # Test 1: Create PowerPoint file
    print("\n1. Creating test PowerPoint file...")
    test_file = Path("test_powerpoint_output.pptx")
    
    slides_data = [
        {
            "title": "Artificial Intelligence & Generative AI",
            "content": [
                "Understanding the Future of Technology",
                "Presented by: Glenn Mossy",
                "Date: November 15, 2024"
            ],
            "layout": "title"
        },
        {
            "title": "What is Artificial Intelligence?",
            "content": [
                "AI enables machines to perform tasks requiring human intelligence",
                "Includes learning, reasoning, problem-solving, and perception",
                "Transforms industries from healthcare to finance",
                "Powers everyday applications like voice assistants and recommendations"
            ]
        },
        {
            "title": "Types of AI Systems",
            "content": [
                "Narrow AI: Specialized for specific tasks (Siri, chess engines)",
                "General AI: Human-level intelligence across domains (theoretical)",
                "Machine Learning: Systems that learn from data",
                "Deep Learning: Neural networks with multiple layers"
            ]
        },
        {
            "title": "What is Generative AI?",
            "content": [
                "AI that creates new content (text, images, code, music)",
                "Trained on massive datasets to understand patterns",
                "Examples: ChatGPT, DALL-E, Midjourney, GitHub Copilot",
                "Revolutionizing creative and analytical work"
            ]
        },
        {
            "title": "Large Language Models (LLMs)",
            "content": [
                "GPT-4: Advanced text generation and reasoning",
                "Claude: Helpful, harmless, and honest AI assistant",
                "LLaMA: Open-source foundation models",
                "Gemini: Google's multimodal AI system"
            ]
        },
        {
            "title": "Applications of Generative AI",
            "content": [
                "Content Creation: Articles, marketing copy, creative writing",
                "Code Generation: Automated programming and debugging",
                "Design: Image generation, UI/UX prototyping",
                "Data Analysis: Insights, reports, and visualizations"
            ]
        },
        {
            "title": "AI in Software Development",
            "content": [
                "GitHub Copilot: AI pair programmer",
                "Code review and optimization",
                "Automated testing and documentation",
                "Natural language to code translation"
            ]
        },
        {
            "title": "Ethical Considerations",
            "content": [
                "Bias and fairness in AI systems",
                "Privacy and data protection",
                "Transparency and explainability",
                "Job displacement and workforce adaptation"
            ]
        },
        {
            "title": "Future of AI",
            "content": [
                "Multimodal AI: Understanding text, images, audio, video",
                "AI agents: Autonomous systems that take actions",
                "Personalized AI: Customized to individual needs",
                "AI safety: Ensuring beneficial and aligned systems"
            ]
        },
        {
            "title": "Getting Started with AI",
            "content": [
                "Learn Python and machine learning basics",
                "Experiment with AI APIs (OpenAI, Anthropic, Google)",
                "Build projects using AI tools",
                "Stay updated with latest research and developments"
            ]
        }
    ]
    
    try:
        create_powerpoint_from_slides(
            slides_data=slides_data,
            output_path=test_file,
            title="Artificial Intelligence and Generative AI Overview"
        )
        print(f"✅ Created: {test_file} ({test_file.stat().st_size} bytes)")
    except Exception as e:
        print(f"❌ Failed to create PowerPoint: {e}")
        assert False, f"Failed to create PowerPoint: {e}"
    
    # Test 2: Extract text from PowerPoint
    print("\n2. Extracting text from PowerPoint file...")
    try:
        text, metadata = extract_text_from_powerpoint(test_file)
        print(f"✅ Extracted {len(text)} characters")
        print(f"\nMetadata:")
        for key, value in metadata.items():
            print(f"  - {key}: {value}")
        
        print(f"\nExtracted content (first 400 chars):")
        print("-" * 50)
        print(text[:400])
        print("-" * 50)
    except Exception as e:
        print(f"❌ Failed to extract text: {e}")
        assert False, f"Failed to extract text: {e}"
    
    # Test 3: Test auto-detection
    print("\n3. Testing auto-detection with extract_text_from_file...")
    try:
        text2, metadata2 = extract_text_from_file(test_file)
        print(f"✅ Auto-detected format: {metadata2.get('format')}")
        print(f"✅ Extracted {len(text2)} characters")
        print(f"✅ Slide count: {metadata2.get('slide_count')}")
    except Exception as e:
        print(f"❌ Failed auto-detection: {e}")
        assert False, f"Failed auto-detection: {e}"
    
    # Test 4: Create simple presentation
    print("\n4. Creating simple presentation...")
    simple_file = Path("test_powerpoint_simple.pptx")
    
    simple_slides = [
        {
            "title": "Welcome",
            "content": "This is a simple test presentation",
            "layout": "title"
        },
        {
            "title": "Key Points",
            "content": [
                "Point 1: PowerPoint support is working",
                "Point 2: Extraction is functional",
                "Point 3: Creation is successful"
            ]
        },
        {
            "title": "Conclusion",
            "content": "All tests passed successfully!"
        }
    ]
    
    try:
        create_powerpoint_from_slides(
            slides_data=simple_slides,
            output_path=simple_file,
            title="Simple Test Presentation"
        )
        print(f"✅ Created simple presentation: {simple_file}")
        
        # Extract from simple presentation
        text3, metadata3 = extract_text_from_powerpoint(simple_file)
        print(f"✅ Simple presentation has {metadata3['slide_count']} slides")
        print(f"✅ Contains {metadata3['text_boxes']} text boxes")
        
    except Exception as e:
        print(f"❌ Failed simple presentation test: {e}")
        assert False, f"Failed simple presentation test: {e}"
    
    print("\n" + "=" * 50)
    print("✅ All PowerPoint tests passed!")
    print("\nTest files created:")
    print(f"  - {test_file}")
    print(f"  - {simple_file}")

if __name__ == "__main__":
    import sys
    success = test_powerpoint_support()
    sys.exit(0 if success else 1)
