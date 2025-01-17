export class CampaignAPI {
    static async generateLink(campaignId) {
        try {
            const response = await fetch(`/campaigns/${campaignId}/generate-link`, {
                method: 'POST'
            });
            
            if (!response.ok) {
                throw new Error('Failed to generate link');
            }
            
            const data = await response.json();
            return data.link;
        } catch (error) {
            console.error('Error generating link:', error);
            throw new Error('Wystąpił błąd podczas generowania linku');
        }
    }

    static async copyLink(campaignId) {
        try {
            const response = await fetch(`/campaigns/${campaignId}/link`);
            
            if (!response.ok) {
                throw new Error('Failed to get link');
            }
            
            const data = await response.json();
            return data.link;
        } catch (error) {
            console.error('Error getting link:', error);
            throw new Error('Wystąpił błąd podczas pobierania linku');
        }
    }

    static async deleteCampaign(campaignId) {
        try {
            const response = await fetch(`/campaigns/${campaignId}/delete`, {
                method: 'POST'
            });
            
            if (!response.ok) {
                throw new Error('Failed to delete campaign');
            }
            
            return true;
        } catch (error) {
            console.error('Error deleting campaign:', error);
            throw new Error('Wystąpił błąd podczas usuwania kampanii');
        }
    }

    static async duplicateCampaign(campaignId) {
        try {
            const response = await fetch(`/campaigns/${campaignId}/duplicate`, {
                method: 'POST'
            });
            
            if (!response.ok) {
                throw new Error('Failed to duplicate campaign');
            }
            
            return true;
        } catch (error) {
            console.error('Error duplicating campaign:', error);
            throw new Error('Wystąpił błąd podczas duplikowania kampanii');
        }
    }

    static async getCampaign(campaignId) {
        try {
            const response = await fetch(`/campaigns/${campaignId}/data`);
            
            if (!response.ok) {
                throw new Error('Failed to get campaign');
            }
            
            return await response.json();
        } catch (error) {
            console.error('Error getting campaign:', error);
            throw new Error('Wystąpił błąd podczas pobierania danych kampanii');
        }
    }

    static async getTestsByGroup(groupId) {
        try {
            const response = await fetch(`/campaigns/group/${groupId}/tests`);
            
            if (!response.ok) {
                throw new Error('Failed to get tests');
            }
            
            return await response.json();
        } catch (error) {
            console.error('Error getting tests:', error);
            throw new Error('Wystąpił błąd podczas pobierania testów');
        }
    }
} 