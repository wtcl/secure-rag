#!/usr/bin/env python3
"""
Demo script for time-based range filtering in RAG system
Shows how to use the new time filtering feature
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from datetime import date, timedelta
from backend.rag_service import RAGService

def demo_time_filtering():
    """Demonstrate time-based filtering capabilities"""
    print("🚀 RAG System Time-Based Filtering Demo")
    print("=" * 50)

    # Show current date and time calculations
    base_date = date(2026, 1, 1)
    current_date = date.today()
    days_since_base = (current_date - base_date).days

    print(f"📅 Current Date: {current_date}")
    print(f"📅 Base Date: {base_date}")
    print(f"⏰ Days Since Base: {days_since_base}")
    print()

    # Show example time ranges
    print("📊 Example Time Range Filtering:")
    print("-" * 30)

    ranges = [
        ("Last 7 days", 7),
        ("Last 30 days", 30),
        ("Last 90 days", 90),
        ("Current month", days_since_base % 30),  # Approximate
        ("All time", 999999)
    ]

    for name, days in ranges:
        start_day = max(0, days_since_base - days)
        end_day = days_since_base
        print(f"• {name}: days {start_day} - {end_day}")

    print()
    print("🔧 API Usage Examples:")
    print("-" * 30)
    print("1. Pure vector search (no time filter):")
    print('   POST /api/query')
    print('   {"query": "your question", "search_mode": "vector_only"}')
    print()
    print("2. Time-filtered search (last 30 days):")
    print('   POST /api/query')
    print('   {')
    print('     "query": "your question",')
    print('     "search_mode": "hybrid",')
    print(f'     "time_range": {{"start_days": {max(0, days_since_base - 30)}, "end_days": {days_since_base}}}')
    print('   }')
    print()
    print("3. Combined scalar + time filtering:")
    print('   POST /api/query')
    print('   {')
    print('     "query": "your question",')
    print('     "search_mode": "hybrid",')
    print('     "scalar_filters": {"category": "tech"},')
    print(f'     "time_range": {{"start_days": 0, "end_days": {days_since_base}}}')
    print('   }')
    print()

    print("🎯 Key Features:")
    print("-" * 30)
    print("✓ Documents tagged with upload date (days since 2026-01-01)")
    print("✓ Range filtering using PPRFANNS algorithm")
    print("✓ Frontend time range selector")
    print("✓ Automatic time tag assignment on document upload")
    print("✓ Backward compatible with existing queries")
    print()

    print("🔄 How It Works:")
    print("-" * 30)
    print("1. Upload document → Calculate days since base date")
    print("2. Assign time tag to all document chunks")
    print("3. Store in PPRFANN database with range filtering capability")
    print("4. Query with time range → Filter vectors by tag range")
    print("5. Perform ANN search on filtered subset")
    print()

    print("✅ Implementation Complete!")
    print("The system now supports both conventional ANN and range-filtered ANN")
    print("as requested, integrated with the existing RAG pipeline.")

if __name__ == "__main__":
    demo_time_filtering()