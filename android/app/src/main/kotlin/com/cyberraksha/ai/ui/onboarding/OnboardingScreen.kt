package com.cyberraksha.ai.ui.onboarding

import android.Manifest
import android.app.Activity
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.net.VpnService
import android.os.Build
import android.provider.Settings
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalLifecycleOwner
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleEventObserver
import com.cyberraksha.ai.core.AppPreferences
import com.cyberraksha.ai.ui.call_protection.CallScreeningHelper
import com.cyberraksha.ai.ui.theme.*
import com.cyberraksha.ai.vpn.CyberRakshaDnsVpnService
import kotlinx.coroutines.launch

@Composable
fun OnboardingScreen(
    prefs: AppPreferences,
    onComplete: () -> Unit,
    viewModel: OnboardingViewModel = remember { OnboardingViewModel(prefs) }
) {
    val context = LocalContext.current
    val lifecycleOwner = LocalLifecycleOwner.current
    val state by viewModel.uiState.collectAsState()
    val coroutineScope = rememberCoroutineScope()

    // Dynamically refresh permission states on lifecycle ON_RESUME
    DisposableEffect(lifecycleOwner) {
        val observer = LifecycleEventObserver { _, event ->
            if (event == Lifecycle.Event.ON_RESUME) {
                viewModel.refreshPermissionState(context)
            }
        }
        lifecycleOwner.lifecycle.addObserver(observer)
        viewModel.refreshPermissionState(context)
        onDispose {
            lifecycleOwner.lifecycle.removeObserver(observer)
        }
    }

    // Launchers
    val smsLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.RequestMultiplePermissions()
    ) {
        coroutineScope.launch { prefs.setSmsProtectionEnabled(true) }
        viewModel.refreshPermissionState(context)
    }

    val notifLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.RequestPermission()
    ) {
        viewModel.refreshPermissionState(context)
    }

    val callRoleLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.StartActivityForResult()
    ) {
        coroutineScope.launch { prefs.setCallProtectionEnabled(true) }
        viewModel.refreshPermissionState(context)
    }

    val vpnLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.StartActivityForResult()
    ) { result ->
        if (result.resultCode == Activity.RESULT_OK) {
            CyberRakshaDnsVpnService.start(context)
            coroutineScope.launch { prefs.setWebProtectionEnabled(true) }
        }
        viewModel.refreshPermissionState(context)
    }

    Surface(
        modifier = Modifier.fillMaxSize(),
        color = MaterialTheme.colorScheme.background
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(20.dp)
                .verticalScroll(rememberScrollState()),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Spacer(modifier = Modifier.height(16.dp))

            // Branding Header
            Icon(
                imageVector = Icons.Default.Shield,
                contentDescription = "Shield",
                tint = CyberCyan,
                modifier = Modifier.size(56.dp)
            )
            Spacer(modifier = Modifier.height(8.dp))
            Text(
                text = "CYBER RAKSHA AI",
                style = MaterialTheme.typography.headlineMedium,
                fontWeight = FontWeight.Bold,
                color = CyberCyan,
                letterSpacing = 2.sp
            )
            Text(
                text = "Autonomous Defense Onboarding & Permissions",
                style = MaterialTheme.typography.bodySmall,
                color = TextSecondary
            )

            Spacer(modifier = Modifier.height(20.dp))

            // ── PERMISSION STATUS DASHBOARD ────────────────────────────────────
            PermissionStatusDashboardCard(state = state)

            Spacer(modifier = Modifier.height(16.dp))

            Text(
                text = "Required Autonomous Defense Shields",
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.Bold,
                color = TextPrimary,
                modifier = Modifier.fillMaxWidth()
            )
            Text(
                text = "Grant each capability below to activate real-time protection.",
                style = MaterialTheme.typography.bodySmall,
                color = TextSecondary,
                modifier = Modifier.fillMaxWidth().padding(bottom = 12.dp)
            )

            // 1. SMS Protection Card
            ShieldConfigCard(
                title = "1. Incoming SMS Scam Shield",
                description = "Enables automatic interception of SMS messages to detect fake bank KYC, UPI scams, and digital arrest threats locally.",
                isActive = state.isSmsActive,
                actionLabel = "Grant SMS Permission",
                onAction = {
                    smsLauncher.launch(
                        arrayOf(
                            Manifest.permission.RECEIVE_SMS,
                            Manifest.permission.READ_SMS
                        )
                    )
                }
            )

            Spacer(modifier = Modifier.height(12.dp))

            // 2. Notification Alerts Card
            ShieldConfigCard(
                title = "2. High-Priority Threat Alerts",
                description = "Required on Android 13+ to post instant heads-up warning banners when fraud or imposter attempts are detected.",
                isActive = state.isNotificationsGranted,
                actionLabel = "Allow Threat Alerts",
                onAction = {
                    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                        notifLauncher.launch(Manifest.permission.POST_NOTIFICATIONS)
                    } else {
                        val intent = Intent(Settings.ACTION_APP_NOTIFICATION_SETTINGS).apply {
                            putExtra(Settings.EXTRA_APP_PACKAGE, context.packageName)
                        }
                        context.startActivity(intent)
                    }
                }
            )

            Spacer(modifier = Modifier.height(12.dp))

            // 3. WhatsApp & Telegram Shield Card
            ShieldConfigCard(
                title = "3. WhatsApp & Telegram Protection",
                description = "Inspects incoming message previews from WhatsApp and Telegram in real-time. Strict zero-cloud privacy: no private chats are decrypted or saved.",
                isActive = state.isWhatsAppActive && state.isTelegramActive,
                actionLabel = "Enable Notification Access",
                onAction = {
                    val intent = Intent(Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS)
                    context.startActivity(intent)
                }
            )

            Spacer(modifier = Modifier.height(12.dp))

            // 4. Call Screening Card
            ShieldConfigCard(
                title = "4. Fraud Call Screener",
                description = "Integrates with Android Telecom to screen incoming calls against verified extortion lists and digital arrest numbers before your phone rings.",
                isActive = state.isCallActive,
                actionLabel = "Set as Call Screening App",
                onAction = {
                    val intent = CallScreeningHelper.createRequestRoleIntent(context)
                    if (intent != null) {
                        callRoleLauncher.launch(intent)
                    } else {
                        val appIntent = Intent(Settings.ACTION_MANAGE_DEFAULT_APPS_SETTINGS)
                        context.startActivity(appIntent)
                    }
                }
            )

            Spacer(modifier = Modifier.height(12.dp))

            // 5. Battery & Background Guidance (vivo & OPPO specific)
            val manufacturer = Build.MANUFACTURER.lowercase()
            val isVivoOrOppo = manufacturer.contains("vivo") || manufacturer.contains("oppo") || manufacturer.contains("realme")
            ShieldConfigCard(
                title = "5. Background Reliability & Autostart",
                description = if (isVivoOrOppo) {
                    "${Build.MANUFACTURER} devices require enabling 'Autostart' and setting Battery to 'Don't optimize' or 'Allow high background power' to prevent Android from killing background fraud detection."
                } else {
                    "Allow background execution to ensure continuous 24/7 protection against fraud even when the app is swiped from Recent Apps."
                },
                isActive = state.isBatteryOptimizedIgnored,
                actionLabel = "Configure Battery Optimization",
                onAction = {
                    try {
                        val intent = Intent(Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS).apply {
                            data = Uri.parse("package:${context.packageName}")
                        }
                        context.startActivity(intent)
                    } catch (_: Exception) {
                        val intent = Intent(Settings.ACTION_IGNORE_BATTERY_OPTIMIZATION_SETTINGS)
                        context.startActivity(intent)
                    }
                }
            )

            Spacer(modifier = Modifier.height(12.dp))

            // 6. DNS Protection Card (Optional)
            ShieldConfigCard(
                title = "6. DNS Phishing Sinkhole (Optional)",
                description = "Routes DNS queries through a local on-device VPN filter to block phishing and malware domains locally.",
                isActive = state.isDnsActive,
                actionLabel = "Enable DNS Shield",
                onAction = {
                    val vpnIntent = VpnService.prepare(context)
                    if (vpnIntent != null) {
                        vpnLauncher.launch(vpnIntent)
                    } else {
                        CyberRakshaDnsVpnService.start(context)
                        coroutineScope.launch { prefs.setWebProtectionEnabled(true) }
                        viewModel.refreshPermissionState(context)
                    }
                }
            )

            Spacer(modifier = Modifier.height(24.dp))

            // Action Button
            Button(
                onClick = { viewModel.completeOnboardingAndRegister(onComplete) },
                modifier = Modifier
                    .fillMaxWidth()
                    .height(52.dp),
                colors = ButtonDefaults.buttonColors(containerColor = CyberCyan, contentColor = Color.Black),
                shape = RoundedCornerShape(10.dp),
                enabled = !state.isLoading
            ) {
                if (state.isLoading) {
                    CircularProgressIndicator(color = Color.Black, modifier = Modifier.size(24.dp))
                } else {
                    Text(
                        "Activate & Enter Security Dashboard",
                        fontWeight = FontWeight.Bold,
                        fontSize = 15.sp
                    )
                }
            }

            Spacer(modifier = Modifier.height(20.dp))
        }
    }
}

