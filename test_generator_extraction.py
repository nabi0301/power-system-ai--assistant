from entity_extraction import extract_case_and_entity_info

# Test different generator analysis queries
test_cases = [
    "analyze generators in case 42",
    "show redispatched generators in case 10",
    "compare SLR and DLR generators in case 5",
    "what generators changed between SLR and DLR in case 3 contingency 2"
]

for test_case in test_cases:
    print(f"Query: {test_case}")
    result = extract_case_and_entity_info(test_case)
    print(f"Result: {result}")
    print()