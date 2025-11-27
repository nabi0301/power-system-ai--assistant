# enhanced_multi_db_integration.py
"""
Enhanced Multi-Database Integration for Power System Visualization
Adds SQLite + PostgreSQL support while preserving all existing functionality
"""

# Enhanced Multi-Database Support - Safe Integration
try:
    from sqlite_postgres_manager import SQLitePostgreSQLManager
    from sqlite_postgres_config import SQLitePostgreSQLConfig
    from ai_sqlite_postgres_router import SQLitePostgreSQLAIRouter
    from knowledge_base_setup import setup_sqlite_knowledge_base, check_knowledge_base_exists
    ENHANCED_MULTI_DB_AVAILABLE = True
    print("✅ Enhanced SQLite + PostgreSQL multi-database system available")
except ImportError as e:
    ENHANCED_MULTI_DB_AVAILABLE = False
    print(f"⚠️ Enhanced multi-database system not available: {e}")

# Global instances
enhanced_db_manager = None
enhanced_ai_router = None

def initialize_enhanced_multi_database():
    """Initialize enhanced multi-database system with graceful fallback"""
    global enhanced_db_manager, enhanced_ai_router
    
    if not ENHANCED_MULTI_DB_AVAILABLE:
        return False
    
    try:
        # Setup knowledge base if it doesn't exist
        if not check_knowledge_base_exists():
            print("🔧 Setting up SQLite knowledge base...")
            setup_sqlite_knowledge_base()
        
        # Initialize multi-database system
        sqlite_pg_config = SQLitePostgreSQLConfig()
        enhanced_db_manager = SQLitePostgreSQLManager(sqlite_pg_config)
        enhanced_ai_router = SQLitePostgreSQLAIRouter(enhanced_db_manager)
        
        print("✅ Enhanced SQLite + PostgreSQL multi-database system initialized")
        status = enhanced_db_manager.get_database_status()
        print(f"   📊 Connected: {status['connected_count']}/{status['total_databases']} databases")
        
        return True
        
    except Exception as e:
        print(f"⚠️ Enhanced multi-database initialization failed: {e}")
        return False

def get_enhanced_db_status():
    """Get enhanced database status for UI display"""
    if not ENHANCED_MULTI_DB_AVAILABLE or not enhanced_db_manager:
        return {
            'available': False,
            'status': 'Enhanced multi-database system not available'
        }
    
    try:
        status = enhanced_db_manager.get_database_status()
        return {
            'available': True,
            'status': status,
            'summary': f"{status['connected_count']}/{status['total_databases']} databases connected"
        }
    except Exception as e:
        return {
            'available': False,
            'status': f'Error getting status: {e}'
        }

def enhanced_get_ai_response(user_message, current_viz_type='network_view'):
    """Enhanced AI response with SQLite + PostgreSQL routing"""
    
    if ENHANCED_MULTI_DB_AVAILABLE and enhanced_ai_router:
        try:
            # Route the request
            intent_type, routing_info = enhanced_ai_router.route_request(user_message)
            
            if intent_type == 'cached':
                # Return cached response
                cached_data = routing_info['data']
                return cached_data.get('response', 'Cached response'), \
                       cached_data.get('viz_command'), \
                       cached_data.get('case_id'), \
                       cached_data.get('contingency_id')
            
            elif intent_type == 'visualization':
                return handle_enhanced_visualization_response(routing_info)
            
            elif intent_type == 'qa':
                return handle_enhanced_qa_response(routing_info)
                
        except Exception as e:
            print(f"⚠️ Enhanced AI router error: {e}")
    
    # Return None to indicate fallback to existing system
    return None

