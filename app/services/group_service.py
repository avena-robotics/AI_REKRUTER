from database import supabase

class GroupService:
    @staticmethod
    def get_user_groups(user_id):
        try:
            response = supabase.table('link_groups_users')\
                .select('groups(*)')\
                .eq('user_id', user_id)\
                .execute()
            
            return [item['groups'] for item in response.data] if response.data else []
        except Exception as e:
            print(f"Error getting user groups: {str(e)}")
            return []

    @staticmethod
    def get_group_tests(group_ids):
        try:
            response = supabase.table('link_groups_tests')\
                .select('test_id')\
                .in_('group_id', group_ids)\
                .execute()
            
            return [item['test_id'] for item in response.data] if response.data else []
        except Exception as e:
            print(f"Error getting group tests: {str(e)}")
            return []

    @staticmethod
    def get_group_campaigns(group_ids):
        try:
            response = supabase.table('link_groups_campaigns')\
                .select('campaign_id')\
                .in_('group_id', group_ids)\
                .execute()
            
            return [item['campaign_id'] for item in response.data] if response.data else []
        except Exception as e:
            print(f"Error getting group campaigns: {str(e)}")
            return []

    @staticmethod
    def get_user_test_ids(user_id):
        try:
            # First get user's group IDs
            groups_response = supabase.table('link_groups_users')\
                .select('group_id')\
                .eq('user_id', user_id)\
                .execute()
            
            if not groups_response.data:
                return []
            
            group_ids = [item['group_id'] for item in groups_response.data]
            
            # Then get test IDs for these groups
            tests_response = supabase.table('link_groups_tests')\
                .select('test_id')\
                .in_('group_id', group_ids)\
                .execute()
            
            test_ids = [item['test_id'] for item in tests_response.data] if tests_response.data else []
            return list(set(test_ids))  # Remove duplicates
            
        except Exception as e:
            print(f"Error getting user tests: {str(e)}")
            return []

    @staticmethod
    def get_user_campaign_ids(user_id):
        try:
            # First get user's group IDs
            groups_response = supabase.table('link_groups_users')\
                .select('group_id')\
                .eq('user_id', user_id)\
                .execute()
            
            if not groups_response.data:
                return []
            
            group_ids = [item['group_id'] for item in groups_response.data]
            
            # Then get campaign IDs for these groups
            campaigns_response = supabase.table('link_groups_campaigns')\
                .select('campaign_id')\
                .in_('group_id', group_ids)\
                .execute()
            
            campaign_ids = [item['campaign_id'] for item in campaigns_response.data] if campaigns_response.data else []
            return list(set(campaign_ids))  # Remove duplicates
            
        except Exception as e:
            print(f"Error getting user campaigns: {str(e)}")
            return [] 