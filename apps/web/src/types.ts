export type RecognitionState = 'ACCEPTED' | 'NEED_REPEAT' | 'NO_SIGN' | 'TRACKING_LOST' | 'UNSUPPORTED'

export interface TrackingInfo {
  left_hand: boolean
  right_hand: boolean
  pose: boolean
  face: boolean
  quality: number
}

export interface PredictionEvent {
  type: 'prediction'
  state: RecognitionState
  label?: string | null
  display_text?: string | null
  confidence: number
  alternatives: Array<{label:string; confidence:number}>
  tracking: TrackingInfo
  domain: string
  reason?: string | null
  latency_ms?: number | null
  model_version?: string | null
  feature_schema: string
  demo?: boolean
}

export interface TrackingEvent {
  type: 'tracking'
  tracking: TrackingInfo
  overlay: {left_hand:number[][]; right_hand:number[][]; pose:number[][]}
  landmark_latency_ms: number
}

export interface Health {
  status: string
  version: string
  model_loaded: boolean
  model_version?: string | null
  model_backend?: string
  model_source?: string
  model_is_bootstrap?: boolean
  model_vocabulary_size?: number
  model_error?: string | null
  perception_available: boolean
  perception_reason?: string | null
  database: string
  feature_schema: string
}

export interface TranscriptTurn {
  id: string
  source: 'ISL' | 'TEXT' | 'SPEECH' | 'DEMO'
  text: string
  confidence?: number
  at: number
}
