package com.cyberraksha.ai.ui.call_protection

import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.graphics.Color
import com.cyberraksha.ai.data.remote.NumberCheckResponse
import com.cyberraksha.ai.ui.theme.*

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun CallProtectionScreen(
    viewModel: CallProtectionViewModel,
    onBack: () -> Unit
) {
    val context = LocalContext.current
    val state by viewModel.uiState.collectAsState()
    var showReportDialog by remember { mutableStateOf(false) }

    val roleLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.StartActivityForResult()
    ) {
        viewModel.updateStatus(context)
    }

    LaunchedEffect(Unit) {
        viewModel.updateStatus(context)
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Icon(
                            imageVector = Icons.Default.PhoneCallback,
                            contentDescription = null,
                            tint = CyberCyan,
                            modifier = Modifier.size(24.dp)
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        Text(
                            "Call Fraud Shield",
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

            // 1. Call Screening Role Status Banner
            item {
                CallScreeningBanner(
                    status = state.screeningStatus,
                    onRequestRole = {
                        val intent = CallScreeningHelper.createRequestRoleIntent(context)
                        if (intent != null) {
                            roleLauncher.launch(intent)
                        }
                    }
                )
            }

            // 2. Caller Reputation Lookup Card
            item {
                NumberLookupCard(
                    inputNumber = state.inputNumber,
                    isLoading = state.isLoading,
                    errorMessage = state.errorMessage,
                    reportSuccess = state.reportSuccessMessage,
                    onNumberChange = viewModel::onInputNumberChanged,
                    onCheck = viewModel::checkNumberReputation
                )
            }

            // 3. Number Result Card
            if (state.checkResult != null) {
                item {
                    NumberResultCard(
                        result = state.checkResult!!,
                        onDismiss = viewModel::clearResult,
                        onReport = { showReportDialog = true }
                    )
                }
            }

            // 4. Feature Capabilities & Tips
            item {
                CapabilitiesCard()
            }

            item { Spacer(modifier = Modifier.height(24.dp)) }
        }
    }

    if (showReportDialog) {
        ReportNumberDialog(
            phoneNumber = state.checkResult?.normalizedNumber ?: state.inputNumber,
            onDismiss = { showReportDialog = false },
            onConfirm = { category, notes ->
                showReportDialog = false
                viewModel.reportCurrentNumber(category, notes)
            }
        )
    }
}

@Composable
private fun CallScreeningBanner(
    status: CallScreeningStatus,
    onRequestRole: () -> Unit
) {
    val (title, desc, color, actionRequired) = when (status) {
        CallScreeningStatus.ACTIVE -> Quad(
            "CALL SCREENING ACTIVE",
            "Cyber Raksha screens incoming callers against threat intelligence database in real-time.",
            SeverityLow,
            false
        )
        CallScreeningStatus.PERMISSION_REQUIRED -> Quad(
            "CALL SCREENING ROLE REQUIRED",
            "To intercept scam calls before your phone rings, enable the Call Screening role.",
            SeverityHigh,
            true
        )
        CallScreeningStatus.NOT_SUPPORTED -> Quad(
            "MANUAL CALL LOOKUP ONLY",
            "Automatic telecom call screening is not available on this Android platform.",
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
                    text = title,
                    style = MaterialTheme.typography.labelMedium,
                    fontWeight = FontWeight.Bold,
                    color = color
                )
            }
            Spacer(modifier = Modifier.height(6.dp))
            Text(text = desc, style = MaterialTheme.typography.bodySmall, color = TextSecondary)

            if (actionRequired) {
                Spacer(modifier = Modifier.height(10.dp))
                Button(
                    onClick = onRequestRole,
                    colors = ButtonDefaults.buttonColors(containerColor = CyberCyan),
                    shape = RoundedCornerShape(8.dp)
                ) {
                    Text("Grant Call Screening Role", color = DarkBackground, fontWeight = FontWeight.Bold, fontSize = 12.sp)
                }
            }
        }
    }
}

