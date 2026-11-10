package com.cyberraksha.ai.ui.onboarding

import android.os.Build
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.cyberraksha.ai.core.AppPreferences
import com.cyberraksha.ai.data.remote.NetworkModule
import com.cyberraksha.ai.data.repository.DeviceRepository
import com.cyberraksha.ai.data.repository.HealthRepository
import com.cyberraksha.ai.data.repository.Result
import com.cyberraksha.ai.domain.usecase.RegisterDeviceUseCase
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

data class OnboardingUiState(
    val currentStep: Int = 0,
    val deviceName: String = "${Build.MANUFACTURER} ${Build.MODEL}".trim(),
    val backendUrl: String = AppPreferences.DEFAULT_BACKEND_URL,
    val isLoading: Boolean = false,
    val errorMessage: String? = null,
    val isRegistered: Boolean = false
)

class OnboardingViewModel(
    private val prefs: AppPreferences
) : ViewModel() {

    private val _uiState = MutableStateFlow(OnboardingUiState())
    val uiState: StateFlow<OnboardingUiState> = _uiState.asStateFlow()

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
        _uiState.update { it.copy(backendUrl = url) }
    }

    fun registerDevice(onSuccess: () -> Unit) {
        val state = _uiState.value
        val url = state.backendUrl.trim()
        val name = state.deviceName.trim().ifEmpty { "Android Device" }

        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true, errorMessage = null) }

            // 1. Save configured URL
            prefs.saveBackendUrl(url)

            // 2. Test connectivity
            val api = NetworkModule.createApiService(url)
            val healthRepo = HealthRepository(api)
            val isHealthy = healthRepo.isBackendHealthy()

            if (!isHealthy) {
                _uiState.update {
                    it.copy(
                        isLoading = false,
                        errorMessage = "Cannot reach Cyber Raksha backend at $url. Ensure server is running and accessible."
                    )
                }
                return@launch
            }

            // 3. Register device
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
                            errorMessage = res.message
                        )
                    }
                }
            }
        }
    }
}

