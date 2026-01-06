const BASE = "http://localhost:8000";

export async function chat(payload: any) {
  // We use fetch directly in App.tsx for streaming, 
  // but keep this for non-streaming calls if needed.
  const r = await fetch(`${BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  return r.json();
}