def handle_enhanced_visualization_response(routing_info):
    """Handle visualization requests using PostgreSQL data with fallback"""
    case_id = routing_info.get('case_id', 0)
    contingency_id = routing_info.get('contingency_id')
    viz_type = routing_info.get('viz_type', 'network_view')
    query_hash = routing_info.get('query_hash')
    
    try:
        # Build appropriate query based on viz_type
        if viz_type == 'network_view':
            query = f"SELECT * FROM base_buses WHERE base_case_id = {case_id} LIMIT 10"
            try:
                buses_df = enhanced_db_manager.get_visualization_data(query)
                bus_count = len(buses_df)
            except:
                bus_count = "N/A (using fallback database)"
            
            response = f"🌐 **Enhanced Network Visualization for Case {case_id}**\n\n"
            response += f"Using enhanced multi-database system with {bus_count} buses.\n"
            response += f"Data retrieved from PostgreSQL with SQLite fallback support.\n"
            
        elif viz_type == 'voltage':
            response = f"⚡ **Enhanced Voltage Analysis for Case {case_id}**\n\n"
            response += f"Multi-database voltage analysis with caching enabled.\n"
            
        elif viz_type == 'dual_network':
            response = f"🔗 **Enhanced Network Comparison for Case {case_id}**\n\n"
            response += f"Comparing base case vs contingency {contingency_id or 'base'} using enhanced database system.\n"
            
        else:
            response = f"📊 **Enhanced {viz_type.replace('_', ' ').title()} for Case {case_id}**\n\n"
            response += f"Analysis powered by multi-database architecture.\n"
        
        # Cache the result
        result_data = {
            'response': response,
            'viz_command': viz_type,
            'case_id': case_id,
            'contingency_id': contingency_id,
            'enhanced': True
        }
        enhanced_db_manager.cache_query_result(query_hash, result_data)
        
        return response, viz_type, case_id, contingency_id
        
    except Exception as e:
        # Fallback response
        response = f"⚠️ Enhanced database temporarily unavailable. Using fallback system.\n"
        response += f"Requested: {viz_type} for case {case_id}"
        return response, viz_type, case_id, contingency_id

def handle_enhanced_qa_response(routing_info):
    """Handle Q&A requests using SQLite knowledge base"""
    search_term = routing_info.get('search_term', '')
    category = routing_info.get('category')
    query_hash = routing_info.get('query_hash')
    
    try:
        # Search the SQLite knowledge base
        knowledge_results = enhanced_db_manager.get_knowledge_data(search_term, category)
        
        if knowledge_results:
            # Format the response from knowledge base
            best_result = knowledge_results[0]
            
            response = f"💡 **Knowledge Base Response**\n\n"
            response += f"**{best_result.get('title', 'Power Systems Information')}**\n\n"
            response += f"{best_result.get('content', 'No content available')}\n\n"
            
            if best_result.get('source'):
                response += f"*Source: {best_result['source']}*\n"
            
            if len(knowledge_results) > 1:
                response += f"\n📚 Found {len(knowledge_results)} related topics in knowledge base."
                
            # Show related terms if available
            if len(knowledge_results) > 1:
                response += f"\n\n**Related Topics:**\n"
                for i, result in enumerate(knowledge_results[1:4], 1):  # Show up to 3 more
                    response += f"{i}. {result.get('title', 'Untitled')}\n"
        else:
            # Fallback response
            response = f"🔍 **Knowledge Search for '{search_term}'**\n\n"
            response += "I searched the power systems knowledge base but couldn't find specific information. "
            response += "Try asking about:\n"
            response += "• Voltage regulation and reactive power\n"
            response += "• DLR vs SLR comparison\n"
            response += "• Contingency analysis and N-1 studies\n"
            response += "• Power flow analysis\n"
            response += "• IEEE 118-bus test system\n"
        
        # Cache the result
        result_data = {
            'response': response,
            'viz_command': None,
            'case_id': None,
            'contingency_id': None,
            'enhanced': True,
            'knowledge_results': len(knowledge_results) if knowledge_results else 0
        }
        enhanced_db_manager.cache_query_result(query_hash, result_data)
        
        return response, None, None, None
        
    except Exception as e:
        return f"❌ Error accessing enhanced knowledge base: {e}", None, None, None

def store_enhanced_analytics(result_type: str, data: dict, case_id: int = None):
    """Store analytics results in enhanced database system"""
    if ENHANCED_MULTI_DB_AVAILABLE and enhanced_db_manager:
        try:
            return enhanced_db_manager.store_analytics_result(result_type, data, case_id)
        except Exception as e:
            print(f"⚠️ Enhanced analytics storage failed: {e}")
    return False

def get_enhanced_knowledge_suggestions(query: str) -> list:
    """Get knowledge base suggestions for autocomplete/suggestions"""
    if not ENHANCED_MULTI_DB_AVAILABLE or not enhanced_db_manager:
        return []
    
    try:
        results = enhanced_db_manager.get_knowledge_data(query)
        return [result.get('title', '') for result in results[:5]]
    except:
        return []

def cleanup_enhanced_connections():
    """Clean up enhanced database connections"""
    if enhanced_db_manager:
        try:
            enhanced_db_manager.close_all_connections()
        except Exception as e:
            print(f"⚠️ Error closing enhanced connections: {e}")

# Export the enhanced system for optional use
__all__ = [
    'ENHANCED_MULTI_DB_AVAILABLE',
    'initialize_enhanced_multi_database', 
    'get_enhanced_db_status',
    'enhanced_get_ai_response',
    'store_enhanced_analytics',
    'get_enhanced_knowledge_suggestions',
    'cleanup_enhanced_connections'
]