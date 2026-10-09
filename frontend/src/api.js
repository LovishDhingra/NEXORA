// Every backend error uses { error: { code, message, fields } } – we turn it into one ApiError type.
export class ApiError extends Error {
  constructor(code, message, fields = {}, status = 0) {
    super(message);
    this.code = code;
    this.fields = fields;
    this.status = status;
  }
}

async function request(path, options = {}) {
  let response;
  try {
    response = await fetch(`/api${path}`, {
      headers: { "Content-Type": "application/json" },
      ...options,
    });
  } catch {
    throw new ApiError("network", "We can't reach the server. Check your connection and try again.");
  }

  let body = null;
  try {
    body = await response.json();
  } catch {
    /* non-JSON response */
  }

  if (!response.ok) {
    const e = body?.error;
    throw new ApiError(
      e?.code || "error",
      e?.message || "Something went wrong. Please try again.",
      e?.fields || {},
      response.status
    );
  }
  return body;
}

export const submitApplication = (data) =>
  request("/applications/", { method: "POST", body: JSON.stringify(data) });

export const changePin = (data) =>
  request("/cards/change-pin/", { method: "POST", body: JSON.stringify(data) });
