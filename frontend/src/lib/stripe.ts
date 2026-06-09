import Stripe from 'stripe';

export const stripe = new Stripe((process.env.STRIPE_SECRET_KEY || 'dummy_key_for_build') as string, {
  apiVersion: '2026-05-27.dahlia',
  appInfo: {
    name: 'AgenticGTM',
    version: '0.1.0',
  },
});
