export const API_URL = process.env.NEXT_PUBLIC_API_URL || '/api';

export const APP_MODE = process.env.NEXT_PUBLIC_APP_MODE || 'demo';
export const IS_WORKSHOP_MODE = APP_MODE === 'workshop';
export const APP_VERSION = process.env.NEXT_PUBLIC_APP_VERSION || '1.0.0';