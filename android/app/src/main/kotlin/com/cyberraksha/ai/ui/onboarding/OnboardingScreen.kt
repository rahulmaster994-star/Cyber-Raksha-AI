package com.cyberraksha.ai.ui.onboarding

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.BugReport
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.Info
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material.icons.filled.Security
import androidx.compose.material.icons.filled.Shield
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.cyberraksha.ai.core.AppPreferences
import com.cyberraksha.ai.data.repository.DiagnosticReport
import com.cyberraksha.ai.ui.theme.*

@Composable
fun OnboardingScreen(
    prefs: AppPreferences,
    onComplete: () -> Unit,
    viewModel: OnboardingViewModel = remember { OnboardingViewModel(prefs) }
) {
    val state by viewModel.uiState.collectAsState()

    Surface(
        modifier = Modifier.fillMaxSize(),
        color = MaterialTheme.colorScheme.background
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(24.dp)
                .verticalScroll(rememberScrollState()),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.SpaceBetween
        ) {
            // Header
            Column(
                horizontalAlignment = Alignment.CenterHorizontally,
                modifier = Modifier.padding(top = 32.dp)
            ) {
                Icon(
                    imageVector = Icons.Default.Shield,
                    contentDescription = "Shield",
                    tint = CyberCyan,
                    modifier = Modifier.size(64.dp)
                )
                Spacer(modifier = Modifier.height(16.dp))
                Text(
                    text = "CYBER RAKSHA AI",
                    style = MaterialTheme.typography.headlineLarge,
                    color = CyberCyan,
                    letterSpacing = 2.sp
                )
                Text(
                    text = "Mobile Protection Layer",
                    style = MaterialTheme.typography.bodyMedium,
                    color = TextSecondary
                )
            }

            // Step Content
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(vertical = 24.dp),
                contentAlignment = Alignment.Center
            ) {
                when (state.currentStep) {
                    0 -> StepIntro()
                    1 -> StepPermissions()
                    2 -> StepRegistration(
                        deviceName = state.deviceName,
                        onDeviceNameChange = viewModel::onDeviceNameChanged,
                        backendUrl = state.backendUrl,
                        onBackendUrlChange = viewModel::onBackendUrlChanged,
                        errorMessage = state.errorMessage,
                        diagnosticReport = state.diagnosticReport,
                        isTestingDiagnostics = state.isTestingDiagnostics,
                        onRunDiagnostics = viewModel::runDiagnostics
                    )
                }
            }

            // Bottom Buttons & Progress
            Column(
                modifier = Modifier.fillMaxWidth(),
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                // Step Indicator Dots
                Row(
                    horizontalArrangement = Arrangement.Center,
                    modifier = Modifier.padding(bottom = 20.dp)
                ) {
                    repeat(3) { index ->
                        Box(
                            modifier = Modifier
                                .padding(4.dp)
                                .size(if (index == state.currentStep) 10.dp else 8.dp)
                                .background(
                                    if (index == state.currentStep) CyberCyan else DarkOutline,
                                    shape = RoundedCornerShape(50)
                                )
                        )
                    }
                }

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    if (state.currentStep > 0) {
                        OutlinedButton(
                            onClick = { viewModel.prevStep() },
                            enabled = !state.isLoading
                        ) {
                            Text("Back", color = TextPrimary)
                        }
                    } else {
                        Spacer(modifier = Modifier.width(80.dp))
                    }

                    if (state.currentStep < 2) {
                        Button(
                            onClick = { viewModel.nextStep() },
                            colors = ButtonDefaults.buttonColors(containerColor = CyberCyan)
                        ) {
                            Text("Continue", color = DarkBackground, fontWeight = FontWeight.Bold)
                        }
                    } else {
                        Button(
                            onClick = { viewModel.registerDevice(onComplete) },
                            enabled = !state.isLoading,
                            colors = ButtonDefaults.buttonColors(containerColor = CyberCyan)
                        ) {
                            if (state.isLoading) {
                                CircularProgressIndicator(
                                    modifier = Modifier.size(20.dp),
                                    color = DarkBackground,
                                    strokeWidth = 2.dp
                                )
                            } else {
                                Text("Activate Protection", color = DarkBackground, fontWeight = FontWeight.Bold)
                            }
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun StepIntro() {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = DarkSurface),
        shape = RoundedCornerShape(16.dp)
    ) {
        Column(
            modifier = Modifier.padding(20.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text(
                text = "Autonomous Cyber Defense",
                style = MaterialTheme.typography.titleLarge,
                color = TextPrimary,
                textAlign = TextAlign.Center
            )
            Spacer(modifier = Modifier.height(12.dp))
            Text(
                text = "Cyber Raksha AI delivers multi-layered, real-time protection against phishing URLs, malicious web infrastructure, digital-arrest impersonations, and communication fraud.",
                style = MaterialTheme.typography.bodyMedium,
                color = TextSecondary,
                textAlign = TextAlign.Center
            )
            Spacer(modifier = Modifier.height(16.dp))
            FeaturePill("Real-time Threat Intelligence")
            Spacer(modifier = Modifier.height(8.dp))
            FeaturePill("Local Device Security Posture")
            Spacer(modifier = Modifier.height(8.dp))
            FeaturePill("Cross-Module Security Sync")
        }
    }
}

@Composable
private fun FeaturePill(text: String) {
    Row(
        verticalAlignment = Alignment.CenterVertically,
        modifier = Modifier
            .fillMaxWidth()
            .background(DarkSurfaceVar, RoundedCornerShape(8.dp))
            .padding(horizontal = 12.dp, vertical = 8.dp)
    ) {
        Icon(
            imageVector = Icons.Default.CheckCircle,
            contentDescription = null,
            tint = SeverityLow,
            modifier = Modifier.size(18.dp)
        )
        Spacer(modifier = Modifier.width(10.dp))
        Text(text = text, style = MaterialTheme.typography.bodyMedium, color = TextPrimary)
    }
}

@Composable
private fun StepPermissions() {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = DarkSurface),
        shape = RoundedCornerShape(16.dp)
    ) {
        Column(
            modifier = Modifier.padding(20.dp),
            horizontalAlignment = Alignment.Start
        ) {
            Text(
                text = "Permissions & Privacy",
                style = MaterialTheme.typography.titleLarge,
                color = TextPrimary
            )
            Spacer(modifier = Modifier.height(12.dp))
            Text(
                text = "To safeguard your device and alert you promptly:",
                style = MaterialTheme.typography.bodyMedium,
                color = TextSecondary
            )
            Spacer(modifier = Modifier.height(16.dp))
            PermissionItem(
                title = "Push Notifications",
                description = "Delivers instantaneous alerts for critical threats and phishing attempts."
            )
            Spacer(modifier = Modifier.height(12.dp))
            PermissionItem(
                title = "Network Access",
                description = "Synchronizes with Cyber Raksha threat intelligence backend for active indicators."
            )
            Spacer(modifier = Modifier.height(16.dp))
            Text(
                text = "• Zero telemetry of private browsing or personal data\n• Unique app-generated installation UUID (no IMEI or phone tracking)",
                style = MaterialTheme.typography.labelSmall,
                color = TextSecondary
            )
        }
    }
}

@Composable
private fun PermissionItem(title: String, description: String) {
    Column {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Icon(
                imageVector = Icons.Default.Security,
                contentDescription = null,
                tint = CyberCyan,
                modifier = Modifier.size(18.dp)
            )
            Spacer(modifier = Modifier.width(8.dp))
            Text(text = title, fontWeight = FontWeight.SemiBold, color = TextPrimary)
        }
        Text(
            text = description,
            style = MaterialTheme.typography.bodyMedium,
            color = TextSecondary,
            modifier = Modifier.padding(start = 26.dp, top = 2.dp)
        )
    }
}