@Composable
private fun NumberLookupCard(
    inputNumber: String,
    isLoading: Boolean,
    errorMessage: String?,
    reportSuccess: String?,
    onNumberChange: (String) -> Unit,
    onCheck: () -> Unit
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = DarkSurface),
        shape = RoundedCornerShape(14.dp)
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text(
                "Verify Caller Reputation",
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.SemiBold,
                color = TextPrimary
            )
            Spacer(modifier = Modifier.height(4.dp))
            Text(
                "Check whether an unknown number is reported for Digital Arrest, bank fraud, or telemarketing.",
                style = MaterialTheme.typography.labelSmall,
                color = TextSecondary
            )

            Spacer(modifier = Modifier.height(12.dp))

            OutlinedTextField(
                value = inputNumber,
                onValueChange = onNumberChange,
                label = { Text("Phone Number (e.g. +91... or 10-digit mobile)") },
                modifier = Modifier.fillMaxWidth(),
                singleLine = true,
                colors = OutlinedTextFieldDefaults.colors(
                    focusedBorderColor = CyberCyan,
                    unfocusedBorderColor = DarkOutline,
                    focusedTextColor = TextPrimary,
                    unfocusedTextColor = TextPrimary
                )
            )

            if (errorMessage != null) {
                Spacer(modifier = Modifier.height(6.dp))
                Text(errorMessage, color = SeverityCritical, style = MaterialTheme.typography.labelSmall)
            }

            if (reportSuccess != null) {
                Spacer(modifier = Modifier.height(6.dp))
                Text(reportSuccess, color = SeverityLow, style = MaterialTheme.typography.labelSmall)
            }

            Spacer(modifier = Modifier.height(14.dp))

            Button(
                onClick = onCheck,
                enabled = !isLoading && inputNumber.isNotBlank(),
                modifier = Modifier.fillMaxWidth(),
                colors = ButtonDefaults.buttonColors(containerColor = CyberCyan),
                shape = RoundedCornerShape(10.dp)
            ) {
                if (isLoading) {
                    CircularProgressIndicator(modifier = Modifier.size(20.dp), color = DarkBackground, strokeWidth = 2.dp)
                } else {
                    Icon(Icons.Default.Search, contentDescription = null, tint = DarkBackground)
                    Spacer(modifier = Modifier.width(8.dp))
                    Text("Check Reputation", color = DarkBackground, fontWeight = FontWeight.Bold)
                }
            }
        }
    }
}

@Composable
private fun NumberResultCard(
    result: NumberCheckResponse,
    onDismiss: () -> Unit,
    onReport: () -> Unit
) {
    val riskColor = when (result.riskLevel.uppercase()) {
        "CRITICAL" -> SeverityCritical
        "HIGH" -> SeverityHigh
        "MEDIUM" -> SeverityMedium
        "SAFE" -> SeverityLow
        else -> TextSecondary
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
                        text = "${result.riskLevel} RISK",
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
                text = result.normalizedNumber,
                style = MaterialTheme.typography.titleLarge,
                fontWeight = FontWeight.Bold,
                color = TextPrimary
            )

            if (!result.fraudCategory.isNullOrEmpty()) {
                Text(
                    text = "Category: ${result.fraudCategory.replace('_', ' ')}",
                    style = MaterialTheme.typography.bodyMedium,
                    color = SeverityHigh,
                    fontWeight = FontWeight.SemiBold
                )
            }

            Text(
                text = "Community Reports: ${result.reportCount} • Source: ${result.source}",
                style = MaterialTheme.typography.labelSmall,
                color = TextSecondary
            )

            if (!result.notes.isNullOrEmpty()) {
                Spacer(modifier = Modifier.height(6.dp))
                Text(
                    text = "Notes: ${result.notes}",
                    style = MaterialTheme.typography.bodySmall,
                    color = TextPrimary
                )
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

            Spacer(modifier = Modifier.height(12.dp))

            OutlinedButton(
                onClick = onReport,
                modifier = Modifier.fillMaxWidth(),
                colors = ButtonDefaults.outlinedButtonColors(contentColor = SeverityHigh),
                border = ButtonDefaults.outlinedButtonBorder.copy(brush = androidx.compose.ui.graphics.SolidColor(SeverityHigh))
            ) {
                Icon(Icons.Default.ReportProblem, contentDescription = null, modifier = Modifier.size(16.dp))
                Spacer(modifier = Modifier.width(6.dp))
                Text("Report as Fraud / Spam", fontSize = 12.sp)
            }
        }
    }
}

