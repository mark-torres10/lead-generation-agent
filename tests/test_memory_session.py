from experiments.run_qualify_followup import *

print('🧠 Testing Memory Functionality in Single Session')
print('=' * 50)

# Clear any existing state
qualification_memory.clear()
sent_emails.clear()

print('1. Initial state - Memory is empty')
print(f'   Leads in memory: {list(qualification_memory.keys())}')
print()

# First qualification
print('2. First qualification of lead_001')
context = extract_lead_context('lead_001')
result1 = llm_qualify_lead(context)
print(f'   Priority: {result1["priority"]}')
print(f'   Score: {result1["lead_score"]}')
print(f'   Reasoning: {result1["reasoning"][:100]}...')
print()

print('3. Memory after first qualification')
print(f'   Leads in memory: {list(qualification_memory.keys())}')
if 'lead_001' in qualification_memory:
    mem = qualification_memory['lead_001']
    print(f'   Stored priority: {mem["priority"]}')
    print(f'   Stored score: {mem["lead_score"]}')
print()

# Second qualification - should use memory
print('4. Second qualification of lead_001 (should use memory)')
result2 = llm_qualify_lead(context)
print(f'   Priority: {result2["priority"]}')
print(f'   Score: {result2["lead_score"]}')
print(f'   Reasoning: {result2["reasoning"][:100]}...')
print()

# Check if the LLM mentions previous qualification
if 'previous' in result2["reasoning"].lower() or 'before' in result2["reasoning"].lower():
    print('✅ LLM appears to be using memory context!')
else:
    print('⚠️  LLM may not be using memory context explicitly')

print('\n🎯 Memory test completed!') 