@Composable
private fun StepRegistration(
    deviceName: String,
    onDeviceNameChange: (String) -> Unit,
    backendUrl: String,
    onBackendUrlChange: (String) -> Unit,
    errorMessage: String?,
    diagnosticReport: DiagnosticReport?,
    isTestingDiagnostics: Boolean,
    onRunDiagnostics: () -> Unit
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = DarkSurface),
        shape = RoundedCornerShape(16.dp)
    ) {
        Column(
            modifier = Modifier.padding(20.dp),
            horizontalAlignment = Alignment.Start
        ) {
            Text(
                text = "Device Registration",
                style = MaterialTheme.typography.titleLarge,
                color = TextPrimary
            )
            Spacer(modifier = Modifier.height(8.dp))
            Text(
                text = "Configure connectivity to your Cyber Raksha AI backend node.",
                style = MaterialTheme.typography.bodyMedium,
                color = TextSecondary
            )
            Spacer(modifier = Modifier.height(16.dp))

            OutlinedTextField(
                value = deviceName,
                onValueChange = onDeviceNameChange,
                label = { Text("Device Name") },
                modifier = Modifier.fillMaxWidth(),
                singleLine = true,
                colors = OutlinedTextFieldDefaults.colors(
                    focusedBorderColor = CyberCyan,
                    unfocusedBorderColor = DarkOutline
                )
            )

            Spacer(modifier = Modifier.height(12.dp))

            OutlinedTextField(
                value = backendUrl,
                onValueChange = onBackendUrlChange,
                label = { Text("Backend URL") },
                modifier = Modifier.fillMaxWidth(),
                singleLine = true,
                colors = OutlinedTextFieldDefaults.colors(
                    focusedBorderColor = CyberCyan,
                    unfocusedBorderColor = DarkOutline
                )
            )

            Text(
                text = "Default: https://cyberraksha-backend.onrender.com (production cloud).",
                style = MaterialTheme.typography.labelSmall,
                color = TextSecondary,
                modifier = Modifier.padding(top = 4.dp)
            )

            Spacer(modifier = Modifier.height(12.dp))

            // Developer Diagnostics Trigger Button
            OutlinedButton(
                onClick = onRunDiagnostics,
                enabled = !isTestingDiagnostics,
                modifier = Modifier.fillMaxWidth()
            ) {
                if (isTestingDiagnostics) {
                    CircularProgressIndicator(
                        modifier = Modifier.size(16.dp),
                        strokeWidth = 2.dp,
                        color = CyberCyan
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                    Text("Probing Backend...")
                } else {
                    Icon(
                        imageVector = Icons.Default.BugReport,
                        contentDescription = "Test",
                        modifier = Modifier.size(16.dp),
                        tint = CyberCyan
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                    Text("Test Connection & Run Diagnostics", color = CyberCyan)
                }
            }

            // Error Display (with exact exception details)
            if (!errorMessage.isNullOrEmpty()) {
                Spacer(modifier = Modifier.height(12.dp))
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    modifier = Modifier
                        .fillMaxWidth()
                        .background(SeverityCritical.copy(alpha = 0.15f), RoundedCornerShape(8.dp))
                        .padding(10.dp)
                ) {
                    Icon(
                        imageVector = Icons.Default.Warning,
                        contentDescription = "Error",
                        tint = SeverityCritical,
                        modifier = Modifier.size(18.dp)
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                    Text(
                        text = errorMessage,
                        style = MaterialTheme.typography.bodyMedium,
                        color = SeverityCritical
                    )
                }
            }

            // Developer Diagnostics Results Card
            if (diagnosticReport != null) {
                Spacer(modifier = Modifier.height(12.dp))
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    colors = CardDefaults.cardColors(
                        containerColor = if (diagnosticReport.isHealthy)
                            SeverityLow.copy(alpha = 0.12f)
                        else
                            SeverityHigh.copy(alpha = 0.12f)
                    ),
                    shape = RoundedCornerShape(8.dp)
                ) {
                    Column(modifier = Modifier.padding(12.dp)) {
                        Row(
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.SpaceBetween,
                            modifier = Modifier.fillMaxWidth()
                        ) {
                            Text(
                                text = if (diagnosticReport.isHealthy) "PROBE STATUS: HEALTHY (200)" else "PROBE STATUS: FAILED",
                                style = MaterialTheme.typography.labelMedium,
                                fontWeight = FontWeight.Bold,
                                color = if (diagnosticReport.isHealthy) SeverityLow else SeverityHigh
                            )
                            Text(
                                text = "${diagnosticReport.latencyMs} ms",
                                style = MaterialTheme.typography.labelSmall,
                                color = TextSecondary
                            )
                        }

                        Spacer(modifier = Modifier.height(6.dp))
                        DiagnosticRow("Target Base URL", diagnosticReport.resolvedBaseUrl)
                        DiagnosticRow("Health Endpoint", diagnosticReport.healthEndpointUrl)
                        DiagnosticRow(
                            "DNS Resolved IPs",
                            diagnosticReport.dnsResolvedIps.joinToString(", ").ifEmpty { "None" }
                        )
                        DiagnosticRow(
                            "HTTP Status",
                            diagnosticReport.httpStatusCode?.toString() ?: "No HTTP response"
                        )

                        if (!diagnosticReport.exceptionType.isNullOrEmpty()) {
                            DiagnosticRow("Exception", diagnosticReport.exceptionType)
                            DiagnosticRow("Details", diagnosticReport.exceptionMessage ?: "N/A")
                        }

                        if (!diagnosticReport.stackTraceSnippet.isNullOrEmpty()) {
                            Spacer(modifier = Modifier.height(4.dp))
                            Text(
                                text = "Stack Trace Snippet:",
                                style = MaterialTheme.typography.labelSmall,
                                fontWeight = FontWeight.Bold,
                                color = TextSecondary
                            )
                            Text(
                                text = diagnosticReport.stackTraceSnippet,
                                style = MaterialTheme.typography.labelSmall,
                                fontFamily = FontFamily.Monospace,
                                color = SeverityCritical,
                                fontSize = 10.sp
                            )
                        }

                        if (!diagnosticReport.responseBodyPreview.isNullOrEmpty()) {
                            Spacer(modifier = Modifier.height(4.dp))
                            Text(
                                text = "Raw Response Preview:",
                                style = MaterialTheme.typography.labelSmall,
                                fontWeight = FontWeight.Bold,
                                color = TextSecondary
                            )
                            Text(
                                text = diagnosticReport.responseBodyPreview,
                                style = MaterialTheme.typography.labelSmall,
                                fontFamily = FontFamily.Monospace,
                                color = TextPrimary,
                                fontSize = 10.sp
                            )
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun DiagnosticRow(label: String, value: String) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 2.dp),
        horizontalArrangement = Arrangement.SpaceBetween
    ) {
        Text(
            text = "$label:",
            style = MaterialTheme.typography.labelSmall,
            color = TextSecondary,
            fontWeight = FontWeight.Medium
        )
        Text(
            text = value,
            style = MaterialTheme.typography.labelSmall,
            color = TextPrimary,
            fontFamily = FontFamily.Monospace,
            fontSize = 11.sp,
            textAlign = TextAlign.End,
            modifier = Modifier.padding(start = 8.dp)
        )
    }
}

