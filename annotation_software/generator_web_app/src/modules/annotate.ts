// Methods for approving predictions in the annotate vue component
// Author: Michael B. Lance
// Created: April 20, 2025
// Updated: April 20, 2025
//---------------------------------------------------------------------------------------------------------------------------//

import { Box, Image, Prediction, Crop } from '../types/generatorobjects';

const api_url: string = 'http://127.0.0.1:5000/api/v1/';

//---------------------------------------------------------------------------------------------------------------------------//

export async function fetchFromApi(endpoint: string): Promise<any> {
    try {
        const response = await(fetch(`${api_url}${endpoint}`))

        if (!response.ok) {
            throw new Error('You did something wrong! status ${response.status}')
        }

        const data = await response.json();
        return data;
    } catch (error) {
        console.error("There was an error fetching the data:", error)
        throw error;
    }
}

//---------------------------------------------------------------------------------------------------------------------------//

export async function createBatch(params: Record<string, any>): Promise<any> {
    try {
        const response = await fetch(`${api_url}create_batch`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(params),
        });

        if (!response.ok) {
            throw new Error('You did something wrong! status ${response.status}')
        }

        const data  = await response.json();
        return data;
    } catch (error: any) {
        console.error("There was an error fetching the data:", error)
        throw error;
    }
}

export default{};