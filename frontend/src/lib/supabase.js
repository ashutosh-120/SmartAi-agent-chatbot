const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

// ── Safety Check ─────────────────────────────────────────────
// Prevent fatal crash if environment variables are missing in Render settings.
let supabaseClient = null;

if (!supabaseUrl || !supabaseAnonKey) {
  console.error('CRITICAL: Supabase environment variables are missing! Authentication and History features will be disabled. Please set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY in your Render dashboard.');
} else {
  try {
    supabaseClient = createClient(supabaseUrl, supabaseAnonKey);
  } catch (err) {
    console.error('CRITICAL: Failed to initialize Supabase client:', err);
  }
}

export const supabase = supabaseClient;
