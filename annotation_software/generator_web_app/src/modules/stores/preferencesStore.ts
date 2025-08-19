// Preference state store 
// Author: Michael B. Lance
// Created: August 15, 2025
// Updated: August 15, 2025
//---------------------------------------------------------------------------------------------------------------------------//

import { defineStore } from "pinia";

export const usePreferenceStore = defineStore('preferenceStore', {
	state: () => ({
		first_login: true, // default to true until set otherwise
		theme: 'light-theme',

	}),
	persist: {
		key: 'user-preferences'
	},
	actions: {
		getBrowserPreference() {
			const hasDarkPreference = window.matchMedia(
        		'(prefers-color-scheme: dark)'
      		).matches;
      		if (hasDarkPreference) {
      		  return 'dark-theme';
      		} else {
       		return 'light-theme';
      		}
		},
		setTheme(theme: string) {
			this.theme = theme;
			document.documentElement.className = theme;
		},
		toggleTheme() {
			this.theme = (this.theme == 'light-theme') ? 'dark-theme' : 'light-theme';
			document.documentElement.className = this.theme;
		}
	}
})