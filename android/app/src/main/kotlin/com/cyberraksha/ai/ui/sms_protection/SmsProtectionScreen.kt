package com.cyberraksha.ai.ui.sms_protection

import android.app.Activity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.cyberraksha.ai.data.local.SmsAnalysisEntity
import com.cyberraksha.ai.data.remote.MessageAnalysisResponse
import com.cyberraksha.ai.ui.theme.*

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SmsProtectionScreen(
    viewModel: SmsProtectionViewModel,
    onBack: () -> Unit
) {
    val context = LocalContext.current
    val state by viewModel.uiState.collectAsState()

    val roleLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.StartActivityForResult()
    ) {
        viewModel.updateAccessMode(context)
    }

    LaunchedEffect(Unit) {
        viewModel.updateAccessMode(context)
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Icon(
                            imageVector = Icons.Default.Sms,
                            contentDescription = null,
                            tint = CyberCyan,
                            modifier = Modifier.size(24.dp)
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        Text(
                            "SMS Fraud Protection",
                            style = MaterialTheme.typography.titleMedium,
                            fontWeight = FontWeight.Bold,
                            color = TextPrimary
                        )
                    }
                },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.Default.ArrowBack, contentDescription = "Back", tint = TextPrimary)
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = DarkSurface)
            )
        },
        containerColor = DarkBackground
    ) { padding ->
        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(horizontal = 16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            item { Spacer(modifier = Modifier.height(8.dp)) }

            // 1. Status Banner
            item {
                StatusBanner(
                    accessMode = state.accessMode,
                    onRequestRole = {
                        val intent = SmsPermissionHelper.createRequestRoleIntent(context)
                        if (intent != null) {
                            roleLauncher.launch(intent)
                        }
                    }
                )
            }

            // 2. Input / Manual Scan Card
            item {
                ManualScanCard(
                    messageText = state.inputText,
                    senderText = state.senderText,
                    isLoading = state.isLoading,
                    errorMessage = state.errorMessage,
                    onMessageChange = viewModel::onInputTextChanged,
                    onSenderChange = viewModel::onSenderTextChanged,
                    onAnalyze = viewModel::analyzeCurrentMessage
                )
            }

            // 3. Current Analysis Result Card
            if (state.currentResult != null) {
                item {
                    AnalysisResultCard(
                        result = state.currentResult!!,
                        onDismiss = viewModel::clearResult
                    )
                }
            }

            // 4. Recent Local History Header
            item {
                Text(
                    text = "Recent Message Inspections",
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.SemiBold,
                    color = TextPrimary
                )
            }

            if (state.history.isEmpty()) {
                item {
                    Card(
                        modifier = Modifier.fillMaxWidth(),
                        colors = CardDefaults.cardColors(containerColor = DarkSurface),
                        shape = RoundedCornerShape(12.dp)
                    ) {
                        Box(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(20.dp),
                            contentAlignment = Alignment.Center
                        ) {
                            Text(
                                "No inspected messages yet. Enter an SMS above to test.",
                                style = MaterialTheme.typography.bodyMedium,
                                color = TextSecondary
                            )
                        }
                    }
                }
            } else {
                items(state.history) { item ->
                    HistoryItemCard(item)
                }
            }

            item { Spacer(modifier = Modifier.height(24.dp)) }
        }
    }
}

