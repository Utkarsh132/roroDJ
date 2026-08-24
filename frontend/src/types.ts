export type CreativeRole = "dj" | "singer" | "producer" | "musician" | "general";

export type Message = {
  id: string;
  author: "user" | "assistant";
  content: string;
};

export type ChatResponse = {
  session_id: string;
  reply: string;
  role: CreativeRole;
  provider: string;
  profile: {
    role: CreativeRole;
    genres: string[];
    goals: string[];
    preferences: Record<string, string>;
  };
  suggested_actions: string[];
};

export type AudioAnalysis = {
  filename: string;
  metrics: {
    duration_seconds: number;
    sample_rate_hz: number;
    bpm: number | null;
    key_estimate: string | null;
    rms_dbfs: number;
    peak_dbfs: number;
    clipping_percent: number;
    silence_percent: number;
    spectral_centroid_hz: number | null;
  };
  warnings: string[];
  suggestions: string[];
};

