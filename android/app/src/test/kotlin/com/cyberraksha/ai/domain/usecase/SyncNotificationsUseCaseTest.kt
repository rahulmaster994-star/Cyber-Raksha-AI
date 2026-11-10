package com.cyberraksha.ai.domain.usecase

import com.cyberraksha.ai.core.AppPreferences
import com.cyberraksha.ai.data.repository.NotificationRepository
import io.mockk.coEvery
import io.mockk.coVerify
import io.mockk.mockk
import kotlinx.coroutines.runBlocking
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test

class SyncNotificationsUseCaseTest {

    private lateinit var notifRepo: NotificationRepository
    private lateinit var prefs: AppPreferences
    private lateinit var useCase: SyncNotificationsUseCase

    @Before
    fun setup() {
        notifRepo = mockk()
        prefs = mockk(relaxed = true)
        useCase = SyncNotificationsUseCase(notifRepo, prefs)
    }

    @Test
    fun `successful sync updates last sync timestamp and returns true`() = runBlocking {
        coEvery { notifRepo.syncFromBackend() } returns true

        val result = useCase()

        assertTrue(result)
        coVerify(exactly = 1) { prefs.updateLastSync() }
    }

    @Test
    fun `failed sync does not update timestamp and returns false`() = runBlocking {
        coEvery { notifRepo.syncFromBackend() } returns false

        val result = useCase()

        assertFalse(result)
        coVerify(exactly = 0) { prefs.updateLastSync() }
    }
}

