-- Add interview email columns to campaigns table
ALTER TABLE campaigns
ADD COLUMN interview_email_subject text,
ADD COLUMN interview_email_content text;

-- Add comment to describe the columns
COMMENT ON COLUMN campaigns.interview_email_subject IS 'Subject for interview invitation email';
COMMENT ON COLUMN campaigns.interview_email_content IS 'Content template for interview invitation email'; 