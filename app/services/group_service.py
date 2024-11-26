from database import supabase

def get_user_groups(user_id):
    """
    Get all groups assigned to a user using two separate queries
    
    Args:
        user_id: The ID of the user
        
    Returns:
        list: List of group dictionaries with id and name
    """
    try:
        print(f"Fetching groups for user_id: {user_id}")
        
        # First query: get group IDs from link table
        link_response = supabase.from_('link_groups_users')\
            .select('group_id')\
            .eq('user_id', user_id)\
            .execute()
            
        print(f"Link table response: {link_response}")
        
        if not link_response.data:
            print("No group links found for user")
            return []
            
        # Extract group IDs
        group_ids = [item['group_id'] for item in link_response.data]
        print(f"Found group IDs: {group_ids}")
        
        # Second query: get group details
        groups_response = supabase.from_('groups')\
            .select('*')\
            .in_('id', group_ids)\
            .execute()
            
        print(f"Groups table response: {groups_response}")
        
        if groups_response.data:
            print(f"Successfully fetched {len(groups_response.data)} groups")
            return groups_response.data
            
        print("No groups found")
        return []
        
    except Exception as e:
        print(f"Error fetching user groups: {str(e)}")
        print(f"Error type: {type(e)}")
        return [] 