@Composable
private fun CapabilitiesCard() {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = DarkSurface),
        shape = RoundedCornerShape(14.dp)
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text(
                "Call Protection Capabilities",
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.SemiBold,
                color = TextPrimary
            )
            Spacer(modifier = Modifier.height(10.dp))
            CapabilityItem(icon = Icons.Default.Gavel, title = "Digital Arrest Protection", desc = "Blocks known VoIP numbers used in fake CBI/police video call extortion.")
            CapabilityItem(icon = Icons.Default.AccountBalance, title = "Bank Impersonation Shield", desc = "Detects personal numbers pretending to be official customer service desks.")
            CapabilityItem(icon = Icons.Default.VerifiedUser, title = "Zero Silent Bypasses", desc = "Requires explicit RoleManager grant before intercepting calls.")
        }
    }
}

@Composable
private fun CapabilityItem(icon: androidx.compose.ui.graphics.vector.ImageVector, title: String, desc: String) {
    Row(modifier = Modifier.padding(vertical = 6.dp), verticalAlignment = Alignment.Top) {
        Icon(icon, contentDescription = null, tint = CyberCyan, modifier = Modifier.size(18.dp))
        Spacer(modifier = Modifier.width(10.dp))
        Column {
            Text(title, style = MaterialTheme.typography.bodyMedium, fontWeight = FontWeight.SemiBold, color = TextPrimary)
            Text(desc, style = MaterialTheme.typography.labelSmall, color = TextSecondary)
        }
    }
}

@Composable
private fun ReportNumberDialog(
    phoneNumber: String,
    onDismiss: () -> Unit,
    onConfirm: (category: String, notes: String) -> Unit
) {
    var category by remember { mutableStateOf("DIGITAL_ARREST") }
    var notes by remember { mutableStateOf("") }

    val categories = listOf("DIGITAL_ARREST", "BANKING_FRAUD", "UPI_SCAM", "LOTTERY_SCAM", "TELEMARKETING")

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Report Scam Number", color = TextPrimary) },
        text = {
            Column {
                Text("Report number $phoneNumber to the Cyber Raksha community defense repository:", color = TextSecondary, fontSize = 13.sp)
                Spacer(modifier = Modifier.height(12.dp))

                Text("Fraud Category:", fontWeight = FontWeight.SemiBold, color = TextPrimary, fontSize = 12.sp)
                categories.forEach { cat ->
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        modifier = Modifier.fillMaxWidth().padding(vertical = 2.dp)
                    ) {
                        RadioButton(
                            selected = category == cat,
                            onClick = { category = cat },
                            colors = RadioButtonDefaults.colors(selectedColor = CyberCyan)
                        )
                        Spacer(modifier = Modifier.width(6.dp))
                        Text(cat.replace('_', ' '), color = TextPrimary, fontSize = 13.sp)
                    }
                }

                Spacer(modifier = Modifier.height(8.dp))
                OutlinedTextField(
                    value = notes,
                    onValueChange = { notes = it },
                    label = { Text("Details (e.g. claimed to be police)") },
                    modifier = Modifier.fillMaxWidth(),
                    maxLines = 3,
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedBorderColor = CyberCyan,
                        unfocusedBorderColor = DarkOutline,
                        focusedTextColor = TextPrimary,
                        unfocusedTextColor = TextPrimary
                    )
                )
            }
        },
        confirmButton = {
            Button(
                onClick = { onConfirm(category, notes) },
                colors = ButtonDefaults.buttonColors(containerColor = SeverityHigh)
            ) {
                Text("Submit Report", color = Color.White)
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text("Cancel", color = TextSecondary)
            }
        },
        containerColor = DarkSurface
    )
}

private data class Quad<A, B, C, D>(val first: A, val second: B, val third: C, val fourth: D)
