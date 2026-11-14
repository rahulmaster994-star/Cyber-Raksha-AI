package com.cyberraksha.ai.ui.auth

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.cyberraksha.ai.core.AppPreferences
import com.cyberraksha.ai.data.remote.NetworkModule
import com.cyberraksha.ai.data.remote.UserLoginRequestDto
import com.cyberraksha.ai.data.remote.UserRegisterRequestDto
import com.cyberraksha.ai.data.remote.MobileOtpRequestDto
import com.cyberraksha.ai.data.remote.MobileOtpVerifyRequestDto
import com.cyberraksha.ai.ui.theme.*
import kotlinx.coroutines.launch

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AuthScreen(
    prefs: AppPreferences,
    onAuthSuccess: () -> Unit
) {
    var isRegisterTab by remember { mutableStateOf(true) }
    var email by remember { mutableStateOf("") }
    var username by remember { mutableStateOf("") }
    var fullName by remember { mutableStateOf("") }
    var mobileNumber by remember { mutableStateOf("") }
    var password by remember { mutableStateOf("") }
    var passwordVisible by remember { mutableStateOf(false) }
    var consentGiven by remember { mutableStateOf(true) }

    var isLoading by remember { mutableStateOf(false) }
    var errorMessage by remember { mutableStateOf<String?>(null) }
    var successMessage by remember { mutableStateOf<String?>(null) }

    // OTP Verification Dialog state
    var showOtpDialog by remember { mutableStateOf(false) }
    var otpInput by remember { mutableStateOf("") }
    var activeToken by remember { mutableStateOf<String?>(null) }

    val coroutineScope = rememberCoroutineScope()
    val backendUrl by prefs.backendUrl.collectAsState(initial = AppPreferences.DEFAULT_BACKEND_URL)

    Surface(
        modifier = Modifier.fillMaxSize(),
        color = MaterialTheme.colorScheme.background
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(24.dp)
                .verticalScroll(rememberScrollState()),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Spacer(modifier = Modifier.height(24.dp))

            // Branding Header
            Icon(
                imageVector = Icons.Default.Shield,
                contentDescription = "Shield",
                tint = CyberCyan,
                modifier = Modifier.size(56.dp)
            )
            Spacer(modifier = Modifier.height(12.dp))
            Text(
                text = "CYBER RAKSHA AI",
                style = MaterialTheme.typography.headlineMedium,
                fontWeight = FontWeight.Bold,
                color = CyberCyan,
                letterSpacing = 2.sp
            )
            Text(
                text = "National Autonomous Digital Fraud Defense",
                style = MaterialTheme.typography.bodySmall,
                color = TextSecondary
            )

            Spacer(modifier = Modifier.height(24.dp))

            // Tabs for Register vs Login
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .background(DarkSurface, RoundedCornerShape(8.dp))
                    .padding(4.dp)
            ) {
                Button(
                    onClick = { isRegisterTab = true; errorMessage = null; successMessage = null },
                    modifier = Modifier.weight(1f),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = if (isRegisterTab) CyberCyan else Color.Transparent,
                        contentColor = if (isRegisterTab) Color.Black else TextSecondary
                    ),
                    shape = RoundedCornerShape(6.dp)
                ) {
                    Text("Register", fontWeight = FontWeight.Bold)
                }
                Button(
                    onClick = { isRegisterTab = false; errorMessage = null; successMessage = null },
                    modifier = Modifier.weight(1f),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = if (!isRegisterTab) CyberCyan else Color.Transparent,
                        contentColor = if (!isRegisterTab) Color.Black else TextSecondary
                    ),
                    shape = RoundedCornerShape(6.dp)
                ) {
                    Text("Login", fontWeight = FontWeight.Bold)
                }
            }

            Spacer(modifier = Modifier.height(20.dp))

            // Form Fields
            if (isRegisterTab) {
                OutlinedTextField(
                    value = fullName,
                    onValueChange = { fullName = it },
                    label = { Text("Full Name") },
                    leadingIcon = { Icon(Icons.Default.Person, contentDescription = null, tint = CyberCyan) },
                    modifier = Modifier.fillMaxWidth(),
                    singleLine = true
                )
                Spacer(modifier = Modifier.height(12.dp))

                OutlinedTextField(
                    value = username,
                    onValueChange = { username = it },
                    label = { Text("Username") },
                    leadingIcon = { Icon(Icons.Default.Badge, contentDescription = null, tint = CyberCyan) },
                    modifier = Modifier.fillMaxWidth(),
                    singleLine = true
                )
                Spacer(modifier = Modifier.height(12.dp))

                OutlinedTextField(
                    value = mobileNumber,
                    onValueChange = { mobileNumber = it },
                    label = { Text("Mobile Number (India +91)") },
                    placeholder = { Text("10-digit number e.g. 9876543210") },
                    leadingIcon = { Icon(Icons.Default.Phone, contentDescription = null, tint = CyberCyan) },
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Phone),
                    modifier = Modifier.fillMaxWidth(),
                    singleLine = true
                )
                Spacer(modifier = Modifier.height(12.dp))
            }

            OutlinedTextField(
                value = email,
                onValueChange = { email = it },
                label = { Text(if (isRegisterTab) "Email Address" else "Email / Mobile / Username") },
                leadingIcon = { Icon(Icons.Default.Email, contentDescription = null, tint = CyberCyan) },
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Email),
                modifier = Modifier.fillMaxWidth(),
                singleLine = true
            )
            Spacer(modifier = Modifier.height(12.dp))

            OutlinedTextField(
                value = password,
                onValueChange = { password = it },
                label = { Text("Password (Min 8 chars)") },
                leadingIcon = { Icon(Icons.Default.Lock, contentDescription = null, tint = CyberCyan) },
                trailingIcon = {
                    IconButton(onClick = { passwordVisible = !passwordVisible }) {
                        Icon(
                            imageVector = if (passwordVisible) Icons.Default.Visibility else Icons.Default.VisibilityOff,
                            contentDescription = "Toggle password",
                            tint = TextSecondary
                        )
                    }
                },
                visualTransformation = if (passwordVisible) VisualTransformation.None else PasswordVisualTransformation(),
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Password),
                modifier = Modifier.fillMaxWidth(),
                singleLine = true
            )

            if (isRegisterTab) {
                Spacer(modifier = Modifier.height(12.dp))
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Checkbox(
                        checked = consentGiven,
                        onCheckedChange = { consentGiven = it },
                        colors = CheckboxDefaults.colors(checkedColor = CyberCyan)
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                    Text(
                        text = "I consent to on-device threat analysis of messages & calls to protect against fraud in compliance with DPDP Act 2023.",
                        style = MaterialTheme.typography.bodySmall,
                        color = TextSecondary
                    )
                }
            }

            // Error & Success Feedback
            errorMessage?.let {
                Spacer(modifier = Modifier.height(12.dp))
                Card(
                    colors = CardDefaults.cardColors(containerColor = Color(0x33FF3B30)),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Text(
                        text = it,
                        color = Color(0xFFFF453A),
                        style = MaterialTheme.typography.bodySmall,
                        modifier = Modifier.padding(12.dp)
                    )
                }
            }

            successMessage?.let {
                Spacer(modifier = Modifier.height(12.dp))
                Card(
                    colors = CardDefaults.cardColors(containerColor = Color(0x3330D158)),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Text(
                        text = it,
                        color = Color(0xFF30D158),
                        style = MaterialTheme.typography.bodySmall,
                        modifier = Modifier.padding(12.dp)
                    )
                }
            }

            Spacer(modifier = Modifier.height(24.dp))

            // Action Button
            Button(
                onClick = {
                    errorMessage = null
                    successMessage = null

                    if (isRegisterTab) {
                        if (email.isBlank() || username.isBlank() || password.length < 8) {
                            errorMessage = "Please enter valid email, username, and password (at least 8 chars)."
                            return@Button
                        }
                        if (!consentGiven) {
                            errorMessage = "Please accept the privacy and defense consent to proceed."
                            return@Button
                        }
                    } else {
                        if (email.isBlank() || password.isBlank()) {
                            errorMessage = "Please enter your identifier and password."
                            return@Button
                        }
                    }

                    isLoading = true
                    coroutineScope.launch {
                        try {
                            val api = NetworkModule.getApiService(backendUrl)
                            if (isRegisterTab) {
                                val resp = api.registerUser(
                                    UserRegisterRequestDto(
                                        email = email.trim(),
                                        username = username.trim(),
                                        password = password,
                                        fullName = fullName.ifBlank { null },
                                        mobileNumber = mobileNumber.ifBlank { null },
                                        consentGiven = consentGiven
                                    )
                                )
                                if (resp.isSuccessful && resp.body() != null) {
                                    val tokenData = resp.body()!!
                                    prefs.saveUserToken(tokenData.accessToken)
                                    prefs.saveUserProfile(
                                        name = fullName.ifBlank { tokenData.username },
                                        email = tokenData.email,
                                        mobile = tokenData.mobileNumber,
                                        isMobileVerified = tokenData.isMobileVerified
                                    )
                                    prefs.setConsentGiven(true)
                                    activeToken = tokenData.accessToken

                                    // If mobile provided, prompt OTP dialog
                                    if (!tokenData.mobileNumber.isNullOrBlank()) {
                                        api.sendMobileOtp(
                                            bearerToken = "Bearer ${tokenData.accessToken}",
                                            request = MobileOtpRequestDto(tokenData.mobileNumber)
                                        )
                                        showOtpDialog = true
                                    } else {
                                        onAuthSuccess()
                                    }
                                } else {
                                    errorMessage = "Registration failed: ${resp.errorBody()?.string() ?: resp.message()}"
                                }
                            } else {
                                val resp = api.loginUser(
                                    UserLoginRequestDto(
                                        identifier = email.trim(),
                                        password = password
                                    )
                                )
                                if (resp.isSuccessful && resp.body() != null) {
                                    val tokenData = resp.body()!!
                                    prefs.saveUserToken(tokenData.accessToken)
                                    prefs.saveUserProfile(
                                        name = tokenData.username,
                                        email = tokenData.email,
                                        mobile = tokenData.mobileNumber,
                                        isMobileVerified = tokenData.isMobileVerified
                                    )
                                    onAuthSuccess()
                                } else {
                                    errorMessage = "Login failed: Invalid credentials or account error."
                                }
                            }
                        } catch (e: Exception) {
                            errorMessage = "Connection error: ${e.localizedMessage ?: "Unable to reach server"}"
                        } finally {
                            isLoading = false
                        }
                    }
                },
                enabled = !isLoading,
                modifier = Modifier
                    .fillMaxWidth()
                    .height(50.dp),
                colors = ButtonDefaults.buttonColors(containerColor = CyberCyan, contentColor = Color.Black),
                shape = RoundedCornerShape(8.dp)
            ) {
                if (isLoading) {
                    CircularProgressIndicator(color = Color.Black, modifier = Modifier.size(24.dp))
                } else {
                    Text(
                        text = if (isRegisterTab) "Create Account & Continue" else "Sign In",
                        fontWeight = FontWeight.Bold,
                        fontSize = 16.sp
                    )
                }
            }
        }
    }

    // OTP Verification Dialog
    if (showOtpDialog) {
        AlertDialog(
            onDismissRequest = { /* Require completion or skip */ },
            title = { Text("Verify Mobile Number", color = CyberCyan) },
            text = {
                Column {
                    Text(
                        "We have sent a 6-digit cryptographic verification code to your Indian mobile number.",
                        style = MaterialTheme.typography.bodySmall,
                        color = TextSecondary
                    )
                    Spacer(modifier = Modifier.height(16.dp))
                    OutlinedTextField(
                        value = otpInput,
                        onValueChange = { if (it.length <= 6) otpInput = it },
                        label = { Text("Enter 6-Digit OTP") },
                        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                        singleLine = true,
                        modifier = Modifier.fillMaxWidth()
                    )
                }
            },
            confirmButton = {
                Button(
                    onClick = {
                        if (otpInput.length != 6) return@Button
                        coroutineScope.launch {
                            try {
                                val api = NetworkModule.getApiService(backendUrl)
                                val resp = api.verifyMobileOtp(
                                    bearerToken = "Bearer ${activeToken ?: ""}",
                                    request = MobileOtpVerifyRequestDto(otpInput)
                                )
                                if (resp.isSuccessful) {
                                    showOtpDialog = false
                                    onAuthSuccess()
                                } else {
                                    errorMessage = "Invalid OTP entered. Please try again."
                                    showOtpDialog = false
                                    onAuthSuccess() // Allow user to continue and verify later
                                }
                            } catch (e: Exception) {
                                showOtpDialog = false
                                onAuthSuccess()
                            }
                        }
                    },
                    colors = ButtonDefaults.buttonColors(containerColor = CyberCyan, contentColor = Color.Black)
                ) {
                    Text("Verify & Start Protection")
                }
            },
            dismissButton = {
                TextButton(onClick = {
                    showOtpDialog = false
                    onAuthSuccess()
                }) {
                    Text("Verify Later", color = TextSecondary)
                }
            }
        )
    }
}
