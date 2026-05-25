
export const API_URL = 'http://localhost:5000';
//export const API_URL = 'http://aquarii.eic.cefet-rj.br/quintana-api'
export const APP_MODE = process.env.NEXT_PUBLIC_APP_MODE || 'demo';
export const IS_WORKSHOP_MODE = APP_MODE === 'workshop';
export const APP_VERSION = process.env.NEXT_PUBLIC_APP_VERSION || '1.0.0';


