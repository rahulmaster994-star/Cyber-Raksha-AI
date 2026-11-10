package com.cyberraksha.ai.ui.call_protection

import android.content.Context
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.cyberraksha.ai.data.remote.NumberCheckResponse
import com.cyberraksha.ai.data.repository.MobileProtectionRepository
import com.cyberraksha.ai.data.repository.Result
import com.cyberraksha.ai.domain.usecase.CheckNumberUseCase
import com.cyberraksha.ai.domain.usecase.ReportThreatUseCase
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

data class CallProtectionUiState(
    val screeningStatus: CallScreeningStatus = CallScreeningStatus.PERMISSION_REQUIRED,
    val inputNumber: String = "",
    val isLoading: Boolean = false,
    val checkResult: NumberCheckResponse? = null,
    val reportSuccessMessage: String? = null,
    val errorMessage: String? = null
)

class CallProtectionViewModel(
    private val checkNumberUseCase: CheckNumberUseCase,
    private val reportThreatUseCase: ReportThreatUseCase
) : ViewModel() {

    private val _uiState = MutableStateFlow(CallProtectionUiState())
    val uiState: StateFlow<CallProtectionUiState> = _uiState.asStateFlow()

    fun updateStatus(context: Context) {
        val status = CallScreeningHelper.getScreeningStatus(context)
        _uiState.update { it.copy(screeningStatus = status) }
    }

    fun onInputNumberChanged(number: String) {
        _uiState.update { it.copy(inputNumber = number, errorMessage = null, reportSuccessMessage = null) }
    }

    fun checkNumberReputation() {
        val number = _uiState.value.inputNumber.trim()
        if (number.isEmpty()) {
            _uiState.update { it.copy(errorMessage = "Please enter a phone number to check.") }
            return
        }

        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true, errorMessage = null, reportSuccessMessage = null) }
            when (val result = checkNumberUseCase(number)) {
                is Result.Success -> {
                    _uiState.update {
                        it.copy(
                            isLoading = false,
                            checkResult = result.data
                        )
                    }
                }
                is Result.Error -> {
                    _uiState.update {
                        it.copy(
                            isLoading = false,
                            errorMessage = result.message
                        )
                    }
                }
            }
        }
    }

    fun reportCurrentNumber(category: String, notes: String) {
        val number = _uiState.value.checkResult?.normalizedNumber
            ?: _uiState.value.inputNumber.trim()

        if (number.isEmpty()) return

        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true) }
            when (val result = reportThreatUseCase("PHONE_NUMBER", number, category, notes)) {
                is Result.Success -> {
                    _uiState.update {
                        it.copy(
                            isLoading = false,
                            reportSuccessMessage = "Number successfully reported to community database."
                        )
                    }
                    // Re-check reputation to see updated count
                    checkNumberUseCase(number).let { res ->
                        if (res is Result.Success) {
                            _uiState.update { it.copy(checkResult = res.data) }
                        }
                    }
                }
                is Result.Error -> {
                    _uiState.update {
                        it.copy(
                            isLoading = false,
                            errorMessage = result.message
                        )
                    }
                }
            }
        }
    }

    fun clearResult() {
        _uiState.update { it.copy(checkResult = null, reportSuccessMessage = null) }
    }
}

