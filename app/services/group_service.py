from database import supabase

def get_user_groups(user_id):
    """
    Get all groups assigned to a user using a single JOIN query
    
    Args:
        user_id: The ID of the user
        
    Returns:
        list: List of group dictionaries with id and name
    """
    try:
        # Single query using JOIN
        response = (
            supabase.from_("link_groups_users")
            .select("groups:group_id(*)")
            .eq("user_id", user_id)
            .execute()
        )
        
        if not response.data:
            return []
            
        # Extract groups from nested response
        return [item["groups"] for item in response.data]
        
    except Exception as e:
        print(f"Error fetching user groups: {str(e)}")
        return []

def get_test_groups(test_id):
    """Get groups assigned to a test using a single JOIN query"""
    try:
        response = (
            supabase.from_("link_groups_tests")
            .select("groups:group_id(*)")
            .eq("test_id", test_id)
            .execute()
        )
        
        if not response.data:
            return []
            
        return [item["groups"] for item in response.data]
        
    except Exception as e:
        print(f"Error fetching test groups: {str(e)}")
        return []

def get_campaign_groups(campaign_id):
    """Get groups assigned to a campaign using a single JOIN query"""
    try:
        response = (
            supabase.from_("link_groups_campaigns")
            .select("groups:group_id(*)")
            .eq("campaign_id", campaign_id)
            .execute()
        )
        
        if not response.data:
            return []
            
        return [item["groups"] for item in response.data]
        
    except Exception as e:
        print(f"Error fetching campaign groups: {str(e)}")
        return []