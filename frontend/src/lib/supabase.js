import { createClient } from '@supabase/supabase-js';
const envUrl = import.meta.env.VITE_SUPABASE_URL;
const envKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

// ── Failsafe Initialization ─────────────────────────────────
// Ensures the app works even if Render environment variables are missing or 'undefined'
const supabaseUrl = (envUrl && envUrl !== 'undefined') ? envUrl : 'https://bmlcjfhdzqumcfbsdxti.supabase.co';
const supabaseAnonKey = (envKey && envKey !== 'undefined') ? envKey : 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJtbGNqZmhkenF1bWNmYnNkeHRpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ3ODM1ODYsImV4cCI6MjA5MDM1OTU4Nn0.JQi6GEnL4sfZzNZqMuCIGa2vlQm0wNHJITIwoDGExLk';

// ── Safety Check ─────────────────────────────────────────────
// Prevent fatal crash if environment variables are missing in Render settings.
let supabaseClient = null;

if (!supabaseUrl || !supabaseAnonKey) {
  console.error('CRITICAL: Supabase keys are missing! Authentication and History features will be disabled.');
} else {
  try {
    supabaseClient = createClient(supabaseUrl, supabaseAnonKey);
  } catch (err) {
    console.error('CRITICAL: Failed to initialize Supabase client:', err);
  }
}

export const supabase = supabaseClient;
