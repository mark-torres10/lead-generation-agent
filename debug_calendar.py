#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from experiments.run_schedule_meeting import mock_calendar_slots, check_calendar_availability

print("Mock calendar slots:")
print(mock_calendar_slots)
print()

test_datetime = "2025-05-26 09:00"
print(f"Testing availability for: {test_datetime}")

# Test the function step by step
try:
    if " " in test_datetime:
        date_part, time_part = test_datetime.split(" ", 1)
        print(f"Date part: '{date_part}'")
        print(f"Time part: '{time_part}'")
        
        print(f"Date in mock_calendar_slots: {date_part in mock_calendar_slots}")
        if date_part in mock_calendar_slots:
            print(f"Available times for {date_part}: {mock_calendar_slots[date_part]}")
            print(f"Time in available times: {time_part in mock_calendar_slots[date_part]}")
        
        result = check_calendar_availability(test_datetime)
        print(f"Final result: {result}")
    
except Exception as e:
    print(f"Error: {e}") 