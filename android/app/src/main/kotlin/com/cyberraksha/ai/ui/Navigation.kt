package com.cyberraksha.ai.ui

import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.platform.LocalContext
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import androidx.room.Room
import com.cyberraksha.ai.core.AppPreferences
import com.cyberraksha.ai.data.local.AppDatabase
import com.cyberraksha.ai.data.remote.NetworkModule
import com.cyberraksha.ai.data.repository.MobileProtectionRepository
import com.cyberraksha.ai.domain.usecase.AnalyzeMessageUseCase
import com.cyberraksha.ai.domain.usecase.CheckNumberUseCase
import com.cyberraksha.ai.domain.usecase.ReportThreatUseCase
import com.cyberraksha.ai.ui.alerts.AlertsScreen
import com.cyberraksha.ai.ui.call_protection.CallProtectionScreen
import com.cyberraksha.ai.ui.call_protection.CallProtectionViewModel
import com.cyberraksha.ai.ui.dashboard.DashboardScreen
import com.cyberraksha.ai.ui.onboarding.OnboardingScreen
import com.cyberraksha.ai.ui.settings.SettingsScreen
import com.cyberraksha.ai.ui.sms_protection.SmsProtectionScreen
import com.cyberraksha.ai.ui.sms_protection.SmsProtectionViewModel
import com.cyberraksha.ai.ui.threat_history.ThreatHistoryScreen
import com.cyberraksha.ai.ui.threat_history.ThreatHistoryViewModel

object Routes {
    const val ONBOARDING       = "onboarding"
    const val DASHBOARD        = "dashboard"
    const val ALERTS           = "alerts"
    const val SETTINGS         = "settings"
    const val SMS_PROTECTION   = "sms_protection"
    const val CALL_PROTECTION  = "call_protection"
    const val THREAT_HISTORY   = "threat_history"
}

@Composable
fun CyberRakshaNavHost(prefs: AppPreferences) {
    val navController           = rememberNavController()
    val onboardingComplete by prefs.onboardingComplete.collectAsState(initial = false)
    val context                 = LocalContext.current

    val db = remember {
        Room.databaseBuilder(
            context,
            AppDatabase::class.java,
            "cyber_raksha_db"
        ).fallbackToDestructiveMigration().build()
    }

    val mobileRepository = remember {
        MobileProtectionRepository(
            api = NetworkModule.getApiService(),
            smsDao = db.smsAnalysisDao(),
            prefs = prefs
        )
    }

    val analyzeMessageUseCase = remember { AnalyzeMessageUseCase(mobileRepository) }
    val checkNumberUseCase    = remember { CheckNumberUseCase(mobileRepository) }
    val reportThreatUseCase   = remember { ReportThreatUseCase(mobileRepository) }

    val start = if (onboardingComplete) Routes.DASHBOARD else Routes.ONBOARDING

    NavHost(navController = navController, startDestination = start) {
        composable(Routes.ONBOARDING) {
            OnboardingScreen(
                prefs = prefs,
                onComplete = {
                    navController.navigate(Routes.DASHBOARD) {
                        popUpTo(Routes.ONBOARDING) { inclusive = true }
                    }
                }
            )
        }
        composable(Routes.DASHBOARD) {
            DashboardScreen(
                prefs = prefs,
                onNavigateToAlerts         = { navController.navigate(Routes.ALERTS) },
                onNavigateToSettings       = { navController.navigate(Routes.SETTINGS) },
                onNavigateToSmsProtection  = { navController.navigate(Routes.SMS_PROTECTION) },
                onNavigateToCallProtection = { navController.navigate(Routes.CALL_PROTECTION) },
                onNavigateToThreatHistory  = { navController.navigate(Routes.THREAT_HISTORY) }
            )
        }
        composable(Routes.ALERTS) {
            AlertsScreen(
                prefs = prefs,
                onBack = { navController.popBackStack() }
            )
        }
        composable(Routes.SETTINGS) {
            SettingsScreen(
                prefs = prefs,
                onBack = { navController.popBackStack() }
            )
        }
        composable(Routes.SMS_PROTECTION) {
            val viewModel = remember {
                SmsProtectionViewModel(
                    repository = mobileRepository,
                    analyzeMessageUseCase = analyzeMessageUseCase
                )
            }
            SmsProtectionScreen(
                viewModel = viewModel,
                onBack = { navController.popBackStack() }
            )
        }
        composable(Routes.CALL_PROTECTION) {
            val viewModel = remember {
                CallProtectionViewModel(
                    checkNumberUseCase = checkNumberUseCase,
                    reportThreatUseCase = reportThreatUseCase
                )
            }
            CallProtectionScreen(
                viewModel = viewModel,
                onBack = { navController.popBackStack() }
            )
        }
        composable(Routes.THREAT_HISTORY) {
            val viewModel = remember {
                ThreatHistoryViewModel(repository = mobileRepository)
            }
            ThreatHistoryScreen(
                viewModel = viewModel,
                onBack = { navController.popBackStack() }
            )
        }
    }
}
