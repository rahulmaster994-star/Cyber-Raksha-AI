package com.cyberraksha.ai.ui.onboarding

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.net.VpnService
import android.os.Build
import android.os.PowerManager
import androidx.core.app.NotificationManagerCompat
import androidx.core.content.ContextCompat
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.cyberraksha.ai.core.AppPreferences
import com.cyberraksha.ai.data.remote.NetworkModule
import com.cyberraksha.ai.data.repository.DeviceRepository
import com.cyberraksha.ai.data.repository.DiagnosticReport
import com.cyberraksha.ai.data.repository.HealthRepository
import com.cyberraksha.ai.data.repository.Result
import com.cyberraksha.ai.domain.usecase.RegisterDeviceUseCase
import com.cyberraksha.ai.ui.call_protection.CallScreeningHelper
import com.cyberraksha.ai.ui.call_protection.CallScreeningStatus
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.firstOrNull
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

data class OnboardingUiState(
    val currentStep: Int = 0,
    val deviceName: String = "${Build.MANUFACTURER} ${Build.MODEL}".trim(),
    val backendUrl: String = AppPreferences.DEFAULT_BACKEND_URL,
    val isLoading: Boolean = false,
    val errorMessage: String? = null,
    val isRegistered: Boolean = false,
    val diagnosticReport: DiagnosticReport? = null,
    val isTestingDiagnostics: Boolean = false,

    // Real-Time Permission & Protection Status Dashboard
    val isSmsActive: Boolean = false,
    val isNotificationsGranted: Boolean = false,
    val isWhatsAppActive: Boolean = false,
    val isTelegramActive: Boolean = false,
    val isCallActive: Boolean = false,
    val isDnsActive: Boolean = false,
    val isBatteryOptimizedIgnored: Boolean = false,
    val isBackendConnected: Boolean = false,
    val backendLatencyMs: Long? = null
)

class OnboardingViewModel(
    private val prefs: AppPreferences
) : ViewModel() {

    private val _uiState = MutableStateFlow(OnboardingUiState())
    val uiState: StateFlow<OnboardingUiState> = _uiState.asStateFlow()

    init {
        viewModelScope.launch {
            val savedUrl = prefs.backendUrl.firstOrNull() ?: AppPreferences.DEFAULT_BACKEND_URL
            val savedName = prefs.deviceName.firstOrNull() ?: "${Build.MANUFACTURER} ${Build.MODEL}".trim()
            _uiState.update { it.copy(backendUrl = savedUrl, deviceName = savedName) }
            checkBackendHealth()
        }
    }

    fun refreshPermissionState(context: Context) {
        val hasSms = ContextCompat.checkSelfPermission(context, Manifest.permission.RECEIVE_SMS) == PackageManager.PERMISSION_GRANTED
        val hasNotif = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            ContextCompat.checkSelfPermission(context, Manifest.permission.POST_NOTIFICATIONS) == PackageManager.PERMISSION_GRANTED
        } else {
            NotificationManagerCompat.from(context).areNotificationsEnabled()
        }
        val hasNotifListener = NotificationManagerCompat.getEnabledListenerPackages(context).contains(context.packageName)
        val hasCallRole = CallScreeningHelper.getScreeningStatus(context) == CallScreeningStatus.ACTIVE
        val vpnReady = VpnService.prepare(context) == null
        val powerManager = context.getSystemService(Context.POWER_SERVICE) as? PowerManager
        val batteryIgnored = powerManager?.isIgnoringBatteryOptimizations(context.packageName) ?: false

        _uiState.update {
            it.copy(
                isSmsActive = hasSms,
                isNotificationsGranted = hasNotif,
                isWhatsAppActive = hasNotifListener,
                isTelegramActive = hasNotifListener,
                isCallActive = hasCallRole,
                isDnsActive = vpnReady,
                isBatteryOptimizedIgnored = batteryIgnored
            )
        }

        checkBackendHealth()
    }

    fun checkBackendHealth() {
        val url = NetworkModule.normalizeBaseUrl(_uiState.value.backendUrl)
        viewModelScope.launch {
            try {
                val api = NetworkModule.getApiService(url)
                val startTime = System.currentTimeMillis()
                val resp = api.getHealth()
                val latency = System.currentTimeMillis() - startTime
                val isOk = resp.isSuccessful && resp.body()?.status == "healthy"
                _uiState.update {
                    it.copy(
                        isBackendConnected = isOk,
                        backendLatencyMs = if (isOk) latency else null
                    )
                }
            } catch (_: Exception) {
                _uiState.update { it.copy(isBackendConnected = false, backendLatencyMs = null) }
            }
        }
    }

    fun nextStep() {
        if (_uiState.value.currentStep < 2) {
            _uiState.update { it.copy(currentStep = it.currentStep + 1, errorMessage = null) }
        }
    }

    fun prevStep() {
        if (_uiState.value.currentStep > 0) {
            _uiState.update { it.copy(currentStep = it.currentStep - 1, errorMessage = null) }
        }
    }

    fun onDeviceNameChanged(name: String) {
        _uiState.update { it.copy(deviceName = name) }
    }

    fun onBackendUrlChanged(url: String) {
        _uiState.update { it.copy(backendUrl = url, errorMessage = null) }
    }

    fun runDiagnostics() {
        val state = _uiState.value
        val url = NetworkModule.normalizeBaseUrl(state.backendUrl)
        viewModelScope.launch {
            _uiState.update { it.copy(isTestingDiagnostics = true, errorMessage = null) }
            val healthRepo = HealthRepository(NetworkModule.getApiService(url))
            val report = healthRepo.checkHealthDetailed(url)
            val err = if (!report.isHealthy) {
                "${report.exceptionType ?: "HTTP ${report.httpStatusCode}"}: ${report.exceptionMessage ?: "Diagnostic failed"}"
            } else null

            _uiState.update {
                it.copy(
                    isTestingDiagnostics = false,
                    diagnosticReport = report,
                    errorMessage = err,
                    isBackendConnected = report.isHealthy,
                    backendLatencyMs = if (report.isHealthy) report.latencyMs else null
                )
            }
        }
    }

    fun completeOnboardingAndRegister(onSuccess: () -> Unit) {
        val state = _uiState.value
        val normalizedUrl = NetworkModule.normalizeBaseUrl(state.backendUrl)
        val name = state.deviceName.trim().ifEmpty { "${Build.MANUFACTURER} ${Build.MODEL}".trim() }

        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true, errorMessage = null) }
            prefs.saveBackendUrl(normalizedUrl)
            prefs.saveDeviceName(name)

            // Register device in backend
            try {
                val api = NetworkModule.getApiService(normalizedUrl)
                val deviceRepo = DeviceRepository(api, prefs)
                val registerUseCase = RegisterDeviceUseCase(prefs, deviceRepo)
                registerUseCase(name)
            } catch (_: Exception) {}

            prefs.setOnboardingComplete()
            _uiState.update { it.copy(isLoading = false, isRegistered = true) }
            onSuccess()
        }
    }
}