@Composable
private fun StatusBanner(
    accessMode: SmsAccessMode,
    onRequestRole: () -> Unit
) {
    val (statusTitle, statusDesc, color, showAction) = when (accessMode) {
        SmsAccessMode.ROLE_DEFAULT_SMS -> Quad(
            "AUTOMATIC SCREENING ACTIVE",
            "App holds default SMS handler role. Incoming messages evaluated in real-time.",
            SeverityLow,
            false
        )
        SmsAccessMode.PERMISSION_GRANTED -> Quad(
            "RUNTIME PERMISSION ACTIVE",
            "Monitoring messages via standard telephony permissions.",
            SeverityLow,
            false
        )
        SmsAccessMode.MANUAL_ONLY -> Quad(
            "MANUAL INSPECTION MODE",
            "Automatic SMS access not granted. Use manual scanner below or enable role.",
            SeverityMedium,
            true
        )
        SmsAccessMode.NOT_SUPPORTED -> Quad(
            "MANUAL SCANNER",
            "Direct SMS access not available on this device architecture.",
            TextSecondary,
            false
        )
    }

    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = DarkSurface),
        shape = RoundedCornerShape(14.dp)
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Box(
                    modifier = Modifier
                        .size(10.dp)
                        .clip(CircleShape)
                        .background(color)
                )
                Spacer(modifier = Modifier.width(8.dp))
                Text(
                    text = statusTitle,
                    style = MaterialTheme.typography.labelMedium,
                    fontWeight = FontWeight.Bold,
                    color = color
                )
            }
            Spacer(modifier = Modifier.height(6.dp))
            Text(
                text = statusDesc,
                style = MaterialTheme.typography.bodySmall,
                color = TextSecondary
            )

            if (showAction) {
                Spacer(modifier = Modifier.height(10.dp))
                OutlinedButton(
                    onClick = onRequestRole,
                    colors = ButtonDefaults.outlinedButtonColors(contentColor = CyberCyan),
                    border = ButtonDefaults.outlinedButtonBorder.copy(brush = androidx.compose.ui.graphics.SolidColor(CyberCyan))
                ) {
                    Text("Enable Automatic Interceptor", fontSize = 12.sp)
                }
            }
        }
    }
}

@Composable
private fun ManualScanCard(
    messageText: String,
    senderText: String,
    isLoading: Boolean,
    errorMessage: String?,
    onMessageChange: (String) -> Unit,
    onSenderChange: (String) -> Unit,
    onAnalyze: () -> Unit
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = DarkSurface),
        shape = RoundedCornerShape(14.dp)
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text(
                "Inspect Suspicious Message",
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.SemiBold,
                color = TextPrimary
            )
            Spacer(modifier = Modifier.height(4.dp))
            Text(
                "Paste suspicious banking, delivery, or lottery message text for heuristic risk scoring.",
                style = MaterialTheme.typography.labelSmall,
                color = TextSecondary
            )

            Spacer(modifier = Modifier.height(12.dp))

            OutlinedTextField(
                value = senderText,
                onValueChange = onSenderChange,
                label = { Text("Sender Header (Optional, e.g. +91... or VM-HDFCBK)") },
                modifier = Modifier.fillMaxWidth(),
                singleLine = true,
                colors = OutlinedTextFieldDefaults.colors(
                    focusedBorderColor = CyberCyan,
                    unfocusedBorderColor = DarkOutline,
                    focusedTextColor = TextPrimary,
                    unfocusedTextColor = TextPrimary
                )
            )

            Spacer(modifier = Modifier.height(8.dp))

            OutlinedTextField(
                value = messageText,
                onValueChange = onMessageChange,
                label = { Text("Message Content") },
                modifier = Modifier
                    .fillMaxWidth()
                    .height(120.dp),
                maxLines = 6,
                colors = OutlinedTextFieldDefaults.colors(
                    focusedBorderColor = CyberCyan,
                    unfocusedBorderColor = DarkOutline,
                    focusedTextColor = TextPrimary,
                    unfocusedTextColor = TextPrimary
                )
            )

            if (errorMessage != null) {
                Spacer(modifier = Modifier.height(6.dp))
                Text(
                    text = errorMessage,
                    color = SeverityCritical,
                    style = MaterialTheme.typography.labelSmall
                )
            }

            Spacer(modifier = Modifier.height(14.dp))

            Button(
                onClick = onAnalyze,
                enabled = !isLoading && messageText.isNotBlank(),
                modifier = Modifier.fillMaxWidth(),
                colors = ButtonDefaults.buttonColors(containerColor = CyberCyan),
                shape = RoundedCornerShape(10.dp)
            ) {
                if (isLoading) {
                    CircularProgressIndicator(modifier = Modifier.size(20.dp), color = DarkBackground, strokeWidth = 2.dp)
                } else {
                    Icon(Icons.Default.Search, contentDescription = null, tint = DarkBackground)
                    Spacer(modifier = Modifier.width(8.dp))
                    Text("Analyze Threat Vectors", color = DarkBackground, fontWeight = FontWeight.Bold)
                }
            }
        }
    }
}

