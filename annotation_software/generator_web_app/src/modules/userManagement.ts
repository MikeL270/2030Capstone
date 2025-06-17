// user state management layer
// Author: Michael B. Lance
// Created: June 16, 2025
// Updated: June 16, 2025
//---------------------------------------------------------------------------------------------------------------------------//

import { authUser } from './apiV1Methods.ts';
import { defineStore } from 'pinia';
import type { User } from '@/types/interfaces.ts';

//---------------------------------------------------------------------------------------------------------------------------//

export const useUserStore = defineStore('userStore', {
    state: () => ({
        logged_in: false,
        user: undefined as User | undefined,
    }),
    getters: {
        userName: (state) => state.logged_in ? state.user?.userName : undefined,
    },
    actions: {
        async authenticate(external_id: string): Promise<boolean> {
            try {
                const response = await authUser(external_id);
                const user = {
                    db_id: response['db_id'],
                    status: response['status'],
                    role: response['role'],
                    created: new Date(response['created']),
                    updated: new Date(response['updated']),
                    locale: response['locale'],
                    userName: response['userName']
                } as User;
            
            this.user = user;
            this.logged_in = true;
            return true
        } catch (error) {
            console.error("Failed to authenticate user: ", error);
            this.logged_in = false;
            this.user = undefined;
            return false
        }
        }
    },
})



