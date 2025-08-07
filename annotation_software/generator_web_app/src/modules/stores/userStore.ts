// user state store
// Author: Michael B. Lance
// Created: June 16, 2025
// Updated: August 6, 2025
//---------------------------------------------------------------------------------------------------------------------------//

import { defineStore } from 'pinia';
import { authUser, checkAuth, getCurrentUser, getUserOrganizations } from '../apiV1Methods.ts';
import { User, Organization } from '@/types/generatorobjects.ts';
import { Checkbox } from 'primevue';

//---------------------------------------------------------------------------------------------------------------------------//

export const useUserStore = defineStore('userStore', {
    state: () => ({
        logged_in: false,
        user: undefined as User | undefined,
        organizations: undefined as Organization[] | undefined,
        organization_idx: undefined as number | undefined,
    }),
    getters: {
        CurrentOrganization: (state) => (state.organizations && state.organization_idx) ?  state.organizations[state.organization_idx] : undefined,
        CurrentUser: (state) => state.user
    },
    actions: {
        async authenticate(external_id: string) {
            this.user = await authUser(external_id) as User;
            this.logged_in = (this.user) ? true : false;
        },
        async get_current_user() {
            this.user = await getCurrentUser() as User;
        },
        async check_auth() {
            this.logged_in = (await checkAuth()) ? true : false;
        },
        async get_user_organizations() {
            this.organizations = await getUserOrganizations();
        },
        set_current_organization(org: Organization) {
            if (this.organizations) {
                const idx = this.organizations.indexOf(org);
                if (this.organization_idx == idx) {
                    this.organization_idx = undefined;
                    return;
                }
                this.organization_idx = idx;
            }
        },
        clear_state() {
            this.logged_in = false;
            this.user = undefined;
            this.organizations =undefined;
			this.organization_idx = undefined;
        }
    }, 
})