@Composable
private fun AnalysisResultCard(
    result: MessageAnalysisResponse,
    onDismiss: () -> Unit
) {
    val riskColor = when (result.riskLevel.uppercase()) {
        "CRITICAL" -> SeverityCritical
        "HIGH" -> SeverityHigh
        "MEDIUM" -> SeverityMedium
        else -> SeverityLow
    }

    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = DarkSurface),
        shape = RoundedCornerShape(14.dp)
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Surface(
                    color = riskColor.copy(alpha = 0.2f),
                    shape = RoundedCornerShape(8.dp)
                ) {
                    Text(
                        text = "${result.riskLevel} RISK (${result.riskScore.toInt()}%)",
                        color = riskColor,
                        fontWeight = FontWeight.Bold,
                        fontSize = 12.sp,
                        modifier = Modifier.padding(horizontal = 10.dp, vertical = 4.dp)
                    )
                }

                IconButton(onClick = onDismiss, modifier = Modifier.size(24.dp)) {
                    Icon(Icons.Default.Close, contentDescription = "Dismiss", tint = TextSecondary)
                }
            }

            Spacer(modifier = Modifier.height(10.dp))
            Text(
                text = "Category: ${result.fraudCategory.replace('_', ' ')}",
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.Bold,
                color = TextPrimary
            )

            Spacer(modifier = Modifier.height(8.dp))
            Text(
                text = "Evidence & Findings:",
                style = MaterialTheme.typography.labelMedium,
                fontWeight = FontWeight.SemiBold,
                color = TextSecondary
            )

            result.detectionReasons.forEach { reason ->
                Row(modifier = Modifier.padding(vertical = 2.dp)) {
                    Text("• ", color = CyberCyan)
                    Text(reason, style = MaterialTheme.typography.bodySmall, color = TextPrimary)
                }
            }

            if (result.extractedUrls.isNotEmpty()) {
                Spacer(modifier = Modifier.height(6.dp))
                Text(
                    text = "Extracted Links (${result.extractedUrls.size}):",
                    style = MaterialTheme.typography.labelSmall,
                    color = TextSecondary
                )
                result.extractedUrls.forEach { url ->
                    Text(url, style = MaterialTheme.typography.bodySmall, color = CyberCyan)
                }
            }

            Spacer(modifier = Modifier.height(12.dp))

            Surface(
                color = riskColor.copy(alpha = 0.12f),
                shape = RoundedCornerShape(8.dp),
                modifier = Modifier.fillMaxWidth()
            ) {
                Row(modifier = Modifier.padding(10.dp), verticalAlignment = Alignment.CenterVertically) {
                    Icon(Icons.Default.Info, contentDescription = null, tint = riskColor, modifier = Modifier.size(20.dp))
                    Spacer(modifier = Modifier.width(8.dp))
                    Text(
                        text = result.recommendedAction,
                        style = MaterialTheme.typography.bodySmall,
                        color = TextPrimary,
                        fontWeight = FontWeight.Medium
                    )
                }
            }
        }
    }
}

@Composable
private fun HistoryItemCard(item: SmsAnalysisEntity) {
    val color = when (item.riskLevel.uppercase()) {
        "CRITICAL" -> SeverityCritical
        "HIGH" -> SeverityHigh
        "MEDIUM" -> SeverityMedium
        else -> SeverityLow
    }

    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = DarkSurface),
        shape = RoundedCornerShape(10.dp)
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(12.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Box(
                modifier = Modifier
                    .size(10.dp)
                    .clip(CircleShape)
                    .background(color)
            )
            Spacer(modifier = Modifier.width(10.dp))
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = item.fraudCategory.replace('_', ' '),
                    style = MaterialTheme.typography.bodyMedium,
                    fontWeight = FontWeight.SemiBold,
                    color = TextPrimary
                )
                Text(
                    text = "Hash: ${item.messageHash.take(12)}... • Score: ${item.riskScore.toInt()}%",
                    style = MaterialTheme.typography.labelSmall,
                    color = TextSecondary
                )
            }
            Surface(
                color = color.copy(alpha = 0.2f),
                shape = RoundedCornerShape(6.dp)
            ) {
                Text(
                    text = item.riskLevel,
                    color = color,
                    fontSize = 10.sp,
                    fontWeight = FontWeight.Bold,
                    modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
                )
            }
        }
    }
}

private data class Quad<A, B, C, D>(val first: A, val second: B, val third: C, val fourth: D)

