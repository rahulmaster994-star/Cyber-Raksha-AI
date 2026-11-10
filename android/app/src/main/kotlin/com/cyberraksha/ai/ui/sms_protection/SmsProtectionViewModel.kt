package com.cyberraksha.ai.ui.sms_protection

import android.content.Context
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.cyberraksha.ai.data.local.SmsAnalysisEntity
import com.cyberraksha.ai.data.remote.MessageAnalysisResponse
import com.cyberraksha.ai.data.repository.MobileProtectionRepository
import com.cyberraksha.ai.data.repository.Result
import com.cyberraksha.ai.domain.usecase.AnalyzeMessageUseCase
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

data class SmsProtectionUiState(
    val accessMode: SmsAccessMode = SmsAccessMode.MANUAL_ONLY,
    val inputText: String = "",
    val senderText: String = "",
    val isLoading: Boolean = false,
    val currentResult: MessageAnalysisResponse? = null,
    val errorMessage: String? = null,
    val history: List<SmsAnalysisEntity> = emptyList()
)

class SmsProtectionViewModel(
    private val repository: MobileProtectionRepository,
    private val analyzeMessageUseCase: AnalyzeMessageUseCase
) : ViewModel() {

    private val _uiState = MutableStateFlow(SmsProtectionUiState())
    val uiState: StateFlow<SmsProtectionUiState> = _uiState.asStateFlow()

    init {
        viewModelScope.launch {
            repository.getLocalAnalyses().collect { list ->
                _uiState.update { it.copy(history = list) }
            }
        }
    }

    fun updateAccessMode(context: Context) {
        val mode = SmsPermissionHelper.getSmsAccessMode(context)
        _uiState.update { it.copy(accessMode = mode) }
    }

    fun onInputTextChanged(text: String) {
        _uiState.update { it.copy(inputText = text, errorMessage = null) }
    }

    fun onSenderTextChanged(sender: String) {
        _uiState.update { it.copy(senderText = sender) }
    }

    fun analyzeCurrentMessage() {
        val text = _uiState.value.inputText.trim()
        if (text.isEmpty()) {
            _uiState.update { it.copy(errorMessage = "Please enter or paste an SMS message to analyze.") }
            return
        }

        val sender = _uiState.value.senderText.trim().ifEmpty { null }

        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true, errorMessage = null) }
            when (val result = analyzeMessageUseCase(text, sender)) {
                is Result.Success -> {
                    _uiState.update {
                        it.copy(
                            isLoading = false,
                            currentResult = result.data,
                            inputText = "",
                            senderText = ""
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

    fun clearResult() {
        _uiState.update { it.copy(currentResult = null) }
    }
}

