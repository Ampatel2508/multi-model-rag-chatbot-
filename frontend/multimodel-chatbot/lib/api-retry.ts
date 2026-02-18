/**
 * API retry utilities with exponential backoff for handling rate limits
 */

interface RetryOptions {
  maxRetries?: number;
  initialDelay?: number;
  maxDelay?: number;
  backoffMultiplier?: number;
}

const DEFAULT_OPTIONS: Required<RetryOptions> = {
  maxRetries: 3,
  initialDelay: 1000, // 1 second
  maxDelay: 10000, // 10 seconds
  backoffMultiplier: 2,
};

/**
 * Retry a fetch request with exponential backoff
 * Useful for handling rate limits (429) and temporary failures
 * BUT: Skips retries for exhausted quotas (limit: 0)
 */
export async function fetchWithRetry(
  url: string,
  options: RequestInit & RetryOptions = {}
): Promise<Response> {
  const {
    maxRetries = DEFAULT_OPTIONS.maxRetries,
    initialDelay = DEFAULT_OPTIONS.initialDelay,
    maxDelay = DEFAULT_OPTIONS.maxDelay,
    backoffMultiplier = DEFAULT_OPTIONS.backoffMultiplier,
    ...fetchOptions
  } = options;

  let lastError: Error | null = null;
  let delay = initialDelay;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      const response = await fetch(url, fetchOptions);

      // Success or non-retryable error
      if (response.ok || !isRetryableStatus(response.status)) {
        return response;
      }

      // Check if this is a quota exhaustion error (limit: 0)
      // If so, don't retry - it won't help
      if (response.status === 429) {
        try {
          const text = await response.clone().text();
          if (text.includes("limit: 0") || text.includes("limit\": 0")) {
            // Quota completely exhausted, return immediately
            console.warn("[Retry] Quota completely exhausted (limit: 0). Returning immediately without retry.");
            return response;
          }
        } catch (e) {
          // If we can't read response, proceed with retry logic
        }
      }

      // Retryable error (429, 503, etc.)
      if (attempt < maxRetries) {
        console.warn(
          `[Retry] Attempt ${attempt + 1}/${maxRetries + 1}: Status ${response.status}. Waiting ${delay}ms before retry...`
        );
        await sleep(delay);
        delay = Math.min(delay * backoffMultiplier, maxDelay);
      } else {
        // Last attempt failed with retryable status
        return response;
      }
    } catch (error) {
      lastError = error as Error;

      if (attempt < maxRetries) {
        console.warn(
          `[Retry] Attempt ${attempt + 1}/${maxRetries + 1}: ${lastError.message}. Waiting ${delay}ms before retry...`
        );
        await sleep(delay);
        delay = Math.min(delay * backoffMultiplier, maxDelay);
      } else {
        throw lastError;
      }
    }
  }

  throw lastError || new Error("Max retries exceeded");
}

/**
 * Check if a status code is retryable
 */
function isRetryableStatus(status: number): boolean {
  // 429 = Too Many Requests (rate limit)
  // 503 = Service Unavailable
  // 504 = Gateway Timeout
  return status === 429 || status === 503 || status === 504;
}

/**
 * Sleep for a given duration
 */
function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Extract retry-after delay from response headers if available
 */
export function getRetryAfterDelay(response: Response): number | null {
  const retryAfter = response.headers.get("Retry-After");
  if (!retryAfter) return null;

  // Retry-After can be in seconds or an HTTP date
  const seconds = parseInt(retryAfter, 10);
  if (!isNaN(seconds)) {
    return seconds * 1000;
  }

  // Try parsing as HTTP date
  const date = new Date(retryAfter);
  if (!isNaN(date.getTime())) {
    return Math.max(0, date.getTime() - Date.now());
  }

  return null;
}