@Composable
private fun PermissionStatusDashboardCard(state: OnboardingUiState) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = DarkSurface),
        shape = RoundedCornerShape(14.dp),
        border = CardDefaults.outlinedCardBorder().copy(
            brush = androidx.compose.ui.graphics.SolidColor(CyberCyan.copy(alpha = 0.5f))
        )
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Icon(
                        imageVector = Icons.Default.Security,
                        contentDescription = null,
                        tint = CyberCyan,
                        modifier = Modifier.size(20.dp)
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                    Text(
                        text = "Protection Status Dashboard",
                        style = MaterialTheme.typography.titleSmall,
                        fontWeight = FontWeight.Bold,
                        color = TextPrimary
                    )
                }
                Surface(
                    color = CyberCyan.copy(alpha = 0.15f),
                    shape = RoundedCornerShape(6.dp)
                ) {
                    Text(
                        text = "LIVE POSTURE",
                        color = CyberCyan,
                        fontSize = 10.sp,
                        fontWeight = FontWeight.Bold,
                        modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
                    )
                }
            }

            Spacer(modifier = Modifier.height(12.dp))
            HorizontalDivider(color = DarkOutline)
            Spacer(modifier = Modifier.height(10.dp))

            StatusDashboardRow("SMS Protection", state.isSmsActive)
            StatusDashboardRow("WhatsApp Protection", state.isWhatsAppActive)
            StatusDashboardRow("Telegram Protection", state.isTelegramActive)
            StatusDashboardRow("Call Protection", state.isCallActive)
            StatusDashboardRow("DNS Protection", state.isDnsActive)

            // Backend Connection Status Row
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(vertical = 4.dp),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Box(
                        modifier = Modifier
                            .size(8.dp)
                            .clip(CircleShape)
                            .background(if (state.isBackendConnected) SeverityLow else SeverityHigh)
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                    Text(
                        text = "Backend Connection",
                        style = MaterialTheme.typography.bodyMedium,
                        color = TextPrimary
                    )
                }
                Text(
                    text = if (state.isBackendConnected) {
                        "Connected (${state.backendLatencyMs ?: 0}ms)"
                    } else {
                        "Disconnected"
                    },
                    color = if (state.isBackendConnected) SeverityLow else SeverityHigh,
                    fontWeight = FontWeight.Bold,
                    fontSize = 12.sp
                )
            }
        }
    }
}

