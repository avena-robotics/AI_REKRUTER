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

    @staticmethod
    def get_user_available_groups(user_id):
        """Get groups that user has access to"""
        try:
            response = supabase.table('link_groups_users')\
                .select('groups(*)')\
                .eq('user_id', user_id)\
                .execute()
            
            groups = [item['groups'] for item in response.data] if response.data else []
            print(f"Available groups for user {user_id}: {groups}")  # Debug log
            return groups
        except Exception as e:
            print(f"Error getting user available groups: {str(e)}")
            return []

    @staticmethod
    def get_test_groups(test_id, user_id):
        """Get groups for a test that user has access to"""
        try:
            # Get user's groups first
            user_groups = GroupService.get_user_available_groups(user_id)
            user_group_ids = [g['id'] for g in user_groups]
            
            # Then get test's groups filtered by user's access
            response = supabase.table('link_groups_tests')\
                .select('group_id')\
                .eq('test_id', test_id)\
                .in_('group_id', user_group_ids)\
                .execute()
            
            groups = [item['group_id'] for item in response.data] if response.data else []
            print(f"Groups for test {test_id}: {groups}")  # Debug log
            return groups
        except Exception as e:
            print(f"Error getting test groups: {str(e)}")
            return [] 