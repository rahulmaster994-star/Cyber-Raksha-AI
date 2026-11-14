package com.cyberraksha.ai.ui.onboarding

import android.os.Build
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.cyberraksha.ai.core.AppPreferences
import com.cyberraksha.ai.data.remote.NetworkModule
import com.cyberraksha.ai.data.repository.DeviceRepository
import com.cyberraksha.ai.data.repository.DiagnosticReport
import com.cyberraksha.ai.data.repository.HealthRepository
import com.cyberraksha.ai.data.repository.Result
import com.cyberraksha.ai.domain.usecase.RegisterDeviceUseCase
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
    val isTestingDiagnostics: Boolean = false
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
                    errorMessage = err
                )
            }
        }
    }

    fun registerDevice(onSuccess: () -> Unit) {
        val state = _uiState.value
        val normalizedUrl = NetworkModule.normalizeBaseUrl(state.backendUrl)
        val name = state.deviceName.trim().ifEmpty { "Android Device" }

        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true, errorMessage = null, diagnosticReport = null) }

            // 1. Save normalized URL to preferences
            prefs.saveBackendUrl(normalizedUrl)

            // 2. Perform deep diagnostic check
            val healthRepo = HealthRepository(NetworkModule.getApiService(normalizedUrl))
            val report = healthRepo.checkHealthDetailed(normalizedUrl)
            _uiState.update { it.copy(diagnosticReport = report) }

            if (!report.isHealthy) {
                val detailError = buildString {
                    if (report.exceptionType != null) {
                        append("${report.exceptionType}: ${report.exceptionMessage}")
                    } else if (report.httpStatusCode != null) {
                        append("HTTP ${report.httpStatusCode} from ${report.healthEndpointUrl}")
                    } else {
                        append("Cannot connect to backend")
                    }
                }
                _uiState.update {
                    it.copy(
                        isLoading = false,
                        errorMessage = detailError
                    )
                }
                return@launch
            }

            // 3. Register device using active API
            val api = NetworkModule.getApiService(normalizedUrl)
            val deviceRepo = DeviceRepository(api, prefs)
            val registerUseCase = RegisterDeviceUseCase(prefs, deviceRepo)
            val res = registerUseCase(name)

            when (res) {
                is Result.Success -> {
                    prefs.saveDeviceName(name)
                    prefs.setOnboardingComplete()
                    _uiState.update { it.copy(isLoading = false, isRegistered = true) }
                    onSuccess()
                }
                is Result.Error -> {
                    _uiState.update {
                        it.copy(
                            isLoading = false,
                            errorMessage = "Registration Failed: ${res.message}"
                        )
                    }
                }
            }
        }
    }
}