@Composable
private fun StatusDashboardRow(label: String, isActive: Boolean) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 4.dp),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Box(
                modifier = Modifier
                    .size(8.dp)
                    .clip(CircleShape)
                    .background(if (isActive) SeverityLow else SeverityCritical)
            )
            Spacer(modifier = Modifier.width(8.dp))
            Text(
                text = label,
                style = MaterialTheme.typography.bodyMedium,
                color = TextPrimary
            )
        }
        Surface(
            color = if (isActive) SeverityLow.copy(alpha = 0.15f) else SeverityCritical.copy(alpha = 0.15f),
            shape = RoundedCornerShape(4.dp)
        ) {
            Text(
                text = if (isActive) "Active" else "Inactive",
                color = if (isActive) SeverityLow else SeverityCritical,
                fontWeight = FontWeight.Bold,
                fontSize = 11.sp,
                modifier = Modifier.padding(horizontal = 8.dp, vertical = 2.dp)
            )
        }
    }
}

@Composable
private fun ShieldConfigCard(
    title: String,
    description: String,
    isActive: Boolean,
    actionLabel: String,
    onAction: () -> Unit
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = DarkSurface),
        shape = RoundedCornerShape(12.dp)
    ) {
        Column(modifier = Modifier.padding(14.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = title,
                    style = MaterialTheme.typography.titleSmall,
                    fontWeight = FontWeight.Bold,
                    color = TextPrimary
                )
                if (isActive) {
                    Icon(
                        imageVector = Icons.Default.CheckCircle,
                        contentDescription = "Active",
                        tint = SeverityLow,
                        modifier = Modifier.size(18.dp)
                    )
                }
            }

            Spacer(modifier = Modifier.height(4.dp))
            Text(
                text = description,
                style = MaterialTheme.typography.bodySmall,
                color = TextSecondary
            )

            Spacer(modifier = Modifier.height(10.dp))
            if (isActive) {
                Surface(
                    color = SeverityLow.copy(alpha = 0.12f),
                    shape = RoundedCornerShape(6.dp),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Row(
                        modifier = Modifier.padding(horizontal = 10.dp, vertical = 6.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Icon(
                            imageVector = Icons.Default.Check,
                            contentDescription = null,
                            tint = SeverityLow,
                            modifier = Modifier.size(14.dp)
                        )
                        Spacer(modifier = Modifier.width(6.dp))
                        Text(
                            text = "Shield Active & Operational",
                            color = SeverityLow,
                            fontSize = 12.sp,
                            fontWeight = FontWeight.SemiBold
                        )
                    }
                }
            } else {
                OutlinedButton(
                    onClick = onAction,
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(8.dp),
                    colors = ButtonDefaults.outlinedButtonColors(contentColor = CyberCyan)
                ) {
                    Text(actionLabel, fontWeight = FontWeight.Bold, fontSize = 12.sp)
                }
            }
        }
    }
}
