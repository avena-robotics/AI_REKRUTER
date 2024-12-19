from supabase import create_client
from common.config import Config

config = Config.instance()

supabase = create_client(
    config.SUPABASE_URL,
    config.SUPABASE_KEY
) 