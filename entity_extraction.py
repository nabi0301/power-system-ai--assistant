def extract_case_and_entity_info(message):
    """
    Extract case ID and entity information (bus, branch, or generator) from user message.
    Returns a dictionary with case_id, contingency_id, entity information, and query type.
    """
    import re
    
    result = {
        'case_id': 0,  # Default case ID
        'contingency_id': None,  # Default to None (means base case)
        'entity_type': None,  # 'bus', 'branch', or 'generator'
        'entity_ids': [],  # List of bus numbers, branch specs, or generator IDs
        'query_type': None  # 'voltage', 'loading', 'status', 'generation', etc.
    }

    # Extract case ID - pattern like "case 5" or "case-5"
    case_matches = re.findall(r'case[\s-]*(\d+)', message.lower())
    if case_matches:
        result['case_id'] = int(case_matches[0])
    else:
        # If no explicit case ID but numbers are mentioned, first number might be case ID
        all_numbers = re.findall(r'\b(\d+)\b', message)
        if all_numbers and not result['case_id'] and 'case' in message.lower():
            result['case_id'] = int(all_numbers[0])
        
    # Check for contingency references
    contingency_keywords = ['contingency', 'outage', 'failure', 'contingent', 'cont', 'contingencies']
    if any(keyword in message.lower() for keyword in contingency_keywords):
        # Look for explicit contingency ID like "contingency 3" or "outage 5"
        contingency_matches = re.findall(r'(?:contingency|outage|failure|cont)[\s-]*(\d+)', message.lower())
        if contingency_matches:
            result['contingency_id'] = int(contingency_matches[0])
        else:
            # If no specific contingency ID, look for second number which might be contingency ID
            all_numbers = re.findall(r'\b(\d+)\b', message)
            if len(all_numbers) >= 2:
                # Check if the message has a format like "case 5 contingency 3"
                if int(all_numbers[0]) == result['case_id']:
                    result['contingency_id'] = int(all_numbers[1])
                # Or a format like "show network for contingency 3 of case 5"
                elif 'case' in message.lower() and int(all_numbers[1]) == result['case_id']:
                    result['contingency_id'] = int(all_numbers[0])
    
    # Determine query type based on keywords
    message_lower = message.lower()
    if any(word in message_lower for word in ['voltage', 'volt', 'pu', 'p.u.', 'kv']):
        result['query_type'] = 'voltage'
    elif any(word in message_lower for word in ['load', 'loading', 'mva', 'mw', 'overload']):
        result['query_type'] = 'loading'
    elif any(word in message_lower for word in ['status', 'condition', 'state', 'health']):
        result['query_type'] = 'status'
    elif any(word in message_lower for word in ['network', 'diagram', 'graph', 'topology', 'structure']):
        result['query_type'] = 'network'
    elif any(word in message_lower for word in ['generation', 'generator', 'generators', 'gen', 'redispatch', 'dispatch']):
        result['query_type'] = 'generation'
        # Check for SLR vs DLR comparison
        if ('slr' in message_lower and 'dlr' in message_lower) or ('compare' in message_lower and ('slr' in message_lower or 'dlr' in message_lower)):
            result['comparison_type'] = 'slr_vs_dlr'

    # Check if the message is about bus analysis
    bus_keywords = ['bus', 'buses', 'node']
    voltage_status_keywords = ['voltage status', 'voltage level', 'bus voltage']
    if (any(keyword in message_lower for keyword in bus_keywords) or 
        any(keyword in message_lower for keyword in voltage_status_keywords) or
        result['query_type'] == 'voltage'):
        result['entity_type'] = 'bus'
        # Extract bus numbers - patterns like "bus 5", "buses 1, 2, 3" or just numbers
        bus_matches = re.findall(r'bus(?:es)?[\s]*(\d+)', message_lower)
        if bus_matches:
            result['entity_ids'] = [int(bus) for bus in bus_matches]
        else:
            # Try to find just numbers after detecting it's a bus analysis
            all_numbers = re.findall(r'\b(\d+)\b', message)
            if all_numbers:
                # Filter out the case ID if it was found
                if case_matches:
                    # Make sure we don't treat case IDs as bus numbers
                    result['entity_ids'] = [int(n) for n in all_numbers if int(n) != result['case_id']]
    
    # Check if the message is about branch analysis
    branch_keywords = ['branch', 'line', 'branches', 'lines', 'transmission', 'flow', 'branch analysis']
    if any(keyword in message.lower() for keyword in branch_keywords) and not result['entity_type']:
        result['entity_type'] = 'branch'
        print(f"DEBUG: Detected branch analysis request: {message}")
        
        # Extract branch specifications like "line 5-10" or "branch from 5 to 10" or "branch between 5 and 10"
        branch_matches = re.findall(r'(?:branch|line)[\s]*(\d+)[\s-]+(?:to|and)?[\s]*(\d+)', message.lower())
        print(f"DEBUG: First pattern branch matches: {branch_matches}")
        
        # If no matches using the standard pattern, try alternative formats
        if not branch_matches:
            # Try pattern like "branch from 5 to 10"
            branch_matches = re.findall(r'(?:branch|line)[\s]*(?:from)?[\s]*(\d+)[\s]*(?:to)[\s]*(\d+)', message.lower())
            print(f"DEBUG: Second pattern branch matches: {branch_matches}")
        
        if branch_matches:
            result['entity_ids'] = [{'from_bus': int(from_bus), 'to_bus': int(to_bus)} 
                                   for from_bus, to_bus in branch_matches]
        else:
            # If we know it's a branch query but no specific branches mentioned, prepare for all branches
            result['query_type'] = result.get('query_type', 'loading')  # Default to loading analysis if none specified
    
    # Check if the message is about generator analysis
    generator_keywords = ['generator', 'generators', 'gen', 'generation', 'redispatch', 'dispatch']
    if (any(keyword in message.lower() for keyword in generator_keywords) and not result['entity_type']) or result['query_type'] == 'generation':
        result['entity_type'] = 'generator'
        # Extract generator bus numbers - patterns like "generator at bus 5", "generators 1, 2, 3"
        gen_bus_matches = re.findall(r'generator(?:s)?[\s]*(?:at)?[\s]*(?:bus)?[\s]*(\d+)', message.lower())
        if gen_bus_matches:
            result['entity_ids'] = [int(bus) for bus in gen_bus_matches]
        else:
            # If no specific generators mentioned, we'll analyze all generators for that case
            pass
    
    # Check if this is a request for network visualization
    network_keywords = ['network graph', 'network diagram', 'show graph', 'show diagram', 'data_viz_fall network', 'fall network']
    if any(keyword in message.lower() for keyword in network_keywords) or result['query_type'] == 'network':
        result['visualization_type'] = 'fall_network'
        # The case_id has already been extracted above
        
    return result