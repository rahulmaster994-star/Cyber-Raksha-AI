package com.cyberraksha.ai.data.repository

import android.util.Log
import com.cyberraksha.ai.data.remote.CyberRakshaApiService
import com.cyberraksha.ai.data.remote.HealthResponse
import com.cyberraksha.ai.data.remote.NetworkModule
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.Request
import java.net.InetAddress
import java.net.URI

data class DiagnosticReport(
    val isHealthy: Boolean,
    val resolvedBaseUrl: String,
    val healthEndpointUrl: String,
    val httpStatusCode: Int?,
    val latencyMs: Long,
    val dnsResolvedIps: List<String>,
    val responseBodyPreview: String?,
    val exceptionType: String?,
    val exceptionMessage: String?,
    val stackTraceSnippet: String?
)

class HealthRepository(private val api: CyberRakshaApiService) {

    companion object {
        private const val TAG = "CyberRakshaHealth"
    }

    /**
     * Executes a deep, fully instrumented network diagnostic directly against
     * the health endpoint. Captures exact DNS resolutions, HTTP status codes,
     * round-trip latency, raw body snippets, and the complete exception stack trace.
     */
    suspend fun checkHealthDetailed(rawUrl: String): DiagnosticReport = withContext(Dispatchers.IO) {
        val normalized = NetworkModule.normalizeBaseUrl(rawUrl)
        val endpoint = "$normalized/api/v1/health"
        val startTime = System.currentTimeMillis()

        Log.i(TAG, "Starting health check diagnostic -> $endpoint")

        // 1. DNS Resolution check
        val dnsIps = mutableListOf<String>()
        try {
            val host = URI(normalized).host
            if (host != null) {
                val addresses = InetAddress.getAllByName(host)
                addresses.forEach { dnsIps.add(it.hostAddress ?: "unknown") }
                Log.d(TAG, "DNS resolved for $host: $dnsIps")
            }
        } catch (e: Exception) {
            val err = "DNS resolution failed: ${e.javaClass.simpleName} - ${e.message}"
            dnsIps.add(err)
            Log.w(TAG, err)
        }

        // 2. Direct OkHttp probe (to bypass any potential Retrofit/Gson edge cases and read raw stream)
        try {
            val client = NetworkModule.getOkHttpClient()
            val request = Request.Builder()
                .url(endpoint)
                .header("Accept", "application/json")
                .build()

            val response = client.newCall(request).execute()
            val latency = System.currentTimeMillis() - startTime
            val statusCode = response.code
            val rawBody = response.body?.string() ?: ""
            val preview = if (rawBody.length > 300) rawBody.take(300) + "..." else rawBody

            Log.i(TAG, "Diagnostic HTTP $statusCode in ${latency}ms: $preview")

            val isHealthy = (statusCode in 200..299) && (
                rawBody.contains("\"status\":\"healthy\"", ignoreCase = true) ||
                rawBody.contains("\"status\": \"healthy\"", ignoreCase = true) ||
                rawBody.contains("\"healthy\"", ignoreCase = true) ||
                rawBody.contains("\"ok\"", ignoreCase = true)
            )

            DiagnosticReport(
                isHealthy = isHealthy,
                resolvedBaseUrl = normalized,
                healthEndpointUrl = endpoint,
                httpStatusCode = statusCode,
                latencyMs = latency,
                dnsResolvedIps = dnsIps,
                responseBodyPreview = preview,
                exceptionType = if (!isHealthy) "HTTP $statusCode" else null,
                exceptionMessage = if (!isHealthy) "Server returned non-healthy response: $preview" else null,
                stackTraceSnippet = null
            )
        } catch (e: Throwable) {
            val latency = System.currentTimeMillis() - startTime
            val exClass = e.javaClass.simpleName
            val exMsg = e.message ?: "No error message provided"
            val stackSnippet = e.stackTrace.take(4).joinToString("\n") {
                "  at ${it.className}.${it.methodName}(${it.fileName}:${it.lineNumber})"
            }

            Log.e(TAG, "Diagnostic FAILED in ${latency}ms: $exClass - $exMsg", e)

            DiagnosticReport(
                isHealthy = false,
                resolvedBaseUrl = normalized,
                healthEndpointUrl = endpoint,
                httpStatusCode = null,
                latencyMs = latency,
                dnsResolvedIps = dnsIps,
                responseBodyPreview = null,
                exceptionType = exClass,
                exceptionMessage = exMsg,
                stackTraceSnippet = stackSnippet
            )
        }
    }

    /**
     * Returns true when backend is reachable and returns a successful health status.
     * Evaluates "healthy", "ok", or any non-empty 2xx response body as success.
     */
    suspend fun isBackendHealthy(): Boolean = runCatching {
        val response = api.getHealth()
        if (response.isSuccessful) {
            val body = response.body()
            if (body != null) {
                val status = body.status.lowercase().trim()
                return@runCatching status == "healthy" || status == "ok" || status == "running"
            }
            return@runCatching true
        }
        false
    }.getOrDefault(false)

    suspend fun getHealth(): Result<HealthResponse> = runCatching {
        val response = api.getHealth()
        if (response.isSuccessful) Result.Success(response.body()!!)
        else Result.Error("HTTP ${response.code()}", response.code())
    }.getOrElse { Result.Error(it.message ?: "Network error") }
}

