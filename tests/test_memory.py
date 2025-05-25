from experiments.run_qualify_followup import *

print('🧠 Testing Memory Functionality')
print('=' * 40)

# First, let's see what's in memory
print(f'Leads in memory: {list(qualification_memory.keys())}')

if 'lead_001' in qualification_memory:
    print('Previous qualification found!')
    prev = qualification_memory['lead_001']
    print(f'Previous priority: {prev["priority"]}')
    print(f'Previous score: {prev["lead_score"]}')
    print(f'Previous reasoning: {prev["reasoning"][:100]}...')
    print()

# Now qualify the same lead again
print('Qualifying lead_001 again with memory context...')
context = extract_lead_context('lead_001')
result = llm_qualify_lead(context)

print(f'New priority: {result["priority"]}')
print(f'New score: {result["lead_score"]}')
print(f'New reasoning: {result["reasoning"][:150]}...')

print('\n✅ Memory test completed!') 